"""Compose studio packages → EXECUTABLE_ANIMATION_SCENE (execution contract)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

PACKAGE_TYPE = "EXECUTABLE_ANIMATION_SCENE"
PACKAGE_VERSION = "1.0.0"

SPOKEN_LINE = "Real discovery begins when we look a little closer."


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_joint_tracks_for_golden_motion(*, duration_sec: float = 14.0) -> list[dict[str, Any]]:
    """Declarative joint tracks the skeletal runtime must execute (not image pans)."""
    # Times align with Golden Motion shot beats
    return [
        {
            "joint": "pelvis",
            "channel": "translation",
            "keys": [
                {"t": 0.0, "value": [0.0, 0.95, -2.5]},
                {"t": 3.0, "value": [0.0, 0.95, 0.2]},
                {"t": 6.0, "value": [0.3, 0.95, 1.2]},
                {"t": 10.0, "value": [0.35, 0.95, 1.25]},
                {"t": 14.0, "value": [0.35, 0.95, 1.3]},
            ],
            "evidence": "pelvis_translation",
        },
        {
            "joint": "spine_01",
            "channel": "rotation_euler",
            "keys": [
                {"t": 0.0, "value": [0, 0, 0]},
                {"t": 5.5, "value": [0, 25, 0]},
                {"t": 8.0, "value": [8, 35, 0]},
                {"t": 12.0, "value": [5, 180, 0]},
            ],
            "evidence": "spine_rotation",
        },
        {
            "joint": "shoulder_right",
            "channel": "rotation_euler",
            "keys": [
                {"t": 6.0, "value": [0, 0, 0]},
                {"t": 7.5, "value": [35, 10, -20]},
                {"t": 9.0, "value": [55, 15, -25]},
                {"t": 12.0, "value": [70, 5, -10]},
            ],
            "evidence": "shoulder_movement",
        },
        {
            "joint": "elbow_right",
            "channel": "rotation_euler",
            "keys": [
                {"t": 6.0, "value": [10, 0, 0]},
                {"t": 8.0, "value": [45, 0, 0]},
                {"t": 9.5, "value": [25, 0, 0]},
            ],
            "evidence": "elbow_articulation",
        },
        {
            "joint": "wrist_right",
            "channel": "rotation_euler",
            "keys": [
                {"t": 7.0, "value": [0, 0, 0]},
                {"t": 8.5, "value": [15, -10, 0]},
                {"t": 9.5, "value": [5, 0, 0]},
            ],
            "evidence": "wrist_movement",
        },
        {
            "joint": "hand_right_fingers",
            "channel": "grasp",
            "keys": [
                {"t": 7.2, "value": 0.0, "note": "fingers_open_before_contact"},
                {"t": 8.2, "value": 0.35},
                {"t": 9.0, "value": 0.85, "note": "fingers_close_around_object"},
                {"t": 14.0, "value": 0.8},
            ],
            "evidence": "finger_movement",
        },
        {
            "joint": "hip_left",
            "channel": "rotation_euler",
            "keys": [
                {"t": 0.0, "value": [15, 0, 0]},
                {"t": 0.5, "value": [-10, 0, 0]},
                {"t": 1.0, "value": [15, 0, 0]},
                {"t": 1.5, "value": [-10, 0, 0]},
                {"t": 2.5, "value": [5, 0, 0]},
                {"t": 3.2, "value": [0, 0, 0]},
            ],
            "evidence": "hip_movement",
        },
        {
            "joint": "knee_left",
            "channel": "rotation_euler",
            "keys": [
                {"t": 0.0, "value": [5, 0, 0]},
                {"t": 0.4, "value": [55, 0, 0]},
                {"t": 0.8, "value": [5, 0, 0]},
                {"t": 1.2, "value": [55, 0, 0]},
                {"t": 3.0, "value": [5, 0, 0]},
            ],
            "evidence": "knee_bending",
        },
        {
            "joint": "knee_right",
            "channel": "rotation_euler",
            "keys": [
                {"t": 0.2, "value": [55, 0, 0]},
                {"t": 0.6, "value": [5, 0, 0]},
                {"t": 1.0, "value": [55, 0, 0]},
                {"t": 1.4, "value": [5, 0, 0]},
                {"t": 3.0, "value": [5, 0, 0]},
            ],
            "evidence": "knee_bending",
        },
        {
            "joint": "ankle_left",
            "channel": "rotation_euler",
            "keys": [
                {"t": 0.35, "value": [12, 0, 0], "note": "heel_strike"},
                {"t": 0.55, "value": [0, 0, 0], "note": "toe_roll"},
                {"t": 1.35, "value": [12, 0, 0]},
            ],
            "evidence": "ankle_articulation",
        },
        {
            "joint": "ankle_right",
            "channel": "rotation_euler",
            "keys": [
                {"t": 0.85, "value": [12, 0, 0], "note": "heel_strike"},
                {"t": 1.05, "value": [0, 0, 0], "note": "toe_roll"},
            ],
            "evidence": "ankle_articulation",
        },
        {
            "joint": "foot_left",
            "channel": "plant",
            "keys": [
                {"t": 0.4, "value": 1.0, "contact": "floor"},
                {"t": 0.9, "value": 0.0},
                {"t": 1.4, "value": 1.0, "contact": "floor"},
                {"t": 3.2, "value": 1.0, "contact": "floor"},
            ],
            "evidence": "planted_feet",
        },
        {
            "joint": "foot_right",
            "channel": "plant",
            "keys": [
                {"t": 0.0, "value": 1.0, "contact": "floor"},
                {"t": 0.5, "value": 0.0},
                {"t": 0.9, "value": 1.0, "contact": "floor"},
                {"t": 3.2, "value": 1.0, "contact": "floor"},
            ],
            "evidence": "planted_feet",
        },
        {
            "joint": "head",
            "channel": "rotation_euler",
            "keys": [
                {"t": 4.5, "value": [0, 0, 0]},
                {"t": 5.2, "value": [10, 20, 0], "note": "look_to_sample"},
                {"t": 11.0, "value": [0, 160, 0], "note": "turn_to_viewer"},
            ],
            "evidence": "head_turns",
        },
        {
            "joint": "eye_left",
            "channel": "gaze",
            "keys": [
                {"t": 4.2, "value": "sample_container", "note": "eyes_before_head"},
                {"t": 10.5, "value": "camera"},
            ],
            "evidence": "eye_movement",
        },
        {
            "joint": "eye_right",
            "channel": "gaze",
            "keys": [
                {"t": 4.2, "value": "sample_container"},
                {"t": 10.5, "value": "camera"},
            ],
            "evidence": "eye_movement",
        },
        {
            "joint": "eyelids",
            "channel": "blink",
            "keys": [
                {"t": 2.1, "value": 1.0},
                {"t": 2.2, "value": 0.0},
                {"t": 7.8, "value": 1.0},
                {"t": 7.9, "value": 0.0},
                {"t": 12.4, "value": 1.0},
                {"t": 12.5, "value": 0.0},
            ],
            "evidence": "blinking",
        },
        {
            "joint": "jaw",
            "channel": "speech",
            "keys": [
                {"t": 10.5, "value": 0.0},
                {"t": 11.0, "value": 0.4},
                {"t": 13.5, "value": 0.35},
                {"t": 14.0, "value": 0.0},
            ],
            "evidence": "mouth_articulation",
            "requires_phoneme_timeline": True,
        },
        {
            "joint": "mouth_corner_left",
            "channel": "smile",
            "keys": [
                {"t": 10.8, "value": 0.0},
                {"t": 11.5, "value": 0.55},
                {"t": 14.0, "value": 0.45},
            ],
            "evidence": "facial_expressions",
        },
        {
            "joint": "mouth_corner_right",
            "channel": "smile",
            "keys": [
                {"t": 10.8, "value": 0.0},
                {"t": 11.5, "value": 0.55},
                {"t": 14.0, "value": 0.45},
            ],
            "evidence": "facial_expressions",
        },
        {
            "joint": "chest",
            "channel": "breath",
            "keys": [
                {"t": 0.0, "value": 0.0},
                {"t": 1.6, "value": 0.08},
                {"t": 3.2, "value": 0.0},
                {"t": 6.4, "value": 0.08},
                {"t": 9.6, "value": 0.0},
                {"t": 12.8, "value": 0.08},
            ],
            "evidence": "subtle_breathing",
        },
    ]


def build_phoneme_timeline_for_line(line: str = SPOKEN_LINE, *, t0: float = 10.5) -> list[dict[str, Any]]:
    """Approximate viseme schedule from syllables — runtime must align to waveform."""
    # Honest: this is a planning timeline. True sync requires audio analysis at runtime.
    words = [
        ("Real", 0.0, 0.28, "R"),
        ("discovery", 0.28, 0.85, "E"),
        ("begins", 0.85, 1.25, "B"),
        ("when", 1.25, 1.45, "W"),
        ("we", 1.45, 1.6, "E"),
        ("look", 1.6, 1.9, "U"),
        ("a", 1.9, 2.0, "A"),
        ("little", 2.0, 2.35, "I"),
        ("closer", 2.35, 2.9, "O"),
    ]
    out = []
    for word, a, b, vis in words:
        out.append(
            {
                "t": round(t0 + a, 3),
                "t_end": round(t0 + b, 3),
                "word": word,
                "viseme": vis,
                "source": "planned_syllable_map",
                "requires_waveform_alignment": True,
            }
        )
    out.append({"line": line, "t0": t0, "t_end": t0 + 2.9})
    return out


def build_executable_animation_scene(
    *,
    director_package: dict[str, Any] | None = None,
    character_performance_package: dict[str, Any] | None = None,
    character_rig_package: dict[str, Any] | None = None,
    world_package: dict[str, Any] | None = None,
    interaction_packages: list[dict[str, Any]] | None = None,
    duration_sec: float = 14.0,
) -> dict[str, Any]:
    """DIRECTOR + PERFORMANCE + RIG + WORLD + INTERACTION → EXECUTABLE_ANIMATION_SCENE."""
    joints = build_joint_tracks_for_golden_motion(duration_sec=duration_sec)
    phonemes = build_phoneme_timeline_for_line()

    camera_plan = [
        {
            "shot": 1,
            "t_start": 0.0,
            "t_end": 3.0,
            "framing": "wide_tracking",
            "follow": "pelvis",
            "purpose": "Doctor enters through doorway",
            "forbid_conceal_missing_animation": True,
        },
        {
            "shot": 2,
            "t_start": 3.0,
            "t_end": 6.0,
            "framing": "medium_three_quarter",
            "follow": "chest",
            "purpose": "Approach worktable / look to sample",
            "forbid_conceal_missing_animation": True,
        },
        {
            "shot": 3,
            "t_start": 6.0,
            "t_end": 10.0,
            "framing": "close_insert_hand",
            "follow": "hand_right",
            "purpose": "Grasp sample container",
            "forbid_conceal_missing_animation": True,
        },
        {
            "shot": 4,
            "t_start": 10.0,
            "t_end": duration_sec,
            "framing": "medium_close_up",
            "follow": "head",
            "purpose": "Spoken line to viewer",
            "forbid_conceal_missing_animation": True,
        },
    ]

    interactions = list(interaction_packages or [])
    if not interactions:
        try:
            from services.physics_interaction import build_interaction_package

            interactions = [
                build_interaction_package(
                    actor="DOCTOR_001",
                    target="door_main",
                    interaction_type="opening_doors",
                    interaction_id="gm_open_door",
                    t_start=0.0,
                    t_end=1.2,
                    world_id="WORLD-GMRI-MEDICAL-LAB",
                ),
                build_interaction_package(
                    actor="DOCTOR_001",
                    target="nav_mesh",
                    interaction_type="walking",
                    interaction_id="gm_walk_enter",
                    t_start=0.2,
                    t_end=3.0,
                    world_id="WORLD-GMRI-MEDICAL-LAB",
                ),
                build_interaction_package(
                    actor="DOCTOR_001",
                    target="sample_container",
                    interaction_type="picking_up_objects",
                    interaction_id="gm_grasp_sample",
                    t_start=6.5,
                    t_end=9.5,
                    world_id="WORLD-GMRI-MEDICAL-LAB",
                ),
                build_interaction_package(
                    actor="DOCTOR_001",
                    target="sample_container",
                    interaction_type="holding_objects",
                    interaction_id="gm_hold_sample",
                    t_start=9.5,
                    t_end=duration_sec,
                    world_id="WORLD-GMRI-MEDICAL-LAB",
                ),
            ]
        except Exception:  # noqa: BLE001
            interactions = []

    evidence_required = sorted(
        {str(j.get("evidence")) for j in joints if j.get("evidence")}
    )

    return {
        "package_type": PACKAGE_TYPE,
        "package_version": PACKAGE_VERSION,
        "created_at": _now(),
        "character_id": "DOCTOR_001",
        "world_id": (world_package or {}).get("world_id") or "WORLD-GMRI-MEDICAL-LAB",
        "duration_sec": duration_sec,
        "spoken_line": SPOKEN_LINE,
        "props": [
            {"id": "door_main", "type": "door"},
            {"id": "worktable", "type": "desk"},
            {"id": "medical_scanner", "type": "console"},
            {"id": "sample_container", "type": "tool", "holdable": True},
        ],
        "actor_transform": {"x": 0.0, "y": 0.0, "z": -2.5, "yaw_deg": 0.0},
        "animation_clips": [
            "walking_cycle",
            "stopping",
            "looking_around",
            "picking_up_objects",
            "explaining",
        ],
        "joint_tracks": joints,
        "facial_tracks": {
            "blinks": [j for j in joints if j.get("joint") == "eyelids"],
            "smile": [j for j in joints if "mouth_corner" in str(j.get("joint"))],
            "gaze": [j for j in joints if "eye_" in str(j.get("joint"))],
            "speech_driven": True,
        },
        "gaze_target": {"sequence": ["sample_container", "camera"]},
        "phoneme_timeline": phonemes,
        "attachments": [
            {"t": 9.0, "hand": "hand_right", "object_id": "sample_container"},
        ],
        "interactions": interactions,
        "physics_state": {
            "no_float": True,
            "no_clip": True,
            "no_teleport": True,
            "foot_planting": True,
            "object_mass_kg": 0.12,
            "arm_weight_reaction": True,
        },
        "camera_plan": camera_plan,
        "lighting_plan": {
            "intent": "scientific",
            "mood": "clinical_warm",
            "motivated": True,
        },
        "source_packages": {
            "director_package": bool(director_package),
            "character_performance_package": bool(character_performance_package),
            "character_rig_package": bool(character_rig_package),
            "world_package": bool(world_package),
            "interaction_packages": len(interactions),
        },
        "director_package": director_package,
        "character_performance_package": character_performance_package,
        "character_rig_package": character_rig_package,
        "world_package": world_package,
        "true_motion_requirements": {
            "rig_driven": True,
            "evidence_required": evidence_required,
            "camera_alone_does_not_count": True,
            "moving_photograph_does_not_count": True,
        },
        "auto_reject_if": [
            "still_image_actor",
            "image_translation_or_scaling_as_motion",
            "flat_photo_background",
            "foot_sliding",
            "no_limb_articulation",
            "failed_grasp",
            "floating_object",
            "absent_lip_sync",
            "frozen_face",
            "camera_conceals_missing_animation",
            "false_capability_claim",
        ],
    }
