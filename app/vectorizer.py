from __future__ import annotations

import io
import xml.etree.ElementTree as ET
from dataclasses import dataclass

from PIL import Image

SUPPORTED_VECTOR_FORMATS = {"svg"}
VECTOR_COLORMODES = {"color", "binary"}
VECTOR_HIERARCHIES = {"stacked", "cutout"}
VECTOR_MODES = {"spline", "polygon", "none"}
VECTOR_PRESETS = {"logo", "artwork", "photo", "line-art"}


@dataclass(frozen=True)
class VectorizeOptions:
    preset: str = "logo"
    colormode: str | None = None
    hierarchical: str | None = None
    mode: str | None = None
    filter_speckle: int | None = None
    color_precision: int | None = None
    layer_difference: int | None = None
    corner_threshold: int | None = None
    length_threshold: float | None = None
    max_iterations: int | None = None
    splice_threshold: int | None = None
    path_precision: int | None = None


@dataclass(frozen=True)
class VectorizeResult:
    data: bytes
    width: int
    height: int
    extension: str
    media_type: str
    engine: str
    options: VectorizeOptions


def vectorize_image(raw: bytes, options: VectorizeOptions) -> VectorizeResult:
    options = normalize_vector_options(options)
    try:
        import vtracer
    except Exception as exc:
        raise RuntimeError("The vectorization dependency is not available. Rebuild the Docker image.") from exc

    with Image.open(io.BytesIO(raw)) as image:
        width, height = image.size
        png_buffer = io.BytesIO()
        image.convert("RGBA").save(png_buffer, format="PNG")

    try:
        svg_text = vtracer.convert_raw_image_to_svg(
            png_buffer.getvalue(),
            img_format="png",
            colormode=options.colormode,
            hierarchical=options.hierarchical,
            mode=options.mode,
            filter_speckle=options.filter_speckle,
            color_precision=options.color_precision,
            layer_difference=options.layer_difference,
            corner_threshold=options.corner_threshold,
            length_threshold=options.length_threshold,
            max_iterations=options.max_iterations,
            splice_threshold=options.splice_threshold,
            path_precision=options.path_precision,
        )
    except Exception as exc:
        raise RuntimeError(f"Vectorization failed: {exc}") from exc

    stripped = svg_text.strip()
    try:
        root = ET.fromstring(stripped)
    except ET.ParseError as exc:
        raise RuntimeError("Vectorization produced malformed SVG output.") from exc
    if root.tag.rsplit("}", 1)[-1].lower() != "svg":
        raise RuntimeError("Vectorization produced malformed SVG output.")
    svg_text = stripped
    return VectorizeResult(
        data=svg_text.encode("utf-8"),
        width=width,
        height=height,
        extension="svg",
        media_type="image/svg+xml",
        engine=f"VTracer {options.preset} ({options.colormode}, {options.mode})",
        options=options,
    )


def normalize_vector_options(options: VectorizeOptions) -> VectorizeOptions:
    preset = (options.preset or "logo").lower().strip().replace("_", "-")
    if preset not in VECTOR_PRESETS:
        raise ValueError(f"Vector preset must be one of: {', '.join(sorted(VECTOR_PRESETS))}.")

    # Presets bias toward practical shop artwork defaults; explicit form values can still override them.
    preset_defaults = {
        "logo": {"colormode": "color", "hierarchical": "stacked", "mode": "spline", "filter_speckle": 4, "color_precision": 6, "layer_difference": 16, "corner_threshold": 60, "length_threshold": 4.0, "path_precision": 3},
        "artwork": {"colormode": "color", "hierarchical": "stacked", "mode": "spline", "filter_speckle": 6, "color_precision": 7, "layer_difference": 12, "corner_threshold": 55, "length_threshold": 4.0, "path_precision": 4},
        "photo": {"colormode": "color", "hierarchical": "stacked", "mode": "spline", "filter_speckle": 8, "color_precision": 5, "layer_difference": 24, "corner_threshold": 70, "length_threshold": 6.0, "path_precision": 3},
        "line-art": {"colormode": "binary", "hierarchical": "stacked", "mode": "spline", "filter_speckle": 3, "color_precision": 6, "layer_difference": 16, "corner_threshold": 50, "length_threshold": 3.8, "path_precision": 3},
    }[preset]

    colormode = (options.colormode or preset_defaults["colormode"]).lower().strip()
    hierarchical = (options.hierarchical or preset_defaults["hierarchical"]).lower().strip()
    mode = (options.mode or preset_defaults["mode"]).lower().strip()
    if colormode not in VECTOR_COLORMODES:
        raise ValueError("Vector color mode must be color or binary.")
    if hierarchical not in VECTOR_HIERARCHIES:
        raise ValueError("Vector layering must be stacked or cutout.")
    if mode not in VECTOR_MODES:
        raise ValueError("Vector curve mode must be spline, polygon, or none.")

    return VectorizeOptions(
        preset=preset,
        colormode=colormode,
        hierarchical=hierarchical,
        mode=mode,
        filter_speckle=_clamp_int(options.filter_speckle, 0, 128, int(preset_defaults["filter_speckle"])),
        color_precision=_clamp_int(options.color_precision, 1, 8, int(preset_defaults["color_precision"])),
        layer_difference=_clamp_int(options.layer_difference, 0, 255, int(preset_defaults["layer_difference"])),
        corner_threshold=_clamp_int(options.corner_threshold, 0, 180, int(preset_defaults["corner_threshold"])),
        length_threshold=_clamp_float(options.length_threshold, 3.5, 10.0, float(preset_defaults["length_threshold"])),
        max_iterations=_clamp_int(options.max_iterations, 1, 50, 10),
        splice_threshold=_clamp_int(options.splice_threshold, 0, 180, 45),
        path_precision=_clamp_int(options.path_precision, 0, 8, int(preset_defaults["path_precision"])),
    )


def _clamp_int(value: object, low: int, high: int, default: int) -> int:
    try:
        parsed = int(float(value))
    except (TypeError, ValueError):
        parsed = default
    return max(low, min(high, parsed))


def _clamp_float(value: object, low: float, high: float, default: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = default
    return max(low, min(high, parsed))
