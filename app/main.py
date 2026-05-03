from __future__ import annotations

import io
import logging
import os
import re
import time
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, UnidentifiedImageError
from starlette.concurrency import run_in_threadpool

from app.background import (
    SUPPORTED_BG_FORMATS,
    BackgroundOptions,
    remove_background,
)
from app.upscaler import SUPPORTED_FORMATS, UpscaleOptions, upscale_image

APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "64"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
MAX_IMAGE_DIMENSION = int(os.getenv("MAX_IMAGE_DIMENSION", "16384"))
logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)

app = FastAPI(
    title="Clarity Image Tools",
    description="Docker-hosted AI image upscaling and background removal.",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
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
        "upscale_formats": sorted(SUPPORTED_FORMATS),
        "background_formats": sorted(SUPPORTED_BG_FORMATS),
        "tools": ["upscale", "remove-background"],
        "runtime": _runtime_info(),
    }


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
        )
        _validate_upscale_resolution(metadata, options.scale)
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
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "X-Upscaler-Engine": result.engine,
        "X-Output-Width": str(result.width),
        "X-Output-Height": str(result.height),
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
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "X-Background-Engine": result.engine,
        "X-Output-Width": str(result.width),
        "X-Output-Height": str(result.height),
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


def _validate_upscale_resolution(metadata: dict[str, object], scale: float) -> None:
    width = int(metadata["width"])
    height = int(metadata["height"])
    output_width = round(width * float(scale))
    output_height = round(height * float(scale))
    if output_width > MAX_IMAGE_DIMENSION or output_height > MAX_IMAGE_DIMENSION:
        raise ValueError(
            f"Requested output would be {output_width} x {output_height}. "
            f"Maximum output resolution is {MAX_IMAGE_DIMENSION} x {MAX_IMAGE_DIMENSION}. "
            "Choose a smaller output size or resize the source image first."
        )


def _safe_stem(filename: str | None) -> str:
    stem = Path(filename or "image").stem
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", stem).strip("-") or "image"


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


@app.exception_handler(HTTPException)
async def http_exception_handler(_, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})
