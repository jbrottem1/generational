"""Physics library — profiles for permanent cast members."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.physics_interaction.models import LIBRARY_VERSION
from services.physics_interaction.package import build_physics_profile

ROOT = Path(__file__).resolve().parents[2]
LIBRARY_PATH = ROOT / "data" / "physics_interaction" / "PHYSICS_LIBRARY.json"
PROFILE_ROOT = ROOT / "data" / "physics_interaction" / "profiles"

DEFAULT_CAST = (
    "DOCTOR_001",
    "FOUNDER_001",
    "TEACHER_001",
    "NURSE_001",
)


def load_library() -> dict[str, Any]:
    if LIBRARY_PATH.is_file():
        return json.loads(LIBRARY_PATH.read_text(encoding="utf-8"))
    return {
        "version": LIBRARY_VERSION,
        "universe": "Generational",
        "profiles": [],
        "rule": "Nothing floats. Nothing clips. Nothing teleports.",
    }


def save_library(data: dict[str, Any]) -> Path:
    LIBRARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    LIBRARY_PATH.write_text(json.dumps(data, indent=2, default=str) + "\n", encoding="utf-8")
    return LIBRARY_PATH


def upsert_profile_entry(entry: dict[str, Any]) -> dict[str, Any]:
    lib = load_library()
    rows = list(lib.get("profiles") or [])
    cid = str(entry.get("character_id") or "").upper()
    found = False
    for i, row in enumerate(rows):
        if str(row.get("character_id") or "").upper() == cid:
            rows[i] = dict(entry)
            found = True
            break
    if not found:
        rows.append(dict(entry))
    lib["profiles"] = rows
    lib["count"] = len(rows)
    lib["version"] = LIBRARY_VERSION
    save_library(lib)
    return entry


def resolve_physics_profile(character_id: str) -> dict[str, Any]:
    cid = str(character_id or "DOCTOR_001").upper()
    path = PROFILE_ROOT / cid / "PHYSICS_PROFILE.json"
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return build_physics_profile(cid)


def ensure_physics_library(*, write_packages: bool = True) -> dict[str, Any]:
    from services.physics_interaction.interaction import build_interaction_package
    from services.physics_interaction.materialize import (
        materialize_interaction,
        materialize_physics_profile,
    )

    # Sample GMRI stage for object physics
    stage = None
    try:
        from services.stage_world_simulation import resolve_world_package

        stage = resolve_world_package("WORLD-GMRI-MEDICAL-LAB")
    except Exception:  # noqa: BLE001
        stage = None

    for cid in DEFAULT_CAST:
        samples = [
            build_interaction_package(
                actor=cid,
                target="microscope",
                interaction_type="using_microscopes",
                interaction_id=f"{cid}_microscope_demo",
                physics_state="manipulating",
                world_id="WORLD-GMRI-MEDICAL-LAB",
            ),
            build_interaction_package(
                actor=cid,
                target="door_main",
                interaction_type="opening_doors",
                interaction_id=f"{cid}_open_door",
                physics_state="contacting",
                world_id="WORLD-GMRI-MEDICAL-LAB",
            ),
            build_interaction_package(
                actor=cid,
                target="nav_mesh",
                interaction_type="walking",
                interaction_id=f"{cid}_walk",
                physics_state="manipulating",
                world_id="WORLD-GMRI-MEDICAL-LAB",
            ),
        ]
        if write_packages:
            for ix in samples:
                materialize_interaction(ix)
        profile = build_physics_profile(
            cid,
            world_id="WORLD-GMRI-MEDICAL-LAB",
            stage_world=stage,
            interactions=samples,
        )
        if write_packages:
            materialize_physics_profile(profile)
        upsert_profile_entry(
            {
                "character_id": cid,
                "physics_profile_ref": f"data/physics_interaction/profiles/{cid}/PHYSICS_PROFILE.json",
                "validation_ok": bool((profile.get("validation") or {}).get("ok")),
                "supported_interaction_count": len(profile.get("supported_interactions") or []),
                "do_not_float": True,
            }
        )
    return load_library()
