"""DOCTOR_001 — technical studio specifications (rig, face, motion, materials)."""

from __future__ import annotations

from typing import Any

from services.studio_assets.doctor_001.catalog import CHARACTER_ID, HAND_POSES
from services.studio_assets.doctor_001.identity import COLOR_PALETTE


def facial_topology() -> dict[str, Any]:
    return {
        "character_id": CHARACTER_ID,
        "topology_style": "cinematic_humanoid_medical_chassis",
        "regions": {
            "forehead_plate": {"edges": "soft_rounded", "seam": "subtle_titanium"},
            "brow_ridge": {"controllable": True, "range": "human_readable"},
            "orbital_sockets": {"eye_cores": "warm_blue_intelligent", "lid_planes": 2},
            "cheek_plates": {"soft_polymer_over_titanium": True},
            "nose_bridge": {"subtle_ridge": True},
            "philtrum_zone": {"present_for_speech_read": True},
            "mouth_aperture": {"viseme_capable": True, "never_horror_gape": True},
            "jaw": {"hinge": "natural", "side_shift_soft_limit": True},
            "chin_glow": {"signature_accent": True, "color": COLOR_PALETTE["accent"]["hex"]},
            "ear_modules": {"flush_medical_sensors": True},
            "neck_collar": {"titanium_transition_to_torso": True},
        },
        "edge_flow_goals": [
            "deformation_around_mouth",
            "lid_fold_readability",
            "cheek_raise_support",
            "stable_silhouette_in_profile",
        ],
        "forbid": ["uncanny_asymmetry_drift", "melting_topology", "random_regen_mesh"],
    }


def eye_movement_model() -> dict[str, Any]:
    return {
        "character_id": CHARACTER_ID,
        "behaviors": [
            "target_based_focus",
            "smooth_saccades",
            "anticipatory_glances",
            "natural_fixation_duration",
            "head_eye_coordination",
            "pupil_response_to_lighting",
            "convergence_near",
            "subtle_asymmetry",
        ],
        "rules": [
            "eyes_move_before_head",
            "blink_irregular",
            "no_lifeless_stare",
            "camera_lock_only_when_addressing_audience",
            "track_holograms_and_speakers",
        ],
        "default_targets": ["audience", "subject", "scanner_readout", "co_host"],
        "reject": ["cross_eyed", "eyes_outside_sockets", "mechanical_sync_only"],
    }


def blinking_model() -> dict[str, Any]:
    return {
        "character_id": CHARACTER_ID,
        "interval_mode": "irregular",
        "base_interval_seconds": [2.2, 5.8],
        "lid_weights": {"upper": 0.85, "lower": 0.15},
        "duration_seconds": [0.08, 0.16],
        "increase_on": ["stress", "transition", "cognitive_load", "sentence_end"],
        "reduce_on": ["intense_focus", "demonstrating_detail"],
        "double_blink_on": ["refocus", "emotional_softening"],
        "forbid_fixed_robotic_interval": True,
    }


def breathing_profile() -> dict[str, Any]:
    return {
        "character_id": CHARACTER_ID,
        "affects": ["upper_chest", "lower_rib", "shoulders", "abdomen", "coat_drape", "neck_tension"],
        "modes": {
            "rest": {"rate_bpm": 12, "amplitude": 0.25},
            "teaching": {"rate_bpm": 12, "amplitude": 0.3, "phrase_coordinated": True},
            "speak": {"rate_bpm": 14, "amplitude": 0.28, "phrase_coordinated": True},
            "walk": {"rate_bpm": 16, "amplitude": 0.35},
            "run": {"rate_bpm": 26, "amplitude": 0.55},
            "concern": {"rate_bpm": 15, "amplitude": 0.32, "bias": "upper_chest"},
            "calm_reassure": {"rate_bpm": 11, "amplitude": 0.22, "bias": "diaphragmatic"},
        },
        "forbid_whole_torso_scale": True,
    }


