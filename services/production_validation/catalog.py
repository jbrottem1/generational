"""Domain production briefs — only human inputs; everything else is automatic."""

from __future__ import annotations

from typing import Any

# Pure content briefs for validation (no infrastructure).
DOMAIN_PRODUCTIONS: tuple[dict[str, Any], ...] = (
    {
        "domain": "artificial_intelligence",
        "topic": "What Artificial Intelligence Actually Is",
        "platform": "youtube_shorts",
        "length_sec": 45,
        "style": "educational",
        "audience": "curious adults 18-40",
        "voice": "professor",
    },
    {
        "domain": "biology",
        "topic": "Why Octopuses Have Three Hearts",
        "platform": "youtube_shorts",
        "length_sec": 45,
        "style": "science_documentary",
        "audience": "science-curious teens and adults",
        "voice": "scientist",
    },
    {
        "domain": "physics",
        "topic": "What Gravity Really Does to Time",
        "platform": "youtube_shorts",
        "length_sec": 60,
        "style": "educational",
        "audience": "high-school and college learners",
        "voice": "professor",
    },
    {
        "domain": "history",
        "topic": "Why the Library of Alexandria Still Matters",
        "platform": "youtube_shorts",
        "length_sec": 45,
        "style": "history",
        "audience": "history lovers 20-50",
        "voice": "documentary_host",
    },
    {
        "domain": "astronomy",
        "topic": "How James Webb Sees the First Galaxies",
        "platform": "youtube_shorts",
        "length_sec": 50,
        "style": "space",
        "audience": "space enthusiasts",
        "voice": "scientist",
    },
    {
        "domain": "medicine",
        "topic": "How Vaccines Train the Immune System",
        "platform": "youtube_shorts",
        "length_sec": 45,
        "style": "medical",
        "audience": "general public",
        "voice": "professor",
    },
    {
        "domain": "finance",
        "topic": "How Compound Interest Quietly Changes Lives",
        "platform": "youtube_shorts",
        "length_sec": 40,
        "style": "explainer",
        "audience": "young adults building savings",
        "voice": "teacher",
    },
    {
        "domain": "psychology",
        "topic": "Why Confirmation Bias Feels Like Truth",
        "platform": "youtube_shorts",
        "length_sec": 45,
        "style": "vox_inspired",
        "audience": "self-improvement audience",
        "voice": "conversational",
    },
    {
        "domain": "engineering",
        "topic": "How Bridges Carry Impossible Weight",
        "platform": "youtube_shorts",
        "length_sec": 50,
        "style": "technology",
        "audience": "curious makers and students",
        "voice": "engineer",
    },
    {
        "domain": "nature",
        "topic": "How Coral Reefs Build Underwater Cities",
        "platform": "youtube_shorts",
        "length_sec": 45,
        "style": "nature",
        "audience": "nature documentary fans",
        "voice": "storyteller",
    },
)

# Mission score keys — what humans care about for publishing readiness
SCORE_DIMENSIONS: tuple[str, ...] = (
    "hook_strength",
    "retention_prediction",
    "visual_quality",
    "animation_quality",
    "narration_quality",
    "audio_mix",
    "caption_quality",
    "educational_accuracy",
    "seo_quality",
    "thumbnail_quality",
    "ctr_prediction",
    "completion_prediction",
    "shareability",
    "overall_production_score",
)

# Weakness taxonomy → impact weight (higher = fix first)
WEAKNESS_CATALOG: dict[str, dict[str, Any]] = {
    "weak_hook": {
        "label": "Weak hook",
        "dimension": "hook_strength",
        "impact": 95,
        "fix_hint": "Tighten first 3 seconds; use open loop + concrete surprise from psychology dims.",
    },
    "static_visuals": {
        "label": "Static visuals",
        "dimension": "visual_quality",
        "impact": 88,
        "fix_hint": "Increase camera movement density and scene variety from cinematography/studio_render.",
    },
    "weak_animation": {
        "label": "Weak animation / motion graphics",
        "dimension": "animation_quality",
        "impact": 82,
        "fix_hint": "Raise kinetic type / diagram density; avoid flat holds longer than 3s.",
    },
    "voice_pacing": {
        "label": "Voice pacing",
        "dimension": "narration_quality",
        "impact": 80,
        "fix_hint": "Adjust WPM and pause plan in voice_audio; align with retention curve.",
    },
    "caption_timing": {
        "label": "Caption timing",
        "dimension": "caption_quality",
        "impact": 75,
        "fix_hint": "Sync subtitle beats to narration word timing; reduce lag on hooks.",
    },
    "music_transitions": {
        "label": "Music transitions",
        "dimension": "audio_mix",
        "impact": 70,
        "fix_hint": "Duck music under narration; match intensity to emotion curve.",
    },
    "thumbnail_clarity": {
        "label": "Thumbnail clarity",
        "dimension": "thumbnail_quality",
        "impact": 85,
        "fix_hint": "One subject + ≤6 claim words; raise contrast per director thumbnail strategy.",
    },
    "seo_packaging": {
        "label": "SEO packaging",
        "dimension": "seo_quality",
        "impact": 65,
        "fix_hint": "Strengthen title curiosity + tags from seo / seo_optimization packages.",
    },
    "educational_depth": {
        "label": "Educational accuracy / depth",
        "dimension": "educational_accuracy",
        "impact": 78,
        "fix_hint": "Raise research citation density and evidence panel clarity.",
    },
    "retention_drop": {
        "label": "Retention risk mid-video",
        "dimension": "retention_prediction",
        "impact": 90,
        "fix_hint": "Insert pattern interrupt at mid-point; tighten cut length for shorts.",
    },
    "rendering_speed": {
        "label": "Rendering speed",
        "dimension": "overall_production_score",
        "impact": 55,
        "fix_hint": "Cache assets; reduce unnecessary revision loops on smoke exports.",
    },
    "low_shareability": {
        "label": "Low shareability",
        "dimension": "shareability",
        "impact": 72,
        "fix_hint": "Sharpen share prompt/CTA and emotional peak placement.",
    },
}

PUBLISH_READY_FLOOR = 90.0
DIMENSION_WEAK_FLOOR = 80.0
