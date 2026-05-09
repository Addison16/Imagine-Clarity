from __future__ import annotations

import io
import os
import threading
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageFilter, ImageOps

SUPPORTED_FORMATS = {"png", "jpeg", "jpg", "webp", "tiff", "tif"}
MODEL_DIR = Path(os.getenv("MODEL_DIR", "/models"))
RESIZE_METHODS = {"auto", "nearest", "bilinear", "bicubic", "lanczos", "mitchell", "preserve"}
TARGET_FIT_MODES = {"stretch", "contain", "pad", "crop", "cover"}
CANVAS_ANCHORS = {
    "center",
    "top-left",
    "top",
    "top-right",
    "left",
    "right",
    "bottom-left",
    "bottom",
    "bottom-right",
}


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
    resize_method: str = "lanczos"
    target_fit: str = "stretch"
    canvas_width: int | None = None
    canvas_height: int | None = None
    canvas_anchor: str = "center"
    dpi: int | None = None
    export_quality: int = 95
    sharpen_amount: int = 70


@dataclass(frozen=True)
class UpscaleResult:
    data: bytes
    width: int
    height: int
    extension: str
    media_type: str
    engine: str


@dataclass(frozen=True)
class ResizePlan:
    content_size: tuple[int, int]
    target_box: tuple[int, int] | None
    fit_mode: str
    final_size: tuple[int, int]


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
    resize_plan = _resolve_resize_plan(img.width, img.height, options)
    process_scale = _target_process_scale(img, resize_plan.content_size)
    if process_scale > MAX_UPSCALE_FACTOR:
        raise ValueError("Target resolution can be up to 8x the source image.")

    auto_selected = options.mode == "auto"
    if auto_selected:
        options = replace(options, mode=_select_auto_mode(img, options))

    has_target = resize_plan.target_box is not None
    if has_target and process_scale <= 1.0:
        output = _resize_to_target(img, resize_plan.content_size, options)
        engine = f"Target {options.resize_method} resize (CPU)"
    elif has_target and options.mode == "conservative":
        output = _resize_to_target(img, resize_plan.content_size, options)
        engine = f"Target conservative {options.resize_method} resize (CPU)"
    elif options.mode == "conservative":
        output = _conservative_resize(img, options.scale, options)
        engine = f"{options.resize_method} resize (CPU)"
    else:
        run_options = replace(options, scale=process_scale) if has_target else options
        output, engine = _neural_resize(img, run_options)
        if has_target and output.size != resize_plan.content_size:
            output = _resize_to_target(output, resize_plan.content_size, options)
            engine = f"{engine} + target resize"

    output = _apply_resize_plan(output, resize_plan, options)
    output = _apply_canvas(output, _resolve_canvas_size(output, options), options.canvas_anchor)

    if auto_selected:
        engine = f"Auto: {MODE_LABELS[options.mode]} -> {engine}"
    if resize_plan.fit_mode in {"pad", "crop", "cover", "contain"}:
        engine = f"{engine} + {resize_plan.fit_mode} target"
    if options.canvas_width or options.canvas_height:
        engine = f"{engine} + canvas {options.canvas_anchor}"

    encoded, extension, media_type = _encode(output, options.output_format, options)
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
    if output_format == "tif":
        output_format = "tiff"
    if output_format not in SUPPORTED_FORMATS:
        raise ValueError("Output format must be png, jpeg, jpg, webp, tif, or tiff.")

    target_width = _normalize_target_dimension(options.target_width, "Target width")
    target_height = _normalize_target_dimension(options.target_height, "Target height")
    canvas_width = _normalize_target_dimension(options.canvas_width, "Canvas width")
    canvas_height = _normalize_target_dimension(options.canvas_height, "Canvas height")

    resize_method = options.resize_method.lower().strip()
    if resize_method not in RESIZE_METHODS:
        raise ValueError("Resize method must be auto, nearest, bilinear, bicubic, lanczos, mitchell, or preserve.")
    if resize_method == "auto":
        resize_method = "lanczos"

    target_fit = options.target_fit.lower().strip().replace("_", "-")
    if target_fit == "fill":
        target_fit = "cover"
    if target_fit not in TARGET_FIT_MODES:
        raise ValueError("Target fit must be stretch, contain, pad, crop, or cover.")

    canvas_anchor = options.canvas_anchor.lower().strip().replace("_", "-")
    if canvas_anchor not in CANVAS_ANCHORS:
        raise ValueError("Canvas anchor must be center, top, bottom, left, right, or a corner.")

    dpi = None if options.dpi in {None, 0} else int(options.dpi)
    if dpi is not None and not 1 <= dpi <= 2400:
        raise ValueError("DPI must be between 1 and 2400.")

    export_quality = max(1, min(int(options.export_quality), 100))
    sharpen_amount = max(0, min(int(options.sharpen_amount), 200))

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
        resize_method=resize_method,
        target_fit=target_fit,
        canvas_width=canvas_width,
        canvas_height=canvas_height,
        canvas_anchor=canvas_anchor,
        dpi=dpi,
        export_quality=export_quality,
        sharpen_amount=sharpen_amount,
    )


