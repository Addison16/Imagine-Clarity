from __future__ import annotations

import io
import json
import os
import re
import uuid
import zipfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

from filelock import FileLock
from PIL import Image, UnidentifiedImageError

STORAGE_DIR = Path(os.getenv("STORAGE_DIR", "/tmp/upscaler"))
OUTPUT_DIR = STORAGE_DIR / "outputs"
SOURCE_DIR = STORAGE_DIR / "sources"
HISTORY_PATH = STORAGE_DIR / "jobs.json"
HISTORY_LIMIT = int(os.getenv("HISTORY_LIMIT", "100"))
JOB_TTL_HOURS = int(os.getenv("JOB_TTL_HOURS", "0"))
MAX_LISTING_PACK_PIXELS = int(os.getenv("MAX_LISTING_PACK_PIXELS", "25000000"))
HISTORY_LOCK_PATH = HISTORY_PATH.with_suffix(".lock")

_history_lock = Lock()


def save_job_result(
    *,
    tool: str,
    source_filename: str | None,
    output_filename: str,
    data: bytes,
    input_metadata: dict[str, Any],
    output_width: int,
    output_height: int,
    output_format: str,
    engine: str,
    settings: dict[str, Any],
    source_data: bytes | None = None,
    queue_job_id: str | None = None,
    parent_queue_job_id: str | None = None,
    quick_fix: str | None = None,
) -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    job_id = uuid.uuid4().hex
    created_at = datetime.now(timezone.utc).isoformat()

    stored_filename = f"{created_at[:10].replace('-', '')}-{job_id[:10]}-{_safe_filename(output_filename)}"
    path = OUTPUT_DIR / stored_filename
    path.write_bytes(data)

    source_stored_filename = None
    source_path: Path | None = None
    if source_data:
        SOURCE_DIR.mkdir(parents=True, exist_ok=True)
        source_name = _safe_filename(source_filename or "source-image")
        source_stored_filename = f"{created_at[:10].replace('-', '')}-{job_id[:10]}-source-{source_name}"
        source_path = SOURCE_DIR / source_stored_filename
        source_path.write_bytes(source_data)

    entry = {
        "id": job_id,
        "created_at": created_at,
        "tool": tool,
        "source_filename": source_filename or "image",
        "filename": output_filename,
        "stored_filename": stored_filename,
        "download_url": f"/api/results/{job_id}",
        "input": {
            "width": int(input_metadata["width"]),
            "height": int(input_metadata["height"]),
            "mode": str(input_metadata["mode"]),
            "has_alpha": bool(input_metadata["has_alpha"]),
        },
        "output": {
            "width": int(output_width),
            "height": int(output_height),
            "format": output_format,
            "size_bytes": len(data),
        },
        "engine": engine,
        "settings": _json_safe(settings),
        "quality_report": build_quality_report(
            input_metadata=input_metadata,
            output_data=data,
            output_width=output_width,
            output_height=output_height,
            output_format=output_format,
            output_size_bytes=len(data),
            tool=tool,
            settings=settings,
        ),
    }
    if (
        tool in {"remove-background", "remove-background-upscale"}
        and entry["quality_report"].get("has_transparency")
        and int(output_width) * int(output_height) <= MAX_LISTING_PACK_PIXELS
    ):
        entry["listing_pack_url"] = f"/api/results/{job_id}/listing-pack"
    if queue_job_id:
        entry["queue_job_id"] = queue_job_id
    if parent_queue_job_id:
        entry["parent_queue_job_id"] = parent_queue_job_id
    if quick_fix:
        entry["quick_fix"] = quick_fix
    if source_stored_filename:
        entry["source_stored_filename"] = source_stored_filename
        entry["source_download_url"] = f"/api/sources/{job_id}"
        entry["source_size_bytes"] = len(source_data or b"")
    try:
        _append_history(entry)
    except Exception:
        path.unlink(missing_ok=True)
        if source_path is not None:
            source_path.unlink(missing_ok=True)
        raise
    return entry


def list_jobs(limit: int = 25) -> list[dict[str, Any]]:
    _purge_expired_jobs()
    jobs = _read_history()
    return jobs[: max(1, min(int(limit), HISTORY_LIMIT))]


def delete_job(job_id: str) -> dict[str, Any] | None:
    with _history_guard():
        jobs = _read_history_unlocked()
        deleted_job: dict[str, Any] | None = None
        kept_jobs: list[dict[str, Any]] = []
        for job in jobs:
            if job.get("id") == job_id:
                deleted_job = job
            else:
                kept_jobs.append(job)

        if deleted_job is None:
            return None

        deleted_files = _delete_stored_files_unlocked(deleted_job)
        _write_history_unlocked(kept_jobs)
        return {
            "deleted": True,
            "deleted_jobs": 1,
            "deleted_files": deleted_files,
            "job": deleted_job,
        }


