"""Opportunity classification — what KIND of opportunity is this?

Three independent axes, all threshold-driven from the config:

- lifecycle:    breaking | exploding | emerging | growing | peak | declining
- content_type: evergreen | seasonal | recurring | topical
- market_reach: niche | mid_market | mass_market

Deterministic rules, no AI: the same signal always classifies the same
way, so downstream filters ("give me emerging opportunities") are stable.
"""

from __future__ import annotations

from services.trend_intelligence.config import (
    TrendIntelligenceConfig,
    get_trend_intelligence_config,
)
from services.trends.models import Opportunity
from services.trends.scorer import EVERGREEN_CATEGORIES

# Keyword markers for time-bound topics. Matching any marker in the topic
# or keywords classifies the opportunity as seasonal.
SEASONAL_MARKERS = (
    "christmas", "halloween", "thanksgiving", "easter", "valentine",
    "new year", "summer", "winter", "spring", "autumn", "fall season",
    "back to school", "black friday", "cyber monday", "tax season",
    "olympics", "world cup", "super bowl", "election",
)

# Markers for habitual/recurring content that re-earns on a cycle.
RECURRING_MARKERS = (
    "daily", "weekly", "monthly", "annual", "every year", "routine",
    "habit", "morning", "night ritual", "challenge",
)


def _text_blob(trend) -> str:
    return " ".join([trend.topic.lower(), *[k.lower() for k in trend.keywords]])


def _lifecycle(trend, config: TrendIntelligenceConfig) -> str:
    if trend.growth_pct >= config.exploding_growth_pct and trend.velocity >= config.exploding_velocity:
        return "exploding"
    if trend.freshness >= config.breaking_freshness and trend.growth_pct >= config.breaking_growth_pct:
        return "breaking"
    if trend.growth_pct >= config.emerging_growth_pct and trend.freshness >= config.emerging_freshness:
        return "emerging"
    if trend.growth_pct < config.declining_growth_pct and trend.freshness < config.declining_freshness:
        return "declining"
    if trend.velocity <= config.peak_velocity and trend.competition >= config.peak_competition:
        return "peak"
    return "growing"


def _content_type(trend, config: TrendIntelligenceConfig) -> str:
    blob = _text_blob(trend)
    if any(marker in blob for marker in SEASONAL_MARKERS):
        return "seasonal"
    if any(marker in blob for marker in RECURRING_MARKERS):
        return "recurring"
    if EVERGREEN_CATEGORIES.get(trend.category.lower(), 0.5) >= config.evergreen_floor:
        return "evergreen"
    return "topical"


def _market_reach(trend, config: TrendIntelligenceConfig) -> str:
    if trend.search_volume >= config.mass_market_search_volume:
        return "mass_market"
    if trend.search_volume < config.niche_search_volume:
        return "niche"
    return "mid_market"


def classify_opportunity(
    opportunity: Opportunity,
    config: "TrendIntelligenceConfig | None" = None,
) -> dict:
    """Classification dict matching CLASSIFICATION_FIELDS."""
    config = config or get_trend_intelligence_config()
    trend = opportunity.trend

    lifecycle = _lifecycle(trend, config)
    content_type = _content_type(trend, config)
    market_reach = _market_reach(trend, config)

    return {
        "trend_id": trend.trend_id,
        "topic": trend.topic,
        "lifecycle": lifecycle,
        "content_type": content_type,
        "market_reach": market_reach,
        "labels": [lifecycle, content_type, market_reach],
    }
