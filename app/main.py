from __future__ import annotations

import io
import hmac
import logging
import os
import re
import time
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, UnidentifiedImageError
from starlette.concurrency import run_in_threadpool

from app.background import (
    BACKGROUND_CUT_MODES,
    BACKGROUND_MODELS,
    SUPPORTED_BG_FORMATS,
    BackgroundOptions,
    remove_background,
)
from app.jobs import (
    HISTORY_LIMIT,
    clear_jobs,
    delete_job,
    get_job,
    list_jobs,
    result_path,
    save_job_result,
    source_path,
    storage_summary,
)
from app.batch_jobs import batch_source_path, build_batch_zip, create_batch, get_batch, list_batches, retry_batch
from app.queued_jobs import (
    clear_queued_jobs,
    create_queued_job,
    delete_queued_job,
    get_queued_job,
    list_queued_jobs,
    queued_source_path,
    retry_queued_job,
    start_queued_workers,
)
from app.upscaler import SUPPORTED_FORMATS, UpscaleOptions, resolve_upscale_sizes, upscale_image

APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "64"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
MAX_IMAGE_DIMENSION = int(os.getenv("MAX_IMAGE_DIMENSION", "16384"))
MAX_UPSCALE_FACTOR = 8.0
MAX_BATCH_FILES = int(os.getenv("MAX_BATCH_FILES", "100"))
MAX_BATCH_TOTAL_MB = int(os.getenv("MAX_BATCH_TOTAL_MB", "512"))
MAX_BATCH_TOTAL_BYTES = MAX_BATCH_TOTAL_MB * 1024 * 1024
API_KEY = os.getenv("CLARITY_API_KEY", "").strip()
CORS_ORIGINS = [origin.strip() for origin in os.getenv("CORS_ALLOW_ORIGINS", "*").split(",") if origin.strip()]
SUPPORTED_TOOLS = ("upscale", "remove-background", "remove-background-upscale")
SUPPORTED_RESPONSE_MODES = ("image", "json")
logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)

app = FastAPI(
    title="Clarity Image Tools",
    description="Docker-hosted image upscaling, background removal, and controlled image prep.",
    version="1.4.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS or ["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.on_event("startup")
def startup_queued_jobs() -> None:
    start_queued_workers()


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "max_upload_mb": MAX_UPLOAD_MB,
        "max_image_dimension": MAX_IMAGE_DIMENSION,
        "max_upscale_factor": MAX_UPSCALE_FACTOR,
        "max_batch_files": MAX_BATCH_FILES,
        "max_batch_total_mb": MAX_BATCH_TOTAL_MB,
        "upscale_formats": sorted(SUPPORTED_FORMATS),
        "background_formats": sorted(SUPPORTED_BG_FORMATS),
        "tools": list(SUPPORTED_TOOLS),
        "history_limit": HISTORY_LIMIT,
        "cors_allow_origins": CORS_ORIGINS or ["*"],
        "runtime": _runtime_info(),
    }


@app.get("/api/jobs")
def api_jobs(limit: int = 25, x_api_key: str | None = Header(default=None), authorization: str | None = Header(default=None)) -> dict[str, object]:
    _require_api_key(x_api_key, authorization)
    safe_limit = max(1, min(int(limit), HISTORY_LIMIT))
    queued = list_queued_jobs(safe_limit, include_done=False)
    completed = [_completed_job_status(job) for job in list_jobs(safe_limit)]
    jobs = sorted(queued + completed, key=lambda job: str(job.get("created_at") or ""), reverse=True)
    return {"jobs": jobs[:safe_limit]}