def _normalize_target_dimension(value: int | None, label: str) -> int | None:
    if value is None:
        return None
    value = int(value)
    if value <= 0:
        raise ValueError(f"{label} must be a positive number.")
    return value


def resolve_upscale_sizes(width: int, height: int, options: UpscaleOptions) -> tuple[tuple[int, int], tuple[int, int]]:
    options = _normalize_options(options)
    plan = _resolve_resize_plan(width, height, options)
    return plan.content_size, plan.final_size


def _resolve_resize_plan(width: int, height: int, options: UpscaleOptions) -> ResizePlan:
    target_box = _resolve_target_box(width, height, options)
    if target_box is None:
        content_size = (max(1, round(width * options.scale)), max(1, round(height * options.scale)))
        final_size = _resolve_canvas_size_for_dimensions(content_size[0], content_size[1], options)
        return ResizePlan(content_size=content_size, target_box=None, fit_mode="scale", final_size=final_size)

    both_dimensions = options.target_width is not None and options.target_height is not None
    fit_mode = options.target_fit if both_dimensions else "contain"
    if fit_mode == "stretch":
        content_size = target_box
        final_size = target_box
    elif fit_mode == "contain":
        content_size = _fit_inside((width, height), target_box)
        final_size = content_size
    elif fit_mode == "pad":
        content_size = _fit_inside((width, height), target_box)
        final_size = target_box
    elif fit_mode in {"crop", "cover"}:
        content_size = _cover_box((width, height), target_box)
        final_size = target_box
    else:
        raise ValueError("Unsupported target fit mode.")

    final_size = _resolve_canvas_size_for_dimensions(final_size[0], final_size[1], options)
    return ResizePlan(content_size=content_size, target_box=target_box, fit_mode=fit_mode, final_size=final_size)


def _resolve_target_box(width: int, height: int, options: UpscaleOptions) -> tuple[int, int] | None:
    target_width = options.target_width
    target_height = options.target_height
    if target_width is None and target_height is None:
        return None
    if target_width is None:
        target_width = round(width * (target_height / height))
    if target_height is None:
        target_height = round(height * (target_width / width))
    return max(1, int(target_width)), max(1, int(target_height))


def _fit_inside(source: tuple[int, int], target: tuple[int, int]) -> tuple[int, int]:
    scale = min(target[0] / source[0], target[1] / source[1])
    return max(1, round(source[0] * scale)), max(1, round(source[1] * scale))


def _cover_box(source: tuple[int, int], target: tuple[int, int]) -> tuple[int, int]:
    scale = max(target[0] / source[0], target[1] / source[1])
    return max(1, round(source[0] * scale)), max(1, round(source[1] * scale))


def _resolve_canvas_size_for_dimensions(width: int, height: int, options: UpscaleOptions) -> tuple[int, int]:
    return options.canvas_width or width, options.canvas_height or height


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


def _conservative_resize(img: Image.Image, scale: float, options: UpscaleOptions) -> Image.Image:
    target = (round(img.width * scale), round(img.height * scale))
    return _resize_to_target(img, target, options)


def _resize_to_target(img: Image.Image, target: tuple[int, int], options: UpscaleOptions) -> Image.Image:
    resample = _resample_filter(options.resize_method)
    if img.mode == "RGBA" and img.getchannel("A").getextrema()[0] < 255:
        resized = _resize_rgba_alpha_safe(img, target, resample)
    else:
        resized = img.resize(target, resample)
    if options.resize_method in {"nearest", "preserve"}:
        return resized
    return _unsharp_preserving_alpha(resized, options.sharpen_amount)


def _resample_filter(method: str) -> int:
    if method in {"nearest", "preserve"}:
        return Image.Resampling.NEAREST
    if method == "bilinear":
        return Image.Resampling.BILINEAR
    if method in {"bicubic", "mitchell"}:
        return Image.Resampling.BICUBIC
    return Image.Resampling.LANCZOS


