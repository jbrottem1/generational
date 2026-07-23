"""Pre-production learning consult — learn before you create.

Searches historical productions, compares winners vs losers, and builds a
learning_brief + recommendations for every downstream engine.
"""

from __future__ import annotations

from typing import Any

from services.analytics.store import get_analytics_store
from services.learning.graph import get_knowledge_graph
from services.learning.patterns import best_performers, mine_patterns, worst_performers
from services.learning.predictions import predict_performance
from services.learning.productions import get_production_memory
from services.learning.recommendations import (
    build_recommendations,
    guidance_for_engine,
    recommendations_by_engine,
)


def build_learning_brief(
    topic: str,
    *,
    niche: str = "",
    platform: str = "youtube_shorts",
    runtime_sec: int = 60,
    context: dict | None = None,
) -> dict[str, Any]:
    """Full pre-production improvement packet."""
    context = context or {}
    memory = get_production_memory()
    similar = memory.find_similar(topic, limit=12)
    records = get_analytics_store().list_records()
    insights = mine_patterns(records)
    recommendations = build_recommendations(insights)
    by_engine = recommendations_by_engine(recommendations)

    highs = [r for r in similar if int(r.get("qa_score") or 0) >= 90]
    lows = [r for r in similar if int(r.get("qa_score") or 0) and int(r.get("qa_score") or 0) < 75]
    if not highs:
        highs = best_performers(records, "hook", limit=5)
    if not lows:
        lows = worst_performers(records, "hook", limit=5)

    improvements: list[str] = []
    for rec in recommendations[:12]:
        if rec.get("evidence", {}).get("lift", 0) > 0:
            improvements.append(rec.get("action") or "")
        else:
            improvements.append(rec.get("action") or "")
    improvements = [i for i in improvements if i][:15]

    # Engine-specific guidance pack
    engine_guidance = {
        key: guidance_for_engine(key, recommendations)
        for key in (
            "psychology",
            "script_generation",
            "visual_intelligence",
            "voice_audio",
            "seo_optimization",
            "trend_discovery",
            "cinematography",
            "viewer_retention",
            "studio_render",
            "optimization_lab",
            "evidence_intelligence",
            "discovery",
        )
    }

    prediction = predict_performance(
        topic=topic,
        niche=niche or str(context.get("niche") or ""),
        platform=platform,
        runtime_sec=runtime_sec,
        psychology_score=context.get("psychology_score"),
        seo_score=context.get("seo_score"),
        qa_score=context.get("qa_score"),
    )

    graph = get_knowledge_graph().snapshot()

    brief = {
        "topic": topic,
        "niche": niche,
        "platform": platform,
        "runtime_sec": runtime_sec,
        "similar_productions": [
            {
                "topic": r.get("topic"),
                "qa_score": r.get("qa_score"),
                "platform": r.get("platform"),
                "psychology_score": r.get("psychology_score"),
                "visual_score": r.get("visual_score"),
            }
            for r in similar[:8]
        ],
        "high_performers": _summarize_items(highs[:5]),
        "low_performers": _summarize_items(lows[:5]),
        "suggested_improvements": improvements,
        "engine_guidance": engine_guidance,
        "predictions": prediction,
        "knowledge_graph": graph,
        "insights_count": len(insights),
        "recommendations_count": len(recommendations),
        "status": "ready" if (similar or recommendations or records) else "cold_start",
    }
    return brief


def consult_context(
    topic: str,
    *,
    niche: str = "",
    platform: str = "youtube_shorts",
    runtime_sec: int = 60,
    context: dict | None = None,
) -> dict[str, Any]:
    """Context keys to merge before psychology / script generation."""
    brief = build_learning_brief(
        topic,
        niche=niche,
        platform=platform,
        runtime_sec=runtime_sec,
        context=context,
    )
    records = get_analytics_store().list_records()
    recommendations = build_recommendations(mine_patterns(records))
    return {
        "learning_brief": brief,
        "learning_recommendations": recommendations_by_engine(recommendations),
        "learning_predictions": brief.get("predictions"),
        "learning_consulted": True,
        "suggested_improvements": brief.get("suggested_improvements") or [],
    }


def _summarize_items(items: list) -> list[dict]:
    out = []
    for item in items:
        if not isinstance(item, dict):
            continue
        metrics = item.get("metrics") if isinstance(item.get("metrics"), dict) else {}
        out.append(
            {
                "topic": item.get("topic") or item.get("title") or item.get("value"),
                "title": item.get("title") or item.get("example_titles", [None])[0] if item.get("example_titles") else item.get("title"),
                "hook": item.get("hook") or (item.get("value") if item.get("dimension") == "hook" else None),
                "qa_score": item.get("qa_score") or item.get("quality_score") or item.get("average_score"),
                "views": metrics.get("views"),
                "ctr": metrics.get("ctr"),
                "platform": item.get("platform"),
                "psychology_strategy": item.get("psychology_strategy"),
                "lift": item.get("lift"),
            }
        )
    return out
