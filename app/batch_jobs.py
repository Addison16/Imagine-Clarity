from __future__ import annotations

import io
import zipfile
from pathlib import Path
from typing import Any

from app.job_queue import (
    BATCH_DIR,
    batch_source_path,
    create_batch_id,
    enqueue_batch_job,
    get_raw_batch,
    list_public_batches,
    public_batch,
    refresh_batch_from_rq,
    safe_filename,
    store_batch,
    now,
)


def list_batches(limit: int = 10) -> list[dict[str, Any]]:
    return list_public_batches(limit)


def get_batch(batch_id: str) -> dict[str, Any] | None:
    raw = refresh_batch_from_rq(batch_id)
    return public_batch(raw) if raw else None


def get_batch_raw(batch_id: str) -> dict[str, Any] | None:
    return get_raw_batch(batch_id)


def create_batch(files: list[tuple[str, bytes]], tool: str, settings: dict[str, Any]) -> dict[str, Any]:
    batch_id = create_batch_id()
    created_at = now()
    source_dir = BATCH_DIR / batch_id / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    items: list[dict[str, Any]] = []
    for index, (filename, data) in enumerate(files):
        item_id = f"{index + 1:04d}"
        source_name = safe_filename(filename or f"image-{item_id}.png")
        path = source_dir / f"{item_id}-{source_name}"
        path.write_bytes(data)
        items.append(
            {
                "id": item_id,
                "filename": source_name,
                "source_path": str(path),
                "status": "queued",
                "phase": "queued",
                "message": "Waiting for a worker.",
                "progress": 0,
                "percent": 0,
                "error": None,
                "result_job_id": None,
                "result_filename": None,
                "result_download_url": None,
            }
        )

    entry = store_batch(
        {
            "id": batch_id,
            "created_at": created_at,
            "updated_at": created_at,
            "status": "queued",
            "phase": "upload",
            "message": "Upload accepted. Waiting for a worker.",
            "current_progress": 5,
            "max_progress": 100,
            "percent": 5,
            "progress": 5,
            "tool": tool,
            "settings": settings,
            "items": items,
            "completed": 0,
            "failed": 0,
            "total": len(items),
            "rq_job_id": None,
            "worker_id": None,
            "error": None,
        }
    )
    try:
        enqueue_batch_job(batch_id)
    except Exception as exc:
        from app.job_queue import update_batch

        entry = update_batch(
            batch_id,
            {
                "status": "error",
                "phase": "queue-error",
                "message": "Could not enqueue batch.",
                "current_progress": 100,
                "percent": 100,
                "finished_at": now(),
                "error": str(exc),
            },
        ) or entry
    raw = get_raw_batch(batch_id) or entry
    return public_batch(raw)


def retry_batch(batch_id: str, failed_only: bool = True) -> dict[str, Any] | None:
    original = get_raw_batch(batch_id)
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


def build_batch_zip(batch_id: str) -> tuple[bytes, str] | None:
    batch = get_raw_batch(batch_id)
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
