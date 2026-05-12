from __future__ import annotations

import io
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable

from PIL import Image
from rq import get_current_job

from app.background import BackgroundOptions, remove_background
from app.job_queue import (
    get_raw_batch,
    get_raw_job,
    now,
    update_batch,
    update_batch_item,
    update_job,
)
from app.jobs import save_job_result
from app.upscaler import UpscaleOptions, upscale_image

ProgressCallback = Callable[[int, str, str], None]


def process_single_job(job_id: str) -> None:
    worker_id = _worker_id()
    try:
        _job_progress(job_id, 8, "preflight", "Worker accepted the job.", status="running", worker_id=worker_id, started=True, error=None)
        raw_job = get_raw_job(job_id)
        if not raw_job:
            return
        source = Path(str(raw_job.get("source_path", "")))
        data = source.read_bytes()
        tool = str(raw_job.get("tool") or "upscale")
        filename = str(raw_job.get("source_filename") or source.name)

        _job_progress(job_id, 12, "preflight", "Checking image and settings.")
        result, settings = _process_one(
            data=data,
            filename=filename,
            tool=tool,
            settings=dict(raw_job.get("settings") or {}),
            input_metadata=dict(raw_job.get("input") or {}),
            progress=lambda percent, phase, message: _job_progress(job_id, percent, phase, message),
        )
        _job_progress(job_id, 94, "save", "Saving result and updating history.")
        saved = save_job_result(
            tool=tool,
            source_filename=filename,
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
        update_job(
            job_id,
            {
                "status": "done",
                "phase": "complete",
                "message": "Complete. Your image is ready.",
                "current_progress": 100,
                "max_progress": 100,
                "percent": 100,
                "finished_at": now(),
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
        update_job(
            job_id,
            {
                "status": "error",
                "phase": "failed",
                "message": "Processing failed.",
                "current_progress": 100,
                "max_progress": 100,
                "percent": 100,
                "finished_at": now(),
                "worker_id": worker_id,
                "error": str(exc),
            },
        )
        raise


def process_batch_job(batch_id: str) -> None:
    worker_id = _worker_id()
    try:
        _batch_progress(batch_id, 8, "preflight", "Worker accepted the batch.", status="running", worker_id=worker_id, started=True, error=None)
        batch = get_raw_batch(batch_id)
        if not batch:
            return
        items = list(batch.get("items") or [])
        total = max(1, len(items))
        for index, item in enumerate(items):
            item_id = str(item.get("id") or "")
            filename = str(item.get("filename") or f"image-{item_id}.png")
            update_batch_item(batch_id, item_id, {"status": "running", "progress": 0, "percent": 0, "error": None})

            def item_progress(percent: int, phase: str, message: str) -> None:
                overall = int(round(((index + (percent / 100.0)) / total) * 100))
                update_batch_item(batch_id, item_id, {"progress": percent, "percent": percent, "phase": phase, "message": message})
                _batch_progress(
                    batch_id,
                    overall,
                    phase,
                    f"{filename}: {message}",
                    current_item_id=item_id,
                    current_item_filename=filename,
                )

            try:
                source = Path(str(item.get("source_path", "")))
                data = source.read_bytes()
                item_progress(8, "preflight", "Checking image and settings.")
                result, settings = _process_one(
                    data=data,
                    filename=filename,
                    tool=str(batch.get("tool") or "upscale"),
                    settings=dict(batch.get("settings") or {}),
                    input_metadata={},
                    progress=item_progress,
                )
                item_progress(94, "save", "Saving result.")
                saved = save_job_result(
                    tool=str(batch.get("tool") or "upscale"),
                    source_filename=filename,
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
                update_batch_item(
                    batch_id,
                    item_id,
                    {
                        "status": "done",
                        "progress": 100,
                        "percent": 100,
                        "phase": "complete",
                        "message": "Complete.",
                        "result_job_id": saved["id"],
                        "result_filename": saved["filename"],
                        "result_download_url": saved["download_url"],
                    },
                )
            except Exception as exc:
                overall = int(round(((index + 1) / total) * 100))
                update_batch_item(
                    batch_id,
                    item_id,
                    {
                        "status": "error",
                        "progress": 100,
                        "percent": 100,
                        "phase": "failed",
                        "message": "Processing failed.",
                        "error": str(exc),
                    },
                )
                _batch_progress(
                    batch_id,
                    overall,
                    "failed",
                    f"{filename}: Processing failed.",
                    current_item_id=item_id,
                    current_item_filename=filename,
                )
        finished = get_raw_batch(batch_id) or batch
        completed = int(finished.get("completed") or 0)
        failed = int(finished.get("failed") or 0)
        update_batch(
            batch_id,
            {
                "status": "done",
                "phase": "complete",
                "message": f"Batch complete. {completed} finished, {failed} failed.",
                "current_progress": 100,
                "max_progress": 100,
                "percent": 100,
                "finished_at": now(),
                "worker_id": worker_id,
            },
        )
    except Exception as exc:
        update_batch(
            batch_id,
            {
                "status": "error",
                "phase": "failed",
                "message": "Batch worker failed.",
                "current_progress": 100,
                "max_progress": 100,
                "percent": 100,
                "finished_at": now(),
                "worker_id": worker_id,
                "error": str(exc),
            },
        )
        raise


def _process_one(
    *,
    data: bytes,
    filename: str,
    tool: str,
    settings: dict[str, Any],
    input_metadata: dict[str, Any],
    progress: ProgressCallback,
) -> tuple[dict[str, Any], dict[str, Any]]:
    metadata = _metadata_for(data, input_metadata)
    stem = Path(filename).stem

    if tool == "remove-background":
        bg = BackgroundOptions(**settings)
        progress(18, "background", "Removing background.")
        result = remove_background(data, bg)
        progress(88, "encode", "Encoding transparent result.")
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
        progress(18, "background", "Removing background.")
        background = remove_background(data, bg)
        progress(55, "upscale", "Background removed. Upscaling transparent image.")
        result = upscale_image(background.data, up)
        progress(88, "encode", "Encoding upscaled transparent result.")
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
    progress(18, "upscale", "Upscaling and resizing image.")
    result = upscale_image(data, up)
    progress(88, "encode", "Encoding upscaled result.")
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


def _job_progress(
    job_id: str,
    percent: int,
    phase: str,
    message: str,
    *,
    status: str = "running",
    started: bool = False,
    worker_id: str | None = None,
    error: str | None = None,
) -> None:
    patch: dict[str, Any] = {
        "status": status,
        "phase": phase,
        "message": message,
        "current_progress": percent,
        "max_progress": 100,
        "percent": percent,
        "error": error,
    }
    if worker_id:
        patch["worker_id"] = worker_id
    if started:
        patch["started_at"] = now()
    update_job(job_id, patch)


def _batch_progress(
    batch_id: str,
    percent: int,
    phase: str,
    message: str,
    *,
    status: str = "running",
    started: bool = False,
    worker_id: str | None = None,
    error: str | None = None,
    current_item_id: str | None = None,
    current_item_filename: str | None = None,
) -> None:
    patch: dict[str, Any] = {
        "status": status,
        "phase": phase,
        "message": message,
        "current_progress": percent,
        "max_progress": 100,
        "percent": percent,
        "error": error,
    }
    if worker_id:
        patch["worker_id"] = worker_id
    if started:
        patch["started_at"] = now()
    if current_item_id:
        patch["current_item_id"] = current_item_id
    if current_item_filename:
        patch["current_item_filename"] = current_item_filename
    update_batch(batch_id, patch)


def _worker_id() -> str:
    current = get_current_job()
    if current is not None and getattr(current, "worker_name", None):
        return str(current.worker_name)
    return os.getenv("HOSTNAME", "worker")
