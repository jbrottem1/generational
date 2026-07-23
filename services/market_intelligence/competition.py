"""Competition analysis — how crowded is this market, and where are the gaps?

Estimates the competitive landscape per opportunity from the normalized
trend signals (competition, search volume, velocity, platform) using
deterministic heuristics, corrected by the learning bridge's
`competition_calibration` as real outcome data accumulates. Real
competitive-intelligence APIs can replace individual estimators later
without changing the COMPETITION_PROFILE_FIELDS contract.
"""

from __future__ import annotations

import hashlib

from services.market_intelligence.models import COMPETITION_PROFILE_FIELDS  # noqa: F401
from services.trends.models import Trend


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _seed(trend: Trend) -> float:
    """Stable 0-1 jitter per topic so estimates vary realistically but
    deterministically across topics."""
    digest = hashlib.md5(trend.topic.lower().encode("utf-8")).hexdigest()
    return int(digest[:6], 16) / 0xFFFFFF


def _demand(trend: Trend) -> float:
    """0-1 normalized demand from search volume (log-ish saturation)."""
    return _clamp(trend.search_volume / 1_000_000.0, 0.0, 1.0) ** 0.5


def analyze_competition(trend: Trend, calibration: "dict | None" = None) -> dict:
    """One COMPETITION_PROFILE_FIELDS dict per trend. Pure and deterministic."""
    calibration_factor = float((calibration or {}).get("competition_calibration", 1.0))
    saturation = _clamp(trend.competition, 0.0, 1.0)
    demand = _demand(trend)
    jitter = _seed(trend)

    # Crowded markets publish more; velocity adds recency pressure.
    publishing_frequency = round(2 + saturation * 40 + trend.velocity * 8 + jitter * 4, 1)

    # Typical performance in the niche: crowded markets fragment views;
    # high demand lifts the ceiling.
    average_views = int(round(
        (5_000 + demand * 400_000) * (1.0 - 0.55 * saturation) * (0.9 + 0.2 * jitter)
    ))
    average_engagement = round(_clamp(6.5 - 3.5 * saturation + 1.5 * trend.velocity, 0.5, 10.0), 2)
    average_retention = round(_clamp(65 - 20 * saturation + 8 * trend.freshness, 20, 95), 1)
    average_ctr = round(_clamp(5.5 - 2.5 * saturation + 1.2 * trend.velocity, 0.5, 12.0), 2)

    # Breaking in is hard when the market is saturated AND demand is soft.
    market_difficulty = int(round(_clamp(
        (0.6 * saturation + 0.25 * (1.0 - demand) + 0.15 * (1.0 - trend.freshness))
        * 100 * calibration_factor,
        0, 100,
    )))

    # The strategic prize: demand the current supply is not meeting.
    content_gap_score = int(round(_clamp(
        (0.5 * demand + 0.3 * (1.0 - saturation) + 0.2 * trend.velocity) * 100
        / calibration_factor if calibration_factor else 0,
        0, 100,
    )))

    return {
        "publishing_frequency": publishing_frequency,
        "creator_saturation": round(saturation, 2),
        "average_views": average_views,
        "average_engagement": average_engagement,
        "average_retention": average_retention,
        "average_ctr": average_ctr,
        "market_difficulty": market_difficulty,
        "content_gap_score": content_gap_score,
    }


def competition_level(profile: dict) -> str:
    """low | medium | high from the market difficulty estimate."""
    difficulty = profile.get("market_difficulty", 50)
    if difficulty < 35:
        return "low"
    if difficulty < 65:
        return "medium"
    return "high"
