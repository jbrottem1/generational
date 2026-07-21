"""Camera follows action — never replaces actor performance."""

from __future__ import annotations

from typing import Any

from services.character_performance_engine.models import (
    CAMERA_FOLLOW_MODES,
    CAMERA_TO_TRUE_MOTION,
)


def plan_camera_follow(
    *,
    locomotion: dict[str, Any],
    objective: dict[str, Any],
    scene_index: int = 0,
    shot_size: str = "dynamic_medium",
) -> dict[str, Any]:
    travel = float(locomotion.get("path_distance_norm") or 0)
    oid = str(objective.get("id") or "")

    if travel >= 0.25:
        mode = "walk_and_talk" if scene_index % 2 == 0 else "tracking"
    elif "evidence" in oid or "equipment" in oid:
        mode = "orbit_demonstrate"
    elif "patient" in oid:
        mode = "over_the_shoulder"
    elif shot_size in {"intimate_close_up", "close_up"}:
        mode = "close_up_reaction"
    elif scene_index == 0:
        mode = "wide_establishing"
    else:
        mode = CAMERA_FOLLOW_MODES[scene_index % len(CAMERA_FOLLOW_MODES)]

    true_cam = CAMERA_TO_TRUE_MOTION.get(mode, "tracking")
    return {
        "mode": mode,
        "true_motion_camera": true_cam,
        "follows_actor_path": True,
        "camera_replaces_action": False,
        "amplitude_scale": 0.55 if travel >= 0.2 else 0.75,
        "notes": (
            "Camera records the performance. "
            "Actor locomotion is primary; camera crop/track is secondary."
        ),
        "forbid_ken_burns_as_performance": True,
    }
