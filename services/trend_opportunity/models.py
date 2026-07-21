"""Trend & Opportunity Intelligence — models and score dimensions."""

from __future__ import annotations

PACKAGE_VERSION = "1.0.0"

# Mission opportunity score dimensions (0–100) → Overall Opportunity Score
SCORE_DIMENSIONS = (
    "trend_score",
    "curiosity_score",
    "educational_score",
    "retention_potential",
    "competition_score",  # higher = more open (less competition)
    "visual_score",
    "thumbnail_score",
    "platform_score",
    "revenue_score",
)

SCORE_WEIGHTS = {
    "trend_score": 0.12,
    "curiosity_score": 0.14,
    "educational_score": 0.14,
    "retention_potential": 0.12,
    "competition_score": 0.10,
    "visual_score": 0.10,
    "thumbnail_score": 0.08,
    "platform_score": 0.08,
    "revenue_score": 0.12,
}

# Analysis factors (inputs to scores — mission vocabulary)
ANALYSIS_FACTORS = (
    "search_demand",
    "trend_velocity",
    "competition",
    "evergreen_potential",
    "curiosity_gap",
    "emotional_impact",
    "educational_value",
    "shareability",
    "visual_potential",
    "thumbnail_potential",
    "audience_size",
    "platform_fit",
    "production_difficulty",
    "revenue_potential",
)

REJECTION_REASONS = (
    "oversaturated",
    "weak_educational_value",
    "low_curiosity",
    "poor_visual_potential",
    "previously_overproduced",
    "low_confidence",
    "outside_content_policy",
)

STATUSES = (
    "discovered",
    "ranked",
    "brief_ready",
    "queued",
    "in_production",
    "published",
    "retired",
    "rejected",
)

# Modular data-source keys (existing providers under providers/trend_sources)
DATA_SOURCE_KEYS = (
    "youtube_trending",
    "youtube_search",
    "google_trends",
    "google_news",
    "reddit",
    "tiktok_trending",
    "instagram_trends",
    "x_twitter",
    "rss_feeds",
)
