"""Per-character identity overrides — inherit BASE_HUMAN_REALISM, never duplicate it.

Only visual identity, personality, voice, clothing, role, gait flavor, and signature
gestures belong here. Anatomy / locomotion / face systems come from the framework.
"""

from __future__ import annotations

from typing import Any

from services.human_realism.base import GOLD_STANDARD_CHARACTER_ID

# Gold-standard reference implementation — richest intentional overrides.
_DOCTOR_GOLD: dict[str, Any] = {
    "character_id": "DOCTOR_001",
    "name": "The Doctor",
    "role": "Canonical Medical Educator",
    "is_gold_standard": True,
    "inherits_from": "BASE_HUMAN_REALISM",
    "visual_identity": {
        "archetype": "humanoid_cyborg_doctor",
        "silhouette": "white_cyborg_doctor_blue_glow",
        "canonical_height_cm": 185,
        "body_mass_estimate_kg": 82,
        "age_range": "adult_ageless_cyborg",
        "biological_build": "athletic_approachable_humanoid",
        "surface": "soft_white_polymer_over_titanium",
        "palette": {
            "primary": "#F4F7FA",
            "titanium": "#8A939E",
            "accent": "#3BA7E0",
            "eyes": "#7FD4FF",
        },
        "hair": {
            "type": "cranial_polymer_plating",
            "has_organic_hair": False,
        },
    },
    "personality": [
        "highly_intelligent",
        "patient",
        "curious",
        "optimistic",
        "encouraging",
        "evidence_driven",
        "compassionate",
    ],
    "voice": {
        "id": "VOICE-THE-DOCTOR-001",
        "style": "warm_clinical_educator",
        "pace": "natural_educational",
    },
    "clothing": {
        "default_outfit": "primary_outfit",
        "signature": "white_medical_chassis_coat",
        "material_type": "medical_coat_polymer_weave",
        "wind_response": "moderate_hem_and_sleeve",
    },
    "gait": {
        "personality_walk": "doctor_calm_authority",
        "traits": [
            "calm_authority",
            "precise_foot_placement",
            "balanced_posture",
            "minimal_wasted_movement",
            "approachable_not_militaristic",
        ],
        "true_motion_hint": "walk_explain",
    },
    "gestures": {
        "favorites": [
            "open_palm_teach",
            "open_palm_reassurance",
            "hologram_pinch",
            "clipboard_point",
            "scanner_sweep",
            "heart_hand",
            "chin_think",
        ],
        "library_extra": {
            "hologram_pinch": {"category": "object_interaction"},
            "clipboard_point": {"category": "teaching"},
            "scanner_sweep": {"category": "object_interaction"},
            "heart_hand": {"category": "compassion"},
        },
    },
    "emotion_bias": {
        "default_primary": "compassion",
        "teaching_primary": "confidence",
        "clinical_primary": "concern",
    },
    "camera_awareness": {
        "default": "address_when_teaching",
        "teaching_may_address_audience": True,
    },
    "home_world_id": "LOC-GMRI",
    "studio_asset_path": "data/studio_assets/DOCTOR_001/",
}

