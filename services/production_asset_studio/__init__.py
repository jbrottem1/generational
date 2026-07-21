"""Generational Production Asset Studio — Phase II.

Architecture is frozen. This studio upgrades assets only.
It does not redesign Scene Director, Performance Engine, Rig Studio,
World Simulation, Physics, Cinematic Direction, or AnimationRuntime.
"""

from __future__ import annotations

from services.production_asset_studio.departments import list_departments
from services.production_asset_studio.library import ensure_library, load_library, resolve_asset
from services.production_asset_studio.materialize import materialize_phase_ii_catalog
from services.production_asset_studio.package import build_asset_studio_package
from services.production_asset_studio.validation import validate_production_asset

__all__ = [
    "build_asset_studio_package",
    "ensure_library",
    "list_departments",
    "load_library",
    "materialize_phase_ii_catalog",
    "resolve_asset",
    "validate_production_asset",
    "run_phase_ii_bootstrap",
]


def run_phase_ii_bootstrap(*, write: bool = True) -> dict:
    """Materialize Phase II catalogs and (optionally) build Blender production assets."""
    from services.production_asset_studio.bootstrap import bootstrap_phase_ii

    return bootstrap_phase_ii(write=write)
