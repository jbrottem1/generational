"""Knowledge Atlas catalog — load, persist, deduplicate."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any

from services.knowledge_atlas.models import AtlasAsset

ROOT = Path(__file__).resolve().parents[2]
ATLAS_DIR = ROOT / "data" / "knowledge_atlas"
CATALOG_PATH = ATLAS_DIR / "catalog.json"
COLLECTIONS_PATH = ATLAS_DIR / "collections.json"


def fingerprint_for(source: str, path: str) -> str:
    key = f"{source.strip().lower()}|{path.strip().lower()}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def _parse(raw: dict[str, Any]) -> AtlasAsset:
    asset = AtlasAsset.from_dict(raw)
    if not asset.fingerprint:
        object.__setattr__(
            asset,
            "fingerprint",
            fingerprint_for(asset.source, asset.path),
        )
    return asset


@lru_cache(maxsize=1)
def load_atlas() -> dict[str, AtlasAsset]:
    if not CATALOG_PATH.is_file():
        return {}
    data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    out: dict[str, AtlasAsset] = {}
    for raw in data.get("assets") or []:
        asset = _parse(raw)
        out[asset.asset_id] = asset
    return out


def get_asset(asset_id: str) -> AtlasAsset | None:
    return load_atlas().get(asset_id)


def save_catalog(assets: dict[str, AtlasAsset]) -> None:
    ATLAS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "project": "generational_knowledge_atlas",
        "updated": date.today().isoformat(),
        "assets": [a.to_dict() for a in sorted(assets.values(), key=lambda x: x.asset_id)],
    }
    CATALOG_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    load_atlas.cache_clear()


def find_by_fingerprint(fp: str) -> AtlasAsset | None:
    for asset in load_atlas().values():
        if asset.fingerprint == fp:
            return asset
    return None


def load_collections() -> dict[str, Any]:
    if not COLLECTIONS_PATH.is_file():
        return {"schema_version": 1, "collections": []}
    return json.loads(COLLECTIONS_PATH.read_text(encoding="utf-8"))
