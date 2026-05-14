from __future__ import annotations

import json
import os
import re
import threading
import uuid
from pathlib import Path
from typing import Any

from app.job_queue import now

STORAGE_DIR = Path(os.getenv("STORAGE_DIR", "/tmp/upscaler"))
PRESET_FILE = STORAGE_DIR / "presets.json"

_LOCK = threading.Lock()


BUILT_IN_PRESETS: list[dict[str, Any]] = [
    {
        "id": "smart",
        "kind": "built-in",
        "name": "Smart Auto",
        "description": "Best guess for most images.",
        "tool": "auto",
        "settings": {"preset_key": "smart"},
    },
    {
        "id": "logo",
        "kind": "built-in",
        "name": "Logo or Sticker",
        "description": "Sharp edges, transparency, and safer lettering.",
        "tool": "remove-background-upscale",
        "settings": {"preset_key": "logo"},
    },
    {
        "id": "photo",
        "kind": "built-in",
        "name": "Photo Detail",
        "description": "People, products, and real photos.",
        "tool": "upscale",
        "settings": {"preset_key": "photo"},
    },
    {
        "id": "artwork",
        "kind": "built-in",
        "name": "Artwork or Illustration",
        "description": "Illustrations, clean lines, and flat colors.",
        "tool": "upscale",
        "settings": {"preset_key": "artwork"},
    },
    {
        "id": "product",
        "kind": "built-in",
        "name": "Product Cutout",
        "description": "Transparent cutouts and cleaner product images.",
        "tool": "remove-background-upscale",
        "settings": {"preset_key": "product"},
    },
    {
        "id": "print",
        "kind": "built-in",
        "name": "Print-Ready Upscale",
        "description": "Standard 4500 x 5400 shirt PNG defaults.",
        "tool": "upscale",
        "settings": {"preset_key": "print"},
    },
    {
        "id": "transparent-sticker",
        "kind": "built-in",
        "name": "Transparent Sticker",
        "description": "Preserves existing transparent PNG detail.",
        "tool": "remove-background-upscale",
        "settings": {"preset_key": "transparent-sticker"},
    },
]


def list_presets() -> list[dict[str, Any]]:
    return [dict(preset) for preset in BUILT_IN_PRESETS] + _read_user_presets()


def create_preset(*, name: str, description: str = "", tool: str = "upscale", settings: dict[str, Any] | None = None) -> dict[str, Any]:
    clean_name = _clean_text(name, limit=80)
    if not clean_name:
        raise ValueError("Preset name is required.")
    clean_description = _clean_text(description, limit=200)
    safe_tool = _clean_text(tool, limit=48) or "upscale"
    safe_settings = _json_safe(settings or {})

    preset = {
        "id": f"user-{uuid.uuid4().hex[:12]}",
        "kind": "user",
        "name": clean_name,
        "description": clean_description,
        "tool": safe_tool,
        "settings": safe_settings,
        "created_at": now(),
        "updated_at": now(),
    }
    with _LOCK:
        presets = _read_user_presets()
        presets.append(preset)
        _write_user_presets(presets)
    return preset


def delete_preset(preset_id: str) -> bool | None:
    if any(preset["id"] == preset_id for preset in BUILT_IN_PRESETS):
        return None
    with _LOCK:
        presets = _read_user_presets()
        kept = [preset for preset in presets if preset.get("id") != preset_id]
        if len(kept) == len(presets):
            return False
        _write_user_presets(kept)
    return True


def _read_user_presets() -> list[dict[str, Any]]:
    if not PRESET_FILE.exists():
        return []
    try:
        data = json.loads(PRESET_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    presets = data.get("presets") if isinstance(data, dict) else data
    if not isinstance(presets, list):
        return []
    return [preset for preset in presets if isinstance(preset, dict) and str(preset.get("kind")) == "user"]


def _write_user_presets(presets: list[dict[str, Any]]) -> None:
    PRESET_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp = PRESET_FILE.with_suffix(".tmp")
    temp.write_text(json.dumps({"presets": _json_safe(presets)}, indent=2), encoding="utf-8")
    temp.replace(PRESET_FILE)


def _clean_text(value: object, *, limit: int) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text[:limit]


def _json_safe(value: Any) -> Any:
    try:
        json.dumps(value)
        return value
    except TypeError:
        if isinstance(value, dict):
            return {str(key): _json_safe(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [_json_safe(item) for item in value]
        return str(value)
