"""Scoring engine — configurable weighted scoring and ranking of variants.

Every variant is scored across the fourteen SCORING_INPUTS dimensions
(psychology, virality, SEO, trend, historical performance, brand fit,
audience match, retention/CTR/engagement/revenue predictions, generation
confidence, platform suitability, localization suitability) and blended
into one 0-100 composite through `weighted_blend` — the same
many-dimensions-to-one-score formula every scoring engine shares.

Weights are data (`OptimizationConfig.scoring_weights`), not code: the
Learning Engine or an operator retunes them via `configure()` without
touching this module. The laboratory only READS upstream scores already
present on the item — it never recomputes or modifies another engine's
output.
"""

from __future__ import annotations

from engines.heuristics import clamp, count_hits, stable_jitter, weighted_blend
from services.optimization.config import get_optimization_config
from services.optimization.models import SCORING_INPUTS
from services.optimization.predictions import get_prediction_model


def _content_text(variant: dict) -> str:
    content = variant.get("content", "")
    if isinstance(content, dict):
        return " ".join(str(v) for v in content.values())
    return str(content)


def _upstream_score(item: dict, *keys, default: int = 50) -> int:
    """The first upstream 0-100 signal present on the item."""
    for key in keys:
        value = item.get(key)
        if value:
            return clamp(float(value), low=0, high=100)
    return default


def _brand_fit(variant: dict, item: dict) -> int:
    """How consistent the variant is with the item's brand vocabulary."""
    brand_terms = [str(item.get("brand", "")), str(item.get("niche", "")), str(item.get("topic", ""))]
    brand_terms = [t for t in brand_terms if t]
    if not brand_terms:
        return 55
    hits = count_hits(_content_text(variant).lower(), [t.lower() for t in brand_terms])
    return clamp(50 + hits * 15)


def _audience_match(variant: dict, item: dict) -> int:
    """Overlap between the variant and what the audience already responds
    to (item keywords stand in for audience interest signals)."""
    keywords = [str(k).lower() for k in (item.get("keywords") or [])][:8]
    if not keywords:
        return 55
    hits = count_hits(_content_text(variant).lower(), keywords)
    return clamp(48 + hits * 12)


def _platform_suitability(variant: dict, item: dict) -> int:
    """Fit for the target platform: short punchy content suits short-form."""
    platforms = item.get("target_platforms") or item.get("platforms") or []
    text = _content_text(variant)
    words = len(text.split())
    score = 60
    metadata_platform = str(variant.get("metadata", {}).get("platform", ""))
    if metadata_platform and platforms and metadata_platform in [str(p) for p in platforms]:
        score += 20
    short_form = any("short" in str(p) or str(p) in ("tiktok", "instagram") for p in platforms)
    if short_form and isinstance(variant.get("content"), str):
        score += 10 if words <= 14 else -min((words - 14) * 2, 20)
    return clamp(score)


def _localization_suitability(variant: dict, item: dict) -> int:
    """Penalize idioms/wordplay that translate poorly; reward plain phrasing."""
    text = _content_text(variant).lower()
    idioms = ["nobody tells you", "don't have to", "so you don't", "vs.", "#1", "insiders"]
    penalty = count_hits(text, idioms) * 6
    language = str(variant.get("metadata", {}).get("language", ""))
    bonus = 12 if language and language != str(item.get("target_language", "en")) else 0
    return clamp(62 - penalty + bonus)


def score_variant(
    variant: dict,
    item: "dict | None" = None,
    context: "dict | None" = None,
    historical_priors: "dict | None" = None,
    weights: "dict | None" = None,
) -> dict:
    """Score one variant in place: per-input breakdown + weighted composite.

    `historical_priors` (label/value → 0-100 prior score, from the learning
    bridge) supplies the historical_performance dimension; without history
    it stays a neutral 50 so cold starts rank purely on prediction.
    """
    item = item or {}
    context = context or {}
    config = get_optimization_config()
    weights = weights or config.scoring_weights

    predictions = get_prediction_model().predict(variant, item=item, context=context)

    priors = historical_priors or {}
    prior = priors.get(variant.get("label", ""), priors.get(_content_text(variant), 50))

    breakdown = {
        "psychology": _upstream_score(item, "psychology_score"),
        "virality": _upstream_score(item, "virality_score", "viral_score"),
        "seo": _upstream_score(item, "seo_score"),
        "trend": _upstream_score(item, "trend_score", "opportunity_score"),
        "historical_performance": clamp(float(prior), low=0, high=100),
        "brand_fit": _brand_fit(variant, item),
        "audience_match": _audience_match(variant, item),
        "retention_prediction": predictions["retention_prediction"],
        "ctr_prediction": predictions["ctr_prediction"],
        "engagement_prediction": predictions["engagement_prediction"],
        "revenue_prediction": predictions["revenue_prediction"],
        "confidence": clamp(float(variant.get("confidence", 50)), low=0, high=100),
        "platform_suitability": _platform_suitability(variant, item),
        "localization_suitability": _localization_suitability(variant, item),
    }

    active = {key: weights.get(key, 0.0) for key in SCORING_INPUTS}
    total_weight = sum(active.values()) or 1.0
    normalized = {key: value / total_weight for key, value in active.items()}

    variant["score_breakdown"] = breakdown
    variant["score"] = weighted_blend(breakdown, normalized, low=0, high=100)
    return variant


def rank_variants(
    variants: list,
    item: "dict | None" = None,
    context: "dict | None" = None,
    historical_priors: "dict | None" = None,
) -> list:
    """Score every variant and return them best-first with 1-based ranks.

    Ranking logic is configurable (`OptimizationConfig.ranking_strategy`):
    "score" ranks on the composite alone; "score_with_history" additionally
    blends historical winner priors so past experiment winners rise.
    """
    config = get_optimization_config()
    priors = historical_priors or {}

    for variant in variants:
        score_variant(variant, item=item, context=context, historical_priors=priors)

    def _ranking_key(variant: dict) -> "tuple[float, int]":
        score = float(variant["score"])
        if config.ranking_strategy == "score_with_history" and priors:
            prior = priors.get(variant.get("label", ""), priors.get(_content_text(variant), 50))
            score = (1 - config.history_influence) * score + config.history_influence * float(prior)
        # Deterministic tie-break so equal scores rank stably.
        return (round(score, 4), stable_jitter(variant["variant_id"], span=1000))

    ranked = sorted(variants, key=_ranking_key, reverse=True)
    for position, variant in enumerate(ranked, start=1):
        variant["rank"] = position
    return ranked