def _resize_rgba_alpha_safe(img: Image.Image, target: tuple[int, int], resample: int) -> Image.Image:
    rgba = img.convert("RGBA")
    arr = np.asarray(rgba).astype("float32")
    alpha = arr[:, :, 3]
    alpha_norm = alpha[:, :, None] / 255.0
    premultiplied = arr[:, :, :3] * alpha_norm

    premul_img = Image.fromarray(premultiplied.clip(0, 255).astype("uint8"), mode="RGB")
    alpha_img = Image.fromarray(alpha.clip(0, 255).astype("uint8"), mode="L")
    resized_premul = np.asarray(premul_img.resize(target, resample)).astype("float32")
    resized_alpha = np.asarray(alpha_img.resize(target, resample)).astype("float32")

    divisor = np.maximum(resized_alpha[:, :, None] / 255.0, 1 / 255.0)
    rgb = resized_premul / divisor
    rgb[resized_alpha <= 1] = 0

    out = np.dstack((rgb.clip(0, 255), resized_alpha.clip(0, 255))).astype("uint8")
    return Image.fromarray(out, mode="RGBA")


def _unsharp_preserving_alpha(img: Image.Image, percent: int) -> Image.Image:
    if percent <= 0:
        return img
    if img.mode != "RGBA":
        return img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=percent, threshold=4))

    alpha = img.getchannel("A")
    sharpened = img.convert("RGB").filter(ImageFilter.UnsharpMask(radius=1.2, percent=percent, threshold=4))
    sharpened.putalpha(alpha)
    return sharpened


def _apply_resize_plan(img: Image.Image, plan: ResizePlan, options: UpscaleOptions) -> Image.Image:
    if not plan.target_box:
        return img
    if plan.fit_mode == "pad":
        return _apply_canvas(img, plan.target_box, options.canvas_anchor)
    if plan.fit_mode in {"crop", "cover"}:
        return _crop_to_canvas(img, plan.target_box, options.canvas_anchor)
    return img


def _resolve_canvas_size(img: Image.Image, options: UpscaleOptions) -> tuple[int, int]:
    return options.canvas_width or img.width, options.canvas_height or img.height


def _apply_canvas(img: Image.Image, canvas_size: tuple[int, int], anchor: str) -> Image.Image:
    if img.size == canvas_size:
        return img
    if canvas_size[0] <= img.width and canvas_size[1] <= img.height:
        return _crop_to_canvas(img, canvas_size, anchor)

    source = img.convert("RGBA")
    canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    offset = _anchor_offset(source.size, canvas_size, anchor)
    canvas.paste(source, offset)
    return canvas


def _crop_to_canvas(img: Image.Image, canvas_size: tuple[int, int], anchor: str) -> Image.Image:
    left, top = _crop_origin(img.size, canvas_size, anchor)
    return img.crop((left, top, left + canvas_size[0], top + canvas_size[1]))


def _anchor_offset(source: tuple[int, int], canvas: tuple[int, int], anchor: str) -> tuple[int, int]:
    return _crop_origin(canvas, source, anchor)


def _crop_origin(source: tuple[int, int], target: tuple[int, int], anchor: str) -> tuple[int, int]:
    extra_x = source[0] - target[0]
    extra_y = source[1] - target[1]
    if "left" in anchor:
        left = 0
    elif "right" in anchor:
        left = extra_x
    else:
        left = extra_x // 2

    if "top" in anchor:
        top = 0
    elif "bottom" in anchor:
        top = extra_y
    else:
        top = extra_y // 2
    return int(left), int(top)


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


def _encode(img: Image.Image, output_format: str, options: UpscaleOptions) -> tuple[bytes, str, str]:
    output_format = "jpeg" if output_format == "jpg" else output_format
    output_format = "tiff" if output_format == "tif" else output_format
    ext = "jpg" if output_format == "jpeg" else output_format
    media_type = "image/tiff" if output_format == "tiff" else f"image/{output_format}"

    save_img = img
    params: dict[str, Any] = {}
    if options.dpi:
        params["dpi"] = (options.dpi, options.dpi)
    if output_format == "jpeg":
        if img.mode == "RGBA":
            background = Image.new("RGB", img.size, "#ffffff")
            background.paste(img, mask=img.getchannel("A"))
            save_img = background
        else:
            save_img = img.convert("RGB")
        params.update(quality=options.export_quality, subsampling=0, optimize=True)
    elif output_format == "webp":
        params.update(quality=options.export_quality, method=6)
    elif output_format == "png":
        params.update(optimize=True)
    elif output_format == "tiff":
        params.update(compression="tiff_lzw")

    buffer = io.BytesIO()
    pil_format = "TIFF" if output_format == "tiff" else output_format.upper()
    save_img.save(buffer, format=pil_format, **params)
    return buffer.getvalue(), ext, media_type
