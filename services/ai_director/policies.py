"""Configurable decision policies for the AI Director.

Policies are plain dicts — swap or extend at runtime via `configure_policies()`
without touching decision logic. Future reinforcement-learning feedback from
Analytics adjusts weights through `apply_learning_feedback()`.
"""

from __future__ import annotations

from copy import deepcopy

# Default policy bundle — versioned so diagnostics can trace which policy
# produced a given DirectorPackage.
DEFAULT_POLICY_VERSION = "1.0"

DEFAULT_POLICIES: dict = {
    "version": DEFAULT_POLICY_VERSION,
    # Format selection weights (higher = more likely when signals tie).
    "format_weights": {
        "short_form": 1.0,
        "long_form": 0.6,
        "documentary": 0.7,
        "educational": 0.8,
        "cartoon": 0.5,
        "cinematic": 0.75,
        "podcast": 0.4,
        "livestream": 0.3,
    },
    # Platform defaults when none specified on the item.
    "default_platforms": ["youtube_shorts"],
    "platform_orientation": {
        "youtube_shorts": "vertical",
        "tiktok": "vertical",
        "instagram_reels": "vertical",
        "youtube": "horizontal",
        "linkedin": "horizontal",
        "podcast": "horizontal",
    },
    "platform_max_duration": {
        "youtube_shorts": 60,
        "tiktok": 180,
        "instagram_reels": 90,
        "youtube": 600,
        "linkedin": 300,
    },
    # Quality tier thresholds (opportunity_score → tier).
    "quality_tiers": {
        "flagship": 85,
        "premium": 70,
        "standard": 50,
        "draft": 0,
    },
    # Emotional intensity from psychology score bands.
    "emotion_bands": {
        "extreme": 90,
        "high": 75,
        "moderate": 50,
        "low": 0,
    },
    # Analytics feedback weights (future RL loop).
    "learning_weights": {
        "format": {},
        "platform": {},
        "style": {},
        "thumbnail": {},
    },
    # Graceful degradation: when upstream package missing, fall back to these.
    "fallbacks": {
        "format": "short_form",
        "orientation": "vertical",
        "visual_style": "minimal",
        "animation_technique": "motion_graphics",
        "voice_delivery": "conversational",
    },
}

_active_policies: dict = deepcopy(DEFAULT_POLICIES)


def get_policies() -> dict:
    """Return a copy of the active policy bundle."""
    return deepcopy(_active_policies)


def configure_policies(updates: dict) -> dict:
    """Merge updates into the active policy bundle. Returns the new bundle."""
    global _active_policies
    merged = deepcopy(_active_policies)
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = {**merged[key], **value}
        else:
            merged[key] = value
    _active_policies = merged
    return deepcopy(_active_policies)


def reset_policies() -> dict:
    """Restore default policies (for tests)."""
    global _active_policies
    _active_policies = deepcopy(DEFAULT_POLICIES)
    return deepcopy(_active_policies)


def apply_learning_feedback(feedback: dict) -> dict:
    """Incorporate analytics/optimization feedback into policy weights.

    `feedback` shape: {dimension: {choice: delta}} where delta is a float
    adjustment applied to the corresponding weight. This is the hook for
    future reinforcement learning — deterministic today, extensible tomorrow.
    """
    weights = deepcopy(_active_policies.get("learning_weights", {}))
    for dimension, adjustments in feedback.items():
        if dimension not in weights:
            weights[dimension] = {}
        bucket = weights[dimension]
        for choice, delta in adjustments.items():
            bucket[choice] = bucket.get(choice, 0.0) + float(delta)
    return configure_policies({"learning_weights": weights})


def quality_tier_for_score(score: int, policies: dict | None = None) -> str:
    """Map an opportunity/quality score to a production tier."""
    tiers = (policies or _active_policies).get("quality_tiers", DEFAULT_POLICIES["quality_tiers"])
    for tier in ("flagship", "premium", "standard", "draft"):
        if score >= tiers.get(tier, 0):
            return tier
    return "draft"


def learning_boost(dimension: str, choice: str, policies: dict | None = None) -> float:
    """Return the RL weight boost for a dimension/choice pair."""
    weights = (policies or _active_policies).get("learning_weights", {})
    return float(weights.get(dimension, {}).get(choice, 0.0))
