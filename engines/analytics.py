"""Analytics Engine — Agent 9's collection stage (key: analytics).

The post-publish measurement stage: consumes finished ContentPackages
(their `publishing_package` jobs carry the `analytics_ref` correlation ids
Agent 7 issued), fetches platform performance metrics through the
`AnalyticsProvider` interface (deterministic mock until real platform APIs
land), writes each ContentPackage `analytics_package` slot, and persists
one structured analytics record per item x platform into the append-only
analytics store — the raw material of the learning loop.

Pipeline position (PIPELINE_SPEC.md):

    Publishing Engine → Analytics Collection → Learning Feedback

Failure policy: analytics NEVER crashes the pipeline. Empty context →
"no_items" summary; unpublished content yields pending records; provider
problems degrade to diagnostics. Ownership rules honored: only the
`analytics_package` / `learning_metadata` slots are written — render, seo,
and publishing slots are read, never mutated.

This module graduates the former planned stub (same key, additive output).
"""

from __future__ import annotations

from datetime import datetime, timezone

from core.log import get_logger, log_event
from engines.contracts import ContractEngine
from services.analytics.collector import collect_analytics
from services.analytics.models import ANALYTICS_ENGINE_VERSION, MetricsStatus
from services.analytics.store import get_analytics_store

logger = get_logger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def collect_analytics_items(context: dict) -> "tuple[list, str]":
    """Items whose analytics this run should collect, preferring canonical
    ContentPackage dicts (same collection order as SEO and Publishing)."""
    packages = context.get("unified_packages") or []
    if packages:
        return list(packages), "unified_packages"
    for key in ("ideas", "selected_ideas"):
        items = context.get(key) or []
        if items:
            return list(items), key
    return [], ""


def _persist_new_records(records: list) -> int:
    """Append collected records to the store, skipping analytics_refs that
    are already recorded — history is cumulative, never duplicated."""
    store = get_analytics_store()
    fresh = [
        record
        for record in records
        if record["metrics_status"] == MetricsStatus.COLLECTED
        and not (record["analytics_ref"] and store.find_by_ref(record["analytics_ref"]))
    ]
    store.add_records(fresh)
    _record_knowledge(fresh)
    return len(fresh)


def _record_knowledge(records: list) -> None:
    """Mirror proven performance into the Knowledge Base PERFORMANCE
    category — the existing `internal_analytics` trend source mines it, so
    the NEXT run's trend discovery automatically weights proven winners.
    A broken Knowledge Base never breaks analytics collection."""
    try:
        from services.analytics.models import performance_score
        from services.knowledge import CATEGORY, get_knowledge_base

        kb = get_knowledge_base()
        for record in records:
            kb.add_entry(
                CATEGORY.PERFORMANCE,
                {
                    "topic": record.get("topic", ""),
                    "title": record.get("title", ""),
                    "hook": record.get("hook", ""),
                    "platform": record.get("platform", ""),
                    "score": performance_score(record.get("metrics", {})),
                    "views": record.get("metrics", {}).get("views", 0),
                },
                metadata={"source": "analytics", "analytics_ref": record.get("analytics_ref", "")},
            )
    except Exception as exc:  # noqa: BLE001 - knowledge mirroring must not break analytics
        log_event(logger, "analytics.knowledge_write_failed", level=30, error=str(exc)[:120])


class AnalyticsEngine(ContractEngine):
    """Agent 9 — platform performance collection (provider-based, mock data)."""

    key = "analytics"
    label = "Analytics"
    icon = "📊"
    description = (
        "Collect post-publish performance metrics per platform, attribute "
        "them to the upstream decisions that produced the content, and "
        "grow the append-only analytics store the Learning Engine mines."
    )
    version = ANALYTICS_ENGINE_VERSION
    input_contract = ["unified_packages"]
    output_contract = ["analytics_summary"]
    dependencies = ["publishing"]
    capabilities = [
        "analytics", "metrics", "attribution", "multi-platform",
        "retention", "engagement", "persistence",
    ]

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        items, source_key = collect_analytics_items(context)

        if not items:
            summary = self._summary([], [], items=0, persisted=0)
            summary["reason"] = "No content in context — nothing to measure."
            return {"analytics_summary": summary, "analytics_records": []}

        records, packages = collect_analytics(items, context)
        persisted = _persist_new_records(records)
        summary = self._summary(records, packages, items=len(items), persisted=persisted)

        log_event(
            logger, "analytics.completed",
            items=len(items), records=len(records),
            collected=summary["collected"], pending=summary["pending"],
            persisted=persisted, source=source_key or "none",
        )

        updates = {
            "analytics_summary": summary,
            "analytics_records": records,
        }
        if source_key:
            updates[source_key] = context.get(source_key, [])
        return updates

    # ------------------------------------------------------------- helpers

    def _summary(self, records: list, packages: list, items: int, persisted: int) -> dict:
        collected = [r for r in records if r["metrics_status"] == MetricsStatus.COLLECTED]
        scores = [p["performance_score"] for p in packages if p.get("status") == "collected"]
        return {
            "engine_version": ANALYTICS_ENGINE_VERSION,
            "status": "collected" if collected else "no_items" if not records else "pending",
            "items": items,
            "records": len(records),
            "collected": len(collected),
            "pending": len(records) - len(collected),
            "persisted": persisted,
            "platforms": sorted({r["platform"] for r in records if r.get("platform")}),
            "average_performance_score": int(round(sum(scores) / len(scores))) if scores else 0,
            "store_size": get_analytics_store().record_count(),
            "generated_at": _now_iso(),
        }