def clear_jobs() -> dict[str, Any]:
    with _history_guard():
        jobs = _read_history_unlocked()
        deleted_files = 0
        for job in jobs:
            deleted_files += _delete_stored_files_unlocked(job)
        _write_history_unlocked([])
        return {
            "deleted": True,
            "deleted_jobs": len(jobs),
            "deleted_files": deleted_files,
        }


def get_job(job_id: str) -> dict[str, Any] | None:
    _purge_expired_jobs()
    for job in _read_history():
        if job.get("id") == job_id:
            return job
    return None


def result_path(job_id: str) -> Path | None:
    job = get_job(job_id)
    if not job:
        return None
    stored_filename = str(job.get("stored_filename", ""))
    if not stored_filename or Path(stored_filename).name != stored_filename:
        return None
    path = OUTPUT_DIR / stored_filename
    if not path.exists() or not path.is_file():
        return None
    return path


def source_path(job_id: str) -> Path | None:
    job = get_job(job_id)
    if not job:
        return None
    stored_filename = str(job.get("source_stored_filename", ""))
    if not stored_filename or Path(stored_filename).name != stored_filename:
        return None
    path = SOURCE_DIR / stored_filename
    if not path.exists() or not path.is_file():
        return None
    return path



def update_job_metadata(job_id: str, *, display_name: str | None = None, note: str | None = None) -> dict[str, Any] | None:
    with _history_guard():
        jobs = _read_history_unlocked()
        updated: dict[str, Any] | None = None
        for job in jobs:
            if job.get("id") != job_id:
                continue
            if display_name is not None:
                job["display_name"] = str(display_name).strip()[:120]
            if note is not None:
                job["note"] = str(note).strip()[:500]
            job["updated_at"] = datetime.now(timezone.utc).isoformat()
            updated = dict(job)
            break
        if updated is None:
            return None
        _write_history_unlocked(jobs)
        return updated


