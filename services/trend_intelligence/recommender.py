"""Recommendation Engine — turns forecasts into structured creative direction.

Given a scored opportunity, its forecast, and its classification, produce
one OpportunityRecommendation: platform, hook direction, psychology
strategy, duration, format, thumbnail/title direction, SEO guidance,
publishing window, and the ROI / confidence / risk / priority numbers.

Directions are STRATEGY, never content — the Script, Visual, and SEO
engines own actual generation. Everything is deterministic and weight-
driven so the Learning Engine can retune outcomes via configuration.
"""

from __future__ import annotations

from services.trend_intelligence.config import (
    TrendIntelligenceConfig,
    get_trend_intelligence_config,
)
from services.trend_intelligence.models import OpportunityRecommendation, TrendForecast
from services.trends.models import Opportunity
from services.trends.scorer import MONETIZATION_CATEGORIES, PLATFORM_VIRALITY

# Platform-native duration ranges (seconds).
PLATFORM_DURATIONS = {
    "tiktok": {"min": 30, "max": 45},
    "youtube_shorts": {"min": 45, "max": 60},
    "instagram": {"min": 30, "max": 60},
    "youtube": {"min": 480, "max": 720},
    "facebook": {"min": 45, "max": 90},
    "x": {"min": 30, "max": 60},
}

# Hook strategy by lifecycle stage.
HOOK_DIRECTIONS = {
    "breaking": "Urgency open — lead with what just happened and why it changes things now.",
    "exploding": "FOMO open — everyone is talking about this; reveal the part they're missing.",
    "emerging": "Early-insider open — position the viewer ahead of the curve before it's mainstream.",
    "growing": "Curiosity-gap open — pose the question the topic makes everyone secretly ask.",
    "peak": "Contrarian open — challenge the consensus take everyone has already seen.",
    "declining": "Retrospective open — what everyone got wrong, now that the dust settled.",
}

# Psychology strategy by trend category (maps to the Psychology Engine's dimensions).
PSYCHOLOGY_STRATEGIES = {
    "psychology": "curiosity gap + self-recognition",
    "finance": "loss aversion + status signaling",
    "health": "fear-of-harm relief + authority proof",
    "science": "awe + counterintuitive reveal",
    "technology": "future-pacing + FOMO",
    "history": "forbidden-knowledge framing + narrative suspense",
    "space": "awe + scale contrast",
    "education": "competence gain + curiosity gap",
    "news": "urgency + social proof",
    "entertainment": "surprise + relatability",
    "general": "curiosity gap + pattern interrupt",
}

# Format by lifecycle (how the story should be told, not what it says).
FORMAT_DIRECTIONS = {
    "breaking": "fast-cut news explainer",
    "exploding": "reaction + breakdown",
    "emerging": "deep-dive early explainer",
    "growing": "listicle / top-N breakdown",
    "peak": "myth-busting counter-take",
    "declining": "retrospective analysis",
}


def _clamp100(value: float) -> int:
    return max(0, min(100, int(round(value))))


def _recommended_platform(trend, config: TrendIntelligenceConfig) -> str:
    """The trend's home platform when it's in scope, else the configured
    platform with the highest short-form virality."""
    home = trend.platform.lower()
    if home in config.platforms:
        return home
    candidates = config.platforms or list(PLATFORM_DURATIONS)
    return max(candidates, key=lambda p: PLATFORM_VIRALITY.get(p, 0.5))


def _seo_recommendations(trend, platform: str) -> dict:
    keywords = [k for k in trend.keywords if k]
    return {
        "primary_keyword": keywords[0] if keywords else trend.topic.lower(),
        "secondary_keywords": keywords[1:6],
        "title_keyword_placement": "front-load the primary keyword in the first 40 characters",
        "hashtag_count": 3 if platform in ("youtube_shorts", "youtube") else 5,
        "language": trend.language,
        "target_country": trend.country,
    }


def _estimated_roi(opportunity: Opportunity, forecast: TrendForecast, config) -> int:
    trend = opportunity.trend
    monetization = MONETIZATION_CATEGORIES.get(trend.category.lower(), 0.5)
    weights = config.roi_weights
    blended = (
        weights.get("opportunity_score", 0.35) * opportunity.opportunity_score
        + weights.get("monetization", 0.25) * monetization * 100
        + weights.get("low_competition", 0.20) * (1.0 - trend.competition) * 100
        + weights.get("future_score", 0.20) * forecast.future_opportunity_score
    )
    return _clamp100(blended)


def _risk_score(trend, forecast: TrendForecast) -> int:
    risk = (
        0.5 * forecast.saturation_risk
        + 0.3 * (1.0 - forecast.forecast_confidence)
        + 0.2 * trend.competition
    )
    return _clamp100(risk * 100)


def _priority_score(
    opportunity: Opportunity,
    forecast: TrendForecast,
    roi: int,
    risk: int,
    config: TrendIntelligenceConfig,
) -> int:
    urgency = 1.0 - min(forecast.days_to_peak, config.max_days_to_peak) / config.max_days_to_peak
    weights = config.priority_weights
    blended = (
        weights.get("opportunity_score", 0.30) * opportunity.opportunity_score
        + weights.get("estimated_roi", 0.25) * roi
        + weights.get("urgency", 0.20) * urgency * 100
        + weights.get("confidence", 0.15) * forecast.forecast_confidence * 100
        + weights.get("risk_penalty", 0.10) * (100 - risk)
    )
    return _clamp100(blended)


def recommend_opportunity(
    opportunity: Opportunity,
    forecast: TrendForecast,
    classification: dict,
    config: "TrendIntelligenceConfig | None" = None,
) -> OpportunityRecommendation:
    """One structured recommendation per opportunity — strategy, never content."""
    config = config or get_trend_intelligence_config()
    trend = opportunity.trend
    lifecycle = classification.get("lifecycle", "growing")

    platform = _recommended_platform(trend, config)
    roi = _estimated_roi(opportunity, forecast, config)
    risk = _risk_score(trend, forecast)
    confidence = round(min(trend.confidence, forecast.forecast_confidence), 2)

    return OpportunityRecommendation(
        trend_id=trend.trend_id,
        topic=trend.topic,
        recommended_platform=platform,
        hook_direction=HOOK_DIRECTIONS.get(lifecycle, HOOK_DIRECTIONS["growing"]),
        psychology_strategy=PSYCHOLOGY_STRATEGIES.get(
            trend.category.lower(), PSYCHOLOGY_STRATEGIES["general"]
        ),
        recommended_duration_sec=dict(
            PLATFORM_DURATIONS.get(platform, PLATFORM_DURATIONS["youtube_shorts"])
        ),
        recommended_format=FORMAT_DIRECTIONS.get(lifecycle, FORMAT_DIRECTIONS["growing"]),
        thumbnail_direction=(
            f"High-contrast close-up anchored on '{trend.topic}' with one bold "
            f"3-5 word overlay; face + emotion if the format allows."
        ),
        title_direction=(
            f"Lead with the primary keyword, open a curiosity gap about "
            f"'{trend.topic}', stay under 60 characters."
        ),
        seo_recommendations=_seo_recommendations(trend, platform),
        publishing_window=dict(forecast.publishing_window),
        estimated_roi=roi,
        confidence_score=confidence,
        risk_score=risk,
        priority_score=_priority_score(opportunity, forecast, roi, risk, config),
    )
