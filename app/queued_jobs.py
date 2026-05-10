from __future__ import annotations

import json
import io
import os
import shutil
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image

from app.background import BackgroundOptions, remove_background
from app.jobs import get_job, save_job_result
from app.upscaler import UpscaleOptions, upscale_image

STORAGE_DIR = Path(os.getenv("STORAGE_DIR", "/tmp/upscaler"))
QUEUE_DIR = STORAGE_DIR / "queued"
QUEUE_PATH = STORAGE_DIR / "queued_jobs.json"
QUEUE_HISTORY_LIMIT = int(os.getenv("QUEUE_HISTORY_LIMIT", "100"))
QUEUE_WORKERS = max(1, int(os.getenv("QUEUE_WORKERS", "1")))

_lock = threading.Lock()
_executor = ThreadPoolExecutor(max_workers=QUEUE_WORKERS, thread_name_prefix="single-job-worker")
_active_jobs: set[str] = set()


def create_queued_job(
    *,
    filename: str,
    data: bytes,
    input_metadata: dict[str, Any],
    tool: str,
    settings: dict[str, Any],
) -> dict[str, Any]:
    job_id = uuid.uuid4().hex
    created_at = _now()
    safe_name = _safe_filename(filename or "image.png")
    source_dir = QUEUE_DIR / job_id / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    source_path = source_dir / safe_name
    source_path.write_bytes(data)

    entry = {
        "id": job_id,
        "created_at": created_at,
        "updated_at": created_at,
        "status": "queued",
        "progress": 0,
        "tool": tool,
        "source_filename": safe_name,
        "source_path": str(source_path),
        "input": _json_safe(input_metadata),
        "settings": _json_safe(settings),
        "error": None,
        "result_job_id": None,
    }
    with _lock:
        jobs = _read_jobs_unlocked()
        jobs.insert(0, entry)
        overflow = jobs[QUEUE_HISTORY_LIMIT:]
        for old_job in overflow:
            _delete_queued_source_unlocked(str(old_job.get("id") or ""))
        _write_jobs_unlocked(jobs[:QUEUE_HISTORY_LIMIT])

    _submit_job(job_id)
    return _public_job(entry)


def list_queued_jobs(limit: int = 25, include_done: bool = False) -> list[dict[str, Any]]:
    with _lock:
        jobs = _read_jobs_unlocked()
    visible = [job for job in jobs if include_done or job.get("status") != "done"]
    return [_public_job(job) for job in visible[: max(1, min(int(limit), QUEUE_HISTORY_LIMIT))]]


def get_queued_job(job_id: str) -> dict[str, Any] | None:
    raw = _get_raw_job(job_id)
    return _public_job(raw) if raw else None


def retry_queued_job(job_id: str) -> dict[str, Any] | None:
    raw = _get_raw_job(job_id)
    if not raw:
        return None
    status = str(raw.get("status") or "")
    if status in {"queued", "running"}:
        return _public_job(raw)

    source = queued_source_path(job_id)
    if not source:
        return None
    return create_queued_job(
        filename=str(raw.get("source_filename") or source.name),
        data=source.read_bytes(),
        input_metadata=dict(raw.get("input") or {}),
        tool=str(raw.get("tool") or "upscale"),
        settings=dict(raw.get("settings") or {}),
    )


def delete_queued_job(job_id: str) -> dict[str, Any] | None:
    with _lock:
        jobs = _read_jobs_unlocked()
        deleted: dict[str, Any] | None = None
        kept: list[dict[str, Any]] = []
        for job in jobs:
            if job.get("id") == job_id:
                deleted = job
            else:
                kept.append(job)

        if not deleted:
            return None
        if deleted.get("status") == "running":
            return {"deleted": False, "reason": "running", "job": _public_job(deleted)}

        _delete_queued_source_unlocked(job_id)
        _write_jobs_unlocked(kept)
        return {"deleted": True, "deleted_jobs": 1, "deleted_files": 1, "job": _public_job(deleted)}


