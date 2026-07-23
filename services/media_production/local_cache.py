"""Local asset cache — images, audio, fonts. Reuse downloads across renders."""

from __future__ import annotations

import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.env import project_root

CACHE_ROOT = project_root() / "data" / "local_cache"
INDEX_PATH = CACHE_ROOT / "index.json"


def _cache_key(kind: str, identifier: str) -> str:
    raw = f"{kind}:{identifier}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:24]


def _load_index() -> dict[str, Any]:
    if not INDEX_PATH.is_file():
        return {"schema_version": 1, "entries": {}}
    try:
        return json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {"schema_version": 1, "entries": {}}


def _save_index(index: dict[str, Any]) -> None:
    CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(index, indent=2), encoding="utf-8")


def cache_path_for(kind: str, identifier: str, *, ext: str) -> Path:
    key = _cache_key(kind, identifier)
    sub = CACHE_ROOT / kind
    sub.mkdir(parents=True, exist_ok=True)
    return sub / f"{key}{ext}"


def get_cached(kind: str, identifier: str) -> Path | None:
    index = _load_index()
    entry = (index.get("entries") or {}).get(f"{kind}:{identifier}")
    if not entry:
        return None
    path = Path(str(entry.get("path") or ""))
    if path.is_file() and path.stat().st_size > 0:
        return path
    return None


def remember(kind: str, identifier: str, path: Path, *, meta: dict[str, Any] | None = None) -> None:
    index = _load_index()
    entries = index.setdefault("entries", {})
    entries[f"{kind}:{identifier}"] = {
        "path": str(path),
        "kind": kind,
        "identifier": identifier,
        "bytes": path.stat().st_size if path.is_file() else 0,
        "cached_at": datetime.now(timezone.utc).isoformat(),
        "meta": meta or {},
    }
    _save_index(index)


def fetch_url_cached(
    url: str,
    *,
    kind: str = "image",
    identifier: str | None = None,
    ext: str = ".jpg",
) -> Path:
    """Download URL once; reuse from cache on subsequent renders."""
    ident = identifier or url
    existing = get_cached(kind, ident)
    if existing is not None:
        return existing

    dest = cache_path_for(kind, ident, ext=ext)
    req = urllib.request.Request(url, headers={"User-Agent": "GenerationalLocalCache/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read()
    if len(data) < 100:
        raise RuntimeError(f"Download too small for {url}")
    dest.write_bytes(data)
    remember(kind, ident, dest, meta={"url": url})
    return dest


def copy_catalog_image_to_cache(image_id: str) -> Path | None:
    """Resolve Reality catalog image through local cache."""
    from services.reality.catalog import get_image

    entry = get_image(image_id)
    if entry is None:
        return None
    src = Path(str(entry.path))
    if not src.is_file():
        root = project_root() / "data" / "reality"
        src = root / entry.path
    if not src.is_file():
        return None
    cached = get_cached("reality_image", image_id)
    if cached is not None:
        return cached
    ext = src.suffix or ".jpg"
    dest = cache_path_for("reality_image", image_id, ext=ext)
    dest.write_bytes(src.read_bytes())
    remember("reality_image", image_id, dest, meta={"source": str(src)})
    return dest
