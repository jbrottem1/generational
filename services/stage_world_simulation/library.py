"""World library — permanent index of recurring stages."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.stage_world_simulation.location_catalog import (
    LOCATION_DEFINITIONS,
    list_world_ids,
    resolve_world_id,
)
from services.stage_world_simulation.models import LIBRARY_VERSION
from services.stage_world_simulation.package import build_world_package

ROOT = Path(__file__).resolve().parents[2]
LIBRARY_PATH = ROOT / "data" / "world_simulation" / "WORLD_LIBRARY.json"
LIB_ROOT = ROOT / "data" / "world_simulation" / "library"


def load_library() -> dict[str, Any]:
    if LIBRARY_PATH.is_file():
        return json.loads(LIBRARY_PATH.read_text(encoding="utf-8"))
    return {
        "version": LIBRARY_VERSION,
        "universe": "Generational",
        "worlds": [],
        "rule": "Every scene takes place inside a persistent world.",
    }


def save_library(data: dict[str, Any]) -> Path:
    LIBRARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    LIBRARY_PATH.write_text(json.dumps(data, indent=2, default=str) + "\n", encoding="utf-8")
    return LIBRARY_PATH


def upsert_world(entry: dict[str, Any]) -> dict[str, Any]:
    lib = load_library()
    worlds = list(lib.get("worlds") or [])
    wid = str(entry.get("world_id") or "").upper()
    found = False
    for i, row in enumerate(worlds):
        if str(row.get("world_id") or "").upper() == wid:
            worlds[i] = dict(entry)
            found = True
            break
    if not found:
        worlds.append(dict(entry))
    lib["worlds"] = worlds
    lib["version"] = LIBRARY_VERSION
    lib["count"] = len(worlds)
    save_library(lib)
    return entry


def list_worlds() -> list[dict[str, Any]]:
    return list(load_library().get("worlds") or [])


def get_world(world_id: str) -> dict[str, Any] | None:
    key = resolve_world_id(world_id)
    for row in list_worlds():
        if str(row.get("world_id") or "").upper() == key:
            return dict(row)
    return None


def resolve_world_package(location_or_id: str | dict[str, Any] | None) -> dict[str, Any]:
    wid = resolve_world_id(location_or_id)
    path = LIB_ROOT / wid / "WORLD_PACKAGE.json"
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return build_world_package(wid)


def ensure_world_library(*, write_packages: bool = True) -> dict[str, Any]:
    from services.stage_world_simulation.materialize import materialize_world_package

    for wid in list_world_ids():
        pkg = build_world_package(wid)
        if write_packages:
            materialize_world_package(pkg)
        defn = LOCATION_DEFINITIONS[wid]
        upsert_world(
            {
                "world_id": wid,
                "display_name": defn.get("display_name"),
                "location_alias": defn.get("location_alias"),
                "persistent": True,
                "world_package_ref": f"data/world_simulation/library/{wid}/WORLD_PACKAGE.json",
                "validation_ok": bool((pkg.get("validation") or {}).get("ok")),
                "do_not_use_flat_photo_backdrop": True,
            }
        )
    return load_library()
