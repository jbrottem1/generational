"""Continuous Learning Dashboard — auto-updating performance intelligence."""

from __future__ import annotations

from typing import Any

from services.analytics.store import get_analytics_store
from services.learning.experiments import get_experiment_manager
from services.learning.graph import get_knowledge_graph
from services.learning.memory import get_memory
from services.learning.patterns import best_performers, mine_patterns, worst_performers
from services.learning.productions import get_production_memory
from services.learning.recommendations import build_recommendations
from services.learning.reports import build_performance_report


def build_learning_dashboard() -> dict[str, Any]:
    """Data payload for the Continuous Learning Dashboard UI."""
    records = get_analytics_store().list_records()
    insights = mine_patterns(records)
    recommendations = build_recommendations(insights)
    productions = get_production_memory().list_records(limit=100)
    report = build_performance_report(records, period="weekly") if records else {}
    memory = get_memory().counts_by_category()
    graph = get_knowledge_graph().snapshot()
    experiments = get_experiment_manager().list_experiments()

    def _top_dim(dimension: str, *, positive: bool = True, limit: int = 5) -> list[dict]:
        rows = [i for i in insights if i.get("dimension") == dimension]
        rows = [i for i in rows if (i.get("lift") or 0) > 0] if positive else [i for i in rows if (i.get("lift") or 0) < 0]
        rows.sort(key=lambda i: (i.get("confidence") or 0, abs(i.get("lift") or 0)), reverse=True)
        return [
            {"value": i.get("value"), "lift": i.get("lift"), "confidence": i.get("confidence"), "samples": i.get("samples")}
            for i in rows[:limit]
        ]

    # Highest CTR / retention from metrics
    with_metrics = [r for r in records if isinstance(r.get("metrics"), dict)]
    by_ctr = sorted(with_metrics, key=lambda r: float((r.get("metrics") or {}).get("ctr") or 0), reverse=True)
    by_ret = sorted(
        with_metrics,
        key=lambda r: float((r.get("metrics") or {}).get("audience_retention") or 0),
        reverse=True,
    )
    by_eng = sorted(
        with_metrics,
        key=lambda r: float((r.get("metrics") or {}).get("likes") or 0)
        + float((r.get("metrics") or {}).get("comments") or 0)
        + float((r.get("metrics") or {}).get("shares") or 0),
        reverse=True,
    )

    viral_queue = [
        {
            "topic": i.get("value"),
            "lift": i.get("lift"),
            "confidence": i.get("confidence"),
            "dimension": i.get("dimension"),
        }
        for i in insights
        if i.get("dimension") in ("topic", "niche") and (i.get("lift") or 0) > 0
    ][:15]

    return {
        "generated_at": report.get("generated_at") if isinstance(report, dict) else None,
        "productions_recorded": get_production_memory().count(),
        "analytics_records": len(records),
        "memory": memory,
        "knowledge_graph": graph,
        "experiments": {
            "total": len(experiments),
            "running": sum(1 for e in experiments if e.get("status") == "running"),
            "completed": sum(1 for e in experiments if e.get("status") == "completed"),
        },
        "top_performing_topics": _top_dim("topic"),
        "fastest_growing_niches": _top_dim("niche"),
        "highest_ctr": [
            {
                "title": r.get("title"),
                "topic": r.get("topic"),
                "ctr": (r.get("metrics") or {}).get("ctr"),
                "views": (r.get("metrics") or {}).get("views"),
            }
            for r in by_ctr[:5]
        ],
        "highest_retention": [
            {
                "title": r.get("title"),
                "topic": r.get("topic"),
                "audience_retention": (r.get("metrics") or {}).get("audience_retention"),
            }
            for r in by_ret[:5]
        ],
        "best_thumbnail_styles": _top_dim("thumbnail_version"),
        "best_hooks": _top_dim("hook"),
        "best_narration_style": _top_dim("voice_version"),
        "best_animation_style": _top_dim("length_bucket"),  # proxy until camera dim mined
        "highest_engagement": [
            {
                "title": r.get("title"),
                "likes": (r.get("metrics") or {}).get("likes"),
                "comments": (r.get("metrics") or {}).get("comments"),
                "shares": (r.get("metrics") or {}).get("shares"),
            }
            for r in by_eng[:5]
        ],
        "worst_performing_videos": [
            {"title": r.get("title") or r.get("value"), "topic": r.get("topic") or r.get("value"), "hook": r.get("value")}
            for r in worst_performers(records, "hook", limit=5)
        ],
        "best_performing_videos": [
            {"title": r.get("title") or r.get("value"), "topic": r.get("topic") or r.get("value"), "hook": r.get("value")}
            for r in best_performers(records, "hook", limit=5)
        ],
        "suggested_improvements": [r.get("action") for r in recommendations[:12] if r.get("action")],
        "trending_opportunities": (report.get("trending_opportunities") if isinstance(report, dict) else None)
        or _top_dim("niche"),
        "viral_opportunity_queue": viral_queue,
        "recent_productions": [
            {
                "topic": p.get("topic"),
                "qa_score": p.get("qa_score"),
                "platform": p.get("platform"),
                "date": p.get("date"),
            }
            for p in productions[:10]
        ],
        "recommendations_count": len(recommendations),
        "insights_count": len(insights),
    }
