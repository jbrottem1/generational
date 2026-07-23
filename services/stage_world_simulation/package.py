"""Build WORLD_PACKAGE — persistent explorable stage contract."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from services.stage_world_simulation.camera import build_camera_system
from services.stage_world_simulation.geometry import build_geometry
from services.stage_world_simulation.interactions import build_interaction_points
from services.stage_world_simulation.living_world import build_living_world
from services.stage_world_simulation.location_catalog import (
    get_location_definition,
    resolve_world_id,
)
from services.stage_world_simulation.models import ENGINE_ID, PACKAGE_TYPE, PACKAGE_VERSION
from services.stage_world_simulation.navigation import build_navigation_mesh
from services.stage_world_simulation.validation import validate_world_package


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_world_package(
    location_or_id: str | dict[str, Any] | None = None,
    *,
    ambient_from_location: list[str] | None = None,
    compose_environment_department: bool = True,
) -> dict[str, Any]:
    """Construct a persistent WORLD_PACKAGE for a recurring stage."""
    world_id = resolve_world_id(location_or_id)
    definition = dict(get_location_definition(world_id) or {})
    if isinstance(location_or_id, dict):
        # Merge CWS location ambient cues
        ambient_from_location = list(
            ambient_from_location
            or location_or_id.get("environmental_animation")
            or location_or_id.get("ambient_life")
            or []
        )

    geometry = build_geometry(definition, world_id=world_id)
    navigation = build_navigation_mesh(
        geometry,
        world_id=world_id,
        has_stairs=bool(definition.get("has_stairs")),
    )
    interaction_points = build_interaction_points(geometry, world_id=world_id)
    living = build_living_world(
        definition,
        world_id=world_id,
        ambient_from_location=ambient_from_location,
    )
    camera = build_camera_system(
        world_id=world_id,
        outdoor=bool(definition.get("outdoor")),
    )

    env_dept = None
    if compose_environment_department:
        try:
            from services.environment_department import build_environment_package

            alias = definition.get("location_alias") or world_id
            env_dept = build_environment_package(alias, owner="STAGE_WORLD")
        except Exception:  # noqa: BLE001
            env_dept = None

    package: dict[str, Any] = {
        "package_type": PACKAGE_TYPE,
        "package_version": PACKAGE_VERSION,
        "engine_id": ENGINE_ID,
        "created_at": _now(),
        "world_id": world_id,
        "display_name": definition.get("display_name") or world_id,
        "location_alias": definition.get("location_alias"),
        "persistent": True,
        "flat_image_background": False,
        "philosophy": {
            "not_a_renderer": True,
            "not_an_image_generator": True,
            "rule": "Characters move through the world. They do not stand in front of photographs.",
            "pipeline": [
                "build_persistent_stage",
                "place_digital_actors",
                "navigate_and_interact",
                "camera_follows_performance",
                "renderer_records",
            ],
        },
        "geometry": geometry,
        "navigation": navigation,
        "interaction_points": interaction_points,
        "lighting": {
            "mood": definition.get("default_lighting") or "soft_daylight",
            "dynamic": True,
        },
        "weather": definition.get("default_weather") or "interior_climate",
        "ambient_effects": living.get("channels"),
        "living_world": living,
        "camera": camera,
        "environment_department_ref": {
            "environment_id": (env_dept or {}).get("environment_id"),
            "composed": bool(env_dept),
        },
        "environment_package": env_dept,
        "home_for": list(definition.get("home_for") or []),
        "architecture": {
            "frozen": True,
            "no_new_renderer": True,
            "no_pipeline_redesign": True,
            "feeds": [
                "character_world_studio",
                "character_performance_engine",
                "environment_department",
                "world_builder",
                "shot_assembly",
                "true_motion",
            ],
        },
        "scene_ref": {
            "world_id": world_id,
            "world_package_ref": f"data/world_simulation/library/{world_id}/WORLD_PACKAGE.json",
            "do_not_use_flat_photo_backdrop": True,
            "persistent": True,
        },
    }
    package["validation"] = validate_world_package(package)
    return package
