from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

STORAGE_DIR = Path(os.getenv("STORAGE_DIR", "/tmp/upscaler"))
OUTPUT_DIR = STORAGE_DIR / "outputs"
HISTORY_PATH = STORAGE_DIR / "jobs.json"
HISTORY_LIMIT = int(os.getenv("HISTORY_LIMIT", "100"))
JOB_TTL_HOURS = int(os.getenv("JOB_TTL_HOURS", "0"))

_history_lock = Lock()


def save_job_result(
    *,
    tool: str,
    source_filename: str | None,
    output_filename: str,
    data: bytes,
    input_metadata: dict[str, Any],
    output_width: int,
    output_height: int,
    output_format: str,
    engine: str,
    settings: dict[str, Any],
) -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    job_id = uuid.uuid4().hex
    created_at = datetime.now(timezone.utc).isoformat()
    stored_filename = f"{created_at[:10].replace('-', '')}-{job_id[:10]}-{_safe_filename(output_filename)}"
    path = OUTPUT_DIR / stored_filename
    path.write_bytes(data)

    entry = {
        "id": job_id,
        "created_at": created_at,
        "tool": tool,
        "source_filename": source_filename or "image",
        "filename": output_filename,
        "stored_filename": stored_filename,
        "download_url": f"/api/results/{job_id}",
        "input": {
            "width": int(input_metadata["width"]),
            "height": int(input_metadata["height"]),
            "mode": str(input_metadata["mode"]),
            "has_alpha": bool(input_metadata["has_alpha"]),
        },
        "output": {
            "width": int(output_width),
            "height": int(output_height),
            "format": output_format,
            "size_bytes": len(data),
        },
        "engine": engine,
        "settings": _json_safe(settings),
    }
    _append_history(entry)
    return entry


def list_jobs(limit: int = 25) -> list[dict[str, Any]]:
    _purge_expired_jobs()
    jobs = _read_history()
    return jobs[: max(1, min(int(limit), HISTORY_LIMIT))]


def delete_job(job_id: str) -> dict[str, Any] | None:
    with _history_lock:
        jobs = _read_history_unlocked()
        deleted_job: dict[str, Any] | None = None
        kept_jobs: list[dict[str, Any]] = []
        for job in jobs:
            if job.get("id") == job_id:
                deleted_job = job
            else:
                kept_jobs.append(job)

        if deleted_job is None:
            return None

        deleted_files = 1 if _delete_stored_file_unlocked(deleted_job) else 0
        _write_history_unlocked(kept_jobs)
        return {
            "deleted": True,
            "deleted_jobs": 1,
            "deleted_files": deleted_files,
            "job": deleted_job,
        }


def clear_jobs() -> dict[str, Any]:
    with _history_lock:
        jobs = _read_history_unlocked()
        deleted_files = 0
        for job in jobs:
            if _delete_stored_file_unlocked(job):
                deleted_files += 1
        _write_history_unlocked([])
        return {
            "deleted": True,
            "deleted_jobs": len(jobs),
            "deleted_files": deleted_files,
        }


def get_job(job_id: str) -> dict[str, Any] | None:
    _purge_expired_jobs()
    for job in _read_history():
        if job.get("id") == job_id:
            return job
    return None


def result_path(job_id: str) -> Path | None:
    job = get_job(job_id)
    if not job:
        return None
    stored_filename = str(job.get("stored_filename", ""))
    if not stored_filename or Path(stored_filename).name != stored_filename:
        return None
    path = OUTPUT_DIR / stored_filename
    if not path.exists() or not path.is_file():
        return None
    return path


def storage_summary() -> dict[str, Any]:
    _purge_expired_jobs()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    jobs = _read_history()
    total_bytes = 0
    for job in jobs:
        total_bytes += int(job.get("output", {}).get("size_bytes", 0) or 0)
    return {
        "output_dir": str(OUTPUT_DIR),
        "history_path": str(HISTORY_PATH),
        "history_limit": HISTORY_LIMIT,
        "job_ttl_hours": JOB_TTL_HOURS,
        "saved_jobs": len(jobs),
        "saved_bytes": total_bytes,
    }


def _purge_expired_jobs() -> None:
    if JOB_TTL_HOURS <= 0:
        return
    cutoff = datetime.now(timezone.utc).timestamp() - (JOB_TTL_HOURS * 3600)
    with _history_lock:
        jobs = _read_history_unlocked()
        kept: list[dict[str, Any]] = []
        for job in jobs:
            created_at = str(job.get("created_at", ""))
            try:
                created_ts = datetime.fromisoformat(created_at).timestamp()
            except ValueError:
                created_ts = 0
            if created_ts >= cutoff:
                kept.append(job)
            else:
                _delete_stored_file_unlocked(job)
        if len(kept) != len(jobs):
            _write_history_unlocked(kept)


def _append_history(entry: dict[str, Any]) -> None:
    with _history_lock:
        jobs = _read_history_unlocked()
        jobs.insert(0, entry)
        jobs = jobs[:HISTORY_LIMIT]
        _write_history_unlocked(jobs)


def _read_history() -> list[dict[str, Any]]:
    with _history_lock:
        return _read_history_unlocked()


def _read_history_unlocked() -> list[dict[str, Any]]:
    if not HISTORY_PATH.exists():
        return []
    try:
        data = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(data, list):
        return []
    return [job for job in data if isinstance(job, dict)]


def _write_history_unlocked(jobs: list[dict[str, Any]]) -> None:
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = HISTORY_PATH.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(jobs, indent=2), encoding="utf-8")
    tmp_path.replace(HISTORY_PATH)


def _delete_stored_file_unlocked(job: dict[str, Any]) -> bool:
    stored_filename = str(job.get("stored_filename", ""))
    if not stored_filename or Path(stored_filename).name != stored_filename:
        return False
    path = OUTPUT_DIR / stored_filename
    try:
        if path.exists() and path.is_file():
            path.unlink()
            return True
    except OSError:
        return False
    return False


def _safe_filename(filename: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9_.-]+", "-", filename).strip("-")
    return clean or "image.png"


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)
