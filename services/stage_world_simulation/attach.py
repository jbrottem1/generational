"""Soft-attach persistent WORLD_PACKAGE refs onto scenes / candidates."""

from __future__ import annotations

from typing import Any

from services.stage_world_simulation.library import resolve_world_package
from services.stage_world_simulation.location_catalog import resolve_world_id


def attach_world_simulation(
    scenes: list[dict[str, Any]],
    *,
    location: dict[str, Any] | str | None = None,
) -> list[dict[str, Any]]:
    """Stamp world_package / nav / interaction refs onto scene bindings."""
    world = resolve_world_package(location)
    wid = world.get("world_id") or resolve_world_id(location)
    slim = {
        "world_id": wid,
        "display_name": world.get("display_name"),
        "scene_ref": world.get("scene_ref"),
        "validation": world.get("validation"),
        "navigation_capabilities": (world.get("navigation") or {}).get("capabilities"),
        "interaction_count": (world.get("interaction_points") or {}).get("count"),
        "living_channels": (world.get("living_world") or {}).get("channels"),
        "camera": {
            "follows_performance": True,
            "camera_replaces_actor_motion": False,
            "default_mode": (world.get("camera") or {}).get("default_mode"),
            "true_motion_map": (world.get("camera") or {}).get("true_motion_map"),
        },
        "persistent": True,
        "flat_image_background": False,
        "do_not_use_flat_photo_backdrop": True,
    }
    out: list[dict[str, Any]] = []
    for scene in scenes:
        row = dict(scene)
        row["stage_world_package"] = slim
        row["world_id"] = wid
        row["world_package_ref"] = (world.get("scene_ref") or {}).get("world_package_ref")
        # Enrich true_motion camera bias toward follow/tracking when on a stage
        tm = dict(row.get("true_motion") or {})
        cam = (world.get("camera") or {})
        if not tm.get("actor_driven"):
            tm.setdefault(
                "camera",
                (cam.get("true_motion_map") or {}).get("tracking", "tracking"),
            )
        tm["stage_world"] = True
        tm["not_flat_photo_backdrop"] = True
        row["true_motion"] = tm
        row["environment_life_plan"] = row.get("environment_life_plan") or world.get(
            "living_world"
        )
        out.append(row)
    return out


def attach_world_to_candidate(
    candidate: dict[str, Any],
    *,
    location: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
    out = dict(candidate)
    loc = location or out.get("studio_location") or (out.get("world_package") or {}).get("world_id")
    world = resolve_world_package(loc)
    out["stage_world_simulation"] = {
        "world_id": world.get("world_id"),
        "display_name": world.get("display_name"),
        "scene_ref": world.get("scene_ref"),
        "validation": world.get("validation"),
        "persistent": True,
    }
    out["world_id"] = world.get("world_id")
    out["world_package_ref"] = (world.get("scene_ref") or {}).get("world_package_ref")
    # Soft-enrich existing world_package without fighting World Builder
    wp = dict(out.get("world_package") or {})
    wp["stage_world_id"] = world.get("world_id")
    wp["persistent_stage"] = True
    wp["flat_image_background"] = False
    wp["navigation"] = (world.get("navigation") or {}).get("nav_mesh")
    wp["interaction_points"] = (world.get("interaction_points") or {}).get("points")
    wp["living_world"] = world.get("living_world")
    out["world_package"] = wp
    return out
