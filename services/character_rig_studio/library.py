"""Character Library — permanent index of digital actors."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.character_rig_studio.cast_catalog import CAST_DEFINITIONS, list_cast_ids
from services.character_rig_studio.models import LIBRARY_VERSION
from services.character_rig_studio.package import build_character_rig

ROOT = Path(__file__).resolve().parents[2]
LIBRARY_PATH = ROOT / "data" / "character_rig_studio" / "CHARACTER_LIBRARY.json"
CAST_ROOT = ROOT / "data" / "studio_assets"


def library_path() -> Path:
    return LIBRARY_PATH


def load_library() -> dict[str, Any]:
    if LIBRARY_PATH.is_file():
        return json.loads(LIBRARY_PATH.read_text(encoding="utf-8"))
    return {
        "version": LIBRARY_VERSION,
        "universe": "Generational",
        "actors": [],
        "rule": "Characters are permanent digital actors — never regenerated per scene.",
    }


def save_library(data: dict[str, Any]) -> Path:
    LIBRARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    LIBRARY_PATH.write_text(json.dumps(data, indent=2, default=str) + "\n", encoding="utf-8")
    return LIBRARY_PATH


def get_actor(character_id: str) -> dict[str, Any] | None:
    key = str(character_id or "").upper()
    for row in load_library().get("actors") or []:
        if str(row.get("character_id") or "").upper() == key:
            return dict(row)
    return None


def upsert_actor(entry: dict[str, Any]) -> dict[str, Any]:
    lib = load_library()
    actors = list(lib.get("actors") or [])
    cid = str(entry.get("character_id") or "").upper()
    found = False
    for i, row in enumerate(actors):
        if str(row.get("character_id") or "").upper() == cid:
            actors[i] = dict(entry)
            found = True
            break
    if not found:
        actors.append(dict(entry))
    lib["actors"] = actors
    lib["version"] = LIBRARY_VERSION
    lib["count"] = len(actors)
    save_library(lib)
    return entry


def list_actors() -> list[dict[str, Any]]:
    return list(load_library().get("actors") or [])


def ensure_library(*, write_packages: bool = True) -> dict[str, Any]:
    """Ensure all cast slots exist in the library (and optionally on disk)."""
    from services.character_rig_studio.materialize import materialize_character_rig

    actors = []
    for cid in list_cast_ids():
        pkg = build_character_rig(cid)
        if write_packages:
            materialize_character_rig(pkg)
        defn = CAST_DEFINITIONS[cid]
        entry = {
            "character_id": cid,
            "canonical_name": defn["canonical_name"],
            "role": defn["role"],
            "status": defn.get("status") or "reserved",
            "continuity_version": defn.get("continuity_version"),
            "studio_asset_path": defn.get("studio_asset_path"),
            "character_rig_ref": f"{defn.get('studio_asset_path')}CHARACTER_RIG/CHARACTER_RIG_PACKAGE.json",
            "validation_ok": bool((pkg.get("validation") or {}).get("ok")),
            "is_gold_standard": bool(defn.get("is_gold_standard")),
            "do_not_regenerate": True,
        }
        upsert_actor(entry)
        actors.append(entry)

    # Soft-register actors into studio_assets REGISTRY (merge, don't wipe DOCTOR fields)
    try:
        from services.studio_assets.registry import get_asset, upsert_asset

        for cid in ("DOCTOR_001", "FOUNDER_001"):
            defn = CAST_DEFINITIONS[cid]
            prior = get_asset(cid) or {}
            upsert_asset(
                {
                    **prior,
                    "id": cid,
                    "name": defn["canonical_name"],
                    "slug": cid,
                    "version": prior.get("version") or defn.get("continuity_version"),
                    "status": defn.get("status") or prior.get("status") or "permanent",
                    "role": prior.get("role") or defn.get("role"),
                    "path": defn.get("studio_asset_path"),
                    "character_rig": True,
                    "character_rig_ref": (
                        f"{defn.get('studio_asset_path')}CHARACTER_RIG/CHARACTER_RIG_PACKAGE.json"
                    ),
                    "permanent_digital_actor": True,
                    "package_type": prior.get("package_type") or "CHARACTER_RIG_PACKAGE",
                }
            )
    except Exception:  # noqa: BLE001
        pass

    return load_library()


def resolve_character_rig(character_id: str) -> dict[str, Any]:
    """Load materialized package if present; otherwise build in memory."""
    cid = str(character_id or "").upper()
    path = CAST_ROOT / cid / "CHARACTER_RIG" / "CHARACTER_RIG_PACKAGE.json"
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return build_character_rig(cid)
