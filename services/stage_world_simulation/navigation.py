"""Navigation mesh — actors move through the stage, not across photographs."""

from __future__ import annotations

from typing import Any

from services.stage_world_simulation.models import NAV_CAPABILITIES


def build_navigation_mesh(
    geometry: dict[str, Any],
    *,
    world_id: str,
    has_stairs: bool = False,
) -> dict[str, Any]:
    dims = geometry.get("dimensions_m") or {"x": 12.0, "z": 10.0}
    x, z = float(dims["x"]), float(dims["z"])

    # Walkable polygon (stage floor) with furniture exclusion radii
    walkable = {
        "polygon": [
            [-x / 2 + 0.4, 0.0, -z / 2 + 0.4],
            [x / 2 - 0.4, 0.0, -z / 2 + 0.4],
            [x / 2 - 0.4, 0.0, z / 2 - 0.4],
            [-x / 2 + 0.4, 0.0, z / 2 - 0.4],
        ],
        "agent_radius_m": 0.35,
        "agent_height_m": 1.8,
    }

    obstacles = []
    for item in list(geometry.get("furniture") or []) + list(geometry.get("props") or []):
        if not item.get("collision"):
            continue
        pos = item.get("position") or [0, 0, 0]
        obstacles.append(
            {
                "id": item.get("id"),
                "center": pos,
                "radius_m": 0.55,
                "navigable_around": bool(item.get("navigable_around", True)),
            }
        )

    waypoints = [
        {"id": "spawn_entrance", "position": [0.0, 0.0, -z / 2 + 1.2], "kind": "entrance"},
        {"id": "center_stage", "position": [0.0, 0.0, 0.0], "kind": "performance"},
        {"id": "teach_mark", "position": [x * 0.15, 0.0, z * 0.1], "kind": "performance"},
        {"id": "prop_approach", "position": [x * 0.2, 0.0, z * 0.15], "kind": "interaction"},
    ]
    if has_stairs:
        waypoints.append(
            {"id": "stair_landing", "position": [-x * 0.3, 0.0, z * 0.25], "kind": "stairs"}
        )

    paths = [
        {"id": "enter_to_center", "from": "spawn_entrance", "to": "center_stage"},
        {"id": "center_to_teach", "from": "center_stage", "to": "teach_mark"},
        {"id": "teach_to_prop", "from": "teach_mark", "to": "prop_approach"},
    ]

    return {
        "world_id": world_id,
        "nav_mesh": {
            "walkable": walkable,
            "obstacles": obstacles,
            "waypoints": waypoints,
            "paths": paths,
            "stairs": bool(has_stairs),
            "collision_avoidance": True,
        },
        "capabilities": list(NAV_CAPABILITIES),
        "forbid_teleport": True,
        "forbid_slide_through_geometry": True,
        "actors_navigate_world": True,
        "not_photo_backdrop": True,
    }