def build_quality_report(
    *,
    input_metadata: dict[str, Any],
    output_data: bytes,
    output_width: int,
    output_height: int,
    output_format: str,
    output_size_bytes: int,
    tool: str,
    settings: dict[str, Any],
) -> dict[str, Any]:
    checks: list[dict[str, str]] = []
    input_width = int(input_metadata.get("width") or 0)
    input_height = int(input_metadata.get("height") or 0)
    fmt = str(output_format or "").lower()
    if tool == "vectorize" or fmt == "svg":
        checks.append({"status": "good", "label": "Vector output", "message": "Saved as SVG paths, so it can scale without raster pixelation."})
        checks.append({"status": "info", "label": "Best source type", "message": "VTracer works best on clean logos, decals, line art, and flat-color artwork. Complex photos should be simplified or treated as posterized art."})
        checks.append({"status": "info", "label": "Trace settings", "message": f"Preset: {settings.get('preset', 'logo')} | Color mode: {settings.get('colormode', 'color')} | Curve mode: {settings.get('mode', 'spline')}."})
        checks.append({"status": "info", "label": "File summary", "message": f"SVG | source {output_width} x {output_height}px | {_format_bytes(output_size_bytes)}."})
        return {
            "verdict": "Vector SVG is ready for scaling; inspect path detail before cutting, printing, or engraving.",
            "suitable_for": {"print": True, "listing": True, "mockup": True, "vector": True},
            "has_alpha": False,
            "has_transparency": False,
            "transparent_pixels_estimate": 0,
            "checks": checks,
        }
    has_alpha = False
    has_transparency = False
    alpha_edge_pixels = 0
    transparent_pixels = 0
    try:
        with Image.open(io.BytesIO(output_data)) as image:
            has_alpha = "A" in image.getbands()
            if has_alpha:
                alpha = image.convert("RGBA").getchannel("A")
                has_transparency = alpha.getextrema()[0] < 255
                sample = alpha.resize((min(alpha.width, 600), min(alpha.height, 600)))
                values = list(sample.get_flattened_data())
                transparent_pixels = sum(1 for value in values if value < 8)
                alpha_edge_pixels = sum(1 for value in values if 0 < value < 245)
    except (UnidentifiedImageError, OSError):
        pass

    uses_cut = tool in {"remove-background", "remove-background-upscale"}
    if uses_cut and has_transparency:
        checks.append({"status": "good", "label": "Transparent output", "message": "Transparent pixels are present for cutout/listing use."})
    elif uses_cut:
        checks.append({"status": "warning", "label": "Transparent output", "message": "This workflow usually expects transparency, but the saved file does not report an alpha channel. Use PNG/WebP for transparent exports."})
    else:
        checks.append({"status": "info", "label": "Transparent output", "message": "This workflow keeps the background unless you choose a background-removal workflow."})

    target = _expected_output_from_settings(tool, settings)
    if target:
        tw, th = target
        if int(output_width) == tw and int(output_height) == th:
            checks.append({"status": "good", "label": "Output dimensions", "message": f"Output matches the requested {tw} x {th} size."})
        else:
            checks.append({"status": "warning", "label": "Output dimensions", "message": f"Expected about {tw} x {th}, but saved {output_width} x {output_height}. Check fit/canvas settings."})
    else:
        checks.append({"status": "info", "label": "Output dimensions", "message": f"Saved at {output_width} x {output_height}px."})

    if input_width and input_height and min(input_width, input_height) < 500:
        checks.append({"status": "warning", "label": "Small source", "message": f"The source was only {input_width} x {input_height}px. Upscaling can help size, but tiny originals may still show soft detail."})
    else:
        checks.append({"status": "good", "label": "Source size", "message": "Source size looks reasonable for this kind of cleanup."})

    if has_transparency and alpha_edge_pixels > 1000:
        checks.append({"status": "warning", "label": "Halo / edge risk", "message": "Some semi-transparent edge pixels were found. Inspect on black/green backgrounds and use Fix white outline / halo if you see a rim."})
    elif has_transparency:
        checks.append({"status": "good", "label": "Halo / edge risk", "message": "No obvious metadata-only edge warning. Still inspect on high-contrast backgrounds before using in a listing."})
    else:
        checks.append({"status": "info", "label": "Halo / edge risk", "message": "Halo checks only apply to transparent outputs."})

    checks.append({"status": "info", "label": "File summary", "message": f"{fmt.upper() or 'FILE'} | {output_width} x {output_height}px | {_format_bytes(output_size_bytes)}."})
    likely_good = output_width >= 1500 and output_height >= 1500 and (not uses_cut or has_transparency)
    return {
        "verdict": "Likely shop-ready for listings/mockups." if likely_good else "Usable, but review size/transparency before listing or print use.",
        "suitable_for": {"print": output_width >= 3000 and output_height >= 3000, "listing": output_width >= 1200 and output_height >= 1200, "mockup": output_width >= 1500 and output_height >= 1500},
        "has_alpha": has_alpha,
        "has_transparency": has_transparency,
        "transparent_pixels_estimate": transparent_pixels,
        "checks": checks,
    }


def build_listing_pack(job_id: str) -> tuple[bytes, str] | None:
    job = get_job(job_id)
    path = result_path(job_id)
    if not job or not path:
        return None
    quality = job.get("quality_report") if isinstance(job.get("quality_report"), dict) else {}
    if job.get("tool") not in {"remove-background", "remove-background-upscale"} or not quality.get("has_transparency"):
        return None
    base = _safe_stem(str(job.get("source_filename") or job.get("filename") or "image"))
    output = job.get("output") if isinstance(job.get("output"), dict) else {}
    width = int(output.get("width") or 0)
    height = int(output.get("height") or 0)
    if width <= 0 or height <= 0 or width * height > MAX_LISTING_PACK_PIXELS:
        return None
    with Image.open(path) as opened:
        image = opened.convert("RGBA")
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        png = io.BytesIO()
        image.save(png, format="PNG")
        archive.writestr(f"{base}-transparent-{width}x{height}.png", png.getvalue())
        white = Image.new("RGB", image.size, "white")
        white.paste(image, mask=image.getchannel("A"))
        jpg = io.BytesIO()
        white.save(jpg, format="JPEG", quality=94, optimize=True)
        archive.writestr(f"{base}-white-bg.jpg", jpg.getvalue())
        web = io.BytesIO()
        image.save(web, format="WEBP", quality=90, method=6)
        archive.writestr(f"{base}-web.webp", web.getvalue())
        thumb_image = image.copy()
        thumb_image.thumbnail((800, 800), Image.Resampling.LANCZOS)
        thumb = io.BytesIO()
        thumb_image.save(thumb, format="PNG")
        archive.writestr(f"{base}-thumbnail.png", thumb.getvalue())
        readme = [
            "PrintForge listing pack",
            f"Source: {job.get('source_filename') or 'image'}",
            f"Result: {job.get('filename') or path.name}",
            f"Dimensions: {width} x {height}px",
            f"Tool: {job.get('tool') or 'unknown'}",
            f"Engine: {job.get('engine') or 'unknown'}",
            "",
            "Included: transparent PNG, white-background JPG, web-ready WebP, thumbnail PNG.",
            "Inspect transparent edges on dark/green backgrounds before publishing.",
        ]
        archive.writestr(f"{base}-metadata.txt", "\n".join(readme))
    return data.getvalue(), f"{base}-printforge-pack.zip"


