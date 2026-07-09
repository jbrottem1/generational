"""Character System — reusable characters with cross-production consistency.

Every character (CHARACTER_FIELDS) carries a stable `visual_signature`:
one canonical appearance description embedded verbatim into every asset
prompt that features the character, so the same face/design comes back
from any generation provider in any production. The `color_anchor` is the
signature color continuity checks verify scene-to-scene.

Roles cover the full cast architecture: original characters, narrators,
mascots, future AI avatars and digital humans, cartoon/branded/educational
characters, and historical figures (usage_rights records the basis — only
public-domain figures ship as built-ins, and accuracy notes live in
design_notes).
"""

from __future__ import annotations

import uuid

from services.creative_studio.models import CharacterKind, CharacterRole

CHARACTER_SYSTEM_VERSION = "1.1"

# Default expressions every character can perform unless a spec narrows them.
_DEFAULT_EXPRESSIONS = ["neutral", "curious", "delighted", "concerned", "surprised", "resolute"]

_CHARACTERS: "dict[str, dict]" = {}


def create_character(spec: dict) -> dict:
    """Create + register one reusable character. Returns the stored dict.

    A missing `visual_signature` is derived from the description so every
    character always has a consistency anchor.
    """
    character_id = spec.get("character_id") or f"char_{uuid.uuid4().hex[:10]}"
    description = spec.get("description", "")
    stored = {
        "character_id": character_id,
        "name": spec.get("name", character_id),
        "role": spec.get("role", CharacterRole.ORIGINAL),
        "archetype": spec.get("archetype", ""),
        "description": description,
        "visual_signature": spec.get("visual_signature") or description,
        "design_notes": spec.get("design_notes", ""),
        "wardrobe": spec.get("wardrobe", ""),
        "color_anchor": spec.get("color_anchor", ""),
        "voice_profile": spec.get("voice_profile", ""),
        "personality": spec.get("personality", ""),
        "usage_rights": spec.get("usage_rights", "original"),
        "brand_id": spec.get("brand_id", ""),
        # --- v1.1 Creative Intelligence extension (additive only).
        "kind": spec.get("kind", CharacterKind.HUMAN),
        "expressions": list(spec.get("expressions", _DEFAULT_EXPRESSIONS)),
        "movement_style": spec.get("movement_style", ""),
        "emotion_profile": dict(spec.get("emotion_profile", {})),
        "outfits": list(spec.get("outfits", ([spec["wardrobe"]] if spec.get("wardrobe") else []))),
        "accessories": list(spec.get("accessories", [])),
        "memory_hooks": list(spec.get("memory_hooks", [character_id])),
    }
    _CHARACTERS[character_id] = stored
    return stored


def register_character(character: dict) -> dict:
    """Alias of create_character for pre-built character dicts."""
    return create_character(character)


def get_character(character_id: str) -> "dict | None":
    return _CHARACTERS.get(character_id)


def all_characters() -> "list[dict]":
    return list(_CHARACTERS.values())


def characters_for_role(role: str) -> "list[dict]":
    return [dict(c) for c in _CHARACTERS.values() if c["role"] == role]


def character_prompt_fragment(character_id: str) -> str:
    """The exact text every generation prompt embeds for this character —
    the mechanism of visual consistency across scenes and productions."""
    character = _CHARACTERS.get(character_id)
    if character is None:
        return ""
    parts = [character["name"], character["visual_signature"]]
    if character["wardrobe"]:
        parts.append(f"wearing {character['wardrobe']}")
    if character["color_anchor"]:
        parts.append(f"signature color {character['color_anchor']}")
    return ", ".join(part for part in parts if part)


def cast_characters(item: dict, production_type: dict) -> "list[dict]":
    """Cast the characters for one production (deterministic).

    Explicit `character_ids` on the item win. Otherwise presenter-driven
    media get the house presenter, kids media get the house mascot, and
    every production gets the house narrator as the storytelling voice.
    """
    requested = [
        dict(_CHARACTERS[character_id])
        for character_id in item.get("character_ids", [])
        if character_id in _CHARACTERS
    ]
    if requested:
        return requested

    cast = [dict(_CHARACTERS["char_narrator_house"])]
    type_id = production_type.get("type_id", "")
    if type_id in ("ai_presenter", "reaction_video"):
        cast.append(dict(_CHARACTERS["char_presenter_nova"]))
    if type_id in ("kids_educational", "cartoon", "animation_2d"):
        cast.append(dict(_CHARACTERS["char_mascot_gen"]))
    return cast


