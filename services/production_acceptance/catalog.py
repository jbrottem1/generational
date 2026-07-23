"""Production Acceptance Testing System V1.0 — category catalog & modes."""

from __future__ import annotations

from typing import Any

ACCEPTANCE_VERSION = "1.0.0"

# smoke = CI / every push; full = pre-release gate; stress = capacity nightlies
MODES = ("smoke", "full", "stress")

CATEGORIES: tuple[str, ...] = (
    "educational",
    "history",
    "science",
    "medicine",
    "technology",
    "business",
    "finance",
    "psychology",
    "space",
    "nature",
)

CATEGORY_TOPICS: dict[str, list[str]] = {
    "educational": [
        "How Photosynthesis Works in 60 Seconds",
        "The Water Cycle Explained Simply",
    ],
    "history": [
        "Why the Roman Empire Fell",
        "The Invention of Writing",
    ],
    "science": [
        "What Is Quantum Entanglement",
        "How Vaccines Train Your Immune System",
    ],
    "medicine": [
        "Why Fever Helps Fight Infection",
        "How Antibiotics Kill Bacteria",
    ],
    "technology": [
        "How the Internet Routes a Packet",
        "Why Batteries Degrade Over Time",
    ],
    "business": [
        "What Unit Economics Actually Mean",
        "How Supply Chains Absorb Shocks",
    ],
    "finance": [
        "How Compound Interest Works",
        "What Inflation Does to Savings",
    ],
    "psychology": [
        "Why Confirmation Bias Feels So Convincing",
        "How Habits Rewire Attention",
    ],
    "space": [
        "Why Octopuses Have Three Hearts",  # also biology-space cross used in ops demos
        "How Black Holes Bend Light",
    ],
    "nature": [
        "How Coral Reefs Build Cities",
        "Why Leaves Change Color",
    ],
}

DURATIONS_SEC: tuple[int, ...] = (10, 20, 30, 45, 60, 90, 180, 300)

PLATFORMS: dict[str, dict[str, Any]] = {
    "youtube_shorts": {"aspect": "9:16", "max_sec": 60, "caption_required": True},
    "tiktok": {"aspect": "9:16", "max_sec": 60, "caption_required": True},
    "instagram_reels": {"aspect": "9:16", "max_sec": 90, "caption_required": True},
    "facebook_reels": {"aspect": "9:16", "max_sec": 90, "caption_required": True},
    "x": {"aspect": "16:9", "max_sec": 140, "caption_required": False},
    "youtube_long": {"aspect": "16:9", "max_sec": 720, "caption_required": True},
}

# Expected ops stage order (must match Production Operations)
EXPECTED_OPS_STAGE_ORDER: tuple[str, ...] = (
    "research",
    "psychology",
    "studio_director",
    "script_generator",
    "scene_builder",
    "media_collection",
    "animation",
    "voice_generation",
    "music_sound",
    "captions",
    "rendering",
    "viewer_retention",
    "optimization_lab",
    "quality_assurance",
    "seo_package",
    "export",
)

# Core engines that must load for production readiness
REQUIRED_ENGINES: tuple[str, ...] = (
    "research",
    "ideation",
    "psychology",
    "ai_director",
    "script_generation",
    "scene_planning",
    "voice_audio",
    "subtitle",
    "studio_render",
    "quality",
    "production_qa",
    "optimization_lab",
    "production_operations",
    "production_pipeline",
)

SMOKE_LIMITS = {
    "categories": 3,
    "topics_per_category": 1,
    "durations": (30, 60),
    "platforms": ("youtube_shorts", "tiktok"),
    "stress_counts": (1,),
    "queued_jobs": 5,
}

FULL_LIMITS = {
    "categories": 10,
    "topics_per_category": 2,
    "durations": DURATIONS_SEC,
    "platforms": tuple(PLATFORMS.keys()),
    "stress_counts": (1, 5, 20),
    "queued_jobs": 50,
}

STRESS_LIMITS = {
    "categories": 10,
    "topics_per_category": 2,
    "durations": DURATIONS_SEC,
    "platforms": tuple(PLATFORMS.keys()),
    "stress_counts": (1, 5, 20),
    "queued_jobs": 50,
}


def limits_for(mode: str) -> dict[str, Any]:
    mode = (mode or "smoke").lower()
    if mode == "full":
        return dict(FULL_LIMITS)
    if mode == "stress":
        return dict(STRESS_LIMITS)
    return dict(SMOKE_LIMITS)
