"""Reusable asset libraries — versioned, cached, deduplicated."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.env import project_root
from services.media_production.local_cache import (
    copy_catalog_image_to_cache,
    fetch_url_cached,
    get_cached,
)

REGISTRY_PATH = project_root() / "data" / "generational_os" / "asset_registry.json"

LIBRARY_TYPES = (
    "characters",
    "backgrounds",
    "props",
    "icons",
    "diagrams",
    "motion_templates",
    "whiteboard",
    "fonts",
    "music",
    "sound_effects",
    "camera_presets",
    "real_images",
)


def _load_registry() -> dict[str, Any]:
    if not REGISTRY_PATH.is_file():
        return {"schema_version": 1, "libraries": {k: {} for k in LIBRARY_TYPES}}
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def _save_registry(reg: dict[str, Any]) -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    reg["updated_at"] = datetime.now(timezone.utc).isoformat()
    REGISTRY_PATH.write_text(json.dumps(reg, indent=2), encoding="utf-8")


def register_asset(
    library: str,
    asset_id: str,
    *,
    path: str,
    version: str = "1.0",
    meta: dict[str, Any] | None = None,
) -> None:
    reg = _load_registry()
    libs = reg.setdefault("libraries", {})
    bucket = libs.setdefault(library, {})
    bucket[asset_id] = {
        "path": path,
        "version": version,
        "registered_at": datetime.now(timezone.utc).isoformat(),
        "meta": meta or {},
    }
    _save_registry(reg)


def resolve_image(image_id: str) -> Path | None:
    """Cache-first image resolution."""
    cached = copy_catalog_image_to_cache(image_id)
    if cached:
        register_asset("real_images", image_id, path=str(cached), version="1.0")
    return cached


def resolve_url(url: str, *, kind: str = "image", ext: str = ".jpg") -> Path:
    return fetch_url_cached(url, kind=kind, identifier=url, ext=ext)


def cache_health() -> dict[str, Any]:
    from services.media_production.local_cache import INDEX_PATH

    index_exists = INDEX_PATH.is_file()
    entry_count = 0
    total_bytes = 0
    if index_exists:
        data = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
        entries = data.get("entries") or {}
        entry_count = len(entries)
        for e in entries.values():
            p = Path(str(e.get("path") or ""))
            if p.is_file():
                total_bytes += p.stat().st_size
    reg = _load_registry()
    lib_counts = {k: len(v) for k, v in (reg.get("libraries") or {}).items()}
    return {
        "cache_index_exists": index_exists,
        "cached_assets": entry_count,
        "cache_bytes": total_bytes,
        "registry_libraries": lib_counts,
    }