CHAR_OVERRIDES: dict[str, dict[str, Any]] = {
    "DOCTOR_001": dict(_DOCTOR_GOLD),
    # Legacy alias — same gold-standard character
    "CHAR-0001": {
        **dict(_DOCTOR_GOLD),
        "character_id": "CHAR-0001",
        "canonical_id": "DOCTOR_001",
        "alias_of": "DOCTOR_001",
        "is_gold_standard": False,
        "reference_implementation": "DOCTOR_001",
    },
    "CHAR-ATLAS": {
        "character_id": "CHAR-ATLAS",
        "name": "Professor Atlas",
        "role": "lead_educator",
        "inherits_from": "BASE_HUMAN_REALISM",
        "reference_implementation": GOLD_STANDARD_CHARACTER_ID,
        "visual_identity": {
            "archetype": "human_educator",
            "silhouette": "tall_blazer_glasses",
            "canonical_height_cm": 188,
            "body_mass_estimate_kg": 84,
            "age_range": "adult_mid",
            "biological_build": "tall_lean_scholar",
            "palette": {
                "skin": "#FFD6B4",
                "hair": "#28201C",
                "coat": "#1C3056",
                "accent": "#30AAA0",
            },
            "hair": {"type": "short_styled", "has_organic_hair": True},
        },
        "personality": ["warm", "authoritative", "curious", "patient"],
        "voice": {"voice": "alloy", "style": "documentary_host", "pace": "measured"},
        "clothing": {
            "default_outfit": "deep_navy_blazer",
            "signature": "navy_blazer_teal_pocket_square_glasses",
            "material_type": "structured_blazer_wool",
            "stiffness": "higher",
        },
        "gait": {
            "personality_walk": "grounded_walk_explain",
            "traits": ["measured_pace", "stable_posture", "direct_gaze"],
            "true_motion_hint": "point_teach",
        },
        "gestures": {
            "favorites": ["open_palm_teach", "point_to_subject", "chin_think", "diagram_trace"],
            "library_extra": {"point_to_subject": {"category": "teaching"}},
        },
        "emotion_bias": {"default_primary": "confidence", "teaching_primary": "curiosity"},
        "camera_awareness": {"teaching_may_address_audience": True},
    },
    "CHAR-NOVA": {
        "character_id": "CHAR-NOVA",
        "name": "Nova",
        "role": "curious_ai_assistant",
        "inherits_from": "BASE_HUMAN_REALISM",
        "reference_implementation": GOLD_STANDARD_CHARACTER_ID,
        "visual_identity": {
            "archetype": "stylized_ai_humanoid",
            "silhouette": "hoodie_glow_band",
            "canonical_height_cm": 168,
            "body_mass_estimate_kg": 58,
            "age_range": "youthful_ageless",
            "biological_build": "light_energetic",
            "facial_exaggeration": 0.15,
            "motion_exaggeration": 0.2,
            "palette": {
                "skin": "#F0DCFF",
                "hair": "#7846DC",
                "coat": "#5834A0",
                "accent": "#50DCFF",
            },
            "hair": {"type": "short_glow_accent", "has_organic_hair": True, "wind_response": "lively"},
        },
        "personality": ["playful", "inquisitive", "bright", "loyal"],
        "voice": {"voice": "nova", "style": "bright_assistant", "pace": "lively"},
        "clothing": {
            "default_outfit": "violet_hoodie",
            "signature": "violet_hoodie_cyan_trim",
            "material_type": "soft_hoodie_knit",
            "wind_response": "higher",
        },
        "gait": {
            "personality_walk": "light_bob_orbit",
            "traits": ["lighter_steps", "curious_glances", "forward_energy"],
            "true_motion_hint": "walk_explain",
        },
        "gestures": {
            "favorites": ["point_spark", "tilt_head", "hand_hologram", "scale_show"],
            "library_extra": {
                "point_spark": {"category": "emphasizing"},
                "tilt_head": {"category": "thinking"},
                "hand_hologram": {"category": "object_interaction"},
            },
        },
        "emotion_bias": {"default_primary": "curiosity", "teaching_primary": "joy"},
        "facial_exaggeration": 0.15,
        "motion_exaggeration": 0.2,
    },
    "CHAR-ORION": {
        "character_id": "CHAR-ORION",
        "name": "Orion",
        "role": "explorer_adventurer",
        "inherits_from": "BASE_HUMAN_REALISM",
        "reference_implementation": GOLD_STANDARD_CHARACTER_ID,
        "visual_identity": {
            "archetype": "human_explorer",
            "silhouette": "field_jacket_compass",
            "canonical_height_cm": 182,
            "body_mass_estimate_kg": 86,
            "age_range": "adult",
            "biological_build": "athletic_field",
            "palette": {
                "skin": "#D2A078",
                "hair": "#1E1612",
                "coat": "#465A30",
                "accent": "#B46E3C",
            },
            "hair": {"type": "short_windswept", "has_organic_hair": True},
        },
        "personality": ["bold", "adventurous", "steady", "observant"],
        "voice": {"voice": "onyx", "style": "field_narrator", "pace": "adventurous"},
        "clothing": {
            "default_outfit": "olive_field_jacket",
            "signature": "field_jacket_compass_scarf",
            "material_type": "canvas_field_shell",
            "stiffness": "higher",
            "wind_response": "strong_outdoor",
        },
        "gait": {
            "personality_walk": "confident_stride",
            "traits": ["longer_stride", "terrain_aware", "alert_head"],
            "true_motion_hint": "walk_explain",
        },
        "gestures": {
            "favorites": ["scout_point", "binoculars", "steady_hand", "warning_focus"],
            "library_extra": {
                "scout_point": {"category": "teaching"},
                "binoculars": {"category": "object_interaction"},
                "steady_hand": {"category": "reassuring"},
            },
        },
        "emotion_bias": {"default_primary": "determination", "teaching_primary": "curiosity"},
        "camera_awareness": {"default": "diegetic_world"},
    },
    "CHAR-PIPER": {
        "character_id": "CHAR-PIPER",
        "name": "Piper",
        "role": "engineer_inventor",
        "inherits_from": "BASE_HUMAN_REALISM",
        "reference_implementation": GOLD_STANDARD_CHARACTER_ID,
        "visual_identity": {
            "archetype": "human_engineer",
            "silhouette": "goggles_toolbelt",
            "canonical_height_cm": 170,
            "body_mass_estimate_kg": 68,
            "age_range": "adult",
            "biological_build": "compact_energetic",
            "palette": {
                "skin": "#FFD2AA",
                "hair": "#B45A28",
                "coat": "#C87828",
                "accent": "#3C4650",
            },
            "hair": {"type": "practical_tied_or_short", "has_organic_hair": True},
        },
        "personality": ["practical", "clever", "energetic", "solving"],
        "voice": {"voice": "shimmer", "style": "hands_on_engineer", "pace": "brisk"},
        "clothing": {
            "default_outfit": "amber_workwear",
            "signature": "workwear_goggles_toolbelt",
            "material_type": "durable_work_twill",
            "stiffness": "higher",
            "accessories_secondary_motion": ["toolbelt", "goggles"],
        },
        "gait": {
            "personality_walk": "busy_hands_teach",
            "traits": ["brisk_cadence", "hands_ready", "inspect_stance"],
            "true_motion_hint": "point_teach",
        },
        "gestures": {
            "favorites": ["wrench_point", "sketch_air", "thumbs_measure", "emphasize"],
            "library_extra": {
                "wrench_point": {"category": "teaching"},
                "sketch_air": {"category": "explaining_scale"},
                "thumbs_measure": {"category": "object_interaction"},
            },
        },
        "emotion_bias": {"default_primary": "curiosity", "teaching_primary": "determination"},
    },
    "CHAR-LUNA": {
        "character_id": "CHAR-LUNA",
        "name": "Luna",
        "role": "biologist_nature_expert",
        "inherits_from": "BASE_HUMAN_REALISM",
        "reference_implementation": GOLD_STANDARD_CHARACTER_ID,
        "visual_identity": {
            "archetype": "human_biologist",
            "silhouette": "lab_coat_leaf_pin",
            "canonical_height_cm": 172,
            "body_mass_estimate_kg": 64,
            "age_range": "adult",
            "biological_build": "soft_precise",
            "palette": {
                "skin": "#EBBEA0",
                "hair": "#5A3228",
                "coat": "#C8DCBE",
                "accent": "#3C8C50",
            },
            "hair": {"type": "soft_medium", "has_organic_hair": True, "wind_response": "gentle"},
        },
        "personality": ["gentle", "wonderstruck", "precise", "empathetic"],
        "voice": {"voice": "nova", "style": "nature_guide", "pace": "soft"},
        "clothing": {
            "default_outfit": "sage_lab_coat",
            "signature": "sage_lab_coat_leaf_pin",
            "material_type": "soft_lab_cotton",
            "wind_response": "gentle_hem",
        },
        "gait": {
            "personality_walk": "soft_present",
            "traits": ["quiet_steps", "observant", "reduced_force"],
            "true_motion_hint": "swim_float",
        },
        "gestures": {
            "favorites": ["cup_hands", "trace_leaf", "quiet_point", "open_palm_reassurance"],
            "library_extra": {
                "cup_hands": {"category": "reassuring"},
                "trace_leaf": {"category": "teaching"},
                "quiet_point": {"category": "teaching"},
            },
        },
        "emotion_bias": {"default_primary": "compassion", "teaching_primary": "curiosity"},
        "breathing": {"modes": {"teaching": {"rate_bpm": 11, "distribution": "calm_diaphragmatic"}}},
    },
}


def list_character_ids() -> list[str]:
    return list(CHAR_OVERRIDES.keys())


def get_override(character_id: str) -> dict[str, Any] | None:
    return CHAR_OVERRIDES.get(str(character_id or "").upper())
