"""Studio Asset registry — permanent IP index."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "data" / "studio_assets" / "REGISTRY.json"


def load_registry() -> dict[str, Any]:
    if not REGISTRY_PATH.is_file():
        return {
            "version": 1,
            "universe": "Generational",
            "assets": [],
            "flagship_science_educator": None,
        }
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def save_registry(data: dict[str, Any]) -> Path:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return REGISTRY_PATH


def list_assets() -> list[dict[str, Any]]:
    return list(load_registry().get("assets") or [])


def get_asset(asset_id: str) -> dict[str, Any] | None:
    key = str(asset_id or "").upper()
    for row in list_assets():
        if str(row.get("id") or "").upper() == key:
            return dict(row)
    return None


def upsert_asset(entry: dict[str, Any]) -> dict[str, Any]:
    reg = load_registry()
    assets = list(reg.get("assets") or [])
    aid = str(entry.get("id") or "").upper()
    found = False
    for i, row in enumerate(assets):
        if str(row.get("id") or "").upper() == aid:
            assets[i] = dict(entry)
            found = True
            break
    if not found:
        assets.append(dict(entry))
    reg["assets"] = assets
    if entry.get("flagship_science_educator"):
        reg["flagship_science_educator"] = entry.get("id")
    save_registry(reg)
    return entry
