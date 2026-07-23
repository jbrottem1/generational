"""Canonical profile — The Doctor (CHAR-0001). Never regenerate identity from scratch."""

from __future__ import annotations

from typing import Any

ASSET_ID = "CHAR-0001"
ASSET_SLUG = "CHAR-0001-THE-DOCTOR"
ASSET_VERSION = "1.1.0"
DISPLAY_NAME = "The Doctor"
HOME_WORLD_ID = "LOC-GMRI"

# Official locked palette — never randomly change.
COLOR_SYSTEM: dict[str, Any] = {
    "primary": {"name": "Medical White", "hex": "#F4F7FA", "rgb": [244, 247, 250]},
    "secondary": {"name": "Premium Titanium", "hex": "#8A939E", "rgb": [138, 147, 158]},
    "accent": {"name": "Warm Trust Blue", "hex": "#3BA7E0", "rgb": [59, 167, 224]},
    "deep_accent": {"name": "Deep Clinical Blue", "hex": "#1A5F8A", "rgb": [26, 95, 138]},
    "chassis_shadow": {"name": "Chassis Shadow", "hex": "#2C343D", "rgb": [44, 52, 61]},
    "visors": {"name": "Intelligent Eye Core", "hex": "#7FD4FF", "rgb": [127, 212, 255]},
    "lighting": {
        "key": "soft_warm_clinical",
        "fill": "cool_rim_blue",
        "practical": "blue_edge_leds",
    },
    "medical_interface": {"ok": "#3DDC97", "info": "#3BA7E0", "warn": "#F0C040"},
    "emergency": {"alert": "#E85D4C", "critical": "#B42318"},
}

EXPRESSIONS = [
    "neutral",
    "happy",
    "curious",
    "thinking",
    "concerned",
    "excited",
    "surprised",
    "confident",
    "smiling",
    "teaching",
    "listening",
    "laughing",
    "serious",
    "focused",
    "blink",
]

POSES = [
    "front_view",
    "rear_view",
    "left_side",
    "right_side",
    "three_quarter",
    "hero",
    "neutral",
    "medical_demonstration",
    "pointing",
    "teaching",
    "walking",
    "running",
    "sitting",
    "standing",
    "hands_behind_back",
    "clipboard",
    "hologram_interaction",
]

ANIMATIONS = [
    "idle",
    "breathing",
    "blinking",
    "thinking",
    "walking",
    "jogging",
    "turning",
    "pointing",
    "teaching",
    "typing",
    "holding_medical_scanner",
    "using_holograms",
    "greeting",
    "listening",
    "explaining",
    "looking_around",
    "picking_up_objects",
    "interacting_with_equipment",
    "reaction_curiosity",
    "reaction_concern",
    "reaction_delight",
]

WARDROBE = [
    "primary_outfit",
    "formal_laboratory",
    "research",
    "field_expedition",
    "space_exploration",
    "medical_examination",
    "winter",
    "protective_equipment",
]

VISEMES = ["REST", "AA", "E", "I", "O", "U", "MBP", "FV", "L", "WQ", "AI"]


