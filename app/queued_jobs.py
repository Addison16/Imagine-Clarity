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


def reprocess_queued_job(
    job_id: str,
    *,
    quick_fix: str | None = None,
    settings: dict[str, Any] | None = None,
    tool: str | None = None,
) -> dict[str, Any] | None:
    raw = refresh_job_from_rq(job_id)
    if not raw:
        return None
    source = queued_source_path(job_id)
    if not source:
        return None

    next_tool = str(tool or raw.get("tool") or "upscale")
    next_settings = dict(settings or raw.get("settings") or {})
    if quick_fix:
        next_tool, next_settings = _apply_quick_fix(next_tool, next_settings, quick_fix)

    return create_queued_job(
        filename=str(raw.get("source_filename") or Path(source).name),
        data=source.read_bytes(),
        input_metadata=dict(raw.get("input") or {}),
        tool=next_tool,
        settings=next_settings,
    )


def delete_queued_job(job_id: str) -> dict[str, Any] | None:
    return delete_job_meta(job_id)


def clear_queued_jobs() -> dict[str, Any]:
    return clear_job_meta()


def start_queued_workers() -> None:
    # Redis/RQ workers now run in a separate Docker service.
    return None


def _apply_quick_fix(tool: str, settings: dict[str, Any], quick_fix: str) -> tuple[str, dict[str, Any]]:
    normalized = str(quick_fix or "").strip().lower().replace("_", "-")
    fixed = dict(settings)
    background = _background_settings(tool, fixed)
    upscale = _upscale_settings(tool, fixed)

    if normalized in {"fix-white-halo", "white-halo"}:
        if background is not None:
            background["edge_trim"] = _clamp_int(background.get("edge_trim"), 0, 8, bump=1, minimum=2)
            background["fringe_cleanup"] = _clamp_int(background.get("fringe_cleanup"), 0, 100, bump=20, minimum=55)
            background["background_tolerance"] = _clamp_int(background.get("background_tolerance"), 4, 96, bump=4)
            background["post_process_mask"] = True
            background["preserve_interior"] = True
        if upscale is not None:
            upscale["resize_method"] = "preserve"
            upscale["sharpen_amount"] = _clamp_int(upscale.get("sharpen_amount"), 0, 200, bump=-10)
        return tool, fixed

    if normalized in {"trim-edge-slightly", "trim-edge", "edge-trim"}:
        if background is not None:
            background["edge_trim"] = _clamp_int(background.get("edge_trim"), 0, 8, bump=1, minimum=1)
            background["edge_refine"] = _clamp_int(background.get("edge_refine"), 0, 20, bump=2)
            background["fringe_cleanup"] = _clamp_int(background.get("fringe_cleanup"), 0, 100, bump=10)
        return tool, fixed

    if normalized in {"preserve-more-detail", "preserve-detail"}:
        if background is not None:
            background["cut_mode"] = "preserve"
            background["alpha_matting"] = False
            background["post_process_mask"] = False
            background["preserve_interior"] = True
            background["edge_trim"] = _clamp_int(background.get("edge_trim"), 0, 8, bump=-1)
            background["fringe_cleanup"] = _clamp_int(background.get("fringe_cleanup"), 0, 100, bump=-25)
            background["inner_cleanup"] = _clamp_int(background.get("inner_cleanup"), 0, 100, bump=-20)
            background["background_tolerance"] = _clamp_int(background.get("background_tolerance"), 4, 96, bump=-10)
        if upscale is not None:
            upscale["mode"] = "conservative"
            upscale["denoise"] = _clamp_float(upscale.get("denoise"), 0.0, 1.0, bump=-0.1)
            upscale["sharpen_amount"] = _clamp_int(upscale.get("sharpen_amount"), 0, 200, bump=-10)
        return tool, fixed

    if normalized in {"stronger-background-cut", "stronger-cut", "strong-cut"}:
        if background is not None:
            background["cut_mode"] = "strong"
            background["edge_refine"] = _clamp_int(background.get("edge_refine"), 0, 20, bump=6, minimum=12)
            background["edge_trim"] = _clamp_int(background.get("edge_trim"), 0, 8, bump=1, minimum=2)
            background["fringe_cleanup"] = _clamp_int(background.get("fringe_cleanup"), 0, 100, bump=25, minimum=70)
            background["inner_cleanup"] = _clamp_int(background.get("inner_cleanup"), 0, 100, bump=25, minimum=55)
            background["background_tolerance"] = _clamp_int(background.get("background_tolerance"), 4, 96, bump=12, minimum=46)
            background["post_process_mask"] = True
            background["preserve_interior"] = False
        return tool, fixed

    raise ValueError(f"Unknown quick fix: {quick_fix}")


def _background_settings(tool: str, settings: dict[str, Any]) -> dict[str, Any] | None:
    if tool == "remove-background-upscale":
        background = dict(settings.get("background") or {})
        settings["background"] = background
        return background
    if tool == "remove-background":
        return settings
    return None


def _upscale_settings(tool: str, settings: dict[str, Any]) -> dict[str, Any] | None:
    if tool == "remove-background-upscale":
        upscale = dict(settings.get("upscale") or {})
        settings["upscale"] = upscale
        return upscale
    if tool == "upscale":
        return settings
    return None


def _clamp_int(value: object, low: int, high: int, *, bump: int = 0, minimum: int | None = None) -> int:
    try:
        current = int(float(value))
    except (TypeError, ValueError):
        current = minimum if minimum is not None else low
    next_value = current + bump
    if minimum is not None:
        next_value = max(next_value, minimum)
    return max(low, min(high, next_value))


def _clamp_float(value: object, low: float, high: float, *, bump: float = 0.0) -> float:
    try:
        current = float(value)
    except (TypeError, ValueError):
        current = low
    return max(low, min(high, round(current + bump, 3)))