@app.post("/api/jobs/queue")
async def api_queue_job(
    image: UploadFile = File(...),
    tool: str = Form("upscale"),
    scale: float = Form(4.0),
    mode: str = Form("auto"),
    face_enhance: bool = Form(False),
    denoise: float = Form(0.55),
    tile: int = Form(512),
    device: str = Form("auto"),
    output_format: str = Form("png"),
    target_width: int | None = Form(None),
    target_height: int | None = Form(None),
    resize_method: str = Form("lanczos"),
    target_fit: str = Form("stretch"),
    canvas_width: int | None = Form(None),
    canvas_height: int | None = Form(None),
    canvas_anchor: str = Form("center"),
    dpi: int | None = Form(None),
    export_quality: int = Form(95),
    sharpen_amount: int = Form(70),
    model: str = Form("auto"),
    cut_mode: str = Form("balanced"),
    alpha_matting: bool = Form(True),
    edge_refine: int = Form(8),
    edge_trim: int = Form(0),
    fringe_cleanup: int = Form(0),
    inner_cleanup: int = Form(0),
    background_tolerance: int = Form(34),
    post_process_mask: bool = Form(True),
    preserve_interior: bool = Form(True),
    respect_existing_alpha: bool = Form(True),
    upscale_device: str = Form("auto"),
    background_device: str = Form("auto"),
    x_api_key: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
) -> JSONResponse:
    _require_api_key(x_api_key, authorization)
    raw, metadata = await _read_validated_upload(image)
    normalized_tool = _normalize_tool(tool)
    try:
        settings = _build_tool_settings(
            normalized_tool=normalized_tool,
            metadata=metadata,
            scale=scale,
            mode=mode,
            face_enhance=face_enhance,
            denoise=denoise,
            tile=tile,
            device=device,
            output_format=output_format,
            target_width=target_width,
            target_height=target_height,
            resize_method=resize_method,
            target_fit=target_fit,
            canvas_width=canvas_width,
            canvas_height=canvas_height,
            canvas_anchor=canvas_anchor,
            dpi=dpi,
            export_quality=export_quality,
            sharpen_amount=sharpen_amount,
            model=model,
            cut_mode=cut_mode,
            alpha_matting=alpha_matting,
            edge_refine=edge_refine,
            edge_trim=edge_trim,
            fringe_cleanup=fringe_cleanup,
            inner_cleanup=inner_cleanup,
            background_tolerance=background_tolerance,
            post_process_mask=post_process_mask,
            preserve_interior=preserve_interior,
            respect_existing_alpha=respect_existing_alpha,
            upscale_device=upscale_device,
            background_device=background_device,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    job = create_queued_job(
        filename=image.filename or "image.png",
        data=raw,
        input_metadata=metadata,
        tool=normalized_tool,
        settings=settings,
    )
    return JSONResponse(status_code=202, content={"job": job})


@app.get("/api/jobs/{job_id}/source")
def api_queued_source(job_id: str, x_api_key: str | None = Header(default=None), authorization: str | None = Header(default=None)) -> FileResponse:
    _require_api_key(x_api_key, authorization)
    path = queued_source_path(job_id)
    if not path:
        raise HTTPException(status_code=404, detail="Queued source image not found.")
    return FileResponse(path, filename=path.name)


@app.get("/api/jobs/{job_id}")
def api_job_status(job_id: str, x_api_key: str | None = Header(default=None), authorization: str | None = Header(default=None)) -> dict[str, object]:
    _require_api_key(x_api_key, authorization)
    queued = get_queued_job(job_id)
    if queued:
        return queued
    completed = get_job(job_id)
    if completed:
        return _completed_job_status(completed)
    raise HTTPException(status_code=404, detail="Job not found.")


@app.post("/api/jobs/{job_id}/retry")
def api_retry_job(job_id: str, x_api_key: str | None = Header(default=None), authorization: str | None = Header(default=None)) -> JSONResponse:
    _require_api_key(x_api_key, authorization)
    job = retry_queued_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Queued job not found or source is unavailable.")
    return JSONResponse(status_code=202, content={"job": job})


def _completed_job_status(job: dict[str, object]) -> dict[str, object]:
    done = dict(job)
    done["status"] = "done"
    done["progress"] = 100
    done["kind"] = "completed"
    return done


@app.get("/api/batches")
def api_batches(limit: int = 10, x_api_key: str | None = Header(default=None), authorization: str | None = Header(default=None)) -> dict[str, object]:
    _require_api_key(x_api_key, authorization)
    return {"batches": list_batches(limit)}


@app.get("/api/batches/{batch_id}")
def api_batch(batch_id: str, x_api_key: str | None = Header(default=None), authorization: str | None = Header(default=None)) -> dict[str, object]:
    _require_api_key(x_api_key, authorization)
    batch = get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found.")
    return batch


@app.get("/api/batches/{batch_id}/zip")
def api_batch_zip(batch_id: str, x_api_key: str | None = Header(default=None), authorization: str | None = Header(default=None)) -> StreamingResponse:
    _require_api_key(x_api_key, authorization)
    payload = build_batch_zip(batch_id)
    if not payload:
        raise HTTPException(status_code=404, detail="Batch not found.")
    data, filename = payload
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/batches/{batch_id}/source/{item_id}")
def api_batch_source(batch_id: str, item_id: str, x_api_key: str | None = Header(default=None), authorization: str | None = Header(default=None)) -> FileResponse:
    _require_api_key(x_api_key, authorization)
    path = batch_source_path(batch_id, item_id)
    if not path:
        raise HTTPException(status_code=404, detail="Batch source image not found.")
    return FileResponse(path, filename=path.name)


@app.post("/api/batches")
async def api_create_batch(
    images: list[UploadFile] = File(...),
    tool: str = Form("upscale"),
    scale: float = Form(4.0),
    mode: str = Form("auto"),
    face_enhance: bool = Form(False),
    denoise: float = Form(0.55),
    tile: int = Form(512),
    device: str = Form("auto"),
    output_format: str = Form("png"),
    target_width: int | None = Form(None),
    target_height: int | None = Form(None),
    resize_method: str = Form("lanczos"),
    target_fit: str = Form("stretch"),
    canvas_width: int | None = Form(None),
    canvas_height: int | None = Form(None),
    canvas_anchor: str = Form("center"),
    dpi: int | None = Form(None),
    export_quality: int = Form(95),
    sharpen_amount: int = Form(70),
    model: str = Form("auto"),
    cut_mode: str = Form("balanced"),
    alpha_matting: bool = Form(True),
    edge_refine: int = Form(8),
    edge_trim: int = Form(0),
    fringe_cleanup: int = Form(0),
    inner_cleanup: int = Form(0),
    background_tolerance: int = Form(34),
    post_process_mask: bool = Form(True),
    preserve_interior: bool = Form(True),
    respect_existing_alpha: bool = Form(True),
    upscale_device: str = Form("auto"),
    background_device: str = Form("auto"),
    x_api_key: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
) -> dict[str, object]:
    _require_api_key(x_api_key, authorization)
    normalized_tool = _normalize_tool(tool)
    if len(images) > MAX_BATCH_FILES:
        raise HTTPException(status_code=400, detail=f"Batch limit exceeded. Max {MAX_BATCH_FILES} files per batch.")
    files: list[tuple[str, bytes]] = []
    metadatas: list[dict[str, object]] = []
    total_bytes = 0
    for upload in images:
        raw, metadata = await _read_validated_upload(upload)
        total_bytes += len(raw)
        if total_bytes > MAX_BATCH_TOTAL_BYTES:
            raise HTTPException(status_code=413, detail=f"Batch upload exceeds {MAX_BATCH_TOTAL_MB} MB total.")
        files.append((upload.filename or "image.png", raw))
        metadatas.append(metadata)
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")
    if normalized_tool == "remove-background":
        settings = vars(BackgroundOptions(model=model, cut_mode=cut_mode, alpha_matting=alpha_matting, edge_refine=edge_refine, edge_trim=edge_trim, fringe_cleanup=fringe_cleanup, inner_cleanup=inner_cleanup, background_tolerance=background_tolerance, device=device, post_process_mask=post_process_mask, preserve_interior=preserve_interior, respect_existing_alpha=respect_existing_alpha, output_format=output_format))
    elif normalized_tool == "remove-background-upscale":
        upscale_options = UpscaleOptions(scale=scale, mode=mode, face_enhance=face_enhance, denoise=denoise, tile=tile, device=upscale_device, output_format=output_format, target_width=target_width, target_height=target_height, resize_method=resize_method, target_fit=target_fit, canvas_width=canvas_width, canvas_height=canvas_height, canvas_anchor=canvas_anchor, dpi=dpi, export_quality=export_quality, sharpen_amount=sharpen_amount)
        try:
            for metadata in metadatas:
                _validate_upscale_resolution(metadata, upscale_options)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        settings = {"background": vars(BackgroundOptions(model=model, cut_mode=cut_mode, alpha_matting=alpha_matting, edge_refine=edge_refine, edge_trim=edge_trim, fringe_cleanup=fringe_cleanup, inner_cleanup=inner_cleanup, background_tolerance=background_tolerance, device=background_device, post_process_mask=post_process_mask, preserve_interior=preserve_interior, respect_existing_alpha=respect_existing_alpha, output_format="png")), "upscale": vars(upscale_options)}
    else:
        upscale_options = UpscaleOptions(scale=scale, mode=mode, face_enhance=face_enhance, denoise=denoise, tile=tile, device=device, output_format=output_format, target_width=target_width, target_height=target_height, resize_method=resize_method, target_fit=target_fit, canvas_width=canvas_width, canvas_height=canvas_height, canvas_anchor=canvas_anchor, dpi=dpi, export_quality=export_quality, sharpen_amount=sharpen_amount)
        try:
            for metadata in metadatas:
                _validate_upscale_resolution(metadata, upscale_options)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        settings = vars(upscale_options)
    batch = create_batch(files, normalized_tool, settings)
    return {"batch": batch}


@app.post("/api/batches/{batch_id}/retry")
def api_retry_batch(
    batch_id: str,
    failed_only: bool = True,
    x_api_key: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
) -> dict[str, object]:
    _require_api_key(x_api_key, authorization)
    batch = retry_batch(batch_id, failed_only=failed_only)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found or no matching items to retry.")
    return {"batch": batch}


@app.delete("/api/jobs")
def api_clear_jobs() -> dict[str, object]:
    completed = clear_jobs()
    queued = clear_queued_jobs()
    return {
        "deleted": True,
        "deleted_jobs": int(completed.get("deleted_jobs", 0)) + int(queued.get("deleted_jobs", 0)),
        "deleted_files": int(completed.get("deleted_files", 0)) + int(queued.get("deleted_jobs", 0)),
        "kept_running": queued.get("kept_running", 0),
    }


@app.delete("/api/jobs/{job_id}")
def api_delete_job(job_id: str) -> dict[str, object]:
    queued = delete_queued_job(job_id)
    if queued is not None:
        if not queued.get("deleted"):
            raise HTTPException(status_code=409, detail="This job is running and cannot be deleted yet.")
        return queued
    result = delete_job(job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Saved job not found.")
    return result


@app.get("/api/results/{job_id}")
def api_result(job_id: str) -> FileResponse:
    path = result_path(job_id)
    if not path:
        raise HTTPException(status_code=404, detail="Result not found.")
    job = get_job(job_id) or {}
    return FileResponse(path, filename=str(job.get("filename") or path.name))


@app.get("/api/sources/{job_id}")
def api_source(job_id: str, x_api_key: str | None = Header(default=None), authorization: str | None = Header(default=None)) -> FileResponse:
    _require_api_key(x_api_key, authorization)
    path = source_path(job_id)
    if not path:
        raise HTTPException(status_code=404, detail="Source image not found for this job.")
    job = get_job(job_id) or {}
    return FileResponse(path, filename=str(job.get("source_filename") or path.name))


@app.get("/api/diagnostics")
def api_diagnostics() -> dict[str, object]:
    runtime = _runtime_info()
    return {
        "status": "ok",
        "runtime": runtime,
        "storage": storage_summary(),
        "limits": {
            "max_upload_mb": MAX_UPLOAD_MB,
            "max_image_dimension": MAX_IMAGE_DIMENSION,
            "max_upscale_factor": MAX_UPSCALE_FACTOR,
            "max_batch_files": MAX_BATCH_FILES,
            "max_batch_total_mb": MAX_BATCH_TOTAL_MB,
        },
        "recommendations": _runtime_recommendations(runtime),
    }


@app.get("/api/capabilities")
def api_capabilities() -> dict[str, object]:
    return {
        "tools": list(SUPPORTED_TOOLS),
        "response_modes": list(SUPPORTED_RESPONSE_MODES),
        "output_formats": sorted(set(SUPPORTED_FORMATS) | set(SUPPORTED_BG_FORMATS)),
        "batch": {
            "max_files": MAX_BATCH_FILES,
            "max_total_mb": MAX_BATCH_TOTAL_MB,
            "zip_downloads": True,
            "server_background_processing": True,
        },
        "queue": {
            "single_image_jobs": True,
            "server_background_processing": True,
            "statuses": ["queued", "running", "done", "error"],
            "source_downloads": True,
            "retry_failed": True,
        },
        "upscale": {
            "modes": ["auto", "photo", "general", "anime", "conservative"],
            "resize_methods": ["nearest", "bilinear", "bicubic", "lanczos", "mitchell", "preserve"],
            "target_fit_modes": ["stretch", "contain", "pad", "crop"],
            "canvas_anchors": [
                "center",
                "top-left",
                "top",
                "top-right",
                "left",
                "right",
                "bottom-left",
                "bottom",
                "bottom-right",
            ],
            "max_upscale_factor": MAX_UPSCALE_FACTOR,
            "max_dimension": MAX_IMAGE_DIMENSION,
        },
        "background": {
            "models": sorted(BACKGROUND_MODELS.keys()),
            "cut_modes": sorted(BACKGROUND_CUT_MODES.keys()),
            "output_formats": sorted(SUPPORTED_BG_FORMATS),
        },
        "security": {"api_key_enabled": bool(API_KEY)},
    }


def _build_tool_settings(
    *,
    normalized_tool: str,
    metadata: dict[str, object],
    scale: float,
    mode: str,
    face_enhance: bool,
    denoise: float,
    tile: int,
    device: str,
    output_format: str,
    target_width: int | None,
    target_height: int | None,
    resize_method: str,
    target_fit: str,
    canvas_width: int | None,
    canvas_height: int | None,
    canvas_anchor: str,
    dpi: int | None,
    export_quality: int,
    sharpen_amount: int,
    model: str,
    cut_mode: str,
    alpha_matting: bool,
    edge_refine: int,
    edge_trim: int,
    fringe_cleanup: int,
    inner_cleanup: int,
    background_tolerance: int,
    post_process_mask: bool,
    preserve_interior: bool,
    respect_existing_alpha: bool,
    upscale_device: str,
    background_device: str,
) -> dict[str, object]:
    if normalized_tool == "remove-background":
        return vars(
            BackgroundOptions(
                model=model,
                cut_mode=cut_mode,
                alpha_matting=alpha_matting,
                edge_refine=edge_refine,
                edge_trim=edge_trim,
                fringe_cleanup=fringe_cleanup,
                inner_cleanup=inner_cleanup,
                background_tolerance=background_tolerance,
                device=device,
                post_process_mask=post_process_mask,
                preserve_interior=preserve_interior,
                respect_existing_alpha=respect_existing_alpha,
                output_format=output_format,
            )
        )

    if normalized_tool == "remove-background-upscale":
        normalized_format = output_format.lower().strip()
        if normalized_format == "jpg":
            normalized_format = "jpeg"
        if normalized_format == "tif":
            normalized_format = "tiff"
        if normalized_format not in (SUPPORTED_FORMATS - {"jpeg", "jpg"}):
            raise ValueError("All-in-one output format must be png, webp, or tiff so transparency is preserved.")

        upscale_options = UpscaleOptions(
            scale=scale,
            mode=mode,
            face_enhance=face_enhance,
            denoise=denoise,
            tile=tile,
            device=upscale_device,
            output_format=normalized_format,
            target_width=target_width,
            target_height=target_height,
            resize_method=resize_method,
            target_fit=target_fit,
            canvas_width=canvas_width,
            canvas_height=canvas_height,
            canvas_anchor=canvas_anchor,
            dpi=dpi,
            export_quality=export_quality,
            sharpen_amount=sharpen_amount,
        )
        _validate_upscale_resolution(metadata, upscale_options)
        return {
            "background": vars(
                BackgroundOptions(
                    model=model,
                    cut_mode=cut_mode,
                    alpha_matting=alpha_matting,
                    edge_refine=edge_refine,
                    edge_trim=edge_trim,
                    fringe_cleanup=fringe_cleanup,
                    inner_cleanup=inner_cleanup,
                    background_tolerance=background_tolerance,
                    device=background_device,
                    post_process_mask=post_process_mask,
                    preserve_interior=preserve_interior,
                    respect_existing_alpha=respect_existing_alpha,
                    output_format="png",
                )
            ),
            "upscale": vars(upscale_options),
        }

    upscale_options = UpscaleOptions(
        scale=scale,
        mode=mode,
        face_enhance=face_enhance,
        denoise=denoise,
        tile=tile,
        device=device,
        output_format=output_format,
        target_width=target_width,
        target_height=target_height,
        resize_method=resize_method,
        target_fit=target_fit,
        canvas_width=canvas_width,
        canvas_height=canvas_height,
        canvas_anchor=canvas_anchor,
        dpi=dpi,
        export_quality=export_quality,
        sharpen_amount=sharpen_amount,
    )
    _validate_upscale_resolution(metadata, upscale_options)
    return vars(upscale_options)


def _require_api_key(x_api_key: str | None, authorization: str | None = None) -> None:
    if not API_KEY:
        return
    bearer_key = None
    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "bearer" and token:
            bearer_key = token.strip()
    provided = (x_api_key or "").strip() or bearer_key or ""
    if not hmac.compare_digest(provided, API_KEY):
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")


def _filename_from_disposition(disposition: str | None) -> str | None:
    if not disposition:
        return None
    match = re.search(r'filename="([^"]+)"', disposition)
    return match.group(1) if match else None


def _process_json_payload(request: Request, response: StreamingResponse, tool: str) -> dict[str, object]:
    headers = response.headers
    relative_download_url = headers.get("X-Download-URL")
    relative_source_url = headers.get("X-Source-URL")
    absolute_download_url = None
    absolute_source_url = None
    if relative_download_url:
        absolute_download_url = str(request.base_url).rstrip("/") + relative_download_url
    if relative_source_url:
        absolute_source_url = str(request.base_url).rstrip("/") + relative_source_url
    return {
        "job_id": headers.get("X-Job-Id"),
        "filename": _filename_from_disposition(headers.get("content-disposition")),
        "download_url": absolute_download_url,
        "relative_download_url": relative_download_url,
        "source_url": absolute_source_url,
        "relative_source_url": relative_source_url,
        "metadata": {
            "tool": tool,
            "output_width": headers.get("X-Output-Width"),
            "output_height": headers.get("X-Output-Height"),
            "output_dpi": headers.get("X-Output-DPI"),
            "engine": headers.get("X-Upscaler-Engine")
            or headers.get("X-Background-Engine")
            or headers.get("X-Pipeline-Engine"),
        },
    }


@app.post("/api/process", response_model=None)
async def api_process(
    request: Request,
    image: UploadFile = File(...),
    tool: str = Form("upscale"),
    response_mode: str = Form("image"),
    x_api_key: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
    scale: float = Form(4.0),
    mode: str = Form("auto"),
    face_enhance: bool = Form(False),
    denoise: float = Form(0.55),
    tile: int = Form(512),
    device: str = Form("auto"),
    output_format: str = Form("png"),
    target_width: int | None = Form(None),
    target_height: int | None = Form(None),
    resize_method: str = Form("lanczos"),
    target_fit: str = Form("stretch"),
    canvas_width: int | None = Form(None),
    canvas_height: int | None = Form(None),
    canvas_anchor: str = Form("center"),
    dpi: int | None = Form(None),
    export_quality: int = Form(95),
    sharpen_amount: int = Form(70),
    model: str = Form("auto"),
    cut_mode: str = Form("balanced"),
    alpha_matting: bool = Form(True),
    edge_refine: int = Form(8),
    edge_trim: int = Form(0),
    fringe_cleanup: int = Form(0),
    inner_cleanup: int = Form(0),
    background_tolerance: int = Form(34),
    post_process_mask: bool = Form(True),
    preserve_interior: bool = Form(True),
    respect_existing_alpha: bool = Form(True),
):
    _require_api_key(x_api_key, authorization)
    tool = tool.strip().lower()
    response_mode = response_mode.strip().lower()
    if response_mode not in SUPPORTED_RESPONSE_MODES:
        raise HTTPException(status_code=400, detail="response_mode must be image or json.")

    if tool == "upscale":
        response = await api_upscale(
            image=image, scale=scale, mode=mode, face_enhance=face_enhance, denoise=denoise, tile=tile,
            device=device, output_format=output_format, target_width=target_width, target_height=target_height,
            resize_method=resize_method, target_fit=target_fit, canvas_width=canvas_width, canvas_height=canvas_height,
            canvas_anchor=canvas_anchor, dpi=dpi, export_quality=export_quality, sharpen_amount=sharpen_amount
        )
    elif tool == "remove-background":
        response = await api_remove_background(
            image=image, model=model, cut_mode=cut_mode, alpha_matting=alpha_matting, edge_refine=edge_refine,
            edge_trim=edge_trim, fringe_cleanup=fringe_cleanup, inner_cleanup=inner_cleanup,
            background_tolerance=background_tolerance, device=device, post_process_mask=post_process_mask,
            preserve_interior=preserve_interior, respect_existing_alpha=respect_existing_alpha,
            output_format=output_format
        )
    elif tool == "remove-background-upscale":
        response = await api_remove_background_upscale(
            image=image, scale=scale, mode=mode, face_enhance=face_enhance, denoise=denoise, tile=tile,
            upscale_device=device, target_width=target_width, target_height=target_height,
            resize_method=resize_method, target_fit=target_fit, canvas_width=canvas_width, canvas_height=canvas_height,
            canvas_anchor=canvas_anchor, dpi=dpi, export_quality=export_quality, sharpen_amount=sharpen_amount, model=model,
            cut_mode=cut_mode, alpha_matting=alpha_matting, edge_refine=edge_refine, edge_trim=edge_trim,
            fringe_cleanup=fringe_cleanup, inner_cleanup=inner_cleanup, background_tolerance=background_tolerance,
            background_device=device, post_process_mask=post_process_mask, preserve_interior=preserve_interior,
            respect_existing_alpha=respect_existing_alpha, output_format=output_format
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported tool. Must be one of: {', '.join(SUPPORTED_TOOLS)}.")

    if response_mode == "image":
        return response

    return JSONResponse(_process_json_payload(request, response, tool))


@app.post("/api/upscale")
async def api_upscale(
    image: UploadFile = File(...),
    scale: float = Form(4.0),
    mode: str = Form("auto"),
    face_enhance: bool = Form(False),
    denoise: float = Form(0.55),
    tile: int = Form(512),
    device: str = Form("auto"),
    output_format: str = Form("png"),
    target_width: int | None = Form(None),
    target_height: int | None = Form(None),
    resize_method: str = Form("lanczos"),
    target_fit: str = Form("stretch"),
    canvas_width: int | None = Form(None),
    canvas_height: int | None = Form(None),
    canvas_anchor: str = Form("center"),
    dpi: int | None = Form(None),
    export_quality: int = Form(95),
    sharpen_amount: int = Form(70),
) -> StreamingResponse:
    raw, metadata = await _read_validated_upload(image)

    try:
        options = UpscaleOptions(
            scale=scale,
            mode=mode,
            face_enhance=face_enhance,
            denoise=denoise,
            tile=tile,
            device=device,
            output_format=output_format,
            target_width=target_width,
            target_height=target_height,
            resize_method=resize_method,
            target_fit=target_fit,
            canvas_width=canvas_width,
            canvas_height=canvas_height,
            canvas_anchor=canvas_anchor,
            dpi=dpi,
            export_quality=export_quality,
            sharpen_amount=sharpen_amount,
        )
        _validate_upscale_resolution(metadata, options)
        started = time.perf_counter()
        logger.info(
            "upscale start filename=%s input=%sx%s mode=%s alpha=%s options=%s",
            image.filename,
            metadata["width"],
            metadata["height"],
            metadata["mode"],
            metadata["has_alpha"],
            options,
        )
        result = await run_in_threadpool(upscale_image, raw, options)
        logger.info(
            "upscale complete filename=%s output=%sx%s engine=%s elapsed=%.1fs",
            image.filename,
            result.width,
            result.height,
            result.engine,
            time.perf_counter() - started,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    stem = _safe_stem(image.filename)
    filename = f"{stem}-upscaled-{result.width}x{result.height}.{result.extension}"
    job = save_job_result(
        tool="upscale",
        source_filename=image.filename,
        output_filename=filename,
        data=result.data,
        input_metadata=metadata,
        output_width=result.width,
        output_height=result.height,
        output_format=result.extension,
        engine=result.engine,
        settings=vars(options),
        source_data=raw,
    )
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "X-Upscaler-Engine": result.engine,
        "X-Output-Width": str(result.width),
        "X-Output-Height": str(result.height),
        "X-Output-DPI": str(options.dpi or ""),
        "X-Job-Id": str(job["id"]),
        "X-Download-URL": str(job["download_url"]),
        "X-Source-URL": str(job.get("source_download_url", "")),
    }

    return StreamingResponse(
        io.BytesIO(result.data),
        media_type=result.media_type,
        headers=headers,
    )


@app.post("/api/remove-background-upscale")
async def api_remove_background_upscale(
    image: UploadFile = File(...),
    scale: float = Form(4.0),
    mode: str = Form("auto"),
    face_enhance: bool = Form(False),
    denoise: float = Form(0.55),
    tile: int = Form(512),
    upscale_device: str = Form("auto"),
    target_width: int | None = Form(None),
    target_height: int | None = Form(None),
    resize_method: str = Form("lanczos"),
    target_fit: str = Form("stretch"),
    canvas_width: int | None = Form(None),
    canvas_height: int | None = Form(None),
    canvas_anchor: str = Form("center"),
    dpi: int | None = Form(None),
    export_quality: int = Form(95),
    sharpen_amount: int = Form(70),
    model: str = Form("auto"),
    cut_mode: str = Form("balanced"),
    alpha_matting: bool = Form(True),
    edge_refine: int = Form(8),
    edge_trim: int = Form(0),
    fringe_cleanup: int = Form(0),
    inner_cleanup: int = Form(0),
    background_tolerance: int = Form(34),
    background_device: str = Form("auto"),
    post_process_mask: bool = Form(True),
    preserve_interior: bool = Form(True),
    respect_existing_alpha: bool = Form(True),
    output_format: str = Form("png"),
) -> StreamingResponse:
    raw, metadata = await _read_validated_upload(image)

    try:
        output_format = output_format.lower().strip()
        if output_format == "jpg":
            output_format = "jpeg"
        if output_format == "tif":
            output_format = "tiff"
        if output_format not in (SUPPORTED_FORMATS - {"jpeg", "jpg"}):
            raise ValueError("All-in-one output format must be png, webp, or tiff so transparency is preserved.")

        background_options = BackgroundOptions(
            model=model,
            cut_mode=cut_mode,
            alpha_matting=alpha_matting,
            edge_refine=edge_refine,
            edge_trim=edge_trim,
            fringe_cleanup=fringe_cleanup,
            inner_cleanup=inner_cleanup,
            background_tolerance=background_tolerance,
            device=background_device,
            post_process_mask=post_process_mask,
            preserve_interior=preserve_interior,
            respect_existing_alpha=respect_existing_alpha,
            output_format="png",
        )
        upscale_options = UpscaleOptions(
            scale=scale,
            mode=mode,
            face_enhance=face_enhance,
            denoise=denoise,
            tile=tile,
            device=upscale_device,
            output_format=output_format,
            target_width=target_width,
            target_height=target_height,
            resize_method=resize_method,
            target_fit=target_fit,
            canvas_width=canvas_width,
            canvas_height=canvas_height,
            canvas_anchor=canvas_anchor,
            dpi=dpi,
            export_quality=export_quality,
            sharpen_amount=sharpen_amount,
        )
        _validate_upscale_resolution(metadata, upscale_options)

        started = time.perf_counter()
        logger.info(
            "all-in-one start filename=%s input=%sx%s mode=%s alpha=%s background=%s upscale=%s",
            image.filename,
            metadata["width"],
            metadata["height"],
            metadata["mode"],
            metadata["has_alpha"],
            background_options,
            upscale_options,
        )
        background_result = await run_in_threadpool(remove_background, raw, background_options)
        result = await run_in_threadpool(upscale_image, background_result.data, upscale_options)
        logger.info(
            "all-in-one complete filename=%s output=%sx%s background_engine=%s upscale_engine=%s elapsed=%.1fs",
            image.filename,
            result.width,
            result.height,
            background_result.engine,
            result.engine,
            time.perf_counter() - started,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    stem = _safe_stem(image.filename)
    filename = f"{stem}-transparent-upscaled-{result.width}x{result.height}.{result.extension}"
    pipeline_engine = f"{background_result.engine} -> {result.engine}"
    job = save_job_result(
        tool="remove-background-upscale",
        source_filename=image.filename,
        output_filename=filename,
        data=result.data,
        input_metadata=metadata,
        output_width=result.width,
        output_height=result.height,
        output_format=result.extension,
        engine=pipeline_engine,
        settings={
            "background": vars(background_options),
            "upscale": vars(upscale_options),
        },
        source_data=raw,
    )
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "X-Background-Engine": background_result.engine,
        "X-Upscaler-Engine": result.engine,
        "X-Pipeline-Engine": pipeline_engine,
        "X-Output-Width": str(result.width),
        "X-Output-Height": str(result.height),
        "X-Output-DPI": str(upscale_options.dpi or ""),
        "X-Job-Id": str(job["id"]),
        "X-Download-URL": str(job["download_url"]),
        "X-Source-URL": str(job.get("source_download_url", "")),
    }

    return StreamingResponse(
        io.BytesIO(result.data),
        media_type=result.media_type,
        headers=headers,
    )


@app.post("/api/remove-background")
async def api_remove_background(
    image: UploadFile = File(...),
    model: str = Form("auto"),
    cut_mode: str = Form("balanced"),
    alpha_matting: bool = Form(True),
    edge_refine: int = Form(8),
    edge_trim: int = Form(0),
    fringe_cleanup: int = Form(0),
    inner_cleanup: int = Form(0),
    background_tolerance: int = Form(34),
    device: str = Form("auto"),
    post_process_mask: bool = Form(True),
    preserve_interior: bool = Form(True),
    respect_existing_alpha: bool = Form(True),
    output_format: str = Form("png"),
) -> StreamingResponse:
    raw, metadata = await _read_validated_upload(image)

    try:
        options = BackgroundOptions(
            model=model,
            cut_mode=cut_mode,
            alpha_matting=alpha_matting,
            edge_refine=edge_refine,
            edge_trim=edge_trim,
            fringe_cleanup=fringe_cleanup,
            inner_cleanup=inner_cleanup,
            background_tolerance=background_tolerance,
            device=device,
            post_process_mask=post_process_mask,
            preserve_interior=preserve_interior,
            respect_existing_alpha=respect_existing_alpha,
            output_format=output_format,
        )
        started = time.perf_counter()
        logger.info(
            "remove-bg start filename=%s input=%sx%s mode=%s options=%s",
            image.filename,
            metadata["width"],
            metadata["height"],
            metadata["mode"],
            options,
        )
        result = await run_in_threadpool(remove_background, raw, options)
        logger.info(
            "remove-bg complete filename=%s output=%sx%s engine=%s elapsed=%.1fs",
            image.filename,
            result.width,
            result.height,
            result.engine,
            time.perf_counter() - started,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    stem = _safe_stem(image.filename)
    filename = f"{stem}-transparent.{result.extension}"
    job = save_job_result(
        tool="remove-background",
        source_filename=image.filename,
        output_filename=filename,
        data=result.data,
        input_metadata=metadata,
        output_width=result.width,
        output_height=result.height,
        output_format=result.extension,
        engine=result.engine,
        settings=vars(options),
        source_data=raw,
    )
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "X-Background-Engine": result.engine,
        "X-Output-Width": str(result.width),
        "X-Output-Height": str(result.height),
        "X-Job-Id": str(job["id"]),
        "X-Download-URL": str(job["download_url"]),
        "X-Source-URL": str(job.get("source_download_url", "")),
    }

    return StreamingResponse(
        io.BytesIO(result.data),
        media_type=result.media_type,
        headers=headers,
    )


async def _read_validated_upload(image: UploadFile) -> tuple[bytes, dict[str, object]]:
    raw = await image.read()
    if not raw:
        raise HTTPException(status_code=400, detail="The uploaded image is empty.")
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"Upload exceeds {MAX_UPLOAD_MB} MB.")

    try:
        with Image.open(io.BytesIO(raw)) as probe:
            metadata = {
                "width": probe.width,
                "height": probe.height,
                "mode": probe.mode,
                "has_alpha": "A" in probe.getbands(),
            }
            _validate_input_resolution(metadata)
            probe.verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(status_code=400, detail="Unsupported or corrupted image.") from exc
    return raw, metadata


def _validate_input_resolution(metadata: dict[str, object]) -> None:
    width = int(metadata["width"])
    height = int(metadata["height"])
    if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
        raise HTTPException(
            status_code=413,
            detail=(
                f"Image is {width} x {height}. Maximum input resolution is "
                f"{MAX_IMAGE_DIMENSION} x {MAX_IMAGE_DIMENSION}."
            ),
        )


def _validate_upscale_resolution(metadata: dict[str, object], options: UpscaleOptions) -> None:
    width = int(metadata["width"])
    height = int(metadata["height"])
    content_size, output_size = resolve_upscale_sizes(width, height, options)
    output_width, output_height = output_size
    if output_width > MAX_IMAGE_DIMENSION or output_height > MAX_IMAGE_DIMENSION:
        raise ValueError(
            f"Requested output would be {output_width} x {output_height}. "
            f"Maximum output resolution is {MAX_IMAGE_DIMENSION} x {MAX_IMAGE_DIMENSION}. "
            "Choose a smaller output size or resize the source image first."
        )
    upscale_factor = max(content_size[0] / width, content_size[1] / height)
    if upscale_factor > MAX_UPSCALE_FACTOR:
        raise ValueError(
            f"Requested output would be {upscale_factor:.2f}x the source image. "
            f"Maximum upscale factor is {MAX_UPSCALE_FACTOR:g}x."
        )


def _resolve_upscale_output_size(width: int, height: int, options: UpscaleOptions) -> tuple[int, int]:
    return resolve_upscale_sizes(width, height, options)[1]


def _safe_stem(filename: str | None) -> str:
    stem = Path(filename or "image").stem
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", stem).strip("-") or "image"


def _normalize_tool(tool: str) -> str:
    normalized = (tool or "upscale").lower().strip().replace("_", "-")
    aliases = {
        "background": "remove-background",
        "background-removal": "remove-background",
        "remove-bg": "remove-background",
        "remove-back-ground": "remove-background",
        "all-in-one": "remove-background-upscale",
        "background-upscale": "remove-background-upscale",
        "remove-bg-upscale": "remove-background-upscale",
        "remove-background-and-upscale": "remove-background-upscale",
    }
    normalized = aliases.get(normalized, normalized)
    if normalized not in SUPPORTED_TOOLS:
        raise HTTPException(status_code=400, detail=f"Tool must be one of: {', '.join(SUPPORTED_TOOLS)}.")
    return normalized


def _normalize_response_mode(response_mode: str) -> str:
    normalized = (response_mode or "image").lower().strip()
    if normalized in {"file", "binary", "bytes"}:
        normalized = "image"
    if normalized not in SUPPORTED_RESPONSE_MODES:
        raise HTTPException(status_code=400, detail="response_mode must be image or json.")
    return normalized


def _automation_response(
    request: Request,
    response_mode: str,
    data: bytes,
    media_type: str,
    filename: str,
    job: dict[str, object],
    headers: dict[str, str],
) -> StreamingResponse | JSONResponse:
    if response_mode == "json":
        json_headers = {key: value for key, value in headers.items() if key.lower() != "content-disposition"}
        json_headers["X-API-Response"] = "json"
        payload = {
            "ok": True,
            "job_id": job["id"],
            "filename": filename,
            "media_type": media_type,
            "download_url": str(request.url_for("api_result", job_id=job["id"])),
            "relative_download_url": job["download_url"],
            "job": job,
        }
        return JSONResponse(payload, headers=json_headers)

    image_headers = dict(headers)
    image_headers["X-API-Response"] = "image"
    return StreamingResponse(io.BytesIO(data), media_type=media_type, headers=image_headers)


@lru_cache(maxsize=1)
def _runtime_info() -> dict[str, object]:
    info: dict[str, object] = {
        "requested_device": os.getenv("UPSCALER_DEVICE", "auto"),
        "background_requested_device": os.getenv("REMBG_DEVICE", os.getenv("UPSCALER_DEVICE", "auto")),
        "available_devices": ["cpu"],
        "torch": None,
        "cuda_available": False,
        "cuda_device": None,
        "onnxruntime": None,
        "onnx_providers": [],
    }
    try:
        import torch

        cuda_available = bool(torch.cuda.is_available())
        info.update(
            {
                "torch": torch.__version__,
                "cuda_available": cuda_available,
                "cuda_device": torch.cuda.get_device_name(0) if cuda_available else None,
                "available_devices": ["cpu", "cuda"] if cuda_available else ["cpu"],
            }
        )
    except Exception as exc:
        info["torch_error"] = str(exc)
    try:
        import onnxruntime as ort

        info["onnxruntime"] = ort.__version__
        info["onnx_providers"] = ort.get_available_providers()
    except Exception as exc:
        info["onnxruntime_error"] = str(exc)
    return info


def _runtime_recommendations(runtime: dict[str, object]) -> list[str]:
    recommendations = [
        "Leave hardware selectors on Auto unless you are troubleshooting a specific job.",
        "Use CPU for maximum compatibility, small graphics, and simple logo cutouts.",
    ]
    if runtime.get("cuda_available"):
        recommendations.insert(
            1,
            "Use NVIDIA GPU for 4x or 8x upscales, large photos, all-in-one jobs, and batches.",
        )
    else:
        recommendations.insert(
            1,
            "No CUDA GPU is visible inside the container, so GPU selections will fall back or error.",
        )

    providers = runtime.get("onnx_providers") or []
    if "CUDAExecutionProvider" not in providers:
        recommendations.append("Background removal is not seeing ONNX CUDA; use CPU or rebuild with GPU dependencies.")
    return recommendations


@app.exception_handler(HTTPException)
async def http_exception_handler(_, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})