def character_profile() -> dict[str, Any]:
    return {
        "asset_number": "0001",
        "id": ASSET_ID,
        "slug": ASSET_SLUG,
        "name": DISPLAY_NAME,
        "role": "Lead Scientific Educator",
        "universe": "Generational",
        "asset_status": ["permanent", "reusable", "version_controlled"],
        "version": ASSET_VERSION,
        "design": {
            "archetype": "humanoid_cyborg_doctor",
            "chassis": "clean_white_medical",
            "materials": ["premium_titanium", "soft_white_polymer", "warm_blue_illumination"],
            "proportions": "human_athletic_approachable",
            "posture": "professional_open",
            "face": "friendly_expressive_intelligent",
            "avoid": ["generic_robot", "uncanny_horror", "cold_industrial_only"],
            "communicate": ["trust", "intelligence", "curiosity", "compassion"],
        },
        "color_system": COLOR_SYSTEM,
        "facial_system": {
            "expressions": EXPRESSIONS,
            "features": [
                "blink_animation",
                "eye_tracking",
                "eyebrow_movement",
                "mouth_shapes",
                "talking_visemes",
                "micro_expressions",
            ],
            "visemes": VISEMES,
        },
        "body_system": {"poses": POSES},
        "movement_library": ANIMATIONS,
        "wardrobe": WARDROBE,
        "voice_profile": {
            "id": "VOICE-THE-DOCTOR-001",
            "character": DISPLAY_NAME,
            "traits": [
                "professional",
                "calm",
                "confident",
                "friendly",
                "curious",
                "educational",
                "encouraging",
                "warm",
            ],
            "pacing": "natural_educational",
            "tts_hint": {"voice": "onyx", "model": "tts-1-hd", "style": "warm_clinical_educator"},
            "sync": "designed_for_high_quality_ai_narration_synchronization",
        },
        "personality": [
            "highly_intelligent",
            "patient",
            "curious",
            "optimistic",
            "encouraging",
            "evidence_driven",
            "never_arrogant",
            "never_condescending",
            "passionate_about_helping_people_understand_science",
        ],
        "home_world_id": HOME_WORLD_ID,
        "home_world_name": "The Generational Medical Research Institute",
        "recurring_cast_relationships": {
            "CHAR-ATLAS": "Colleague educator — collaborative lectures; mutual respect.",
            "CHAR-NOVA": "Frequently co-teaches tech topics; Nova asks, The Doctor grounds answers.",
            "CHAR-ORION": "Field joint missions — Doctor handles bioscience, Orion logistics.",
            "CHAR-PIPER": "Lab partners on medical devices and engineering explainers.",
            "CHAR-LUNA": "Closest peer on biology / ecology; warm professional friendship.",
            "CHAR-DASH": "Separate brand universe stick host — may cameo, never redesign either.",
            "CHAR-PROFESSOR-001": "Foundation peer — respect locked stick IP boundaries.",
        },
        "continuity": {
            "rule": "Always reference this permanent Studio Asset. Never regenerate from scratch.",
            "changes": "Only via intentional version upgrades (VERSION.json).",
            "visual_identity_locked": True,
        },
        "domains": [
            "science",
            "biology",
            "medicine",
            "engineering",
            "chemistry",
            "anatomy",
            "physics",
            "technology",
            "health",
        ],
    }


def the_doctor_host_profile() -> dict[str, Any]:
    """Shape compatible with Character & World Studio HOST_CAST."""
    pal = COLOR_SYSTEM
    return {
        "id": ASSET_ID,
        "name": DISPLAY_NAME,
        "short_name": "Doctor",
        "role": "lead_scientific_educator",
        "asset_status": "permanent",
        "studio_asset_path": f"data/studio_assets/{ASSET_SLUG}/",
        "version": ASSET_VERSION,
        "biography": (
            "Permanent flagship face of scientific education in the Generational Universe. "
            "A humanoid cyborg physician-educator built for clarity, compassion, and evidence."
        ),
        "personality": [
            "intelligent",
            "patient",
            "curious",
            "optimistic",
            "encouraging",
            "evidence_driven",
        ],
        "voice_profile": {
            "voice": "onyx",
            "style": "warm_clinical_educator",
            "pace": "natural_educational",
        },
        "movement_style": "calm_teach_demonstrate",
        "facial_range": [
            "teaching",
            "curious",
            "thinking",
            "confident",
            "concerned",
            "excited",
            "smiling",
            "focused",
        ],
        "favorite_gestures": [
            "open_palm_teach",
            "hologram_pinch",
            "clipboard_point",
            "scanner_sweep",
            "heart_hand",
        ],
        "signature_clothing": {
            "coat": "white_medical_chassis_coat",
            "shirt": "titanium_underplating",
            "accent": "warm_blue_illumination",
            "accessory": "medical_scanner_module",
        },
        "silhouette": "white_cyborg_doctor_blue_glow",
        "palette": {
            "skin": tuple(pal["primary"]["rgb"]),
            "hair": tuple(pal["secondary"]["rgb"]),
            "coat": tuple(pal["primary"]["rgb"]),
            "accent": tuple(pal["accent"]["rgb"]),
            "titanium": tuple(pal["secondary"]["rgb"]),
            "eyes": tuple(pal["visors"]["rgb"]),
            "shadow": tuple(pal["chassis_shadow"]["rgb"]),
        },
        "true_motion_performance": "point_teach",
        "recurring_environments": [HOME_WORLD_ID, "LOC-MEDICAL-RESEARCH", "LOC-SCIENCE-MUSEUM"],
        "domains": [
            "science",
            "biology",
            "medicine",
            "engineering",
            "chemistry",
            "anatomy",
            "physics",
            "technology",
            "health",
        ],
        "permanent_ip": True,
        "flagship_science_educator": True,
        "style_mode": "cinematic_realism",
        "human_realism_package": f"data/studio_assets/{ASSET_SLUG}/HUMAN_REALISM/",
        "human_realism_root_profiles": True,
    }
