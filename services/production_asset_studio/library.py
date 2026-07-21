"""Production Asset Studio library index."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.production_asset_studio.departments import list_departments
from services.production_asset_studio.models import ENGINE_ID, PACKAGE_VERSION, PHASE

ROOT = Path(__file__).resolve().parents[2]
LIB_ROOT = ROOT / "data" / "production_asset_studio"
LIBRARY_PATH = LIB_ROOT / "ASSET_LIBRARY.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_library(*, write: bool = True) -> dict[str, Any]:
    LIB_ROOT.mkdir(parents=True, exist_ok=True)
    departments = list_departments()
    assets: list[dict[str, Any]] = []
    for dep in departments:
        for a in dep.get("assets") or []:
            assets.append(
                {
                    **a,
                    "department_id": dep["department_id"],
                    "phase": PHASE,
                    "engine_id": ENGINE_ID,
                }
            )
    library = {
        "library_type": "PRODUCTION_ASSET_LIBRARY",
        "phase": PHASE,
        "package_version": PACKAGE_VERSION,
        "engine_id": ENGINE_ID,
        "updated_at": _now(),
        "department_count": len(departments),
        "asset_count": len(assets),
        "departments": [
            {
                "department_id": d["department_id"],
                "display_name": d["display_name"],
                "asset_count": len(d.get("assets") or []),
            }
            for d in departments
        ],
        "assets": assets,
        "architecture": {
            "frozen": True,
            "does_not_replace": [
                "Scene Director",
                "Character Performance Engine",
                "Character Rig Studio",
                "Stage & World Simulation",
                "Physics & Interaction",
                "Cinematic Direction Studio",
                "Animation Runtime",
                "BlenderRuntime",
                "Golden Motion Pipeline",
            ],
            "evolves_via": "better_assets_only",
        },
    }
    if write:
        LIBRARY_PATH.write_text(json.dumps(library, indent=2) + "\n")
        for dep in departments:
            path = LIB_ROOT / "departments" / f"{dep['department_id']}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(dep, indent=2) + "\n")
    return library


def load_library() -> dict[str, Any]:
    if LIBRARY_PATH.is_file():
        return json.loads(LIBRARY_PATH.read_text())
    return ensure_library(write=False)


def resolve_asset(asset_id: str) -> dict[str, Any] | None:
    lib = load_library()
    for a in lib.get("assets") or []:
        if a.get("asset_id") == asset_id:
            return a
    return None
