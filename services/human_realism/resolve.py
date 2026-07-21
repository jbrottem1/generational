"""Resolve a full character Human Realism package via framework inheritance."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from services.human_realism.base import (
    FRAMEWORK_ID,
    FRAMEWORK_VERSION,
    GOLD_STANDARD_CHARACTER_ID,
    base_framework,
)
from services.human_realism.characters import get_override
from services.human_realism.merge import deep_merge


def resolve_character(character_id: str) -> dict[str, Any]:
    """Return base framework + character overrides as one canonical package."""
    cid = str(character_id or "").upper()
    override = get_override(cid)
    if not override:
        # Future characters: still inherit full framework with minimal identity shell
        override = {
            "character_id": cid or "CHAR-UNKNOWN",
            "name": cid or "Unknown",
            "role": "generational_character",
            "inherits_from": "BASE_HUMAN_REALISM",
            "reference_implementation": GOLD_STANDARD_CHARACTER_ID,
            "visual_identity": {"archetype": "humanoid", "silhouette": "pending"},
            "personality": ["curious"],
            "gestures": {"favorites": ["open_palm_teach"]},
            "gait": {"personality_walk": "professional", "true_motion_hint": "walk_explain"},
            "emotion_bias": {"default_primary": "curiosity"},
        }

    package = deep_merge(base_framework(), {})
    # Identity overlays (do not replace core anatomy systems wholesale)
    package["character_id"] = override["character_id"]
    package["name"] = override.get("name")
    package["role"] = override.get("role")
    package["is_gold_standard"] = bool(override.get("is_gold_standard"))
    package["inherits_from"] = override.get("inherits_from", "BASE_HUMAN_REALISM")
    package["reference_implementation"] = override.get(
        "reference_implementation",
        GOLD_STANDARD_CHARACTER_ID if cid != GOLD_STANDARD_CHARACTER_ID else None,
    )

    for key in (
        "visual_identity",
        "personality",
        "voice",
        "clothing",
        "gait",
        "gestures",
        "emotion_bias",
        "camera_awareness",
        "home_world_id",
        "studio_asset_path",
        "breathing",
    ):
        if key in override:
            if isinstance(package.get(key), dict) and isinstance(override[key], dict):
                package[key] = deep_merge(package.get(key) or {}, override[key])
            else:
                package[key] = deepcopy(override[key])

    # Float top-level exaggeration if character wants slightly stylized motion (Nova)
    for key in ("facial_exaggeration", "motion_exaggeration", "anatomy_exaggeration"):
        if key in override:
            package[key] = override[key]
        vi = override.get("visual_identity") or {}
        if key in vi:
            package[key] = vi[key]

    # Merge gesture library extras into inherited gesture library
    extras = ((override.get("gestures") or {}).get("library_extra")) or {}
    lib = package.setdefault("gestures", {}).setdefault("library", {})
    lib.update(deepcopy(extras))

    package["framework_id"] = FRAMEWORK_ID
    package["framework_version"] = FRAMEWORK_VERSION
    package["resolved"] = True
    return package


def profile_views(resolved: dict[str, Any]) -> dict[str, Any]:
    """Split a resolved package into constitution-named profile documents."""
    cid = resolved["character_id"]
    vi = resolved.get("visual_identity") or {}
    clothing = resolved.get("clothing") or {}
    gait = resolved.get("gait") or {}
    gestures = resolved.get("gestures") or {}
    face = resolved.get("face") or {}
    return {
        "CHARACTER_IDENTITY.json": {
            "character_id": cid,
            "name": resolved.get("name"),
            "role": resolved.get("role"),
            "style_mode": resolved.get("style_mode"),
            "is_gold_standard": resolved.get("is_gold_standard"),
            "inherits_from": resolved.get("inherits_from"),
            "reference_implementation": resolved.get("reference_implementation"),
            "canonical_height_cm": vi.get("canonical_height_cm"),
            "body_mass_estimate_kg": vi.get("body_mass_estimate_kg"),
            "age_range": vi.get("age_range"),
            "biological_build": vi.get("biological_build"),
            "silhouette": vi.get("silhouette"),
            "palette": vi.get("palette"),
            "personality": resolved.get("personality"),
            "voice": resolved.get("voice"),
            "wardrobe_default": clothing.get("default_outfit"),
            "gait_characteristics": gait.get("traits"),
            "forbid_regenerate_from_scratch": True,
            "framework_id": resolved.get("framework_id"),
        },
        "SKELETON_PROFILE.json": {
            "character_id": cid,
            **(resolved.get("skeleton") or {}),
            "proportions_from": vi.get("biological_build"),
        },
        "MUSCLE_PROFILE.json": {"character_id": cid, **(resolved.get("muscles") or {})},
        "FACE_RIG_PROFILE.json": {
            "character_id": cid,
            **face,
            "eyes": resolved.get("eyes"),
            "blinking": resolved.get("blinking"),
            "breathing_defaults": (resolved.get("breathing") or {}).get("modes"),
        },
        "GAIT_PROFILE.json": {
            "character_id": cid,
            **gait,
            "locomotion": resolved.get("locomotion"),
        },
        "GESTURE_LIBRARY.json": {"character_id": cid, **gestures},
        "EMOTION_LIBRARY.json": {
            "character_id": cid,
            "emotion": resolved.get("emotion"),
            "emotion_bias": resolved.get("emotion_bias"),
        },
        "HAIR_PROFILE.json": {
            "character_id": cid,
            **(resolved.get("hair") or {}),
            **(vi.get("hair") or {}),
        },
        "WARDROBE_PROFILE.json": {"character_id": cid, **clothing},
        "ANIMATION_QUALITY_VALIDATION.json": {
            "character_id": cid,
            **(resolved.get("quality_validation") or {}),
        },
        "RESOLVED_PACKAGE.json": resolved,
    }
