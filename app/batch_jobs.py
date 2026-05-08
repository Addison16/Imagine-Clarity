from __future__ import annotations

import io
import json
import os
import shutil
import threading
import time
import uuid
import zipfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.background import BackgroundOptions, remove_background
from app.jobs import save_job_result
from app.upscaler import UpscaleOptions, upscale_image

STORAGE_DIR = Path(os.getenv("STORAGE_DIR", "/tmp/upscaler"))
BATCH_DIR = STORAGE_DIR / "batches"
BATCH_HISTORY = STORAGE_DIR / "batches.json"
BATCH_HISTORY_LIMIT = int(os.getenv("BATCH_HISTORY_LIMIT", "50"))

_lock = threading.Lock()
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="batch-worker")


@dataclass
class BatchItem:
    id: str
    filename: str
    source_path: str
    status: str = "queued"
    error: str | None = None
    result_job_id: str | None = None
    result_filename: str | None = None
    result_download_url: str | None = None



def _read_batches() -> list[dict[str, Any]]:
    if not BATCH_HISTORY.exists():
        return []
    try:
        data = json.loads(BATCH_HISTORY.read_text(encoding="utf-8"))
    except Exception:
        return []
    return data if isinstance(data, list) else []


def _write_batches(data: list[dict[str, Any]]) -> None:
    BATCH_HISTORY.parent.mkdir(parents=True, exist_ok=True)
    tmp = BATCH_HISTORY.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(BATCH_HISTORY)


def _update_batch(batch_id: str, mutator) -> dict[str, Any] | None:
    with _lock:
        batches = _read_batches()
        for idx, batch in enumerate(batches):
            if batch.get("id") == batch_id:
                mutator(batch)
                batches[idx] = batch
                _write_batches(batches)
                return batch
    return None


def list_batches(limit: int = 10) -> list[dict[str, Any]]:
    with _lock:
        return [_public_batch(batch) for batch in _read_batches()[: max(1, min(limit, 100))]]


def get_batch(batch_id: str) -> dict[str, Any] | None:
    with _lock:
        for batch in _read_batches():
            if batch.get("id") == batch_id:
                return _public_batch(batch)
    return None


def get_batch_raw(batch_id: str) -> dict[str, Any] | None:
    with _lock:
        for batch in _read_batches():
            if batch.get("id") == batch_id:
                return batch
    return None


def create_batch(files: list[tuple[str, bytes]], tool: str, settings: dict[str, Any]) -> dict[str, Any]:
    batch_id = uuid.uuid4().hex
    created_at = datetime.now(timezone.utc).isoformat()
    source_dir = BATCH_DIR / batch_id / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    items: list[dict[str, Any]] = []
    for idx, (filename, data) in enumerate(files):
        item_id = f"{idx+1:04d}"
        safe_name = Path(filename or f"image-{item_id}.png").name
        path = source_dir / f"{item_id}-{safe_name}"
        path.write_bytes(data)
        items.append(asdict(BatchItem(id=item_id, filename=safe_name, source_path=str(path))))

    entry = {
        "id": batch_id,
        "created_at": created_at,
        "status": "queued",
        "tool": tool,
        "settings": settings,
        "items": items,
        "completed": 0,
        "failed": 0,
        "total": len(items),
    }
    with _lock:
        batches = _read_batches()
        batches.insert(0, entry)
        overflow = batches[BATCH_HISTORY_LIMIT:]
        for old_batch in overflow:
            _delete_batch_sources(str(old_batch.get("id") or ""))
        batches = batches[:BATCH_HISTORY_LIMIT]
        _write_batches(batches)

    _executor.submit(_process_batch, batch_id)
    return _public_batch(entry)


def retry_batch(batch_id: str, failed_only: bool = True) -> dict[str, Any] | None:
    original = get_batch_raw(batch_id)
    if not original:
        return None
    files: list[tuple[str, bytes]] = []
    for item in original.get("items", []):
        status = item.get("status")
        if failed_only and status != "error":
            continue
        source = Path(str(item.get("source_path", "")))
        if source.exists() and source.is_file():
            files.append((str(item.get("filename") or source.name), source.read_bytes()))
    if not files:
        return None
    return create_batch(files, str(original.get("tool") or "upscale"), dict(original.get("settings") or {}))


def _process_batch(batch_id: str) -> None:
    _update_batch(batch_id, lambda b: b.update({"status": "running", "started_at": datetime.now(timezone.utc).isoformat()}))
    batch = get_batch_raw(batch_id)
    if not batch:
        return
    for item in batch.get("items", []):
        _update_item(batch_id, item["id"], {"status": "running"})
        try:
            src = Path(item["source_path"]).read_bytes()
            result, tool_name, settings = _process_one(src, item["filename"], batch["tool"], batch.get("settings", {}))
            job = save_job_result(
                tool=tool_name,
                source_filename=item["filename"],
                output_filename=result["filename"],
                data=result["data"],
                input_metadata=result["input_metadata"],
                output_width=result["width"],
                output_height=result["height"],
                output_format=result["extension"],
                engine=result["engine"],
                settings=settings,
            )
            _update_item(batch_id, item["id"], {
                "status": "done",
                "result_job_id": job["id"],
                "result_filename": job["filename"],
                "result_download_url": job["download_url"],
            })
        except Exception as exc:
            _update_item(batch_id, item["id"], {"status": "error", "error": str(exc)})
    _finish_batch(batch_id)


