"""Materialize Phase II catalogs into data/production_asset_studio/."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.production_asset_studio.library import ensure_library
from services.production_asset_studio.models import PHASE, RUNTIME_CONTRACT
from services.production_asset_studio.package import build_asset_studio_package

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "production_asset_studio"


def materialize_phase_ii_catalog(*, write: bool = True) -> dict[str, Any]:
    library = ensure_library(write=write)
    package = build_asset_studio_package()
    if write:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "PRODUCTION_ASSET_PACKAGE.json").write_text(json.dumps(package, indent=2) + "\n")
        (OUT / "RUNTIME_CONTRACT.json").write_text(json.dumps(RUNTIME_CONTRACT, indent=2) + "\n")
        (OUT / "PHASE.json").write_text(
            json.dumps(
                {
                    "phase": PHASE,
                    "title": "Production Asset Studio",
                    "objective": "Replace placeholder assets with production-quality assets",
                    "runtime_frozen": True,
                },
                indent=2,
            )
            + "\n"
        )
        # Staging dirs for authored sources
        for name in (
            "characters/DOCTOR_001",
            "environments/GENERATIONAL_MEDICAL_LAB",
            "props",
            "materials",
            "lighting",
            "facial/DOCTOR_001",
            "animation_clips",
            "storytelling",
        ):
            (OUT / "library" / name).mkdir(parents=True, exist_ok=True)
    return {
        "ok": True,
        "phase": PHASE,
        "library_path": str(OUT / "ASSET_LIBRARY.json"),
        "package_path": str(OUT / "PRODUCTION_ASSET_PACKAGE.json"),
        "asset_count": library.get("asset_count"),
        "department_count": library.get("department_count"),
    }
