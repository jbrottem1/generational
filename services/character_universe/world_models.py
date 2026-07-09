"""World-side data models — universes, locations, organizations, brands,
franchises, style packs, and the Story Bible.

Same conventions as `models.py`: JSON-safe dicts, `build_*` normalizers,
*_FIELDS tuples as the additive-only contract, unknown keys preserved.
"""

from __future__ import annotations

from services.character_universe.models import _now_iso, normalize

# ----------------------------------------------------------------- Timeline

TIMELINE_FIELDS = ("timeline_id", "universe_id", "name", "era", "events", "notes")

_TIMELINE_DEFAULTS = {"events": list, "era": "present"}


def build_timeline(spec: dict) -> dict:
    return normalize(spec, TIMELINE_FIELDS, _TIMELINE_DEFAULTS, "timeline_id", "tl_")


# ----------------------------------------------------------------- Universe

UNIVERSE_FIELDS = (
    "universe_id", "name", "description", "timeline", "history",
    "location_ids", "organization_ids", "cultures", "technology",
    "magic_rules", "economy", "politics", "conflicts", "lore",
    "canon_event_ids", "story_hooks", "rules", "brand_id", "shared_with",
    "status", "version", "created_at", "updated_at",
)

_UNIVERSE_DEFAULTS = {
    "history": list, "location_ids": list, "organization_ids": list,
    "cultures": list, "conflicts": list, "lore": list,
    "canon_event_ids": list, "story_hooks": list, "rules": list,
    "shared_with": list, "timeline": dict, "status": "active", "version": 1,
}


def build_universe(spec: dict) -> dict:
    universe = normalize(spec, UNIVERSE_FIELDS, _UNIVERSE_DEFAULTS, "universe_id", "uni_")
    if not universe["name"]:
        universe["name"] = universe["universe_id"]
    universe["timeline"] = build_timeline(
        {**(universe.get("timeline") or {}), "universe_id": universe["universe_id"]}
    )
    return universe


# ----------------------------------------------------------------- Location

LOCATION_FIELDS = (
    "location_id", "universe_id", "name", "location_type", "parent_id",
    "description", "environment_rules", "lighting_profile", "weather",
    "architecture", "map_notes", "reference_prompts", "status",
)

LOCATION_TYPES = (
    "country", "city", "building", "room", "landmark", "vehicle", "region", "world",
)

_LOCATION_DEFAULTS = {
    "location_type": "city", "environment_rules": list,
    "reference_prompts": list, "status": "active",
}


def build_location(spec: dict) -> dict:
    return normalize(spec, LOCATION_FIELDS, _LOCATION_DEFAULTS, "location_id", "loc_")


# ------------------------------------------------------------- Organization

ORGANIZATION_FIELDS = (
    "organization_id", "universe_id", "name", "org_type", "description",
    "member_ids", "leader_id", "goals", "rivals", "headquarters_id", "status",
)

_ORGANIZATION_DEFAULTS = {
    "org_type": "team", "member_ids": list, "goals": list, "rivals": list,
    "status": "active",
}


def build_organization(spec: dict) -> dict:
    return normalize(spec, ORGANIZATION_FIELDS, _ORGANIZATION_DEFAULTS, "organization_id", "org_")


# ------------------------------------------------------------ BrandIdentity

BRAND_IDENTITY_FIELDS = (
    "brand_identity_id", "brand_id", "name", "guidelines", "mascot_ids",
    "logo_references", "visual_identity", "approved_colors",
    "typography_references", "marketing_rules", "version",
    "created_at", "updated_at",
)

_BRAND_IDENTITY_DEFAULTS = {
    "guidelines": list, "mascot_ids": list, "logo_references": list,
    "approved_colors": list, "typography_references": list,
    "marketing_rules": list, "visual_identity": dict, "version": 1,
}


def build_brand_identity(spec: dict) -> dict:
    return normalize(spec, BRAND_IDENTITY_FIELDS, _BRAND_IDENTITY_DEFAULTS, "brand_identity_id", "brid_")


# ---------------------------------------------------------------- StylePack

STYLE_PACK_FIELDS = (
    "style_pack_id", "name", "art_style", "animation_style", "color_palette",
    "prompt_fragments", "negative_prompts", "consistency_rules",
    "brand_id", "universe_id",
)

_STYLE_PACK_DEFAULTS = {
    "color_palette": list, "prompt_fragments": list, "negative_prompts": list,
    "consistency_rules": list,
}


def build_style_pack(spec: dict) -> dict:
    return normalize(spec, STYLE_PACK_FIELDS, _STYLE_PACK_DEFAULTS, "style_pack_id", "stp_")


# ---------------------------------------------------------------- Franchise

FRANCHISE_FIELDS = (
    "franchise_id", "name", "franchise_type", "description", "universe_id",
    "brand_id", "character_ids", "seasons", "spinoff_of", "collections",
    "performance", "status", "version", "created_at", "updated_at",
)

FRANCHISE_TYPES = (
    "series", "educational_program", "channel", "brand_show", "collection",
    "shared_universe", "spinoff",
)

_FRANCHISE_DEFAULTS = {
    "franchise_type": "series", "character_ids": list, "seasons": list,
    "collections": list, "performance": dict, "status": "active", "version": 1,
}


def build_franchise(spec: dict) -> dict:
    return normalize(spec, FRANCHISE_FIELDS, _FRANCHISE_DEFAULTS, "franchise_id", "fra_")


SEASON_FIELDS = ("season_id", "franchise_id", "name", "number", "episodes", "status")

_SEASON_DEFAULTS = {"number": 1, "episodes": list, "status": "planned"}


def build_season(spec: dict) -> dict:
    return normalize(spec, SEASON_FIELDS, _SEASON_DEFAULTS, "season_id", "sea_")


EPISODE_FIELDS = (
    "episode_id", "season_id", "franchise_id", "title", "number",
    "content_id", "character_ids", "location_ids", "canon_event_ids", "status",
)

_EPISODE_DEFAULTS = {
    "number": 1, "character_ids": list, "location_ids": list,
    "canon_event_ids": list, "status": "planned",
}


def build_episode(spec: dict) -> dict:
    return normalize(spec, EPISODE_FIELDS, _EPISODE_DEFAULTS, "episode_id", "epi_")


# ---------------------------------------------------------------- StoryBible

STORY_BIBLE_FIELDS = (
    "bible_id", "universe_id", "generated_at", "universe", "characters",
    "relationships", "locations", "organizations", "canon_events",
    "franchises", "style_packs", "continuity_issues", "version",
)


def build_story_bible(spec: dict) -> dict:
    bible = dict(spec or {})
    bible.setdefault("bible_id", f"bib_{bible.get('universe_id', 'all')}")
    bible.setdefault("generated_at", _now_iso())
    bible.setdefault("version", 1)
    for name in (
        "characters", "relationships", "locations", "organizations",
        "canon_events", "franchises", "style_packs", "continuity_issues",
    ):
        bible.setdefault(name, [])
    bible.setdefault("universe", {})
    bible.setdefault("universe_id", "")
    return bible
