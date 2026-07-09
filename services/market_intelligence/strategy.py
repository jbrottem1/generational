"""Strategic recommendations — what the company should DO with an opportunity.

Issues an ordered list of STRATEGIC_ACTION values per opportunity, driven
by its forecast, competition profile, content nature, and the
localization weighting table. Actions are strategy only — execution
belongs to the production engines.
"""

from __future__ import annotations

from services.market_intelligence.config import (
    MarketIntelligenceConfig,
    get_market_intelligence_config,
)
from services.market_intelligence.models import STRATEGIC_ACTION


def strategic_actions(
    forecast: dict,
    competition: dict,
    nature: str,
    trend_score: int,
    confidence: float,
    config: "MarketIntelligenceConfig | None" = None,
) -> "list[str]":
    """Ordered strategic actions (most important first)."""
    config = config or get_market_intelligence_config()
    actions: "list[str]" = []
    days_to_peak = int(forecast.get("days_to_peak", 7))
    saturation = float(forecast.get("market_saturation", 0.5))
    gap = int(competition.get("content_gap_score", 50))
    longevity = forecast.get("expected_longevity", "medium")

    # ---------------------------------------------------------- timing
    if confidence < config.min_confidence or trend_score < config.min_opportunity_score:
        actions.append(STRATEGIC_ACTION.MONITOR)
    elif days_to_peak <= 3 and forecast.get("trajectory") in ("explosive", "rising"):
        actions.append(STRATEGIC_ACTION.PUBLISH_IMMEDIATELY)
    elif saturation >= 0.75:
        actions.append(STRATEGIC_ACTION.DELAY)       # let the crowd thin out
    elif days_to_peak > 10 and longevity in ("long", "evergreen"):
        actions.append(STRATEGIC_ACTION.MONITOR)     # early — watch it develop
    else:
        actions.append(STRATEGIC_ACTION.PUBLISH_IMMEDIATELY)

    # ---------------------------------------------------------- expansion
    if longevity in ("long", "evergreen") and gap >= 60:
        actions.append(STRATEGIC_ACTION.EXPAND_INTO_SERIES)
    if nature in ("evergreen", "educational", "reference"):
        actions.append(STRATEGIC_ACTION.CREATE_LONG_FORM)
        actions.append(STRATEGIC_ACTION.REPURPOSE_EXISTING)
    else:
        actions.append(STRATEGIC_ACTION.CREATE_SHORT_FORM)
    if int(forecast.get("virality_potential", 0)) >= 70:
        actions.append(STRATEGIC_ACTION.CREATE_VARIANTS)

    # ---------------------------------------------------------- localization
    # Worth translating when the topic outlives the translation lead time
    # and additional configured languages exist.
    extra_languages = [lang for lang in config.localization_weighting if lang != "en"]
    if extra_languages and longevity in ("long", "evergreen") and trend_score >= 50:
        actions.append(STRATEGIC_ACTION.TRANSLATE)
        actions.append(STRATEGIC_ACTION.LOCALIZE)

    # De-duplicate preserving order.
    seen: "set[str]" = set()
    return [a for a in actions if not (a in seen or seen.add(a))]


def localization_targets(
    trend_score: int,
    nature: str,
    config: "MarketIntelligenceConfig | None" = None,
) -> "list[dict]":
    """Ranked language/region targets worth localizing this opportunity into."""
    config = config or get_market_intelligence_config()
    if nature not in ("evergreen", "educational", "reference") or trend_score < 50:
        return []
    targets = [
        {
            "language": language,
            "region": entry.get("region", ""),
            "weight": float(entry.get("weight", 0.5)),
            "localization_score": int(round(trend_score * float(entry.get("weight", 0.5)))),
        }
        for language, entry in config.localization_weighting.items()
        if language != "en"
    ]
    targets.sort(key=lambda t: t["localization_score"], reverse=True)
    return targets


def recommended_content_type(nature: str, forecast: dict) -> str:
    """short_form | long_form | series — the primary format to lead with."""
    if forecast.get("expected_longevity") == "evergreen" and \
            int(forecast.get("virality_potential", 0)) < 60:
        return "long_form"
    if nature in ("educational", "reference") and forecast.get("expected_longevity") in ("long", "evergreen"):
        return "series"
    return "short_form"


CONTENT_LENGTHS = {
    "short_form": {"min_sec": 30, "max_sec": 60},
    "long_form": {"min_sec": 480, "max_sec": 720},
    "series": {"min_sec": 45, "max_sec": 60},   # per-episode short-form series
}


def recommended_content_length(content_type: str) -> dict:
    return dict(CONTENT_LENGTHS.get(content_type, CONTENT_LENGTHS["short_form"]))
