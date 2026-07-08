"""Opportunity scoring — one 0-100 score per trend, with factor breakdown.

Eleven factors blend into the final score. Weights are data, not code, so
the future Learning Engine can tune them from real performance without
touching scoring logic.
"""

from __future__ import annotations

import math

from services.trends.models import Opportunity, Trend

# Categories that keep earning views long after the trend peaks.
EVERGREEN_CATEGORIES = {
    "science": 0.9, "psychology": 0.9, "history": 0.85, "health": 0.8,
    "finance": 0.8, "education": 0.85, "technology": 0.7, "space": 0.85,
    "general": 0.5, "news": 0.2, "entertainment": 0.4,
}

# Relative CPM / monetization strength by category.
MONETIZATION_CATEGORIES = {
    "finance": 0.95, "technology": 0.8, "health": 0.75, "education": 0.7,
    "science": 0.65, "psychology": 0.6, "history": 0.5, "space": 0.55,
    "general": 0.5, "news": 0.45, "entertainment": 0.4,
}

# How hard the content is to produce well (higher = easier).
DIFFICULTY_CATEGORIES = {
    "psychology": 0.8, "history": 0.75, "general": 0.7, "entertainment": 0.75,
    "education": 0.65, "science": 0.6, "space": 0.6, "finance": 0.55,
    "technology": 0.55, "health": 0.5, "news": 0.65,
}

# Platform short-form virality multipliers.
PLATFORM_VIRALITY = {
    "tiktok": 0.95, "youtube_shorts": 0.9, "youtube": 0.75, "instagram": 0.85,
    "reddit": 0.6, "google": 0.55, "news": 0.5, "rss": 0.45, "": 0.5,
}

# Learning Engine will eventually tune these from observed performance.
FACTOR_WEIGHTS = {
    "search_demand": 0.14,
    "growth_velocity": 0.14,
    "competition": 0.12,
    "historical_performance": 0.08,
    "content_difficulty": 0.07,
    "monetization_potential": 0.10,
    "virality_potential": 0.12,
    "evergreen_potential": 0.08,
    "freshness": 0.06,
    "audience_size": 0.05,
    "international_potential": 0.04,
}


def _clamp100(value: float) -> int:
    return max(0, min(100, int(round(value))))


def _demand_score(search_volume: int) -> int:
    """Log-scaled: 1k → ~43, 100k → ~71, 10M → ~100."""
    if search_volume <= 0:
        return 10
    return _clamp100(math.log10(search_volume) * 100 / 7)


def score_opportunity(trend: Trend, historical_performance: float = 0.5) -> Opportunity:
    """Score a single trend. `historical_performance` (0-1) comes from the
    Knowledge Base when available; defaults to neutral until the Learning
    Engine supplies real per-niche data."""
    category = trend.category.lower()
    platform = trend.platform.lower()

    factors = {
        "search_demand": _demand_score(trend.search_volume),
        "growth_velocity": _clamp100(
            0.6 * min(trend.growth_pct, 200) / 2 + 0.4 * trend.velocity * 100
        ),
        "competition": _clamp100((1 - trend.competition) * 100),
        "historical_performance": _clamp100(historical_performance * 100),
        "content_difficulty": _clamp100(DIFFICULTY_CATEGORIES.get(category, 0.6) * 100),
        "monetization_potential": _clamp100(MONETIZATION_CATEGORIES.get(category, 0.5) * 100),
        "virality_potential": _clamp100(
            (0.6 * PLATFORM_VIRALITY.get(platform, 0.5) + 0.4 * trend.velocity) * 100
        ),
        "evergreen_potential": _clamp100(EVERGREEN_CATEGORIES.get(category, 0.5) * 100),
        "freshness": _clamp100(trend.freshness * 100),
        "audience_size": _clamp100(
            0.7 * _demand_score(trend.search_volume)
            + 0.3 * PLATFORM_VIRALITY.get(platform, 0.5) * 100
        ),
        "international_potential": _clamp100(
            (0.7 if trend.language == "en" else 0.4) * 100 * trend.confidence
        ),
    }

    weighted = sum(FACTOR_WEIGHTS[name] * value for name, value in factors.items())
    # Confidence discounts the whole signal, never boosts it.
    total = _clamp100(weighted * (0.7 + 0.3 * trend.confidence))
    return Opportunity(trend=trend, opportunity_score=total, factors=factors)


def rank_opportunities(
    trends: list[Trend],
    historical_performance: float = 0.5,
    top_n: int | None = None,
) -> list[Opportunity]:
    """Score all trends and return them ranked best-first."""
    opportunities = [score_opportunity(t, historical_performance) for t in trends]
    opportunities.sort(key=lambda o: (o.opportunity_score, o.trend.confidence), reverse=True)
    return opportunities[:top_n] if top_n else opportunities
