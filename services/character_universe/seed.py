"""The house cast — Generational's day-one intellectual property.

Seeded idempotently (stable ids, created only when missing) so every
pipeline run has a consistent cast and universe to draw on, mirroring the
Creative Studio's built-in cast. All four are original characters.
"""

from __future__ import annotations

import copy

from services.character_universe.registry import CharacterUniverseRegistry

HOUSE_UNIVERSE_ID = "uni_generational"

HOUSE_UNIVERSE = {
    "universe_id": HOUSE_UNIVERSE_ID,
    "name": "The Generational Universe",
    "description": "The shared home world of Generational's house cast — a bright, optimistic near-future where curiosity is the most valuable currency.",
    "lore": ["Knowledge is shared freely", "Every question deserves a real answer"],
    "rules": [{"forbid": "graphic violence", "scope": "biography", "reason": "family-friendly universe"}],
    "story_hooks": ["Nova investigates a new frontier each season", "Gen discovers something it cannot explain"],
}

HOUSE_CAST = (
    {
        "character_id": "char_narrator_house",
        "name": "The Narrator",
        "role": "narrator",
        "species": "voice",
        "biography": "An unseen, authoritative storytelling voice that guides every Generational production.",
        "personality_traits": ["curious", "credible", "calm"],
        "speech_style": "warm, measured, documentary-grade",
        "voice_style": "documentary narration",
        "universe_id": HOUSE_UNIVERSE_ID,
        "brand_importance": 90,
        "visual_profile": {"visual_signature": "voice-only narrator — no on-screen depiction"},
        "voice_profile": {"tone": "warm", "narration_style": "documentary", "speaking_speed": "measured"},
    },
    {
        "character_id": "char_presenter_nova",
        "name": "Nova",
        "role": "ai_presenter",
        "biography": "A photorealistic AI presenter and the face of Generational's on-camera content.",
        "occupation": "host",
        "personality_traits": ["sharp", "friendly", "direct-to-camera confidence"],
        "speech_style": "energetic, conversational",
        "humor_style": "quick, observational",
        "universe_id": HOUSE_UNIVERSE_ID,
        "brand_importance": 85,
        "visual_profile": {
            "hair": "short dark hair",
            "eyes": "warm brown eyes",
            "body_type": "early 30s presenter",
            "wardrobe": ["navy blazer", "white tee"],
            "color_palette": ["navy blue"],
            "art_style": "photorealistic",
            "visual_signature": "photorealistic presenter, early 30s, short dark hair, warm brown eyes, navy blazer over white tee",
            "consistency_rules": ["always the same face across providers", "navy anchor color present"],
        },
        "voice_profile": {"voice_id": "voice_nova_v1", "tone": "energetic", "narration_style": "conversational"},
    },
    {
        "character_id": "char_mascot_gen",
        "name": "Gen",
        "role": "mascot",
        "species": "spark",
        "biography": "A round, glowing spark-shaped mascot with big expressive eyes — Generational's brand mascot.",
        "personality_traits": ["encouraging", "endlessly curious"],
        "speech_style": "bright, playful",
        "catchphrases": ["Let's find out together!"],
        "universe_id": HOUSE_UNIVERSE_ID,
        "brand_importance": 95,
        "visual_profile": {
            "body_type": "round spark",
            "color_palette": ["amber"],
            "art_style": "cartoon",
            "visual_signature": "round glowing spark-shaped cartoon mascot, big expressive eyes, four-fingered gloves, soft amber glow",
            "consistency_rules": ["amber glow in every shot", "four-fingered gloves"],
        },
        "voice_profile": {"tone": "bright", "pitch": "high", "narration_style": "playful"},
    },
    {
        "character_id": "char_prof_atlas",
        "name": "Professor Atlas",
        "role": "educational_host",
        "species": "owl",
        "occupation": "professor",
        "biography": "A stylized owl professor who turns hard subjects into stories children remember.",
        "personality_traits": ["patient", "precise", "loves questions"],
        "speech_style": "gentle, patient, precise",
        "universe_id": HOUSE_UNIVERSE_ID,
        "brand_importance": 80,
        "visual_profile": {
            "wardrobe": ["tweed vest", "round brass glasses"],
            "color_palette": ["warm brown"],
            "art_style": "stylized cartoon",
            "visual_signature": "stylized cartoon owl professor, round brass glasses, tweed vest, feather texture in warm browns",
            "consistency_rules": ["brass glasses always on", "warm brown feathers"],
        },
        "voice_profile": {"tone": "gentle", "speaking_speed": "slow", "narration_style": "educational"},
    },
)


def ensure_house_cast(registry: CharacterUniverseRegistry) -> dict:
    """Create the house universe + cast if missing. Returns counts."""
    created = {"universes": 0, "characters": 0}
    if registry.get("universes", HOUSE_UNIVERSE_ID) is None:
        registry.create_universe(copy.deepcopy(HOUSE_UNIVERSE))
        created["universes"] += 1
    for spec in HOUSE_CAST:
        if registry.get("characters", spec["character_id"]) is None:
            registry.create_character(copy.deepcopy(spec))
            created["characters"] += 1
    return created
