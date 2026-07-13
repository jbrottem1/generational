"""Market forecasting — pluggable models predicting where a market is going.

Builds MARKET_FORECAST_FIELDS dicts: growth rate, peak/decline dates,
lifespan, virality potential, saturation, competition level, forecast
confidence, expected longevity, and historical similarity (from the
learning bridge).

Models are a registry (`FORECAST_MODELS`) selected by configuration —
real time-series/ML models register alongside the deterministic
`momentum` baseline without changing any consumer. This layer builds on
Agent 11's per-opportunity forecaster (`services/trend_intelligence/
forecaster.py`) and extends it with market-level fields.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from services.market_intelligence.competition import competition_level
from services.market_intelligence.learning_bridge import historical_similarity
from services.trend_intelligence.forecaster import forecast_opportunity
from services.trends.models import Opportunity


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _longevity_class(lifespan_days: int) -> str:
    if lifespan_days >= 90:
        return "evergreen"
    if lifespan_days >= 30:
        return "long"
    if lifespan_days >= 10:
        return "medium"
    return "short"


def momentum_forecast(
    opportunity: Opportunity,
    competition_profile: dict,
    calibration: "dict | None" = None,
) -> dict:
    """The deterministic baseline model — momentum-driven projection."""
    calibration = calibration or {}
    trend = opportunity.trend

    base = forecast_opportunity(opportunity)   # Agent 11 discovery-layer forecast
    now = datetime.now(timezone.utc)
    peak = now + timedelta(days=base.days_to_peak)
    decline = peak + timedelta(days=max(1, int(round(base.expected_lifespan_days * 0.6))))

    virality = int(round(_clamp(
        0.45 * min(trend.growth_pct, 200) / 2
        + 0.35 * trend.velocity * 100
        + 0.20 * trend.freshness * 100,
        0, 100,
    )))

    confidence_calibration = float(calibration.get("confidence_calibration", 1.0))
    confidence = round(_clamp(base.forecast_confidence * confidence_calibration, 0.0, 1.0), 2)

    return {
        "growth_rate_pct": round(min(trend.growth_pct, 400.0), 1),
        "peak_date": peak.date().isoformat(),
        "decline_date": decline.date().isoformat(),
        "lifespan_days": base.expected_lifespan_days,
        "virality_potential": virality,
        "market_saturation": base.saturation_risk,
        "competition_level": competition_level(competition_profile),
        "forecast_confidence": confidence,
        "expected_longevity": _longevity_class(base.expected_lifespan_days),
        "historical_similarity": historical_similarity(
            trend.category, trend.platform, calibration
        ),
        "model": "momentum",
        # Carried through for downstream scheduling (additive extras).
        "days_to_peak": base.days_to_peak,
        "publishing_window": base.publishing_window,
        "future_opportunity_score": base.future_opportunity_score,
        "trajectory": base.trajectory,
    }


# Model registry — configuration selects by key; future ML models register
# here (or via register_forecast_model) without changing any consumer.
FORECAST_MODELS = {
    "momentum": momentum_forecast,
}


def register_forecast_model(key: str, model) -> None:
    """Plug in an additional forecast model (real time-series/ML later)."""
    FORECAST_MODELS[key] = model


def build_market_forecast(
    opportunity: Opportunity,
    competition_profile: dict,
    calibration: "dict | None" = None,
    model: str = "momentum",
) -> dict:
    """Run the configured model; unknown models fall back to the baseline."""
    forecast_model = FORECAST_MODELS.get(model, momentum_forecast)
    return forecast_model(opportunity, competition_profile, calibration)


def forecast_score(forecast: dict) -> int:
    """0-100 'future potential' — how much upside the forecast promises."""
    virality = float(forecast.get("virality_potential", 0))
    future = float(forecast.get("future_opportunity_score", 0))
    saturation = float(forecast.get("market_saturation", 0.5))
    confidence = float(forecast.get("forecast_confidence", 0.5))
    score = (0.35 * virality + 0.35 * future + 0.30 * (1.0 - saturation) * 100)
    # Low-confidence forecasts discount their own promises.
    return int(round(_clamp(score * (0.7 + 0.3 * confidence), 0, 100)))


def validate_forecast(forecast: dict) -> "list[str]":
    """Problems with a forecast dict (empty = valid). Never raises."""
    problems = []
    try:
        if forecast.get("peak_date", "") > forecast.get("decline_date", ""):
            problems.append("peak_date after decline_date")
        if not 0 <= float(forecast.get("forecast_confidence", -1)) <= 1:
            problems.append("forecast_confidence out of range")
        if not 0 <= float(forecast.get("market_saturation", -1)) <= 1:
            problems.append("market_saturation out of range")
        if int(forecast.get("lifespan_days", 0)) <= 0:
            problems.append("non-positive lifespan_days")
        if forecast.get("expected_longevity") not in ("short", "medium", "long", "evergreen"):
            problems.append("unknown expected_longevity class")
    except (TypeError, ValueError) as exc:
        problems.append(f"malformed forecast: {exc}")
    return problems
