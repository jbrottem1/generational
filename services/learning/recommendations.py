"""Recommendation engine + the feedback interfaces into upstream engines.

Turns mined insights into RECOMMENDATION_FIELDS dicts routed to the
engines that own each decision (psychology, script, visual, voice, SEO,
publishing, trend discovery), each with a confidence score. The
per-engine guidance adapters are the feedback-loop contract: upstream
engines (or the orchestrator context) read them — this module never
imports or calls an engine (Architecture Directive #1).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from services.learning.models import (
    DIMENSION_TARGETS,
    MIN_SAMPLES_FOR_RECOMMENDATION,
    TARGET_ENGINES,
)
from services.learning.patterns import mine_patterns


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


_ACTIONS = {
    "hook": "Prefer hooks in the style of: {value}",
    "psychology_strategy": "Lean on the '{value}' psychological strategy",
    "thumbnail_version": "Reuse the thumbnail style fingerprinted {value}",
    "voice_version": "Reuse the narration/voice style fingerprinted {value}",
    "posting_hour": "Prioritize posting around {value} UTC",
    "platform": "Weight distribution toward {value}",
    "topic": "Produce more content on: {value}",
    "niche": "Invest further in the '{value}' niche",
    "length_bucket": "Target the '{value}' video length range",
    "title": "Model titles on: {value}",
    "keyword": "Keep targeting the keyword '{value}'",
}

_AVOID_ACTIONS = {
    "hook": "Avoid hooks in the style of: {value}",
    "psychology_strategy": "De-prioritize the '{value}' psychological strategy",
    "thumbnail_version": "Retire the thumbnail style fingerprinted {value}",
    "voice_version": "Rework the narration style fingerprinted {value}",
    "posting_hour": "Avoid posting around {value} UTC",
    "platform": "Reduce reliance on {value}",
    "topic": "Reduce output on: {value}",
    "niche": "Reconsider the '{value}' niche",
    "length_bucket": "Move away from the '{value}' video length range",
    "title": "Avoid title patterns like: {value}",
    "keyword": "Drop the underperforming keyword '{value}'",
}


def _recommendation(insight: dict, positive: bool) -> "list[dict]":
    """RECOMMENDATION dicts (one per target engine) from one insight."""
    templates = _ACTIONS if positive else _AVOID_ACTIONS
    action = templates.get(insight["dimension"], "Review attribute {value}").format(
        value=insight["value"]
    )
    return [
        {
            "recommendation_id": f"rec_{uuid.uuid4().hex[:12]}",
            "target_engine": engine,
            "dimension": insight["dimension"],
            "action": action,
            "value": insight["value"],
            "confidence": insight["confidence"],
            "evidence": {
                "samples": insight["samples"],
                "average_score": insight["average_score"],
                "baseline_score": insight["baseline_score"],
                "lift": insight["lift"],
            },
            "generated_at": _now_iso(),
        }
        for engine in DIMENSION_TARGETS.get(insight["dimension"], ())
    ]


def build_recommendations(insights: list, limit_per_dimension: int = 3) -> list:
    """All actionable recommendations from mined insights.

    Positive recommendations come from meaningful winners (lift > 0),
    avoidance recommendations from meaningful losers (lift < 0); values
    without enough samples stay signals, not strategy.
    """
    recommendations = []
    per_dimension: "dict[str, int]" = {}
    for insight in insights:
        if insight["samples"] < MIN_SAMPLES_FOR_RECOMMENDATION or insight["lift"] == 0:
            continue
        taken = per_dimension.get(insight["dimension"], 0)
        if taken >= limit_per_dimension:
            continue
        per_dimension[insight["dimension"]] = taken + 1
        recommendations.extend(_recommendation(insight, positive=insight["lift"] > 0))
    recommendations.sort(key=lambda r: (r["confidence"], abs(r["evidence"]["lift"])), reverse=True)
    return recommendations


def recommendations_by_engine(recommendations: list) -> dict:
    """target_engine → its recommendations — the `learning_recommendations`
    context key shape (every TARGET_ENGINES key always present)."""
    routed = {engine: [] for engine in TARGET_ENGINES}
    for recommendation in recommendations:
        routed.setdefault(recommendation["target_engine"], []).append(recommendation)
    return routed


def recommendations_from_records(records: list) -> "tuple[list, list]":
    """(insights, recommendations) straight from analytics records."""
    insights = mine_patterns(records)
    return insights, build_recommendations(insights)


# ------------------------------------------------- per-engine feedback API
#
# The stable interfaces upstream engines consume. Each returns a guidance
# dict in the vocabulary of the receiving engine; empty structures when
# there is nothing learned yet — callers never need to null-check.


def psychology_guidance(recommendations: list) -> dict:
    """Feedback for the Psychology & Virality Engine."""
    mine = [r for r in recommendations if r["target_engine"] == "psychology"]
    return {
        "preferred_strategies": [
            r["value"] for r in mine
            if r["dimension"] == "psychology_strategy" and r["evidence"]["lift"] > 0
        ],
        "avoided_strategies": [
            r["value"] for r in mine
            if r["dimension"] == "psychology_strategy" and r["evidence"]["lift"] < 0
        ],
        "winning_hooks": [r["value"] for r in mine if r["dimension"] == "hook"],
        "recommendations": mine,
    }


def script_guidance(recommendations: list) -> dict:
    """Feedback for the Script Generation Engine."""
    mine = [r for r in recommendations if r["target_engine"] == "script_generation"]
    return {
        "winning_hooks": [
            r["value"] for r in mine if r["dimension"] == "hook" and r["evidence"]["lift"] > 0
        ],
        "preferred_lengths": [r["value"] for r in mine if r["dimension"] == "length_bucket"],
        "preferred_topics": [r["value"] for r in mine if r["dimension"] == "topic"],
        "recommendations": mine,
    }


def visual_guidance(recommendations: list) -> dict:
    """Feedback for the Visual Intelligence Engine."""
    mine = [r for r in recommendations if r["target_engine"] == "visual_intelligence"]
    return {
        "winning_thumbnail_styles": [
            r["value"] for r in mine
            if r["dimension"] == "thumbnail_version" and r["evidence"]["lift"] > 0
        ],
        "recommendations": mine,
    }


def voice_guidance(recommendations: list) -> dict:
    """Feedback for the Voice & Audio Engine."""
    mine = [r for r in recommendations if r["target_engine"] == "voice_audio"]
    return {
        "winning_voice_styles": [
            r["value"] for r in mine
            if r["dimension"] == "voice_version" and r["evidence"]["lift"] > 0
        ],
        "preferred_lengths": [r["value"] for r in mine if r["dimension"] == "length_bucket"],
        "recommendations": mine,
    }


def seo_guidance(recommendations: list) -> dict:
    """Feedback for the Global Content Optimization (SEO) Engine."""
    mine = [r for r in recommendations if r["target_engine"] == "seo_optimization"]
    return {
        "winning_keywords": [
            r["value"] for r in mine if r["dimension"] == "keyword" and r["evidence"]["lift"] > 0
        ],
        "winning_titles": [
            r["value"] for r in mine if r["dimension"] == "title" and r["evidence"]["lift"] > 0
        ],
        "best_posting_hours": [r["value"] for r in mine if r["dimension"] == "posting_hour"],
        "platform_weights": [r["value"] for r in mine if r["dimension"] == "platform"],
        "recommendations": mine,
    }


ENGINE_GUIDANCE_ADAPTERS = {
    "psychology": psychology_guidance,
    "script_generation": script_guidance,
    "visual_intelligence": visual_guidance,
    "voice_audio": voice_guidance,
    "seo_optimization": seo_guidance,
}


def guidance_for_engine(engine_key: str, recommendations: list) -> dict:
    """One engine's guidance dict (generic routing for engines without a
    dedicated adapter, e.g. publishing / trend_discovery)."""
    adapter = ENGINE_GUIDANCE_ADAPTERS.get(engine_key)
    if adapter:
        return adapter(recommendations)
    mine = [r for r in recommendations if r["target_engine"] == engine_key]
    return {"recommendations": mine}
