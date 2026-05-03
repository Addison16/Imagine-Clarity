from __future__ import annotations

import io
import os
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image

MODEL_DIR = Path(os.getenv("MODEL_DIR", "/models"))
REMBG_MODEL_DIR = MODEL_DIR / "rembg"
os.environ.setdefault("U2NET_HOME", str(REMBG_MODEL_DIR))

BACKGROUND_MODELS: dict[str, str] = {
    "auto": "auto",
    "logo": "edge-color",
    "accurate": "isnet-general-use",
    "balanced": "u2net",
    "fast": "u2netp",
    "anime": "isnet-anime",
    "portrait": "u2net_human_seg",
    "biref-lite": "birefnet-general-lite",
}

BACKGROUND_CUT_MODES: dict[str, tuple[int, int]] = {
    "preserve": (200, 2),
    "balanced": (230, 10),
    "strong": (245, 24),
}

SUPPORTED_BG_FORMATS = {"png", "webp"}

_session_cache: dict[str, Any] = {}
_cache_lock = threading.Lock()


@dataclass(frozen=True)
class BackgroundOptions:
    model: str = "auto"
    cut_mode: str = "balanced"
    alpha_matting: bool = True
    edge_refine: int = 8
    background_tolerance: int = 34
    post_process_mask: bool = True
    preserve_interior: bool = True
    respect_existing_alpha: bool = True
    output_format: str = "png"


@dataclass(frozen=True)
class BackgroundResult:
    data: bytes
    width: int
    height: int
    extension: str
    media_type: str
    engine: str


def remove_background(raw: bytes, options: BackgroundOptions) -> BackgroundResult:
    options = _normalize_options(options)
    source_img = Image.open(io.BytesIO(raw)).convert("RGBA")

    if options.respect_existing_alpha and _has_existing_cutout(source_img):
        encoded, extension, media_type = _encode(source_img, options.output_format)
        return BackgroundResult(
            data=encoded,
            width=source_img.width,
            height=source_img.height,
            extension=extension,
            media_type=media_type,
            engine="existing-alpha (passthrough)",
        )

    if options.model == "logo" or (
        options.model == "auto" and _should_use_edge_color_cut(source_img, options.background_tolerance)
    ):
        img = _edge_color_cutout(source_img, options)
        encoded, extension, media_type = _encode(img, options.output_format)
        return BackgroundResult(
            data=encoded,
            width=img.width,
            height=img.height,
            extension=extension,
            media_type=media_type,
            engine="edge-color safe cut",
        )

    try:
        from rembg import new_session, remove
        providers = _select_onnx_providers()
    except Exception as exc:
        raise RuntimeError("The background-removal dependencies are not available. Rebuild the Docker image.") from exc

    model_name = "isnet-general-use" if options.model == "auto" else BACKGROUND_MODELS[options.model]
    provider_key = ",".join(providers)
    with _cache_lock:
        session = _session_cache.get(f"{model_name}:{provider_key}")
        if session is None:
            REMBG_MODEL_DIR.mkdir(parents=True, exist_ok=True)
            session = new_session(model_name, providers=providers)
            _session_cache[f"{model_name}:{provider_key}"] = session

    try:
        foreground_threshold, background_threshold = BACKGROUND_CUT_MODES[options.cut_mode]
        result = remove(
            raw,
            session=session,
            alpha_matting=options.alpha_matting,
            alpha_matting_foreground_threshold=foreground_threshold,
            alpha_matting_background_threshold=background_threshold,
            alpha_matting_erode_size=options.edge_refine,
            post_process_mask=options.post_process_mask,
            force_return_bytes=True,
        )
    except Exception as exc:
        raise RuntimeError(f"Background removal failed: {exc}") from exc

    img = Image.open(io.BytesIO(result)).convert("RGBA")
    if options.preserve_interior:
        img = _preserve_interior_alpha(img, source_img)
    encoded, extension, media_type = _encode(img, options.output_format)
    active_providers = getattr(getattr(session, "inner_session", None), "get_providers", lambda: providers)()
    return BackgroundResult(
        data=encoded,
        width=img.width,
        height=img.height,
        extension=extension,
        media_type=media_type,
        engine=f"{model_name} ({active_providers[0]})",
    )


