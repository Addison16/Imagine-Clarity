from __future__ import annotations

import io
import os
import threading
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageFilter, ImageOps

SUPPORTED_FORMATS = {"png", "jpeg", "jpg", "webp"}
MODEL_DIR = Path(os.getenv("MODEL_DIR", "/models"))


@dataclass(frozen=True)
class UpscaleOptions:
    scale: float = 4.0
    mode: str = "auto"
    face_enhance: bool = False
    denoise: float = 0.55
    tile: int = 256
    device: str = "auto"
    output_format: str = "png"
    target_width: int | None = None
    target_height: int | None = None


@dataclass(frozen=True)
class UpscaleResult:
    data: bytes
    width: int
    height: int
    extension: str
    media_type: str
    engine: str


@dataclass(frozen=True)
class ModelSpec:
    key: str
    display_name: str
    scale: int
    arch: str
    model_url: str
    dni_url: str | None = None
    num_block: int = 23


MODEL_SPECS: dict[str, ModelSpec] = {
    "photo": ModelSpec(
        key="RealESRGAN_x4plus",
        display_name="Real-ESRGAN x4+",
        scale=4,
        arch="rrdb",
        model_url="https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth",
        num_block=23,
    ),
    "anime": ModelSpec(
        key="RealESRGAN_x4plus_anime_6B",
        display_name="Real-ESRGAN anime x4",
        scale=4,
        arch="rrdb",
        model_url="https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth",
        num_block=6,
    ),
    "general": ModelSpec(
        key="realesr-general-x4v3",
        display_name="Real-ESRGAN general x4 v3",
        scale=4,
        arch="srvgg",
        model_url="https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth",
        dni_url="https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-wdn-x4v3.pth",
        num_block=32,
    ),
}

MAX_UPSCALE_FACTOR = 8.0

MODE_LABELS = {
    "photo": "photo detail",
    "general": "balanced clean",
    "anime": "artwork and illustration",
    "conservative": "conservative exact resize",
}

GFPGAN_URL = "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.3.pth"

_upsampler_cache: dict[tuple[str, str], Any] = {}
_face_cache: dict[tuple[str, str, int], Any] = {}
_cache_lock = threading.Lock()


def upscale_image(raw: bytes, options: UpscaleOptions) -> UpscaleResult:
    options = _normalize_options(options)
    img = _open_image(raw)
    target_size = _resolve_target_size(img, options)
    process_scale = _target_process_scale(img, target_size) if target_size else options.scale
    if target_size and process_scale > MAX_UPSCALE_FACTOR:
        raise ValueError("Target resolution can be up to 8x the source image.")

    auto_selected = options.mode == "auto"
    if auto_selected:
        options = replace(options, mode=_select_auto_mode(img, options))

    if target_size and process_scale <= 1.0:
        output = _resize_to_target(img, target_size)
        engine = "Target resize + unsharp mask (CPU)"
    elif target_size and options.mode == "conservative":
        output = _resize_to_target(img, target_size)
        engine = "Target conservative resize + unsharp mask (CPU)"
    elif options.mode == "conservative":
        output = _conservative_resize(img, options.scale)
        engine = "Lanczos + unsharp mask (CPU)"
    else:
        run_options = replace(options, scale=process_scale) if target_size else options
        output, engine = _neural_resize(img, run_options)
        if target_size and output.size != target_size:
            output = _resize_to_target(output, target_size)
            engine = f"{engine} + target resize"

    if auto_selected:
        engine = f"Auto: {MODE_LABELS[options.mode]} -> {engine}"

    encoded, extension, media_type = _encode(output, options.output_format)
    return UpscaleResult(
        data=encoded,
        width=output.width,
        height=output.height,
        extension=extension,
        media_type=media_type,
        engine=engine,
    )


def _normalize_options(options: UpscaleOptions) -> UpscaleOptions:
    scale = float(options.scale)
    if scale not in {2.0, 3.0, 4.0, 8.0}:
        raise ValueError("Scale must be 2, 3, 4, or 8.")

    mode = options.mode.lower().strip()
    if mode not in {"auto", "photo", "general", "anime", "conservative"}:
        raise ValueError("Mode must be photo, general, anime, conservative, or auto.")

    output_format = options.output_format.lower().strip()
    if output_format == "jpg":
        output_format = "jpeg"
    if output_format not in SUPPORTED_FORMATS:
        raise ValueError("Output format must be png, jpeg, jpg, or webp.")

    target_width = _normalize_target_dimension(options.target_width, "Target width")
    target_height = _normalize_target_dimension(options.target_height, "Target height")

    denoise = max(0.0, min(float(options.denoise), 1.0))
    tile = int(options.tile)
    if tile not in {0, 128, 256, 384, 512}:
        raise ValueError("Tile must be 0, 128, 256, 384, or 512.")

    return UpscaleOptions(
        scale=scale,
        mode=mode,
        face_enhance=bool(options.face_enhance),
        denoise=denoise,
        tile=tile,
        device=_normalize_device(options.device),
        output_format=output_format,
        target_width=target_width,
        target_height=target_height,
    )


