"""Environment package composer + continuity + validation."""

from __future__ import annotations

from typing import Any

from services.environment_department.definition import resolve_environment
from services.environment_department.layout import build_layout
from services.environment_department.world_systems import (
    architecture_package,
    atmosphere_package,
    lighting_package,
    materials_library,
    set_dressing,
    vegetation_package,
    weather_state,
)


def continuity_rules(environment_id: str) -> list[str]:
    return [
        f"Never regenerate {environment_id} from scratch.",
        "Props keep default_location unless story explains move.",
        "Architecture function remains readable across episodes.",
        "Lighting sources remain motivated and consistent with time_of_day.",
        "Weather is a shared world state affecting cloth, plants, and reflections.",
        "Foreground / midground / background layers required every shot.",
    ]


def validation_rules() -> list[str]:
    return [
        "foreground_presence",
        "midground_readability",
        "background_depth",
        "architecture_coherence",
        "material_quality",
        "atmospheric_perspective",
        "lighting_plausibility",
        "weather_consistency",
        "vegetation_fit",
        "prop_continuity",
        "spatial_continuity",
        "character_ground_contact",
        "motion_coherence",
        "environment_identity_consistency",
        "empty_space_ratio",
        "placeholder_geometry_count",
    ]


def build_environment_package(
    location_or_id: str | dict[str, Any] | None = None,
    *,
    owner: str = "DOCTOR_001",
    weather: str | None = None,
    lighting_mood: str = "clinical_warm",
) -> dict[str, Any]:
    env = resolve_environment(location_or_id)
    eid = str(env.get("environment_id"))
    weather_type = weather or str(env.get("weather") or "clear")
    layout = build_layout(env)
    layers = layout.get("layered_spatial_design") or {}
    dressing = set_dressing(owner=owner)
    package = {
        "environment_id": eid,
        "definition": env,
        "layout": layout,
        "foreground": layers.get("foreground") or [],
        "midground": layers.get("midground") or [],
        "background": layers.get("background") or [],
        "architecture": architecture_package(env),
        "materials": materials_library(),
        "vegetation": vegetation_package(),
        "props": dressing.get("props") or [],
        "set_dressing": dressing,
        "weather": weather_state(weather_type=weather_type),
        "atmosphere": atmosphere_package(),
        "lighting": lighting_package(
            time_of_day=str(env.get("time_of_day") or "morning"),
            mood=lighting_mood,
        ),
        "ambient_motion": dressing.get("ambient_motion") or [],
        "camera_boundaries": layout.get("camera_safe_zones") or [],
        "character_zones": layout.get("character_movement_zones") or [],
        "continuity_rules": continuity_rules(eid),
        "validation_rules": validation_rules(),
        "pipeline": [
            "story_requirement",
            "environment_type",
            "spatial_layout",
            "foreground_midground_background",
            "architecture",
            "materials",
            "vegetation",
            "props_and_set_dressing",
            "weather_and_atmosphere",
            "lighting",
            "ambient_motion",
            "continuity_validation",
            "rendered_environment_validation",
        ],
        "quality_caveat": (
            "An Environment Package is an execution contract — not proof of quality. "
            "Final acceptance requires inspecting the rendered MP4 for depth, materials, "
            "weather response, lighting coherence, and environmental continuity."
        ),
    }
    return package
