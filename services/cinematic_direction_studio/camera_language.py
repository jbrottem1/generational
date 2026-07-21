"""Camera language — movement chosen from emotion, never purposeless."""

from __future__ import annotations

from typing import Any

from services.cinematic_direction_studio.models import EMOTION_CAMERA


def choose_camera_language(
    *,
    emotion: str,
    shot_type: str,
    vfd_seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    emotion = str(emotion or "curiosity").lower()
    preset = dict(EMOTION_CAMERA.get(emotion) or EMOTION_CAMERA["curiosity"])

    # Shot type can refine movement
    if shot_type == "tracking":
        preset["movement"] = "tracking_walk_and_talk"
        preset["true_motion"] = "tracking"
    elif shot_type == "follow":
        preset["movement"] = "follow"
        preset["true_motion"] = "tracking"
    elif shot_type == "orbit":
        preset["movement"] = "orbit_reveal"
        preset["true_motion"] = "orbit"
    elif shot_type == "over_the_shoulder":
        preset["movement"] = "over_the_shoulder"
        preset["true_motion"] = "handheld"
    elif shot_type in {"close_up", "extreme_close_up", "reaction"}:
        preset["movement"] = "slow_push_in"
        preset["true_motion"] = "push_in"
    elif shot_type in {"establishing", "wide"}:
        preset["movement"] = "slow_dolly"
        preset["true_motion"] = "pull_out"

    vfd = vfd_seed or {}
    if vfd.get("true_motion_camera"):
        preset["true_motion"] = str(vfd["true_motion_camera"])

    return {
        "emotion": emotion,
        "movement": preset["movement"],
        "true_motion_camera": preset["true_motion"],
        "shot_type": shot_type,
        "motivated": True,
        "purpose": f"Camera supports {emotion} — {preset['movement'].replace('_', ' ')}",
        "forbid_purposeless_move": True,
        "camera_replaces_actor_motion": False,
    }