def skeletal_proportions() -> dict[str, Any]:
    return {
        "character_id": CHARACTER_ID,
        "height_cm": 185,
        "hierarchy": [
            "root",
            "pelvis",
            "spine_01",
            "spine_02",
            "chest",
            "neck",
            "head",
            "jaw",
            "eye_left",
            "eye_right",
            "clavicle_left",
            "upper_arm_left",
            "forearm_left",
            "hand_left",
            "clavicle_right",
            "upper_arm_right",
            "forearm_right",
            "hand_right",
            "thigh_left",
            "shin_left",
            "foot_left",
            "toes_left",
            "thigh_right",
            "shin_right",
            "foot_right",
            "toes_right",
        ],
        "ratios": {
            "head_height": 0.125,
            "shoulder_width": 0.26,
            "torso_length": 0.30,
            "upper_arm": 0.17,
            "forearm": 0.15,
            "hand": 0.105,
            "thigh": 0.25,
            "shin": 0.23,
            "foot": 0.14,
        },
        "ik_targets": ["hand_left", "hand_right", "foot_left", "foot_right"],
    }


def muscle_definition() -> dict[str, Any]:
    return {
        "character_id": CHARACTER_ID,
        "emphasis": "subtle_readability_under_polymer_not_bodybuilder",
        "regions": [
            "facial",
            "neck",
            "deltoid",
            "pectoral_plate_suggestion",
            "forearm",
            "hand_intrinsics",
            "quad",
            "calf",
        ],
        "response_drivers": ["flexion", "extension", "load", "tension", "relaxation"],
    }


def skin_material() -> dict[str, Any]:
    return {
        "character_id": CHARACTER_ID,
        "type": "soft_white_medical_polymer_over_titanium",
        "albedo": COLOR_PALETTE["primary"]["hex"],
        "roughness": 0.45,
        "specular": 0.35,
        "subsurface_hint": 0.12,
        "micro_detail": ["soft_seam_lines", "matte_clinical_finish"],
        "forbid": ["wet_horror_sheen", "cheap_plastic_clipart"],
    }


def hair_profile() -> dict[str, Any]:
    return {
        "character_id": CHARACTER_ID,
        "has_organic_hair": False,
        "type": "cranial_polymer_plating",
        "secondary_motion": "subtle_seam_highlight_with_head_turn",
        "wind_response": "minimal_chassis",
        "collision": ["coat_collar", "shoulders"],
    }


def materials() -> dict[str, Any]:
    return {
        "character_id": CHARACTER_ID,
        "surfaces": {
            "polymer_shell": skin_material(),
            "titanium_trim": {
                "albedo": COLOR_PALETTE["secondary"]["hex"],
                "roughness": 0.35,
                "metalness": 0.75,
            },
            "eye_core_glass": {
                "albedo": COLOR_PALETTE["eye_core"]["hex"],
                "roughness": 0.15,
                "emission": 0.55,
            },
            "coat_weave": {
                "albedo": COLOR_PALETTE["primary"]["hex"],
                "roughness": 0.55,
                "fabric": True,
            },
            "led_accent": {
                "albedo": COLOR_PALETTE["accent"]["hex"],
                "emission": 0.7,
            },
        },
    }


def clothing_simulation() -> dict[str, Any]:
    return {
        "character_id": CHARACTER_ID,
        "default_outfit": "primary_medical_coat",
        "garments": {
            "primary_medical_coat": {
                "material_type": "medical_coat_polymer_weave",
                "thickness": "medium",
                "weight": "medium",
                "stiffness": "controlled_drape",
                "wind_response": "moderate_hem_and_sleeve",
                "fold_zones": ["shoulders", "elbows", "waist", "hem"],
                "collision_layers": ["arms", "torso", "thighs"],
            }
        },
        "rules": [
            "fabric_not_painted_still",
            "responds_to_walk_turn_stop",
            "no_limb_clipping",
            "preserve_silhouette",
            "secondary_motion_never_overpowers_performance",
        ],
        "variants": [
            "primary_outfit",
            "formal_laboratory",
            "research",
            "field_expedition",
            "space_exploration",
            "medical_examination",
            "winter",
            "protective_equipment",
        ],
    }


