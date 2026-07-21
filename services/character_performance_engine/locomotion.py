"""Locomotion paths with foot contact — no float, slide, or teleport."""

from __future__ import annotations

from typing import Any

from services.character_performance_engine.models import MIN_LOCOMOTION_WAYPOINTS


def build_locomotion(
    blocking: dict[str, Any],
    *,
    duration_sec: float,
    walking_style: str = "grounded_walk_explain",
) -> dict[str, Any]:
    walk = blocking.get("where_walking") or {}
    waypoints = list(walk.get("waypoints") or [])
    if len(waypoints) < MIN_LOCOMOTION_WAYPOINTS:
        # Force a minimum travel even on short beats
        waypoints = [
            {"t": 0.0, "x": 0.30, "y": 0.52, "facing": "right", "action": "plant"},
            {"t": max(duration_sec * 0.55, 0.8), "x": 0.58, "y": 0.50, "facing": "camera", "action": "arrive"},
        ]

    # Ensure final waypoint lands at duration
    last = dict(waypoints[-1])
    if float(last.get("t") or 0) < duration_sec - 0.05:
        last = {**last, "t": duration_sec, "action": last.get("action") or "hold_grounded"}
        waypoints = [*waypoints[:-1], last]

    foot_plants = []
    for i, wp in enumerate(waypoints):
        foot_plants.append(
            {
                "t": float(wp.get("t") or 0),
                "foot": "left" if i % 2 == 0 else "right",
                "grounded": True,
                "weight": 0.55 if i % 2 == 0 else 0.45,
            }
        )

    travel = _path_distance(waypoints)
    return {
        "style": walking_style,
        "waypoints": waypoints,
        "foot_plants": foot_plants,
        "weight_transfer": True,
        "hip_rotation": True,
        "shoulder_counter": True,
        "walk_bob_amp": 0.012,
        "stride_sec": 0.48,
        "path_distance_norm": travel,
        "never_float": True,
        "never_slide": True,
        "never_teleport": True,
        "floor_y_band": [0.48, 0.58],
        "continuous": True,
    }


def _path_distance(waypoints: list[dict[str, Any]]) -> float:
    if len(waypoints) < 2:
        return 0.0
    total = 0.0
    for a, b in zip(waypoints, waypoints[1:]):
        dx = float(b.get("x") or 0) - float(a.get("x") or 0)
        dy = float(b.get("y") or 0) - float(a.get("y") or 0)
        total += (dx * dx + dy * dy) ** 0.5
    return round(total, 4)
