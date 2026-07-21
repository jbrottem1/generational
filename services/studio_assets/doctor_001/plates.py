"""DOCTOR_001 — studio reference plate generation (procedural, reusable)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from services.studio_assets.doctor_001.catalog import EXPRESSION_FAMILY
from services.studio_assets.the_doctor.renderer import draw_environment_plate, draw_the_doctor_plate


POSE_FOR_VIEW = {
    "front": "front_view",
    "side_left": "left_side",
    "side_right": "right_side",
    "back": "rear_view",
    "three_quarter": "three_quarter",
}

CAMERA_POSE = {
    "closeup_eyes": ("front_view", "curious"),
    "closeup_face": ("front_view", "teaching"),
    "medium_bust": ("three_quarter", "confident"),
    "full_body_hero": ("hero", "teaching"),
    "silhouette_readability": ("front_view", "neutral"),
    "over_shoulder_teach": ("three_quarter", "explaining"),
    "profile_listen": ("left_side", "listening"),
    "low_angle_authority": ("hero", "determined"),
    "high_angle_gentle": ("front_view", "compassionate"),
    "practical_rim_clinical": ("three_quarter", "focused"),
}

HAND_POSE_MAP = {
    "relaxed_open": "standing",
    "soft_fist": "standing",
    "point_index": "pointing",
    "point_two_finger": "pointing",
    "open_palm_up": "teaching",
    "open_palm_forward": "teaching",
    "pinch_precision": "hologram_interaction",
    "grip_scanner": "medical_demonstration",
    "grip_clipboard": "clipboard",
    "thumbs_measure": "teaching",
    "cup_hands": "standing",
    "heart_height_open": "hero",
    "ok_reassure": "teaching",
    "stop_gentle": "pointing",
    "diagram_trace": "hologram_interaction",
    "hologram_pinch": "hologram_interaction",
    "typing_rest": "standing",
    "behind_back": "hands_behind_back",
}

ENV_ROOM = {
    "touch_console": "holographic_theater",
    "open_door": "main_entrance_lobby",
    "lift_scanner": "diagnostic_imaging_suite",
    "place_clipboard": "classroom_lecture_hall",
    "gesture_to_hologram": "holographic_theater",
    "walk_corridor": "main_entrance_lobby",
    "sit_exam_stool": "patient_simulation_ward",
    "stand_at_bedside": "patient_simulation_ward",
}


def _family(expression: str) -> str:
    return EXPRESSION_FAMILY.get(expression, "neutral")


def render_expression(out: Path, expression: str) -> Path:
    return draw_the_doctor_plate(
        out_path=out,
        expression=_family(expression),
        pose="front_view",
    )


def render_orthographic(out: Path, view: str) -> Path:
    pose = POSE_FOR_VIEW.get(view, "front_view")
    return draw_the_doctor_plate(out_path=out, expression="teaching", pose=pose)


def render_hand_pose(out: Path, hand_pose: str) -> Path:
    pose = HAND_POSE_MAP.get(hand_pose, "standing")
    return draw_the_doctor_plate(out_path=out, expression="focused", pose=pose)


def render_camera_test(out: Path, test_name: str) -> Path:
    pose, exp = CAMERA_POSE.get(test_name, ("front_view", "neutral"))
    size = 1280 if "full" in test_name or "hero" in test_name else 1024
    return draw_the_doctor_plate(
        out_path=out,
        size=size,
        expression=_family(exp),
        pose=pose,
    )


def render_closeup(out: Path) -> Path:
    return draw_the_doctor_plate(out_path=out, expression="teaching", pose="front_view", size=1280)


def render_fullbody(out: Path) -> Path:
    return draw_the_doctor_plate(out_path=out, expression="confident", pose="hero", size=1280)


def render_scale_reference(out: Path) -> Path:
    """Full-body with height marker annotation baked as plate (procedural)."""
    from PIL import Image, ImageDraw

    path = draw_the_doctor_plate(out_path=out, expression="neutral", pose="front_view", size=1280)
    img = Image.open(path).convert("RGBA")
    d = ImageDraw.Draw(img)
    # Height bar 185 cm reference
    d.rectangle((40, 80, 70, 1200), outline=(26, 95, 138, 255), width=4)
    d.line((70, 80, 110, 80), fill=(59, 167, 224, 255), width=3)
    d.line((70, 1200, 110, 1200), fill=(59, 167, 224, 255), width=3)
    d.text((90, 90), "185 cm", fill=(26, 95, 138, 255))
    d.text((90, 1170), "0", fill=(26, 95, 138, 255))
    d.text((90, 60), "DOCTOR_001 SCALE", fill=(44, 52, 61, 255))
    img.save(path)
    return path


def render_env_interaction(out: Path, name: str) -> Path:
    room = ENV_ROOM.get(name, "classroom_lecture_hall")
    return draw_environment_plate(out_path=out, room=room)


def render_lighting_ref(out: Path, name: str) -> Path:
    # Character plate under named lighting intent (metadata carried in sidecar JSON)
    exp = "teaching" if "teach" in name or "beauty" in name else "focused"
    if "emergency" in name:
        exp = "serious"
    if "garden" in name:
        exp = "smiling"
    return draw_the_doctor_plate(out_path=out, expression=_family(exp), pose="three_quarter")


def lighting_sidecar(name: str) -> dict[str, Any]:
    presets = {
        "day_teach_soft_key": {"key": "soft_warm_clinical", "fill": "cool_rim_blue", "mood": "clarity"},
        "night_research_cool_rim": {"key": "cool_low", "fill": "blue_rim", "mood": "focus"},
        "emergency_alert_red_practical": {"key": "practical_alert", "fill": "deep_shadow", "mood": "urgency_controlled"},
        "theater_holo_blue": {"key": "holo_cyan", "fill": "soft_white", "mood": "wonder"},
        "garden_walk_golden": {"key": "golden_hour", "fill": "sky_soft", "mood": "hope"},
        "closeup_beauty_clinical": {"key": "beauty_soft", "fill": "catchlight", "mood": "trust"},
    }
    return {"lighting_ref": name, "character_id": "DOCTOR_001", **(presets.get(name) or {})}
