"""The learning loop — historical records in, cumulative intelligence out.

One call (`run_learning(context)`) does the whole feedback cycle:

1. Load ALL historical analytics records (the store is cumulative).
2. Mine patterns → insights with confidence scores.
3. Build per-engine recommendations (the feedback loop).
4. Grow long-term memory (append-only; duplicates of already-known
   strategies are skipped, existing knowledge is never overwritten).
5. Write `learning_metadata` into every item in the context (Agent 9's
   ContentPackage slot) and return the learning report + the
   `learning_recommendations` context key.
"""

from __future__ import annotations

from datetime import datetime, timezone

from core.log import get_logger, log_event
from services.analytics.models import LEARNING_ENGINE_VERSION
from services.analytics.store import get_analytics_store
from services.learning.memory import MEMORY_CATEGORY, HistoricalMemory, get_memory
from services.learning.models import (
    FAILURE_SCORE_THRESHOLD,
    LEARNING_REPORT_VERSION,
    SUCCESS_SCORE_THRESHOLD,
)
from services.learning.patterns import mine_patterns, platform_breakdown
from services.learning.recommendations import (
    build_recommendations,
    recommendations_by_engine,
)

logger = get_logger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ------------------------------------------------------------------ memory


def _already_known(memory: HistoricalMemory, category: str, dimension: str, value: str) -> bool:
    """Whether this exact strategy observation is already remembered —
    keeps the append-only memory cumulative without endless duplicates."""
    for entry in memory.recall(category):
        content = entry.get("content", {})
        if isinstance(content, dict) and content.get("dimension") == dimension and content.get("value") == value:
            return True
    return False


def grow_memory(insights: list, memory: "HistoricalMemory | None" = None) -> int:
    """Persist newly-confirmed strategies into long-term memory.

    Winners (average score above the success threshold) become
    successful strategies; confirmed losers become failed strategies;
    platform patterns, recurring topics, and audience preferences land in
    their own categories. Returns the number of entries added.
    """
    memory = memory or get_memory()
    added = 0
    for insight in insights:
        if insight["samples"] < 2:
            continue

        category = ""
        if insight["dimension"] == "platform":
            category = MEMORY_CATEGORY.PLATFORM_TRENDS
        elif insight["dimension"] in ("length_bucket", "posting_hour"):
            category = MEMORY_CATEGORY.AUDIENCE_PREFERENCES
        elif insight["dimension"] in ("topic", "niche") and insight["average_score"] >= SUCCESS_SCORE_THRESHOLD:
            category = MEMORY_CATEGORY.EVERGREEN_CONTENT
        elif insight["average_score"] >= SUCCESS_SCORE_THRESHOLD and insight["lift"] > 0:
            category = MEMORY_CATEGORY.SUCCESSFUL_STRATEGIES
        elif insight["average_score"] <= FAILURE_SCORE_THRESHOLD and insight["lift"] < 0:
            category = MEMORY_CATEGORY.FAILED_STRATEGIES
        if not category:
            continue

        if _already_known(memory, category, insight["dimension"], insight["value"]):
            continue
        memory.remember(
            category,
            {"dimension": insight["dimension"], "value": insight["value"]},
            confidence=insight["confidence"],
            evidence={
                "samples": insight["samples"],
                "average_score": insight["average_score"],
                "baseline_score": insight["baseline_score"],
                "lift": insight["lift"],
            },
            source="learning",
        )
        added += 1
    return added


# ------------------------------------------------------------ per-item slot


def _item_signals(item: dict, insights: list, limit: int = 5) -> list:
    """Insights that touch this item's own attributes (its hook, topic,
    platform, psychology strategy, ...)."""
    own_values = {
        str(item.get("hook", "")),
        str(item.get("topic", "")),
        str(item.get("niche", "")),
        str(item.get("title", "")),
    }
    own_values.update(str(v) for v in (item.get("psychology_strategy") or []))
    own_values.update(str(p) for p in (item.get("target_platforms") or item.get("platforms") or []))
    own_values.discard("")
    return [i for i in insights if i["value"] in own_values][:limit]