def _normalize_target_dimension(value: int | None, label: str) -> int | None:
    if value is None:
        return None
    value = int(value)
    if value <= 0:
        raise ValueError(f"{label} must be a positive number.")
    return value


def _resolve_target_size(img: Image.Image, options: UpscaleOptions) -> tuple[int, int] | None:
    target_width = options.target_width
    target_height = options.target_height
    if target_width is None and target_height is None:
        return None
    if target_width is None:
        target_width = round(img.width * (target_height / img.height))
    if target_height is None:
        target_height = round(img.height * (target_width / img.width))
    return max(1, int(target_width)), max(1, int(target_height))


def _target_process_scale(img: Image.Image, target_size: tuple[int, int]) -> float:
    return max(target_size[0] / img.width, target_size[1] / img.height)


def _select_auto_mode(img: Image.Image, options: UpscaleOptions) -> str:
    """Pick a conservative default for graphics and a neural mode for natural images."""
    if options.face_enhance:
        return "photo"

    rgba = img.convert("RGBA")
    alpha = np.asarray(rgba.getchannel("A"))
    transparent_ratio = float((alpha < 250).mean())

    rgb = rgba.convert("RGB")
    sample = rgb.copy()
    sample.thumbnail((192, 192), Image.Resampling.BILINEAR)
    arr = np.asarray(sample)
    quantized = (arr // 32).reshape(-1, 3)
    unique_bins = len({tuple(pixel) for pixel in quantized})

    gray = sample.convert("L")
    gray_arr = np.asarray(gray).astype("float32")
    contrast = float(gray_arr.std())
    edges = np.asarray(gray.filter(ImageFilter.FIND_EDGES)).astype("float32")
    edge_density = float((edges > 38).mean())

    is_low_color = unique_bins <= 140
    is_very_low_color = unique_bins <= 36
    is_hard_edge = 0.045 <= edge_density <= 0.35 and contrast >= 28

    if transparent_ratio >= 0.01:
        return "conservative"
    if is_very_low_color and 0.018 <= edge_density <= 0.35 and contrast >= 35:
        return "conservative"
    if is_low_color and is_hard_edge:
        return "anime"
    if options.denoise >= 0.7:
        return "general"
    return "photo"


def _normalize_device(requested: str) -> str:
    device = (requested or "auto").lower().strip()
    if device == "auto":
        device = os.getenv("UPSCALER_DEVICE", "auto").lower().strip()
    if device == "gpu":
        device = "cuda"
    if device in {"auto", "cpu"} or device.startswith("cuda"):
        return device
    raise ValueError("Upscale device must be auto, cpu, or cuda.")


def _open_image(raw: bytes) -> Image.Image:
    try:
        img = Image.open(io.BytesIO(raw))
        img = ImageOps.exif_transpose(img)
        if img.mode not in {"RGB", "RGBA", "L"}:
            img = img.convert("RGBA" if "A" in img.getbands() else "RGB")
        if img.mode == "RGBA" and img.getchannel("A").getextrema() == (255, 255):
            img = img.convert("RGB")
        return img.copy()
    except Exception as exc:
        raise ValueError("Unsupported or corrupted image.") from exc


def _conservative_resize(img: Image.Image, scale: float) -> Image.Image:
    target = (round(img.width * scale), round(img.height * scale))
    return _resize_to_target(img, target)


def _resize_to_target(img: Image.Image, target: tuple[int, int]) -> Image.Image:
    resized = img.resize(target, Image.Resampling.LANCZOS)
    # A mild radius keeps text and line art cleaner without inventing new texture.
    return resized.filter(ImageFilter.UnsharpMask(radius=1.2, percent=70, threshold=4))


def _neural_resize(img: Image.Image, options: UpscaleOptions) -> tuple[Image.Image, str]:
    try:
        import cv2
        import torch
        from basicsr.archs.rrdbnet_arch import RRDBNet
        from basicsr.utils.download_util import load_file_from_url
        from realesrgan import RealESRGANer
        from realesrgan.archs.srvgg_arch import SRVGGNetCompact
    except Exception as exc:
        raise RuntimeError(
            "The neural upscaling dependencies are not available. Rebuild the Docker image or use conservative mode."
        ) from exc

    spec = MODEL_SPECS[options.mode]
    device = _select_device(torch, options.device)
    device_key = str(device)
    half = device.type == "cuda"

    with _cache_lock:
        upsampler = _upsampler_cache.get((spec.key, device_key))
        if upsampler is None:
            MODEL_DIR.mkdir(parents=True, exist_ok=True)
            model_path = _download_model(load_file_from_url, spec.model_url)
            dni_weight = None
            if spec.dni_url:
                dni_path = _download_model(load_file_from_url, spec.dni_url)
                model_path = [model_path, dni_path]
                dni_weight = [options.denoise, 1 - options.denoise]

            model = _build_model(spec, RRDBNet, SRVGGNetCompact)
            upsampler = RealESRGANer(
                scale=spec.scale,
                model_path=model_path,
                dni_weight=dni_weight,
                model=model,
                tile=options.tile,
                tile_pad=10,
                pre_pad=0,
                half=half,
                device=device,
            )
            _upsampler_cache[(spec.key, device_key)] = upsampler

    upsampler.tile = options.tile
    if spec.dni_url and hasattr(upsampler, "dni_weight"):
        upsampler.dni_weight = [options.denoise, 1 - options.denoise]

    cv_img = _pil_to_cv(img, cv2)
    try:
        if options.face_enhance:
            face_enhancer = _get_face_enhancer(device_key, max(1, round(options.scale)), upsampler)
            _, _, output = face_enhancer.enhance(
                cv_img,
                has_aligned=False,
                only_center_face=False,
                paste_back=True,
            )
            engine = f"{spec.display_name} + GFPGAN ({device.type.upper()})"
        else:
            output, _ = upsampler.enhance(cv_img, outscale=options.scale)
            engine = f"{spec.display_name} ({device.type.upper()})"
    except RuntimeError as exc:
        if "out of memory" in str(exc).lower() and options.tile == 0:
            raise RuntimeError("Upscale ran out of memory. Retry with tile size 256 or 128.") from exc
        raise

    return _cv_to_pil(output, cv2), engine


def _build_model(spec: ModelSpec, rrdb_cls: Any, srvgg_cls: Any) -> Any:
    if spec.arch == "rrdb":
        return rrdb_cls(
            num_in_ch=3,
            num_out_ch=3,
            num_feat=64,
            num_block=spec.num_block,
            num_grow_ch=32,
            scale=spec.scale,
        )
    if spec.arch == "srvgg":
        return srvgg_cls(
            num_in_ch=3,
            num_out_ch=3,
            num_feat=64,
            num_conv=spec.num_block,
            upscale=spec.scale,
            act_type="prelu",
        )
    raise ValueError(f"Unknown model architecture: {spec.arch}")


def _select_device(torch: Any, requested: str) -> Any:
    if requested == "cpu":
        return torch.device("cpu")
    if requested.startswith("cuda"):
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA was selected for this upscale job, but CUDA is not available in this container.")
        return torch.device(requested)
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _download_model(load_file_from_url: Any, url: str) -> str:
    return load_file_from_url(url=url, model_dir=str(MODEL_DIR), progress=True, file_name=None)


def _get_face_enhancer(device_key: str, scale: int, bg_upsampler: Any) -> Any:
    try:
        from basicsr.utils.download_util import load_file_from_url
        from gfpgan import GFPGANer
    except Exception as exc:
        raise RuntimeError("GFPGAN face restoration dependencies are not available.") from exc

    cache_key = ("GFPGANv1.3", device_key, scale)
    with _cache_lock:
        face_enhancer = _face_cache.get(cache_key)
        if face_enhancer is None:
            model_path = _download_model(load_file_from_url, GFPGAN_URL)
            face_enhancer = GFPGANer(
                model_path=model_path,
                upscale=scale,
                arch="clean",
                channel_multiplier=2,
                bg_upsampler=bg_upsampler,
            )
            _face_cache[cache_key] = face_enhancer
        return face_enhancer


def _pil_to_cv(img: Image.Image, cv2: Any) -> np.ndarray:
    if img.mode == "RGBA":
        return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGBA2BGRA)
    if img.mode == "L":
        return np.asarray(img)
    return cv2.cvtColor(np.asarray(img.convert("RGB")), cv2.COLOR_RGB2BGR)


def _cv_to_pil(img: np.ndarray, cv2: Any) -> Image.Image:
    if img.ndim == 2:
        return Image.fromarray(img, mode="L")
    if img.shape[2] == 4:
        return Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA))
    return Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))


def _encode(img: Image.Image, output_format: str) -> tuple[bytes, str, str]:
    output_format = "jpeg" if output_format == "jpg" else output_format
    ext = "jpg" if output_format == "jpeg" else output_format
    media_type = f"image/{output_format}"

    save_img = img
    params: dict[str, Any] = {}
    if output_format == "jpeg":
        save_img = img.convert("RGB")
        params.update(quality=95, subsampling=0, optimize=True)
    elif output_format == "webp":
        params.update(quality=95, method=6)
    elif output_format == "png":
        params.update(optimize=True)

    buffer = io.BytesIO()
    save_img.save(buffer, format=output_format.upper(), **params)
    return buffer.getvalue(), ext, media_type
