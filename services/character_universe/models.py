"""Character-side data models — Agent 15 (Character, Universe & IP Engine).

Every model is a plain JSON-safe dict produced by a `build_*` normalizer:
the exported *_FIELDS tuples are the testable contract (additive-only,
per DATA_CONTRACTS.md). Unknown keys on an incoming spec are preserved so
future providers can attach data without a schema change.

World-side models (Universe, Location, Organization, BrandIdentity,
Franchise, StylePack, StoryBible) live in `world_models.py`.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

CHARACTER_UNIVERSE_VERSION = "1.0.0"


def _uid(prefix: str) -> str:
    return f"{prefix}{uuid.uuid4().hex[:10]}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize(spec: dict, fields: tuple, defaults: dict, id_field: str, prefix: str) -> dict:
    """Return a record with every contract field present (unknown keys kept).

    Mutable defaults are declared as types (list/dict) so every record gets
    its own fresh copy.
    """
    record = dict(spec or {})
    record[id_field] = record.get(id_field) or _uid(prefix)
    for name in fields:
        if name in record:
            continue
        default = defaults.get(name, "")
        record[name] = default() if isinstance(default, type) else default
    return record


# ------------------------------------------------------------------ enums

class CharacterStatus:
    ACTIVE = "active"
    DEVELOPING = "developing"
    RETIRED = "retired"
    DECEASED = "deceased"
    ARCHIVED = "archived"
    ALL = (ACTIVE, DEVELOPING, RETIRED, DECEASED, ARCHIVED)


class RelationType:
    FAMILY = "family"
    FRIEND = "friend"
    ENEMY = "enemy"
    RIVAL = "rival"
    MENTOR = "mentor"
    STUDENT = "student"
    ROMANTIC = "romantic"
    TEAMMATE = "teammate"
    MEMBER_OF = "member_of"
    HISTORICAL = "historical"
    ALL = (FAMILY, FRIEND, ENEMY, RIVAL, MENTOR, STUDENT, ROMANTIC, TEAMMATE, MEMBER_OF, HISTORICAL)


# ------------------------------------------------------- CharacterProfile

VISUAL_PROFILE_FIELDS = (
    "hair", "eyes", "skin", "height", "body_type", "facial_features",
    "expressions", "wardrobe", "accessories", "color_palette",
    "animation_style", "art_style", "brand_style", "reference_prompts",
    "consistency_rules", "visual_signature",
)

_VISUAL_DEFAULTS = {
    "expressions": list, "wardrobe": list, "accessories": list,
    "color_palette": list, "reference_prompts": list, "consistency_rules": list,
}


def build_visual_profile(spec: dict) -> dict:
    profile = dict(spec or {})
    for name in VISUAL_PROFILE_FIELDS:
        if name in profile:
            continue
        default = _VISUAL_DEFAULTS.get(name, "")
        profile[name] = default() if isinstance(default, type) else default
    if not profile["visual_signature"]:
        parts = [profile[part] for part in ("hair", "eyes", "body_type", "art_style") if profile[part]]
        profile["visual_signature"] = ", ".join(parts)
    return profile


# ----------------------------------------------------------- VoiceProfile

VOICE_PROFILE_FIELDS = (
    "voice_id", "provider", "accent", "tone", "emotion_range",
    "speaking_speed", "pitch", "pronunciation_rules", "narration_style",
    "fallback_providers",
)

_VOICE_DEFAULTS = {
    "emotion_range": list, "pronunciation_rules": list, "fallback_providers": list,
    "speaking_speed": "normal", "pitch": "medium",
}


def build_voice_profile(spec: dict) -> dict:
    profile = dict(spec or {})
    for name in VOICE_PROFILE_FIELDS:
        if name in profile:
            continue
        default = _VOICE_DEFAULTS.get(name, "")
        profile[name] = default() if isinstance(default, type) else default
    return profile


# -------------------------------------------------------- CharacterMemory

CHARACTER_MEMORY_FIELDS = (
    "events", "relationships", "achievements", "failures", "goals",
    "knowledge", "personality_evolution", "growth_log",
)


def build_character_memory(spec: "dict | None" = None) -> dict:
    memory = dict(spec or {})
    for name in CHARACTER_MEMORY_FIELDS:
        memory.setdefault(name, [])
    return memory


# ----------------------------------------------------------- CharacterArc

CHARACTER_ARC_FIELDS = (
    "arc_id", "name", "description", "stage", "milestones",
    "started_at", "completed",
)

_ARC_DEFAULTS = {"milestones": list, "completed": False, "stage": "setup"}


def build_character_arc(spec: dict) -> dict:
    arc = normalize(spec, CHARACTER_ARC_FIELDS, _ARC_DEFAULTS, "arc_id", "arc_")
    if not arc["started_at"]:
        arc["started_at"] = _now_iso()
    return arc


# -------------------------------------------------------------- Character

CHARACTER_FIELDS = (
    "character_id", "name", "nicknames", "aliases", "biography", "age",
    "species", "gender", "occupation", "role", "goals", "motivations",
    "strengths", "weaknesses", "personality_traits", "speech_style",
    "voice_style", "vocabulary", "humor_style", "catchphrases",
    "relationship_ids", "emotional_state", "backstory", "growth_arc",
    "current_arc", "status", "popularity_score", "brand_importance",
    "visual_profile", "voice_profile", "memory", "universe_id", "brand_id",
    "usage_rights", "version", "created_at", "updated_at",
)

_CHARACTER_DEFAULTS = {
    "nicknames": list, "aliases": list, "goals": list, "motivations": list,
    "strengths": list, "weaknesses": list, "personality_traits": list,
    "vocabulary": list, "catchphrases": list, "relationship_ids": list,
    "species": "human", "emotional_state": "neutral",
    "status": CharacterStatus.ACTIVE, "popularity_score": 50,
    "brand_importance": 50, "usage_rights": "original", "version": 1,
    "growth_arc": dict, "current_arc": dict,
}


def build_character(spec: dict) -> dict:
    character = normalize(spec, CHARACTER_FIELDS, _CHARACTER_DEFAULTS, "character_id", "char_")
    if not character["name"]:
        character["name"] = character["character_id"]
    character["visual_profile"] = build_visual_profile(character.get("visual_profile") or {})
    character["voice_profile"] = build_voice_profile(character.get("voice_profile") or {})
    character["memory"] = build_character_memory(character.get("memory") or {})
    if character["current_arc"]:
        character["current_arc"] = build_character_arc(character["current_arc"])
    return character


# ------------------------------------------------------------ Relationship

RELATIONSHIP_FIELDS = (
    "relationship_id", "source_id", "target_id", "relation_type", "label",
    "strength", "status", "history", "started_at", "ended_at",
)

_RELATIONSHIP_DEFAULTS = {
    "relation_type": RelationType.FRIEND, "strength": 50,
    "status": "active", "history": list,
}


def build_relationship(spec: dict) -> dict:
    relationship = normalize(spec, RELATIONSHIP_FIELDS, _RELATIONSHIP_DEFAULTS, "relationship_id", "rel_")
    if not relationship["started_at"]:
        relationship["started_at"] = _now_iso()
    relationship["strength"] = max(0, min(100, int(relationship["strength"] or 0)))
    return relationship


# -------------------------------------------------------------- CanonEvent

CANON_EVENT_FIELDS = (
    "event_id", "universe_id", "title", "description", "sequence",
    "occurred_at", "participants", "location_id", "source_content_id",
    "consequences", "tags",
)

_CANON_EVENT_DEFAULTS = {
    "sequence": 0, "participants": list, "consequences": list, "tags": list,
}


def build_canon_event(spec: dict) -> dict:
    return normalize(spec, CANON_EVENT_FIELDS, _CANON_EVENT_DEFAULTS, "event_id", "evt_")


# -------------------------------------------------- Appearance (continuity)

APPEARANCE_FIELDS = (
    "appearance_id", "character_id", "content_id", "content_type", "title",
    "outfit", "location_id", "universe_id", "voice_id", "visual_signature",
    "emotional_state", "franchise_id", "episode_ref", "recorded_at",
)

_APPEARANCE_DEFAULTS = {"content_type": "video"}


def build_appearance(spec: dict) -> dict:
    appearance = normalize(spec, APPEARANCE_FIELDS, _APPEARANCE_DEFAULTS, "appearance_id", "app_")
    if not appearance["recorded_at"]:
        appearance["recorded_at"] = _now_iso()
    return appearance


# --------------------------------------------------------- ContinuityIssue

CONTINUITY_ISSUE_FIELDS = (
    "issue_id", "severity", "category", "entity_type", "entity_id",
    "description", "evidence", "suggestion", "detected_at",
)

ISSUE_CATEGORIES = (
    "duplicate_character", "contradictory_history", "missing_reference",
    "timeline_error", "relationship_error", "lore_violation",
    "visual_drift", "voice_drift", "brand_drift", "status_error",
)

_ISSUE_DEFAULTS = {"severity": "warning", "evidence": dict}


def build_continuity_issue(spec: dict) -> dict:
    issue = normalize(spec, CONTINUITY_ISSUE_FIELDS, _ISSUE_DEFAULTS, "issue_id", "iss_")
    if not issue["detected_at"]:
        issue["detected_at"] = _now_iso()
    return issue


# ---------------------------------------------------------- AssetReference

ASSET_REFERENCE_FIELDS = (
    "asset_reference_id", "asset_id", "asset_type", "entity_type",
    "entity_id", "label", "prompt", "style_pack_id", "source", "status",
)

_ASSET_REFERENCE_DEFAULTS = {"status": "requested", "source": "character_universe"}


def build_asset_reference(spec: dict) -> dict:
    return normalize(spec, ASSET_REFERENCE_FIELDS, _ASSET_REFERENCE_DEFAULTS, "asset_reference_id", "ref_")