def build_learning_metadata(
    item: dict,
    insights: list,
    recommendations: list,
    knowledge_size: int,
) -> dict:
    """The ContentPackage `learning_metadata` slot value for one item."""
    signals = _item_signals(item, insights)
    top = recommendations[:5]
    confidences = [r["confidence"] for r in top]
    return {
        "engine_version": LEARNING_ENGINE_VERSION,
        "status": "learned" if insights else "insufficient_data",
        "signals": signals,
        "recommendations": top,
        "knowledge_size": knowledge_size,
        "confidence": int(round(sum(confidences) / len(confidences))) if confidences else 0,
        "generated_at": _now_iso(),
    }


# -------------------------------------------------------------- stage logic


def collect_learning_items(context: dict) -> "tuple[list, str]":
    """Items whose `learning_metadata` slot this run should fill,
    preferring canonical ContentPackage dicts (same collection order as
    the SEO and Publishing engines)."""
    packages = context.get("unified_packages") or []
    if packages:
        return list(packages), "unified_packages"
    for key in ("ideas", "selected_ideas"):
        items = context.get(key) or []
        if items:
            return list(items), key
    return [], ""


def run_learning(context: dict, memory: "HistoricalMemory | None" = None) -> dict:
    """The full learning cycle over ALL historical records. Returns the
    context updates (`learning_report`, `learning_recommendations`)."""
    records = get_analytics_store().list_records()
    insights = mine_patterns(records)
    recommendations = build_recommendations(insights)
    memory_added = grow_memory(insights, memory=memory) if insights else 0

    # Permanent production archive + knowledge graph expansion
    from services.learning.graph import get_knowledge_graph
    from services.learning.productions import record_productions_from_context

    saved = record_productions_from_context(
        context,
        pipeline_used=str(context.get("pipeline_used") or context.get("workflow") or "intelligence"),
        run_id=str(context.get("executive_run_id") or context.get("run_id") or ""),
    )
    graph = get_knowledge_graph()
    for prod in saved:
        graph.expand_from_production(prod)
    for insight in insights[:40]:
        graph.expand_from_insight(insight)

    # Bridge PQA predicted vs actual when analytics metrics exist
    try:
        from services.production_qa.learning import record_performance_feedback

        for item in (
            context.get("selected_ideas")
            or context.get("ideas")
            or context.get("candidates")
            or []
        ):
            if not isinstance(item, dict):
                continue
            idea_id = str(item.get("id") or item.get("idea_id") or "")
            metrics = item.get("analytics_metrics") or (item.get("analytics_package") or {}).get("metrics")
            if idea_id and isinstance(metrics, dict) and metrics:
                record_performance_feedback(idea_id, metrics, persist=True)
    except Exception:
        pass

    items, source_key = collect_learning_items(context)
    for item in items:
        item["learning_metadata"] = build_learning_metadata(
            item, insights, recommendations, knowledge_size=len(records)
        )

    confidences = [r["confidence"] for r in recommendations]
    report = {
        "report_version": LEARNING_REPORT_VERSION,
        "engine_version": LEARNING_ENGINE_VERSION,
        "status": "learned" if insights else "insufficient_data",
        "records_analyzed": len(records),
        "insights": insights[:25],
        "recommendations": recommendations,
        "platform_breakdown": platform_breakdown(records),
        "memory_entries_added": memory_added,
        "productions_recorded": len(saved),
        "knowledge_graph": graph.snapshot(),
        "confidence": int(round(sum(confidences) / len(confidences))) if confidences else 0,
        "generated_at": _now_iso(),
    }

    log_event(
        logger, "learning.completed",
        records=len(records), insights=len(insights),
        recommendations=len(recommendations), memory_added=memory_added,
        productions=len(saved),
        items=len(items), source=source_key or "none",
    )

    updates = {
        "learning_report": report,
        "learning_recommendations": recommendations_by_engine(recommendations),
        "production_memory_count": len(saved),
    }
    if source_key:
        updates[source_key] = context.get(source_key, [])
    return updates