def _normalize_options(options: BackgroundOptions) -> BackgroundOptions:
    model = options.model.lower().strip()
    if model not in BACKGROUND_MODELS:
        allowed = ", ".join(sorted(BACKGROUND_MODELS))
        raise ValueError(f"Background model must be one of: {allowed}.")

    cut_mode = options.cut_mode.lower().strip()
    if cut_mode not in BACKGROUND_CUT_MODES:
        allowed = ", ".join(sorted(BACKGROUND_CUT_MODES))
        raise ValueError(f"Background cut mode must be one of: {allowed}.")

    edge_refine = max(0, min(20, int(options.edge_refine)))
    background_tolerance = max(4, min(96, int(options.background_tolerance)))

    output_format = options.output_format.lower().strip()
    if output_format not in SUPPORTED_BG_FORMATS:
        raise ValueError("Background removal output format must be png or webp.")

    return BackgroundOptions(
        model=model,
        cut_mode=cut_mode,
        alpha_matting=bool(options.alpha_matting),
        edge_refine=edge_refine,
        background_tolerance=background_tolerance,
        post_process_mask=bool(options.post_process_mask),
        preserve_interior=bool(options.preserve_interior),
        respect_existing_alpha=bool(options.respect_existing_alpha),
        output_format=output_format,
    )


def _has_existing_cutout(img: Image.Image) -> bool:
    import numpy as np

    alpha = np.array(img.getchannel("A"))
    transparent = alpha <= 8
    if transparent.mean() < 0.01:
        return False

    edge = np.concatenate((alpha[0, :], alpha[-1, :], alpha[:, 0], alpha[:, -1]))
    return bool((edge <= 8).mean() > 0.05)


