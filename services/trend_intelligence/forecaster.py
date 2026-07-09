"""Forecast Engine — deterministic projections of where a trend is going.

Predicts time to peak, expected lifespan, growth trajectory, saturation
risk, the recommended publishing window and frequency, a projected future
opportunity score, and a confidence figure for the forecast itself.

All math is pure and deterministic (no AI, no network): the same
opportunity always produces the same forecast, which keeps the engine
testable and the pipeline reproducible. Real time-series models can
replace individual functions later without changing the TrendForecast
contract.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from services.trend_intelligence.config import (
    TrendIntelligenceConfig,
    get_trend_intelligence_config,
)
from services.trend_intelligence.models import TrendForecast
from services.trends.models import Opportunity
from services.trends.scorer import EVERGREEN_CATEGORIES


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _momentum(trend) -> float:
    """0-1 blend of velocity and normalized growth — how hard it's moving."""
    growth_norm = _clamp(trend.growth_pct / 200.0, 0.0, 1.0)
    return _clamp(0.5 * trend.velocity + 0.5 * growth_norm, 0.0, 1.0)


def _days_to_peak(trend, config: TrendIntelligenceConfig) -> int:
    """Fast movers peak sooner; stale slow signals take longer (or already peaked)."""
    momentum = _momentum(trend)
    spread = config.max_days_to_peak - 1
    staleness = 0.5 + 0.5 * (1.0 - trend.freshness)
    return int(round(_clamp(1 + (1.0 - momentum) * spread * staleness, 1, config.max_days_to_peak)))


def _expected_lifespan_days(trend, config: TrendIntelligenceConfig) -> int:
    """Evergreen categories keep earning for months; news burns out in days."""
    evergreen = EVERGREEN_CATEGORIES.get(trend.category.lower(), 0.5)
    span = config.evergreen_lifespan_days - config.base_lifespan_days
    velocity_damping = 0.6 + 0.4 * (1.0 - trend.velocity)   # fast spikes die faster
    return int(round(config.base_lifespan_days + evergreen * span * velocity_damping))


def _trajectory(trend, config: TrendIntelligenceConfig) -> str:
    if trend.growth_pct >= config.explosive_growth_pct and trend.velocity >= config.explosive_velocity:
        return "explosive"
    if trend.growth_pct >= 60:
        return "rising"
    if trend.growth_pct < 10 or trend.freshness < 0.35:
        return "declining"
    if trend.growth_pct >= 20:
        return "steady"
    return "flattening"


def _saturation_risk(trend) -> float:
    """How likely the topic is already crowded by the time content ships."""
    growth_headroom = 1.0 - _clamp(trend.growth_pct / 200.0, 0.0, 1.0)
    risk = 0.55 * trend.competition + 0.30 * (1.0 - trend.freshness) + 0.15 * growth_headroom
    return round(_clamp(risk, 0.0, 1.0), 2)


def _publishing_window(trend, days_to_peak: int, lifespan: int) -> dict:
    """Publish before the peak; evergreen tails extend the closing edge."""
    momentum = _momentum(trend)
    start_days = 0 if momentum > 0.7 else max(0, int(round(days_to_peak * 0.25)))
    end_days = max(start_days + 1, int(round(days_to_peak + lifespan * 0.25)))
    now = datetime.now(timezone.utc)
    return {
        "start": (now + timedelta(days=start_days)).date().isoformat(),
        "end": (now + timedelta(days=end_days)).date().isoformat(),
        "start_in_days": start_days,
        "end_in_days": end_days,
    }


def _posts_per_week(trend, lifespan: int) -> int:
    evergreen = EVERGREEN_CATEGORIES.get(trend.category.lower(), 0.5)
    cadence = 1 + _momentum(trend) * 4 + evergreen * 2
    if lifespan <= 7:            # short-lived: front-load while it exists
        cadence += 1
    return int(round(_clamp(cadence, 1, 7)))


def _future_score(opportunity: Opportunity, trend, saturation: float) -> int:
    """Projected 0-100 score at the publishing-window midpoint."""
    momentum = _momentum(trend)
    projected = opportunity.opportunity_score * (1.0 + 0.15 * momentum - 0.25 * saturation)
    return int(round(_clamp(projected, 0, 100)))


def _forecast_confidence(trend) -> float:
    """Provider confidence discounted by how complete the signal actually is."""
    signals = (
        trend.search_volume > 0,
        trend.growth_pct > 0,
        trend.velocity > 0,
        trend.freshness > 0,
    )
    completeness = sum(signals) / len(signals)
    return round(_clamp(trend.confidence * (0.6 + 0.4 * completeness), 0.0, 1.0), 2)


def forecast_opportunity(
    opportunity: Opportunity,
    config: "TrendIntelligenceConfig | None" = None,
) -> TrendForecast:
    """One deterministic forecast per scored opportunity."""
    config = config or get_trend_intelligence_config()
    trend = opportunity.trend

    days_to_peak = _days_to_peak(trend, config)
    lifespan = _expected_lifespan_days(trend, config)
    saturation = _saturation_risk(trend)

    return TrendForecast(
        trend_id=trend.trend_id,
        topic=trend.topic,
        days_to_peak=days_to_peak,
        expected_lifespan_days=lifespan,
        trajectory=_trajectory(trend, config),
        saturation_risk=saturation,
        publishing_window=_publishing_window(trend, days_to_peak, lifespan),
        recommended_posts_per_week=_posts_per_week(trend, lifespan),
        future_opportunity_score=_future_score(opportunity, trend, saturation),
        forecast_confidence=_forecast_confidence(trend),
    )
