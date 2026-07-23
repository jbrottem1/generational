"""Opportunity scoring — weighted Overall Opportunity Score (0–100)."""

from __future__ import annotations

import math
import re
from typing import Any

from services.trend_opportunity.models import SCORE_DIMENSIONS, SCORE_WEIGHTS


def _clamp(v: float) -> float:
    return max(0.0, min(100.0, float(v)))


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", (text or "").lower()) if len(t) > 2}


_CURIOSITY = ("why", "how", "secret", "myth", "actually", "nobody", "shocking", "hidden", "wrong", "truth")
_EDU = ("explained", "science", "biology", "physics", "chemistry", "brain", "space", "history", "learn")
_EMO = ("amazing", "terrifying", "beautiful", "deadly", "incredible", "mind", "crazy", "surprising")


def score_opportunity_card(
    topic: str,
    *,
    category: str = "science",
    source_signals: dict[str, Any] | None = None,
    discovery_item: dict[str, Any] | None = None,
    audience_intel: dict[str, Any] | None = None,
    historical_performance: float = 0.5,
    production_count: int = 0,
) -> dict[str, Any]:
    """Evaluate one topic across mission dimensions. Composes discovery/AI when present."""
    signals = dict(source_signals or {})
    item = dict(discovery_item or {})
    ai = dict(audience_intel or {})
    factors = dict(item.get("factors") or {})
    brief = dict(item.get("production_brief") or {})
    psych = dict(ai.get("psychological_drivers") or {})
    eng = dict(ai.get("engagement") or {})

    search_volume = int(item.get("estimated_audience") or signals.get("search_volume") or 0)
    demand = _clamp(math.log10(search_volume) * 100 / 7) if search_volume > 0 else float(factors.get("search_demand") or 40)

    velocity = float(item.get("growth_rate") or signals.get("growth_pct") or 0)
    trend_vel = _clamp(0.55 * min(abs(velocity), 200) / 2 + 0.45 * float(factors.get("growth_velocity") or 50))

    competition_raw = float(item.get("competition") if item.get("competition") is not None else signals.get("competition") or 0.5)
    # Mission competition_score = openness (higher better)
    competition_score = _clamp((1.0 - competition_raw) * 100)
    if float(factors.get("competition_openness") or 0):
        competition_score = _clamp(0.5 * competition_score + 0.5 * float(factors["competition_openness"]))

    evergreen = float(factors.get("longevity") or brief.get("evergreen_score") or (85 if category == "science" else 55))
    blob = topic.lower()
    curiosity = float(psych.get("curiosity_potential") or 0)
    if not curiosity:
        curiosity = 45 + 10 * sum(1 for w in _CURIOSITY if w in blob)
    emotional = float(psych.get("emotional_intensity") or 0) or (40 + 8 * sum(1 for w in _EMO if w in blob))
    educational = float(psych.get("educational_value") or factors.get("educational_value") or 0)
    if not educational:
        educational = 50 + 8 * sum(1 for w in _EDU if w in blob)
        if category in ("science", "education", "psychology", "space"):
            educational = max(educational, 72)

    shareability = float(eng.get("shareability") or factors.get("virality_potential") or 55)
    visual = float(factors.get("visual_asset_readiness") or brief.get("visual_potential") or 60)
    if any(w in blob for w in ("ocean", "space", "animal", "planet", "cell", "heart", "volcano")):
        visual = max(visual, 75)
    thumbnail = float((ai.get("creative") or {}).get("thumbnail_score") or 0) or min(100, visual * 0.85 + curiosity * 0.15)
    audience_size = demand
    platform_fit = 88.0 if category in ("science", "education") else 70.0
    if str(item.get("recommended_video_type") or "short") == "short":
        platform_fit = min(100, platform_fit + 5)

    difficulty_ease = float(factors.get("content_difficulty") or 60)  # higher in trends scorer = easier
    # Mission production_difficulty: higher = harder (invert for analysis display)
    production_difficulty = _clamp(100 - difficulty_ease)
    revenue = _clamp(
        0.4 * float(brief.get("monetization") or (65 if category == "science" else 50))
        + 0.3 * audience_size
        + 0.3 * evergreen
    )

    # Historical / overproduction dampening
    hist_boost = _clamp(historical_performance * 100)
    overprod_penalty = min(35, production_count * 12)

    trend_score = _clamp(0.45 * demand + 0.45 * trend_vel + 0.1 * hist_boost)
    curiosity_score = _clamp(curiosity)
    educational_score = _clamp(educational)
    retention_potential = _clamp(
        0.35 * curiosity_score
        + 0.25 * educational_score
        + 0.2 * float(eng.get("retention_probability") or 55)
        + 0.2 * evergreen
    )
    visual_score = _clamp(visual)
    thumbnail_score = _clamp(thumbnail)
    platform_score = _clamp(platform_fit)
    revenue_score = _clamp(revenue - overprod_penalty * 0.3)

    dims = {
        "trend_score": round(trend_score, 1),
        "curiosity_score": round(curiosity_score, 1),
        "educational_score": round(educational_score, 1),
        "retention_potential": round(retention_potential, 1),
        "competition_score": round(competition_score, 1),
        "visual_score": round(visual_score, 1),
        "thumbnail_score": round(thumbnail_score, 1),
        "platform_score": round(platform_score, 1),
        "revenue_score": round(revenue_score, 1),
    }
    overall = sum(dims[k] * SCORE_WEIGHTS[k] for k in SCORE_DIMENSIONS)
    overall = _clamp(overall - overprod_penalty * 0.5)

    analysis = {
        "search_demand": round(demand, 1),
        "trend_velocity": round(trend_vel, 1),
        "competition": round(competition_raw * 100, 1),
        "evergreen_potential": round(evergreen, 1),
        "curiosity_gap": round(curiosity_score, 1),
        "emotional_impact": round(emotional, 1),
        "educational_value": round(educational_score, 1),
        "shareability": round(shareability, 1),
        "visual_potential": round(visual_score, 1),
        "thumbnail_potential": round(thumbnail_score, 1),
        "audience_size": round(audience_size, 1),
        "platform_fit": round(platform_score, 1),
        "production_difficulty": round(production_difficulty, 1),
        "revenue_potential": round(revenue_score, 1),
    }

    return {
        "scores": dims,
        "overall_opportunity_score": round(overall, 1),
        "analysis": analysis,
        "overproduction_penalty": overprod_penalty,
        "historical_performance": historical_performance,
    }