def clear_queued_jobs() -> dict[str, Any]:
    with _lock:
        jobs = _read_jobs_unlocked()
        kept: list[dict[str, Any]] = []
        deleted = 0
        for job in jobs:
            job_id = str(job.get("id") or "")
            if job.get("status") == "running":
                kept.append(job)
                continue
            _delete_queued_source_unlocked(job_id)
            deleted += 1
        _write_jobs_unlocked(kept)
    return {"deleted_jobs": deleted, "kept_running": len(kept)}


def queued_source_path(job_id: str) -> Path | None:
    raw = _get_raw_job(job_id)
    if not raw:
        return None
    source = Path(str(raw.get("source_path", "")))
    source_dir = QUEUE_DIR / job_id / "source"
    try:
        if source.exists() and source.is_file() and source.resolve().is_relative_to(source_dir.resolve()):
            return source
    except (OSError, ValueError):
        return None
    return None


def start_queued_workers() -> None:
    with _lock:
        jobs = _read_jobs_unlocked()
        pending_ids: list[str] = []
        changed = False
        for job in jobs:
            if job.get("status") in {"queued", "running"}:
                job["status"] = "queued"
                job["progress"] = int(job.get("progress") or 0)
                job["updated_at"] = _now()
                pending_ids.append(str(job.get("id")))
                changed = True
        if changed:
            _write_jobs_unlocked(jobs)

    for job_id in pending_ids:
        _submit_job(job_id)


def _submit_job(job_id: str) -> None:
    with _lock:
        if job_id in _active_jobs:
            return
        _active_jobs.add(job_id)
    _executor.submit(_process_queued_job, job_id)


def _process_queued_job(job_id: str) -> None:
    try:
        _update_job(job_id, {"status": "running", "progress": 5, "started_at": _now(), "error": None})
        raw = _get_raw_job(job_id)
        if not raw:
            return
        source = Path(str(raw.get("source_path", "")))
        data = source.read_bytes()
        _update_job(job_id, {"progress": 15})
        result, settings = _process_one(
            data=data,
            filename=str(raw.get("source_filename") or source.name),
            tool=str(raw.get("tool") or "upscale"),
            settings=dict(raw.get("settings") or {}),
            input_metadata=dict(raw.get("input") or {}),
        )
        _update_job(job_id, {"progress": 90})
        saved = save_job_result(
            tool=str(raw.get("tool") or "upscale"),
            source_filename=str(raw.get("source_filename") or source.name),
            output_filename=result["filename"],
            data=result["data"],
            input_metadata=result["input_metadata"],
            output_width=result["width"],
            output_height=result["height"],
            output_format=result["extension"],
            engine=result["engine"],
            settings=settings,
            source_data=data,
        )
        _update_job(
            job_id,
            {
                "status": "done",
                "progress": 100,
                "finished_at": _now(),
                "result_job_id": saved["id"],
                "result_filename": saved["filename"],
                "result_download_url": saved["download_url"],
                "result_source_url": saved.get("source_download_url"),
                "output": saved["output"],
                "engine": saved["engine"],
                "error": None,
            },
        )
    except Exception as exc:
        _update_job(job_id, {"status": "error", "progress": 100, "finished_at": _now(), "error": str(exc)})
    finally:
        with _lock:
            _active_jobs.discard(job_id)


