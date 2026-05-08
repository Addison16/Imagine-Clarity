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
    storage_summary,
)
from app.batch_jobs import build_batch_zip, create_batch, get_batch, list_batches, retry_batch
from app.upscaler import SUPPORTED_FORMATS, UpscaleOptions, upscale_image

APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "64"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
MAX_IMAGE_DIMENSION = int(os.getenv("MAX_IMAGE_DIMENSION", "16384"))
MAX_UPSCALE_FACTOR = 8.0
MAX_BATCH_FILES = int(os.getenv("MAX_BATCH_FILES", "100"))
API_KEY = os.getenv("CLARITY_API_KEY", "").strip()
CORS_ORIGINS = [origin.strip() for origin in os.getenv("CORS_ALLOW_ORIGINS", "*").split(",") if origin.strip()]
SUPPORTED_TOOLS = ("upscale", "remove-background", "remove-background-upscale")
SUPPORTED_RESPONSE_MODES = ("image", "json")
logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)

app = FastAPI(
    title="Clarity Image Tools",
    description="Docker-hosted AI image upscaling and background removal.",
    version="1.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS or ["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


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
    return {"jobs": list_jobs(limit)}


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
    if len(images) > MAX_BATCH_FILES:
        raise HTTPException(status_code=400, detail=f"Batch limit exceeded. Max {MAX_BATCH_FILES} files per batch.")
    files: list[tuple[str, bytes]] = []
    for upload in images:
        raw, _ = await _read_validated_upload(upload)
        files.append((upload.filename or "image.png", raw))
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")
    if tool == "remove-background":
        settings = vars(BackgroundOptions(model=model, cut_mode=cut_mode, alpha_matting=alpha_matting, edge_refine=edge_refine, edge_trim=edge_trim, fringe_cleanup=fringe_cleanup, inner_cleanup=inner_cleanup, background_tolerance=background_tolerance, device=device, post_process_mask=post_process_mask, preserve_interior=preserve_interior, respect_existing_alpha=respect_existing_alpha, output_format=output_format))
    elif tool == "remove-background-upscale":
        settings = {"background": vars(BackgroundOptions(model=model, cut_mode=cut_mode, alpha_matting=alpha_matting, edge_refine=edge_refine, edge_trim=edge_trim, fringe_cleanup=fringe_cleanup, inner_cleanup=inner_cleanup, background_tolerance=background_tolerance, device=background_device, post_process_mask=post_process_mask, preserve_interior=preserve_interior, respect_existing_alpha=respect_existing_alpha, output_format="png")), "upscale": vars(UpscaleOptions(scale=scale, mode=mode, face_enhance=face_enhance, denoise=denoise, tile=tile, device=upscale_device, output_format=output_format, target_width=target_width, target_height=target_height))}
    else:
        settings = vars(UpscaleOptions(scale=scale, mode=mode, face_enhance=face_enhance, denoise=denoise, tile=tile, device=device, output_format=output_format, target_width=target_width, target_height=target_height))
    batch = create_batch(files, tool, settings)
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
    return clear_jobs()


@app.delete("/api/jobs/{job_id}")
def api_delete_job(job_id: str) -> dict[str, object]:
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
        },
        "recommendations": _runtime_recommendations(runtime),
    }


@app.get("/api/capabilities")
def api_capabilities() -> dict[str, object]:
    return {
        "tools": list(SUPPORTED_TOOLS),
        "response_modes": list(SUPPORTED_RESPONSE_MODES),
        "output_formats": sorted(set(SUPPORTED_FORMATS) | set(SUPPORTED_BG_FORMATS)),
        "upscale": {
            "modes": ["auto", "photo", "general", "anime", "conservative"],
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
    absolute_download_url = None
    if relative_download_url:
        absolute_download_url = str(request.base_url).rstrip("/") + relative_download_url
    return {
        "job_id": headers.get("X-Job-Id"),
        "filename": _filename_from_disposition(headers.get("content-disposition")),
        "download_url": absolute_download_url,
        "relative_download_url": relative_download_url,
        "metadata": {
            "tool": tool,
            "output_width": headers.get("X-Output-Width"),
            "output_height": headers.get("X-Output-Height"),
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
            device=device, output_format=output_format, target_width=target_width, target_height=target_height
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
            upscale_device=device, target_width=target_width, target_height=target_height, model=model,
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
    )
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "X-Upscaler-Engine": result.engine,
        "X-Output-Width": str(result.width),
        "X-Output-Height": str(result.height),
        "X-Job-Id": str(job["id"]),
        "X-Download-URL": str(job["download_url"]),
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
        if output_format not in SUPPORTED_BG_FORMATS:
            raise ValueError("All-in-one output format must be png or webp so transparency is preserved.")

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
    )
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "X-Background-Engine": background_result.engine,
        "X-Upscaler-Engine": result.engine,
        "X-Pipeline-Engine": pipeline_engine,
        "X-Output-Width": str(result.width),
        "X-Output-Height": str(result.height),
        "X-Job-Id": str(job["id"]),
        "X-Download-URL": str(job["download_url"]),
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
    )
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "X-Background-Engine": result.engine,
        "X-Output-Width": str(result.width),
        "X-Output-Height": str(result.height),
        "X-Job-Id": str(job["id"]),
        "X-Download-URL": str(job["download_url"]),
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
    output_width, output_height = _resolve_upscale_output_size(width, height, options)
    if output_width > MAX_IMAGE_DIMENSION or output_height > MAX_IMAGE_DIMENSION:
        raise ValueError(
            f"Requested output would be {output_width} x {output_height}. "
            f"Maximum output resolution is {MAX_IMAGE_DIMENSION} x {MAX_IMAGE_DIMENSION}. "
            "Choose a smaller output size or resize the source image first."
        )
    upscale_factor = max(output_width / width, output_height / height)
    if upscale_factor > MAX_UPSCALE_FACTOR:
        raise ValueError(
            f"Requested output would be {upscale_factor:.2f}x the source image. "
            f"Maximum upscale factor is {MAX_UPSCALE_FACTOR:g}x."
        )


def _resolve_upscale_output_size(width: int, height: int, options: UpscaleOptions) -> tuple[int, int]:
    target_width = options.target_width
    target_height = options.target_height
    if target_width is None and target_height is None:
        scale = float(options.scale)
        return round(width * scale), round(height * scale)

    if target_width is None:
        target_width = round(width * (target_height / height))
    if target_height is None:
        target_height = round(height * (target_width / width))
    return max(1, int(target_width)), max(1, int(target_height))


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