def _expected_output_from_settings(tool: str, settings: dict[str, Any]) -> tuple[int, int] | None:
    upscale = settings.get("upscale") if tool == "remove-background-upscale" and isinstance(settings.get("upscale"), dict) else settings
    if not isinstance(upscale, dict):
        return None
    width = upscale.get("canvas_width") or upscale.get("target_width")
    height = upscale.get("canvas_height") or upscale.get("target_height")
    try:
        if width and height:
            return int(width), int(height)
    except (TypeError, ValueError):
        return None
    return None


def _safe_stem(filename: str) -> str:
    stem = Path(filename or "image").stem.lower()
    clean = re.sub(r"[^a-z0-9]+", "-", stem).strip("-")
    return clean or "image"


def _format_bytes(bytes_value: int) -> str:
    if bytes_value < 1024 * 1024:
        return f"{max(1, round(bytes_value / 1024))} KB"
    return f"{bytes_value / 1024 / 1024:.1f} MB"

def storage_summary() -> dict[str, Any]:
    _purge_expired_jobs()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    jobs = _read_history()
    total_bytes = 0
    source_bytes = 0
    for job in jobs:
        total_bytes += int(job.get("output", {}).get("size_bytes", 0) or 0)
        source_bytes += int(job.get("source_size_bytes", 0) or 0)
    return {
        "output_dir": str(OUTPUT_DIR),
        "source_dir": str(SOURCE_DIR),
        "history_path": str(HISTORY_PATH),
        "history_limit": HISTORY_LIMIT,
        "job_ttl_hours": JOB_TTL_HOURS,
        "saved_jobs": len(jobs),
        "saved_bytes": total_bytes,
        "saved_source_bytes": source_bytes,
    }


def _purge_expired_jobs() -> None:
    if JOB_TTL_HOURS <= 0:
        return
    cutoff = datetime.now(timezone.utc).timestamp() - (JOB_TTL_HOURS * 3600)
    with _history_guard():
        jobs = _read_history_unlocked()
        kept: list[dict[str, Any]] = []
        for job in jobs:
            created_at = str(job.get("created_at", ""))
            try:
                created_ts = datetime.fromisoformat(created_at).timestamp()
            except ValueError:
                created_ts = 0
            if created_ts >= cutoff:
                kept.append(job)
            else:
                _delete_stored_files_unlocked(job)
        if len(kept) != len(jobs):
            _write_history_unlocked(kept)


def _append_history(entry: dict[str, Any]) -> None:
    with _history_guard():
        jobs = _read_history_unlocked()
        jobs.insert(0, entry)
        overflow = jobs[HISTORY_LIMIT:]
        for job in overflow:
            _delete_stored_files_unlocked(job)
        jobs = jobs[:HISTORY_LIMIT]
        _write_history_unlocked(jobs)


def _read_history() -> list[dict[str, Any]]:
    with _history_guard():
        return _read_history_unlocked()


@contextmanager
def _history_guard():
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _history_lock:
        with FileLock(str(HISTORY_LOCK_PATH), timeout=30):
            yield


def _read_history_unlocked() -> list[dict[str, Any]]:
    if not HISTORY_PATH.exists():
        return []
    try:
        data = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(data, list):
        return []
    return [job for job in data if isinstance(job, dict)]


def _write_history_unlocked(jobs: list[dict[str, Any]]) -> None:
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = HISTORY_PATH.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(jobs, indent=2), encoding="utf-8")
    tmp_path.replace(HISTORY_PATH)


def _delete_stored_files_unlocked(job: dict[str, Any]) -> int:
    deleted = 0
    for key, directory in (("stored_filename", OUTPUT_DIR), ("source_stored_filename", SOURCE_DIR)):
        stored_filename = str(job.get(key, ""))
        if not stored_filename or Path(stored_filename).name != stored_filename:
            continue
        path = directory / stored_filename
        try:
            if path.exists() and path.is_file():
                path.unlink()
                deleted += 1
        except OSError:
            continue
    return deleted


def _safe_filename(filename: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9_.-]+", "-", filename).strip("-")
    return clean or "image.png"


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)