def _process_one(
    *,
    data: bytes,
    filename: str,
    tool: str,
    settings: dict[str, Any],
    input_metadata: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    metadata = _metadata_for(data, input_metadata)
    stem = Path(filename).stem

    if tool == "remove-background":
        bg = BackgroundOptions(**settings)
        result = remove_background(data, bg)
        return (
            {
                "data": result.data,
                "width": result.width,
                "height": result.height,
                "extension": result.extension,
                "engine": result.engine,
                "filename": f"{stem}-transparent.{result.extension}",
                "input_metadata": metadata,
            },
            asdict(bg),
        )

    if tool == "remove-background-upscale":
        bg = BackgroundOptions(**dict(settings.get("background") or {}))
        up = UpscaleOptions(**dict(settings.get("upscale") or {}))
        background = remove_background(data, bg)
        result = upscale_image(background.data, up)
        return (
            {
                "data": result.data,
                "width": result.width,
                "height": result.height,
                "extension": result.extension,
                "engine": f"{background.engine} -> {result.engine}",
                "filename": f"{stem}-transparent-upscaled-{result.width}x{result.height}.{result.extension}",
                "input_metadata": metadata,
            },
            {"background": asdict(bg), "upscale": asdict(up)},
        )

    up = UpscaleOptions(**settings)
    result = upscale_image(data, up)
    return (
        {
            "data": result.data,
            "width": result.width,
            "height": result.height,
            "extension": result.extension,
            "engine": result.engine,
            "filename": f"{stem}-upscaled-{result.width}x{result.height}.{result.extension}",
            "input_metadata": metadata,
        },
        asdict(up),
    )


def _metadata_for(data: bytes, fallback: dict[str, Any]) -> dict[str, Any]:
    if fallback.get("width") and fallback.get("height"):
        return fallback
    with Image.open(io.BytesIO(data)) as image:
        return {"width": image.width, "height": image.height, "mode": image.mode, "has_alpha": "A" in image.getbands()}


def _get_raw_job(job_id: str) -> dict[str, Any] | None:
    with _lock:
        for job in _read_jobs_unlocked():
            if job.get("id") == job_id:
                return job
    return None


def _update_job(job_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
    with _lock:
        jobs = _read_jobs_unlocked()
        for index, job in enumerate(jobs):
            if job.get("id") == job_id:
                job.update(_json_safe(patch))
                job["updated_at"] = _now()
                jobs[index] = job
                _write_jobs_unlocked(jobs)
                return job
    return None


def _public_job(job: dict[str, Any]) -> dict[str, Any]:
    job_id = str(job.get("id") or "")
    public = {
        "id": job_id,
        "queue_job_id": job_id,
        "kind": "queued",
        "created_at": job.get("created_at"),
        "updated_at": job.get("updated_at"),
        "started_at": job.get("started_at"),
        "finished_at": job.get("finished_at"),
        "status": job.get("status") or "queued",
        "progress": int(job.get("progress") or 0),
        "tool": job.get("tool") or "upscale",
        "source_filename": job.get("source_filename") or "image",
        "source_url": f"/api/jobs/{job_id}/source" if job_id else None,
        "error": job.get("error"),
    }
    if job.get("input"):
        public["input"] = job["input"]
    if job.get("output"):
        public["output"] = job["output"]
    if job.get("engine"):
        public["engine"] = job["engine"]
    if job.get("result_job_id"):
        public["result_job_id"] = job["result_job_id"]
        public["download_url"] = job.get("result_download_url")
        public["source_download_url"] = job.get("result_source_url")
        public["filename"] = job.get("result_filename")
        saved = get_job(str(job["result_job_id"]))
        if saved:
            public.update(
                {
                    "download_url": saved.get("download_url"),
                    "source_download_url": saved.get("source_download_url"),
                    "filename": saved.get("filename"),
                    "output": saved.get("output"),
                    "engine": saved.get("engine"),
                }
            )
    return public


def _read_jobs_unlocked() -> list[dict[str, Any]]:
    if not QUEUE_PATH.exists():
        return []
    try:
        data = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(data, list):
        return []
    return [job for job in data if isinstance(job, dict)]


def _write_jobs_unlocked(jobs: list[dict[str, Any]]) -> None:
    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = QUEUE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(jobs, indent=2), encoding="utf-8")
    tmp.replace(QUEUE_PATH)


def _delete_queued_source_unlocked(job_id: str) -> None:
    if not job_id or Path(job_id).name != job_id:
        return
    path = QUEUE_DIR / job_id
    try:
        if path.exists() and path.is_dir():
            shutil.rmtree(path)
    except OSError:
        return


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_filename(filename: str) -> str:
    import re

    clean = re.sub(r"[^A-Za-z0-9_.-]+", "-", Path(filename).name).strip("-")
    return clean or "image.png"


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)
