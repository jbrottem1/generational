"""Environment validation — plan checks + rendered MP4 inspection checklist."""

from __future__ import annotations

from pathlib import Path
from typing import Any


REQUIRED_ENV_FIELDS = [
    "environment_id",
    "layout",
    "foreground",
    "midground",
    "background",
    "architecture",
    "materials",
    "weather",
    "lighting",
    "ambient_motion",
    "continuity_rules",
]

RENDERED_ENV_CHECKLIST = [
    "foreground_present",
    "midground_readable",
    "background_has_depth",
    "architecture_feels_functional",
    "materials_not_uniform_plastic",
    "atmospheric_perspective_visible",
    "lighting_has_motivated_sources",
    "weather_affects_surfaces_when_applicable",
    "vegetation_fits_biome",
    "props_continuous_across_shots",
    "no_flat_empty_backdrop",
    "no_placeholder_geometry",
    "scale_consistent",
    "visual_history_present",
    "world_feels_inhabited",
]


def validate_environment_package(package: dict[str, Any] | None) -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[str] = []
    if not isinstance(package, dict) or not package:
        return {
            "ok": False,
            "failures": ["missing_environment_package"],
            "warnings": [],
            "plan_only": True,
            "rendered_inspection_required": True,
        }
    for field in REQUIRED_ENV_FIELDS:
        if field not in package or package.get(field) in (None, "", []):
            failures.append(f"missing_{field}")
    if len(package.get("foreground") or []) < 1:
        failures.append("no_foreground_layer")
    if len(package.get("midground") or []) < 1:
        failures.append("no_midground_layer")
    if len(package.get("background") or []) < 1:
        failures.append("no_background_layer")
    if not (package.get("ambient_motion") or []):
        warnings.append("no_ambient_motion_listed")
    return {
        "ok": not failures,
        "failures": failures,
        "warnings": warnings,
        "plan_only": True,
        "rendered_inspection_required": True,
        "rendered_inspection_checklist": list(RENDERED_ENV_CHECKLIST),
        "quality_rule": (
            "Do not treat package completeness as proof of a living world. Inspect the final MP4."
        ),
    }


def rendered_environment_inspection_template(*, mp4_path: str | Path | None = None) -> dict[str, Any]:
    return {
        "mp4_path": str(mp4_path) if mp4_path else None,
        "status": "PENDING_HUMAN_OR_FRAME_INSPECTION",
        "checklist": {item: None for item in RENDERED_ENV_CHECKLIST},
        "reject_if": [
            "flat_background",
            "empty_environment",
            "placeholder_geometry",
            "impossible_architecture",
            "uniform_materials",
            "unmotivated_lighting",
            "props_teleport",
            "unreadable_depth",
            "no_visual_history",
        ],
    }
