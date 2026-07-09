"""Opportunity Engine — assembles the department's atom: MarketOpportunity.

For each scored trend opportunity (Agent 1's contract) it runs competition
analysis, the configured forecast model, the evergreen engine, and the
strategy layer, then blends everything into the final ranked
MarketOpportunity: ROI estimate, difficulty, confidence, and the priority
number the whole company sorts by. All weights come from configuration;
all calibration comes from the learning bridge.
"""

from __future__ import annotations

from datetime import datetime, timezone

from services.market_intelligence.competition import analyze_competition
from services.market_intelligence.config import (
    MarketIntelligenceConfig,
    get_market_intelligence_config,
)
from services.market_intelligence.evergreen import content_nature
from services.market_intelligence.forecasting import (
    build_market_forecast,
    forecast_score,
)
from services.market_intelligence.models import MarketOpportunity
from services.market_intelligence.strategy import (
    recommended_content_length,
    recommended_content_type,
    strategic_actions,
)
from services.trend_intelligence.classifier import classify_opportunity
from services.trends.models import Opportunity
from services.trends.scorer import MONETIZATION_CATEGORIES


def _clamp100(value: float) -> int:
    return max(0, min(100, int(round(value))))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _audience(classification: dict, trend) -> str:
    reach = classification.get("market_reach", "mid_market")
    return f"{reach} {trend.category}".strip()


def _roi_estimate(
    opportunity: Opportunity,
    forecast: dict,
    competition: dict,
    calibration: dict,
    config: MarketIntelligenceConfig,
) -> int:
    trend = opportunity.trend
    monetization = MONETIZATION_CATEGORIES.get(trend.category.lower(), 0.5)
    weights = config.roi_weights
    blended = (
        weights.get("monetization", 0.30) * monetization * 100
        + weights.get("trend_score", 0.25) * opportunity.opportunity_score
        + weights.get("competition_gap", 0.20) * competition.get("content_gap_score", 50)
        + weights.get("forecast_score", 0.15) * forecast_score(forecast)
        + weights.get("historical_calibration", 0.10)
        * calibration.get("historical_performance", 0.5) * 100
    )
    market_lift = config.market_weight(trend.category)
    roi_calibration = float(calibration.get("roi_calibration", 1.0))
    return _clamp100(blended * market_lift * roi_calibration)


def _confidence(opportunity: Opportunity, forecast: dict, calibration: dict) -> float:
    base = min(opportunity.trend.confidence, float(forecast.get("forecast_confidence", 0.5)))
    calibrated = base * float(calibration.get("confidence_calibration", 1.0))
    return round(max(0.0, min(1.0, calibrated)), 2)


def _priority(
    opportunity: Opportunity,
    forecast: dict,
    competition: dict,
    roi: int,
    confidence: float,
    config: MarketIntelligenceConfig,
) -> int:
    weights = config.ranking_weights
    platform_lift = config.platform_weight(opportunity.trend.platform)
    blended = (
        weights.get("trend_score", 0.25) * opportunity.opportunity_score
        + weights.get("forecast_score", 0.20) * forecast_score(forecast)
        + weights.get("roi_estimate", 0.20) * roi
        + weights.get("content_gap", 0.15) * competition.get("content_gap_score", 50)
        + weights.get("confidence", 0.10) * confidence * 100
        + weights.get("difficulty_penalty", 0.10)
        * (100 - competition.get("market_difficulty", 50))
    )
    return _clamp100(blended * platform_lift)


def build_market_opportunity(
    opportunity: Opportunity,
    calibration: "dict | None" = None,
    config: "MarketIntelligenceConfig | None" = None,
) -> MarketOpportunity:
    """One fully-analyzed MarketOpportunity per scored trend opportunity."""
    config = config or get_market_intelligence_config()
    calibration = calibration or {}
    trend = opportunity.trend

    competition = analyze_competition(trend, calibration)
    forecast = build_market_forecast(
        opportunity, competition, calibration, model=config.forecast_model
    )
    classification = classify_opportunity(opportunity)
    nature = content_nature(opportunity, classification)

    roi = _roi_estimate(opportunity, forecast, competition, calibration, config)
    confidence = _confidence(opportunity, forecast, calibration)
    content_type = recommended_content_type(nature, forecast)
    actions = strategic_actions(
        forecast, competition, nature,
        trend_score=opportunity.opportunity_score,
        confidence=confidence, config=config,
    )

    return MarketOpportunity(
        platform=trend.platform or "youtube_shorts",
        topic=trend.topic,
        category=trend.category,
        audience=_audience(classification, trend),
        language=trend.language,
        region=trend.country,
        difficulty=int(competition.get("market_difficulty", 50)),
        confidence=confidence,
        roi_estimate=roi,
        competition_score=_clamp100(100 - competition.get("market_difficulty", 50)),
        trend_score=opportunity.opportunity_score,
        forecast_score=forecast_score(forecast),
        priority=_priority(opportunity, forecast, competition, roi, confidence, config),
        recommended_publish_window=dict(forecast.get("publishing_window", {})),
        recommended_content_length=recommended_content_length(content_type),
        recommended_content_type=content_type,
        content_nature=nature,
        strategic_actions=actions,
        forecast=forecast,
        competition=competition,
        signals={
            "trend_id": trend.trend_id,
            "source": trend.source,
            "source_priority": config.provider_priority(trend.source),
            "keywords": list(trend.keywords),
            "growth_pct": trend.growth_pct,
            "search_volume": trend.search_volume,
        },
        created_at=_now_iso(),
    )


def build_market_opportunities(
    opportunities: "list[Opportunity]",
    calibration: "dict | None" = None,
    config: "MarketIntelligenceConfig | None" = None,
) -> "list[MarketOpportunity]":
    """Analyze and rank a batch, best-first by priority."""
    config = config or get_market_intelligence_config()
    built = [
        build_market_opportunity(opportunity, calibration, config)
        for opportunity in opportunities
    ]
    built.sort(key=lambda o: (o.priority, o.confidence), reverse=True)
    return built[: config.max_opportunities]
