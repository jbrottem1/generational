"""Quality gates — reject flat photo stages and camera-as-acting."""

from __future__ import annotations

from typing import Any

from services.stage_world_simulation.models import (
    LIVING_CHANNELS,
    NAV_CAPABILITIES,
    REJECT_REASONS,
)


def validate_world_package(package: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(package, dict) or not package:
        return {
            "ok": False,
            "score": 0,
            "failures": ["missing_world_package"],
            "rejects": list(REJECT_REASONS),
        }

    failures: list[str] = []
    rejects: list[str] = []

    geometry = package.get("geometry") or {}
    if not geometry.get("not_a_flat_image") or not geometry.get("explorable_volume"):
        failures.append("geometry_is_flat_or_non_explorable")
        rejects.append("flat_image_background")
    if not geometry.get("floor"):
        failures.append("missing_floor")
        rejects.append("actors_cannot_navigate")
    if not (geometry.get("furniture") or geometry.get("props")):
        failures.append("missing_set_dressing")

    nav = package.get("navigation") or {}
    mesh = nav.get("nav_mesh") or {}
    if not mesh.get("walkable") or not mesh.get("waypoints"):
        failures.append("nav_mesh_incomplete")
        rejects.append("actors_cannot_navigate")
    if not set(NAV_CAPABILITIES).issubset(set(nav.get("capabilities") or [])):
        failures.append("nav_capabilities_incomplete")
        rejects.append("actors_cannot_navigate")

    interactions = package.get("interaction_points") or {}
    if int(interactions.get("count") or len(interactions.get("points") or [])) < 3:
        failures.append("insufficient_interaction_points")
        rejects.append("objects_not_interactable")
    if not interactions.get("every_prop_advertises_interactions"):
        failures.append("props_do_not_advertise_interactions")
        rejects.append("objects_not_interactable")

    living = package.get("living_world") or {}
    if not living.get("living") or living.get("forbid_static_environment") is not True:
        failures.append("environment_not_living")
        rejects.append("environment_static")
    channels = set(living.get("channels") or [])
    if len(channels.intersection(LIVING_CHANNELS)) < 3:
        failures.append("insufficient_living_channels")
        rejects.append("environment_static")

    cam = package.get("camera") or {}
    if cam.get("camera_replaces_actor_motion") is True:
        failures.append("camera_replaces_actor_motion")
        rejects.append("camera_replaces_character_movement")
    if not cam.get("follows_performance"):
        failures.append("camera_does_not_follow_performance")
        rejects.append("camera_replaces_character_movement")

    if package.get("flat_image_background") is True:
        failures.append("flat_image_flag")
        rejects.append("flat_image_background")

    if not package.get("persistent"):
        failures.append("world_not_marked_persistent")

    score = max(0, 100 - 10 * len(failures))
    return {
        "ok": not failures,
        "score": score,
        "failures": failures,
        "rejects_hit": sorted(set(rejects)),
        "reject_catalog": list(REJECT_REASONS),
        "success": (
            "Persistent worlds populated by reusable digital actors — "
            "filmed on a real set, not assembled from disconnected images."
        ),
        "mp4_required": True,
        "note": (
            "Passing this plan gate is necessary but not sufficient. "
            "Inspect the final MP4: actors must navigate living stages, not photos."
        ),
    }