# --------------------------------------------------------------- built-ins
# The house cast — reusable across every production from day one.

_BUILTINS = (
    {
        "character_id": "char_narrator_house",
        "name": "The Narrator",
        "role": CharacterRole.NARRATOR,
        "archetype": "trusted guide",
        "description": "An unseen, authoritative storytelling voice.",
        "visual_signature": "voice-only narrator — no on-screen depiction",
        "voice_profile": "warm, measured, documentary-grade",
        "personality": "curious, credible, calm",
        "usage_rights": "original",
    },
    {
        "character_id": "char_presenter_nova",
        "name": "Nova",
        "role": CharacterRole.AI_AVATAR,
        "archetype": "on-camera host",
        "description": "A photorealistic AI presenter in their early 30s with short dark hair.",
        "visual_signature": (
            "photorealistic presenter, early 30s, short dark hair, warm brown eyes, "
            "navy blazer over white tee"
        ),
        "wardrobe": "navy blazer, white tee",
        "color_anchor": "navy blue",
        "voice_profile": "energetic, conversational",
        "personality": "sharp, friendly, direct-to-camera confidence",
        "usage_rights": "original",
        "kind": CharacterKind.HUMAN,
        "movement_style": "grounded presenter energy — open gestures, direct address",
        "emotion_profile": {
            "curiosity": "leans toward camera, eyebrow lift",
            "surprise": "half-step back, open palms",
            "satisfaction": "settled smile, slow nod",
        },
        "accessories": ["lapel mic"],
        "memory_hooks": ["char_presenter_nova", "house_presenter"],
    },
    {
        "character_id": "char_mascot_gen",
        "name": "Gen",
        "role": CharacterRole.MASCOT,
        "archetype": "friendly guide",
        "description": "A round, glowing spark-shaped mascot with big expressive eyes.",
        "visual_signature": (
            "round glowing spark-shaped cartoon mascot, big expressive eyes, "
            "four-fingered gloves, soft amber glow"
        ),
        "color_anchor": "amber",
        "voice_profile": "bright, playful",
        "personality": "encouraging, endlessly curious",
        "usage_rights": "original",
        "kind": CharacterKind.BRAND_MASCOT,
        "movement_style": "bouncy squash-and-stretch, hovers when excited",
        "emotion_profile": {
            "curiosity": "glow brightens, tilts whole body",
            "tension": "glow dims, shrinks slightly",
            "satisfaction": "spin and sparkle burst",
        },
        "memory_hooks": ["char_mascot_gen", "house_mascot"],
    },
    {
        "character_id": "char_prof_atlas",
        "name": "Professor Atlas",
        "role": CharacterRole.EDUCATIONAL,
        "archetype": "wise teacher",
        "description": "A stylized owl professor with round glasses and a tweed vest.",
        "visual_signature": (
            "stylized cartoon owl professor, round brass glasses, tweed vest, "
            "feather texture in warm browns"
        ),
        "wardrobe": "tweed vest, brass glasses",
        "color_anchor": "warm brown",
        "voice_profile": "gentle, patient, precise",
        "personality": "patient explainer who loves questions",
        "usage_rights": "original",
        "kind": CharacterKind.ANIMAL,
        "movement_style": "deliberate head turns, wing gestures like a lecturer",
        "emotion_profile": {
            "curiosity": "head tilt, glasses adjust",
            "surprise": "feathers puff, eyes widen",
            "satisfaction": "slow satisfied blink",
        },
        "accessories": ["pointer stick", "pocket watch"],
        "memory_hooks": ["char_prof_atlas", "house_teacher"],
    },
)

for _character in _BUILTINS:
    register_character(_character)