def silhouette_rules() -> dict[str, Any]:
    return {
        "character_id": CHARACTER_ID,
        "must_read_in_black_shape": True,
        "keys": [
            "tall_upright_medical_coat",
            "rounded_cranial_module",
            "chest_interface_block",
            "open_professional_stance",
            "no_spiky_menace_appendages",
        ],
        "tests": ["silhouette_readability plate", "backlit corridor", "distant establishing"],
        "reject_if": ["unrecognizable_at_distance", "confused_with_generic_robot"],
    }


def rig_specification() -> dict[str, Any]:
    return {
        "character_id": CHARACTER_ID,
        "rig_type": "humanoid_ik_fk_hybrid_spec",
        "note": "Specification for Animation Engine / future-compatible motion — not a new renderer.",
        "spine_controls": ["pelvis", "spine_01", "spine_02", "chest", "neck", "head"],
        "face_controls": [
            "brow_inner_l",
            "brow_inner_r",
            "brow_outer_l",
            "brow_outer_r",
            "lid_upper_l",
            "lid_upper_r",
            "lid_lower_l",
            "lid_lower_r",
            "eye_aim_l",
            "eye_aim_r",
            "cheek_l",
            "cheek_r",
            "mouth_corner_l",
            "mouth_corner_r",
            "jaw_open",
            "lips_press",
        ],
        "hand_controls": HAND_POSES,
        "ik": {"hands": True, "feet": True, "pole_vectors": True},
        "space_switches": ["world", "body", "prop"],
    }


def animation_constraints() -> dict[str, Any]:
    return {
        "character_id": CHARACTER_ID,
        "joint_limits_soft": True,
        "forbid": [
            "limb_length_drift",
            "foot_slide",
            "hand_intersection",
            "clothing_penetration",
            "weightless_float",
            "rigid_spin_turns",
            "instant_expression_switch",
            "purposeless_motion",
        ],
        "require": [
            "anticipation",
            "overlap",
            "follow_through",
            "foot_contact",
            "eye_led_turns",
            "breath_alive_idle",
        ],
        "walk_phases": [
            "heel_strike",
            "flatten",
            "weight_accept",
            "mid_stance",
            "heel_rise",
            "toe_off",
            "swing",
        ],
        "doctor_walk_traits": [
            "calm_authority",
            "precise_foot_placement",
            "minimal_waste",
            "approachable_not_militaristic",
        ],
    }


def gesture_library() -> dict[str, Any]:
    return {
        "character_id": CHARACTER_ID,
        "rules": [
            "motivated_by_communication",
            "begin_before_emphasized_word",
            "return_to_rest",
            "vary_repeats",
        ],
        "gestures": {
            "open_palm_teach": {"category": "teaching"},
            "open_palm_reassurance": {"category": "reassuring"},
            "heart_hand": {"category": "greeting_compassion"},
            "clipboard_point": {"category": "teaching"},
            "hologram_pinch": {"category": "object"},
            "scanner_sweep": {"category": "object"},
            "diagram_trace": {"category": "teaching"},
            "scale_show": {"category": "explaining_scale"},
            "chin_think": {"category": "thinking"},
            "listen_fold": {"category": "listening"},
            "emphasize": {"category": "emphasizing"},
            "warning_focus": {"category": "warning"},
            "bedside_soft_point": {"category": "clinical_care"},
        },
    }


def hand_pose_library() -> dict[str, Any]:
    return {
        "character_id": CHARACTER_ID,
        "poses": {
            p: {
                "id": f"HAND-{p.upper()}",
                "articulation": ["wrist", "palm", "thumb", "index", "middle", "ring", "little"],
                "forbid_flat_default": True,
            }
            for p in HAND_POSES
        },
    }


def animation_clip(name: str, *, loop: bool = False, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    row = {
        "id": f"ANIM-{CHARACTER_ID}-{name.upper()}",
        "name": name,
        "character_id": CHARACTER_ID,
        "loop": loop,
        "reusable": True,
        "true_motion_hint": "point_teach"
        if any(k in name for k in ("teach", "point", "talk"))
        else "walk_explain",
        "constraints_ref": "ANIMATION_CONSTRAINTS.json",
        "rig_ref": "RIG_SPECIFICATION.json",
    }
    if extra:
        row.update(extra)
    return row