def _should_use_edge_color_cut(img: Image.Image, tolerance: int) -> bool:
    import numpy as np

    arr = np.array(img.convert("RGBA"))
    rgb = arr[:, :, :3].astype("int16")
    alpha = arr[:, :, 3]
    edge_rgb = _edge_pixels(rgb)
    edge_alpha = _edge_pixels(alpha)
    edge_rgb = edge_rgb[edge_alpha > 16]
    if len(edge_rgb) < 20:
        return False

    bg_color = np.median(edge_rgb, axis=0)
    edge_dist = np.sqrt(np.sum((edge_rgb - bg_color) ** 2, axis=1))
    edge_consistency = float((edge_dist <= max(tolerance, 28)).mean())
    edge_texture = float(np.mean(np.std(edge_rgb, axis=0)))
    if edge_consistency < 0.62 or edge_texture > 42:
        return False

    small = Image.fromarray(arr[:, :, :3], mode="RGB")
    small.thumbnail((160, 160), Image.Resampling.BILINEAR)
    small_arr = np.array(small)
    quantized = (small_arr // 32).reshape(-1, 3)
    unique_bins = len({tuple(pixel) for pixel in quantized})
    return unique_bins <= 220


def _edge_color_cutout(source_img: Image.Image, options: BackgroundOptions) -> Image.Image:
    import cv2
    import numpy as np

    source = source_img.convert("RGBA")
    arr = np.array(source)
    rgb = arr[:, :, :3].astype("int16")
    source_alpha = arr[:, :, 3]

    edge_rgb = _edge_pixels(rgb)
    edge_alpha = _edge_pixels(source_alpha)
    edge_rgb = edge_rgb[edge_alpha > 16]
    if len(edge_rgb) == 0:
        return source

    bg_color = np.median(edge_rgb, axis=0)
    multiplier = {"preserve": 0.75, "balanced": 1.0, "strong": 1.35}[options.cut_mode]
    tolerance = max(4, int(round(options.background_tolerance * multiplier)))
    feather = max(2, min(24, options.edge_refine + 4))
    distance = np.sqrt(np.sum((rgb - bg_color) ** 2, axis=2))

    flood_limit = tolerance + feather
    flood_candidate = ((distance <= flood_limit) | (source_alpha <= 8)).astype("uint8")
    background = _edge_connected_mask(flood_candidate)
    if not options.preserve_interior:
        background = flood_candidate.astype(bool)

    alpha = source_alpha.astype("float32")
    ramp = ((distance - tolerance) / max(1, feather) * 255).clip(0, 255)
    alpha[background] = np.minimum(alpha[background], ramp[background])
    alpha[source_alpha <= 8] = 0

    if options.post_process_mask:
        alpha = _clean_alpha(alpha, options.edge_refine, cv2)

    result = arr.copy()
    result[:, :, 3] = alpha.clip(0, 255).astype("uint8")
    return Image.fromarray(result, mode="RGBA")


def _edge_pixels(arr: "Any") -> "Any":
    import numpy as np

    return np.concatenate((arr[0, ...], arr[-1, ...], arr[:, 0, ...], arr[:, -1, ...]), axis=0)


def _edge_connected_mask(candidate: "Any") -> "Any":
    import cv2
    import numpy as np

    external = candidate.copy().astype("uint8")
    height, width = external.shape
    fill_mask = np.zeros((height + 2, width + 2), dtype="uint8")

    def fill_from(x: int, y: int) -> None:
        if external[y, x] == 1:
            cv2.floodFill(external, fill_mask, (x, y), 2)

    for x in range(width):
        fill_from(x, 0)
        fill_from(x, height - 1)
    for y in range(height):
        fill_from(0, y)
        fill_from(width - 1, y)

    return external == 2


def _clean_alpha(alpha: "Any", edge_refine: int, cv2: "Any") -> "Any":
    soft = cv2.GaussianBlur(alpha.astype("float32"), (0, 0), sigmaX=max(0.35, edge_refine / 12))
    edge_band = (alpha > 0) & (alpha < 255)
    refined = alpha.copy()
    refined[edge_band] = soft[edge_band]
    refined[refined < 2] = 0
    refined[refined > 253] = 255
    return refined


def _preserve_interior_alpha(img: Image.Image, source_img: Image.Image) -> Image.Image:
    import cv2
    import numpy as np

    if source_img.size != img.size:
        source_img = source_img.resize(img.size, Image.Resampling.LANCZOS)

    alpha = np.array(img.getchannel("A"))
    source = np.array(source_img.convert("RGBA"))
    source_alpha = source[:, :, 3]
    transparent = (alpha <= 32).astype("uint8")
    if not transparent.any():
        return img

    height, width = transparent.shape
    external = transparent.copy()
    fill_mask = np.zeros((height + 2, width + 2), dtype="uint8")

    def fill_from(x: int, y: int) -> None:
        if external[y, x] == 1:
            cv2.floodFill(external, fill_mask, (x, y), 2)

    for x in range(width):
        fill_from(x, 0)
        fill_from(x, height - 1)
    for y in range(height):
        fill_from(0, y)
        fill_from(width - 1, y)

    enclosed_holes = (transparent == 1) & (external != 2) & (source_alpha > 64)
    if not enclosed_holes.any():
        return img

    restored = np.array(img.convert("RGBA"))
    restored[enclosed_holes] = source[enclosed_holes]
    return Image.fromarray(restored, mode="RGBA")


def _encode(img: Image.Image, output_format: str) -> tuple[bytes, str, str]:
    buffer = io.BytesIO()
    if output_format == "webp":
        img.save(buffer, format="WEBP", lossless=True, method=6)
        return buffer.getvalue(), "webp", "image/webp"

    img.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue(), "png", "image/png"


def _select_onnx_providers() -> list[str]:
    requested = os.getenv("REMBG_DEVICE", os.getenv("UPSCALER_DEVICE", "auto")).lower()
    if requested == "cpu":
        return ["CPUExecutionProvider"]

    torch_cuda_available = False
    try:
        import torch

        torch_cuda_available = bool(torch.cuda.is_available())
    except Exception:
        torch_cuda_available = False

    import onnxruntime as ort

    available = ort.get_available_providers()
    if torch_cuda_available and "CUDAExecutionProvider" in available:
        return ["CUDAExecutionProvider", "CPUExecutionProvider"]
    return ["CPUExecutionProvider"]
