from __future__ import annotations

from pathlib import Path
from typing import Any

from app.job_queue import (
    QUEUE_DIR,
    clear_job_meta,
    create_job_id,
    delete_job_meta,
    enqueue_single_job,
    get_raw_job,
    list_public_jobs,
    public_job,
    queued_source_path,
    refresh_job_from_rq,
    safe_filename,
    store_job,
    now,
)


def create_queued_job(
    *,
    filename: str,
    data: bytes,
    input_metadata: dict[str, Any],
    tool: str,
    settings: dict[str, Any],
) -> dict[str, Any]:
    job_id = create_job_id()
    created_at = now()
    source_name = safe_filename(filename or "image.png")
    source_dir = QUEUE_DIR / job_id / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    source_path = source_dir / source_name
    source_path.write_bytes(data)

    entry = store_job(
        {
            "id": job_id,
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
            "source_filename": source_name,
            "source_path": str(source_path),
            "input": input_metadata,
            "settings": settings,
            "error": None,
            "result_job_id": None,
            "rq_job_id": None,
            "worker_id": None,
        }
    )
    try:
        enqueue_single_job(job_id)
    except Exception as exc:
        from app.job_queue import update_job

        entry = update_job(
            job_id,
            {
                "status": "error",
                "phase": "queue-error",
                "message": "Could not enqueue job.",
                "current_progress": 100,
                "percent": 100,
                "finished_at": now(),
                "error": str(exc),
            },
        ) or entry
    raw = get_raw_job(job_id) or entry
    return public_job(raw)


def list_queued_jobs(limit: int = 25, include_done: bool = False) -> list[dict[str, Any]]:
    return list_public_jobs(limit, include_done)


def get_queued_job(job_id: str) -> dict[str, Any] | None:
    raw = refresh_job_from_rq(job_id)
    return public_job(raw) if raw else None


def retry_queued_job(job_id: str) -> dict[str, Any] | None:
    raw = refresh_job_from_rq(job_id)
    if not raw:
        return None
    status = str(raw.get("status") or "")
    if status in {"queued", "running"}:
        return public_job(raw)

    source = queued_source_path(job_id)
    if not source:
        return None
    return create_queued_job(
        filename=str(raw.get("source_filename") or Path(source).name),
        data=source.read_bytes(),
        input_metadata=dict(raw.get("input") or {}),
        tool=str(raw.get("tool") or "upscale"),
        settings=dict(raw.get("settings") or {}),
    )


def delete_queued_job(job_id: str) -> dict[str, Any] | None:
    return delete_job_meta(job_id)


def clear_queued_jobs() -> dict[str, Any]:
    return clear_job_meta()


def start_queued_workers() -> None:
    # Redis/RQ workers now run in a separate Docker service.
    return None