def _update_item(batch_id: str, item_id: str, patch: dict[str, Any]) -> None:
    def mutate(batch):
        for item in batch.get("items", []):
            if item.get("id") == item_id:
                item.update(patch)
        done = sum(1 for i in batch.get("items", []) if i.get("status") == "done")
        err = sum(1 for i in batch.get("items", []) if i.get("status") == "error")
        batch["completed"] = done
        batch["failed"] = err

    _update_batch(batch_id, mutate)


def _finish_batch(batch_id: str) -> None:
    def mutate(batch):
        total = batch.get("total", 0)
        done = batch.get("completed", 0)
        failed = batch.get("failed", 0)
        batch["status"] = "completed" if done + failed >= total else "running"
        batch["finished_at"] = datetime.now(timezone.utc).isoformat()

    _update_batch(batch_id, mutate)


def build_batch_zip(batch_id: str) -> tuple[bytes, str] | None:
    batch = get_batch_raw(batch_id)
    if not batch:
        return None
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for item in batch.get("items", []):
            url = item.get("result_download_url")
            if not url:
                continue
            job_id = str(url).split("/")[-1]
            from app.jobs import result_path
            path = result_path(job_id)
            if path and path.exists():
                zf.write(path, arcname=Path(item.get("result_filename") or path.name).name)
    return stream.getvalue(), f"batch-{batch_id[:8]}.zip"


def batch_source_path(batch_id: str, item_id: str) -> Path | None:
    batch = get_batch_raw(batch_id)
    if not batch:
        return None
    for item in batch.get("items", []):
        if str(item.get("id")) != str(item_id):
            continue
        source = Path(str(item.get("source_path", "")))
        batch_dir = BATCH_DIR / batch_id / "source"
        try:
            if source.exists() and source.is_file() and source.resolve().is_relative_to(batch_dir.resolve()):
                return source
        except (OSError, ValueError):
            return None
    return None


def _delete_batch_sources(batch_id: str) -> None:
    if not batch_id or Path(batch_id).name != batch_id:
        return
    batch_dir = BATCH_DIR / batch_id
    try:
        if batch_dir.exists() and batch_dir.is_dir():
            shutil.rmtree(batch_dir)
    except OSError:
        return


def _process_one(raw: bytes, filename: str, tool: str, settings: dict[str, Any]):
    from PIL import Image
    import io as _io
    img = Image.open(_io.BytesIO(raw))
    metadata = {"width": img.width, "height": img.height, "mode": img.mode, "has_alpha": "A" in img.getbands()}
    stem = Path(filename).stem
    if tool == "remove-background":
        bg = BackgroundOptions(**settings)
        r = remove_background(raw, bg)
        return ({"data": r.data, "width": r.width, "height": r.height, "extension": r.extension, "engine": r.engine, "filename": f"{stem}-transparent.{r.extension}", "input_metadata": metadata}, tool, asdict(bg))
    if tool == "remove-background-upscale":
        bg = BackgroundOptions(**settings["background"])
        up = UpscaleOptions(**settings["upscale"])
        b = remove_background(raw, bg)
        r = upscale_image(b.data, up)
        return ({"data": r.data, "width": r.width, "height": r.height, "extension": r.extension, "engine": f"{b.engine} -> {r.engine}", "filename": f"{stem}-transparent-upscaled.{r.extension}", "input_metadata": metadata}, tool, {"background": asdict(bg), "upscale": asdict(up)})
    up = UpscaleOptions(**settings)
    r = upscale_image(raw, up)
    return ({"data": r.data, "width": r.width, "height": r.height, "extension": r.extension, "engine": r.engine, "filename": f"{stem}-upscaled.{r.extension}", "input_metadata": metadata}, tool, asdict(up))


def _public_batch(batch: dict[str, Any]) -> dict[str, Any]:
    redacted = dict(batch)
    batch_id = str(redacted.get("id") or "")
    redacted["zip_url"] = f"/api/batches/{batch_id}/zip" if batch_id else None
    redacted.pop("settings", None)
    items: list[dict[str, Any]] = []
    for item in batch.get("items", []):
        clean = dict(item)
        item_id = str(clean.get("id") or "")
        if batch_id and item_id:
            clean["source_url"] = f"/api/batches/{batch_id}/source/{item_id}"
        clean.pop("source_path", None)
        items.append(clean)
    redacted["items"] = items
    return redacted
