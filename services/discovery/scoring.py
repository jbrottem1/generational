"""Educational trust scoring — Generational discovery ranking.

Extends Agent 1 opportunity scores with mission-critical factors:
educational value, brand alignment, factual confidence, visual assets,
geographic reach, and longevity. Clicks alone never win.
"""

from __future__ import annotations

from services.discovery.models import DiscoveryScore
from services.trends.models import Opportunity, Trend
from services.trends.scorer import EVERGREEN_CATEGORIES, score_opportunity

# Mission-weighted blend — trust + education outweigh pure virality.
DISCOVERY_WEIGHTS = {
    "search_demand": 0.11,
    "growth_velocity": 0.10,
    "audience_engagement": 0.08,
    "geographic_reach": 0.05,
    "longevity": 0.10,
    "educational_value": 0.14,
    "virality_potential": 0.08,
    "brand_alignment": 0.12,
    "factual_confidence": 0.12,
    "visual_asset_readiness": 0.06,
    "competition_openness": 0.04,
}

BRAND_ALIGNED_CATEGORIES = {
    "science": 0.95,
    "psychology": 0.92,
    "education": 0.95,
    "space": 0.90,
    "health": 0.82,
    "history": 0.88,
    "technology": 0.78,
    "finance": 0.55,
    "news": 0.45,
    "entertainment": 0.35,
    "general": 0.55,
}

EDUCATIONAL_CATEGORIES = {
    "science": 0.95,
    "education": 0.98,
    "psychology": 0.90,
    "history": 0.88,
    "space": 0.90,
    "health": 0.80,
    "technology": 0.75,
    "finance": 0.60,
    "news": 0.40,
    "entertainment": 0.30,
    "general": 0.50,
}

# Keywords that signal teachable, explainable topics.
_EDU_CUES = (
    "explained", "science", "why", "how", "myth", "origin", "evolution",
    "brain", "cell", "physics", "biology", "chemistry", "history", "fossil",
)


def _clamp100(value: float) -> int:
    return max(0, min(100, int(round(value))))


def _educational_value(trend: Trend) -> int:
    cat = EDUCATIONAL_CATEGORIES.get(trend.category.lower(), 0.5)
    blob = f"{trend.topic} {' '.join(trend.keywords)}".lower()
    cue_hits = sum(1 for c in _EDU_CUES if c in blob)
    return _clamp100(cat * 75 + min(cue_hits, 4) * 6)


def _brand_alignment(trend: Trend) -> int:
    return _clamp100(BRAND_ALIGNED_CATEGORIES.get(trend.category.lower(), 0.5) * 100)


def _factual_confidence(trend: Trend, *, verification_confidence: float | None = None) -> int:
    base = trend.confidence
    if verification_confidence is not None:
        base = 0.45 * base + 0.55 * verification_confidence
    # News/entertainment start lower until verified
    if trend.category.lower() in ("news", "entertainment"):
        base *= 0.85
    return _clamp100(base * 100)


def _visual_asset_readiness(trend: Trend, *, asset_score: float | None = None) -> int:
    if asset_score is not None:
        return _clamp100(asset_score * 100)
    # Heuristic: science/nature topics usually have Wikimedia/reality assets
    cat = trend.category.lower()
    prior = {
        "science": 0.8,
        "space": 0.85,
        "history": 0.7,
        "biology": 0.8,
        "health": 0.65,
        "psychology": 0.55,
        "technology": 0.6,
        "news": 0.45,
        "general": 0.5,
    }.get(cat, 0.5)
    return _clamp100(prior * 100)


def _geographic_reach(trend: Trend) -> int:
    # English + high confidence ≈ broader international Shorts reach
    lang = 0.75 if trend.language.lower() == "en" else 0.45
    return _clamp100((0.55 * lang + 0.45 * trend.confidence) * 100)


def score_discovery_opportunity(
    trend: Trend,
    *,
    historical_performance: float = 0.5,
    verification_confidence: float | None = None,
    visual_asset_score: float | None = None,
) -> tuple[Opportunity, DiscoveryScore]:
    """Return base Opportunity plus Generational discovery score."""
    base = score_opportunity(trend, historical_performance=historical_performance)
    factors = base.factors
    discovery = DiscoveryScore(
        search_demand=int(factors.get("search_demand", 0)),
        growth_velocity=int(factors.get("growth_velocity", 0)),
        audience_engagement=int(factors.get("audience_size", 0)),
        geographic_reach=_geographic_reach(trend),
        longevity=int(factors.get("evergreen_potential", EVERGREEN_CATEGORIES.get(trend.category.lower(), 0.5) * 100)),
        educational_value=_educational_value(trend),
        virality_potential=int(factors.get("virality_potential", 0)),
        brand_alignment=_brand_alignment(trend),
        factual_confidence=_factual_confidence(trend, verification_confidence=verification_confidence),
        visual_asset_readiness=_visual_asset_readiness(trend, asset_score=visual_asset_score),
        competition_openness=int(factors.get("competition", 0)),
    )
    weighted = sum(
        DISCOVERY_WEIGHTS[name] * getattr(discovery, name)
        for name in DISCOVERY_WEIGHTS
    )
    # Factual confidence is a hard discount — never boost rumors
    discovery.total = _clamp100(weighted * (0.65 + 0.35 * (discovery.factual_confidence / 100)))
    return base, discovery


def rank_discovery_opportunities(
    trends: list[Trend],
    *,
    historical_performance: float = 0.5,
    top_n: int | None = None,
) -> list[tuple[Opportunity, DiscoveryScore]]:
    ranked = [
        score_discovery_opportunity(t, historical_performance=historical_performance)
        for t in trends
    ]
    ranked.sort(key=lambda pair: (pair[1].total, pair[0].opportunity_score, pair[0].trend.confidence), reverse=True)
    return ranked[:top_n] if top_n else ranked
