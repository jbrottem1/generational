"""Stage camera — follows performance; never replaces actor motion."""

from __future__ import annotations

from typing import Any

from services.stage_world_simulation.models import CAMERA_MODES, CAMERA_TO_TRUE_MOTION


def build_camera_system(*, world_id: str, outdoor: bool = False) -> dict[str, Any]:
    modes = list(CAMERA_MODES)
    default = "wide_establishing" if outdoor else "medium_coverage"
    return {
        "world_id": world_id,
        "modes": modes,
        "default_mode": default,
        "follows_performance": True,
        "camera_replaces_actor_motion": False,
        "motivated_only": True,
        "true_motion_map": dict(CAMERA_TO_TRUE_MOTION),
        "recommended_coverage": [
            {"beat": "enter", "mode": "wide_establishing"},
            {"beat": "walk_explain", "mode": "tracking"},
            {"beat": "interact_prop", "mode": "over_the_shoulder"},
            {"beat": "reaction", "mode": "close_up_reaction"},
            {"beat": "teach", "mode": "medium_coverage"},
        ],
        "forbid_ken_burns_as_performance": True,
        "notes": "Camera records the stage performance. Actor locomotion is primary.",
    }


def choose_stage_camera(mode: str | None = None) -> dict[str, Any]:
    m = str(mode or "tracking")
    if m not in CAMERA_MODES:
        m = "tracking"
    return {
        "mode": m,
        "true_motion_camera": CAMERA_TO_TRUE_MOTION.get(m, "tracking"),
        "follows_performance": True,
        "camera_replaces_actor_motion": False,
    }
