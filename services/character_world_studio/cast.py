"""Reusable Generational host cast — memorable characters, not placeholders.

Additive to locked universe IPs (Dash / Professor Gen stick). These hosts are the
stylized cinematic educational cast for Character & World Studio productions.

Flagship permanent Studio Asset #0001 (The Doctor) is loaded from
`services.studio_assets` and must never be regenerated from scratch.
"""

from __future__ import annotations

from typing import Any

from services.studio_assets.doctor_001 import doctor_001_host_profile

# Character IDs are stable across productions for continuity.
# Canonical medical educator: DOCTOR_001 (legacy alias CHAR-0001).
_THE_DOCTOR = doctor_001_host_profile()

def _hr_meta(character_id: str, **extra: Any) -> dict[str, Any]:
    return {
        "human_realism_framework": "HUMAN_REALISM_FRAMEWORK_V1",
        "human_realism_path": f"data/human_realism/characters/{character_id}/",
        "inherits_human_realism": True,
        "reference_implementation": "DOCTOR_001",
        "style_mode": "cinematic_realism",
        **extra,
    }


HOST_CAST: dict[str, dict[str, Any]] = {
    "DOCTOR_001": {
        **_THE_DOCTOR,
        **_hr_meta("DOCTOR_001", is_gold_standard=True, reference_implementation=None),
    },
    # Legacy alias — same permanent Studio Character
    "CHAR-0001": {
        **_THE_DOCTOR,
        "id": "CHAR-0001",
        "canonical_studio_character_id": "DOCTOR_001",
        "alias_of": "DOCTOR_001",
        **_hr_meta("DOCTOR_001", is_gold_standard=True, reference_implementation=None),
    },
    "CHAR-ATLAS": {
        "id": "CHAR-ATLAS",
        "name": "Professor Atlas",
        "short_name": "Atlas",
        "role": "lead_educator",
        **_hr_meta("CHAR-ATLAS"),
        "biography": (
            "Lead educator of the Generational Universe. Calm, precise, endlessly curious. "
            "Turns hard science into journeys without ever talking down."
        ),
        "personality": ["warm", "authoritative", "curious", "patient"],
        "voice_profile": {"voice": "alloy", "style": "documentary_host", "pace": "measured"},
        "movement_style": "grounded_walk_explain",
        "facial_range": ["smile", "raised_brow", "concern", "delight", "focus"],
        "favorite_gestures": ["open_palm_teach", "point_to_subject", "chin_think"],
        "signature_clothing": {
            "coat": "deep_navy_blazer",
            "shirt": "soft_cream",
            "accent": "teal_pocket_square",
            "accessory": "round_glasses",
        },
        "silhouette": "tall_blazer_glasses",
        "palette": {"skin": (255, 214, 180), "hair": (40, 32, 28), "coat": (28, 48, 86), "accent": (48, 170, 160)},
        "true_motion_performance": "point_teach",
        "recurring_environments": ["LOC-AI-LAB", "LOC-SCIENCE-MUSEUM", "LOC-ANCIENT-LIBRARY"],
        "domains": ["science", "infrastructure", "general", "history", "psychology"],
    },
    "CHAR-NOVA": {
        "id": "CHAR-NOVA",
        "name": "Nova",
        "short_name": "Nova",
        "role": "curious_ai_assistant",
        "biography": (
            "Curious AI assistant who asks the questions viewers are thinking. "
            "Playful energy, precise recall, occasional mischievous spark."
        ),
        "personality": ["playful", "inquisitive", "bright", "loyal"],
        "voice_profile": {"voice": "nova", "style": "bright_assistant", "pace": "lively"},
        "movement_style": "light_bob_orbit",
        "facial_range": ["wide_eyes", "grin", "puzzled", "awe"],
        "favorite_gestures": ["point_spark", "tilt_head", "hand_hologram"],
        "signature_clothing": {
            "coat": "violet_hoodie",
            "shirt": "soft_white",
            "accent": "cyan_circuit_trim",
            "accessory": "ear_glow_band",
        },
        "silhouette": "hoodie_glow_band",
        "palette": {"skin": (240, 220, 255), "hair": (120, 70, 220), "coat": (88, 52, 160), "accent": (80, 220, 255)},
        "true_motion_performance": "walk_explain",
        "recurring_environments": ["LOC-AI-LAB", "LOC-SPACE-STATION", "LOC-FUTURE-CITY"],
        "domains": ["ai", "technology", "space", "computing", "patterns"],
        **_hr_meta("CHAR-NOVA"),
    },
    "CHAR-ORION": {
        "id": "CHAR-ORION",
        "name": "Orion",
        "short_name": "Orion",
        "role": "explorer_adventurer",
        "biography": (
            "Explorer who takes the audience into field sites — reefs, ruins, mountains. "
            "Bold, grounded, and protective of the worlds he documents."
        ),
        "personality": ["bold", "adventurous", "steady", "observant"],
        "voice_profile": {"voice": "onyx", "style": "field_narrator", "pace": "adventurous"},
        "movement_style": "confident_stride",
        "facial_range": ["grit", "wonder", "alert", "smile"],
        "favorite_gestures": ["scout_point", "binoculars", "steady_hand"],
        "signature_clothing": {
            "coat": "olive_field_jacket",
            "shirt": "dusty_tan",
            "accent": "copper_compass",
            "accessory": "scarfed_collar",
        },
        "silhouette": "field_jacket_compass",
        "palette": {"skin": (210, 160, 120), "hair": (30, 22, 18), "coat": (70, 90, 48), "accent": (180, 110, 60)},
        "true_motion_performance": "walk_explain",
        "recurring_environments": ["LOC-OCEAN-OBSERVATORY", "LOC-RAINFOREST-CAMP", "LOC-HISTORICAL-VILLAGE"],
        "domains": ["ocean", "nature", "exploration", "geography", "adventure", "folklore"],
        **_hr_meta("CHAR-ORION"),
    },
    "CHAR-PIPER": {
        "id": "CHAR-PIPER",
        "name": "Piper",
        "short_name": "Piper",
        "role": "engineer_inventor",
        "biography": (
            "Engineer and inventor who reverse-engineers how things work — hydrants, engines, "
            "gadgets. Hands always busy; explanations always concrete."
        ),
        "personality": ["practical", "clever", "energetic", "solving"],
        "voice_profile": {"voice": "shimmer", "style": "hands_on_engineer", "pace": "brisk"},
        "movement_style": "busy_hands_teach",
        "facial_range": ["focused", "aha", "skeptical", "proud"],
        "favorite_gestures": ["wrench_point", "sketch_air", "thumbs_measure"],
        "signature_clothing": {
            "coat": "amber_workwear",
            "shirt": "slate_tee",
            "accent": "toolbelt",
            "accessory": "goggles_forehead",
        },
        "silhouette": "goggles_toolbelt",
        "palette": {"skin": (255, 210, 170), "hair": (180, 90, 40), "coat": (200, 120, 40), "accent": (60, 70, 80)},
        "true_motion_performance": "point_teach",
        "recurring_environments": ["LOC-ENGINEERING-WORKSHOP", "LOC-FUTURE-CITY", "LOC-SCIENCE-MUSEUM"],
        "domains": ["engineering", "infrastructure", "mechanics", "invention", "physics"],
        **_hr_meta("CHAR-PIPER"),
    },
    "CHAR-LUNA": {
        "id": "CHAR-LUNA",
        "name": "Luna",
        "short_name": "Luna",
        "role": "biologist_nature_expert",
        "biography": (
            "Biologist and nature expert. Soft-spoken wonder with rigorous care for living systems — "
            "cells, animals, ecosystems."
        ),
        "personality": ["gentle", "wonderstruck", "precise", "empathetic"],
        "voice_profile": {"voice": "nova", "style": "nature_guide", "pace": "soft"},
        "movement_style": "soft_present",
        "facial_range": ["soft_smile", "awe", "concern", "delight"],
        "favorite_gestures": ["cup_hands", "trace_leaf", "quiet_point"],
        "signature_clothing": {
            "coat": "sage_lab_coat",
            "shirt": "moss_green",
            "accent": "leaf_pin",
            "accessory": "sample_pouch",
        },
        "silhouette": "lab_coat_leaf_pin",
        "palette": {"skin": (235, 190, 160), "hair": (90, 50, 40), "coat": (200, 220, 190), "accent": (60, 140, 80)},
        "true_motion_performance": "swim_float",
        "recurring_environments": ["LOC-RAINFOREST-CAMP", "LOC-OCEAN-OBSERVATORY", "LOC-MEDICAL-RESEARCH"],
        "domains": ["biology", "nature", "medicine", "ecology", "animals", "health"],
        **_hr_meta("CHAR-LUNA"),
    },
}


def list_hosts() -> list[dict[str, Any]]:
    return [dict(v) for v in HOST_CAST.values()]


def get_host(character_id: str) -> dict[str, Any] | None:
    row = HOST_CAST.get(str(character_id or "").upper())
    return dict(row) if row else None


def get_host_by_name(name: str) -> dict[str, Any] | None:
    key = str(name or "").strip().lower()
    for row in HOST_CAST.values():
        if key in {str(row["name"]).lower(), str(row["short_name"]).lower(), str(row["id"]).lower()}:
            return dict(row)
    return None
