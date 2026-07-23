"""Canonical FACE_RIG_PROFILE — reusable version-controlled facial controls."""

from __future__ import annotations

from typing import Any


DEFAULT_CONTROLS: dict[str, dict[str, float]] = {
    "forehead_raise": {"min": 0.0, "max": 1.0},
    "brow_inner_left": {"min": 0.0, "max": 1.0},
    "brow_inner_right": {"min": 0.0, "max": 1.0},
    "brow_outer_left": {"min": 0.0, "max": 1.0},
    "brow_outer_right": {"min": 0.0, "max": 1.0},
    "upper_lid_left": {"min": 0.0, "max": 1.0},
    "upper_lid_right": {"min": 0.0, "max": 1.0},
    "lower_lid_left": {"min": 0.0, "max": 1.0},
    "lower_lid_right": {"min": 0.0, "max": 1.0},
    "eyeball_yaw_left": {"min": -1.0, "max": 1.0},
    "eyeball_yaw_right": {"min": -1.0, "max": 1.0},
    "eyeball_pitch_left": {"min": -1.0, "max": 1.0},
    "eyeball_pitch_right": {"min": -1.0, "max": 1.0},
    "pupil_dilate_left": {"min": 0.0, "max": 1.0},
    "pupil_dilate_right": {"min": 0.0, "max": 1.0},
    "cheek_raise_left": {"min": 0.0, "max": 1.0},
    "cheek_raise_right": {"min": 0.0, "max": 1.0},
    "nose_bridge_wrinkle": {"min": 0.0, "max": 1.0},
    "nostril_flare": {"min": 0.0, "max": 1.0},
    "upper_lip": {"min": 0.0, "max": 1.0},
    "lower_lip": {"min": 0.0, "max": 1.0},
    "lip_corner_left": {"min": -1.0, "max": 1.0},
    "lip_corner_right": {"min": -1.0, "max": 1.0},
    "jaw_open": {"min": 0.0, "max": 1.0},
    "chin_raise": {"min": 0.0, "max": 1.0},
    "neck_tension": {"min": 0.0, "max": 1.0},
    "ear_left": {"min": 0.0, "max": 1.0},
    "ear_right": {"min": 0.0, "max": 1.0},
}


def face_rig_profile(
    character_id: str,
    *,
    rig_version: str = "1.0.0",
    extras: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cid = str(character_id or "UNKNOWN").upper()
    return {
        "character_id": cid,
        "rig_version": rig_version,
        "canonical": True,
        "controls": dict(DEFAULT_CONTROLS),
        "regions": [
            "forehead",
            "inner_eyebrows",
            "outer_eyebrows",
            "upper_eyelids",
            "lower_eyelids",
            "eyeballs",
            "pupils",
            "cheeks",
            "nose_bridge",
            "nostrils",
            "upper_lip",
            "lower_lip",
            "lip_corners",
            "jaw",
            "chin",
            "neck_tension",
            "ear_movement",
        ],
        "continuity_rule": "Same canonical facial rig across all scenes for this character.",
        "pipeline": [
            "scene_intent",
            "emotional_state",
            "attention_target",
            "facial_performance_plan",
            "eye_and_head_coordination",
            "expression_blending",
            "speech_and_viseme_animation",
            "micro_expression_layer",
            "rendered_performance_validation",
        ],
        **(extras or {}),
    }
