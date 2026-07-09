"""Continuous-learning integration — how Agent 9 attaches to the system.

Three sanctioned seams, none of which modify other engines or the
orchestrator (Architecture Directive #1 + engines/analytics/README.md):

1. `AnalyticsHook` / `LearningHook` — OrchestratorHooks (kinds
   "analytics" / "learning") notified after EVERY `run_full_pipeline()`
   call. They drive the analytics and learning stages through the
   orchestrator's own stage runners, so post-publish measurement and the
   feedback loop happen automatically at the end of each run.
2. `AnalyticsPublishListener` — a PublishListener fired by the Publishing
   Engine after every publish attempt, so content published from the
   scheduled queue OUTSIDE a pipeline run is still measured.
3. `learning_context_extra()` — the recommendations payload a caller
   merges into the next run's context (`context_extra=`), so the next
   generation of content starts from everything already learned.

Call `enable_continuous_learning()` once (idempotent) to arm all three.
"""

from __future__ import annotations

from core.log import get_logger, log_event
from services.analytics.store import get_analytics_store
from services.orchestrator.hooks import OrchestratorHook
from services.publishing.extensions import PublishListener, register_publish_listener

logger = get_logger(__name__)


class AnalyticsHook(OrchestratorHook):
    """Runs the analytics stage after every completed pipeline run."""

    kind = "analytics"
    name = "agent9-analytics"

    def on_pipeline_complete(self, result) -> None:
        # Orchestrator already runs analytics in-pipeline; skip if populated.
        if result.context.get("analytics_summary"):
            log_event(logger, "analytics.hook_skipped", reason="already_ran")
            return
        from services.orchestrator import get_orchestrator

        report = get_orchestrator().run_analytics_stage(result.context)
        log_event(
            logger, "analytics.hook_ran",
            status=report.status,
            records=result.context.get("analytics_summary", {}).get("records", 0),
        )


class LearningHook(OrchestratorHook):
    """Runs the learning stage after every completed pipeline run."""

    kind = "learning"
    name = "agent9-learning"

    def on_pipeline_complete(self, result) -> None:
        if result.context.get("learning_report"):
            log_event(logger, "learning.hook_skipped", reason="already_ran")
            return
        from services.orchestrator import get_orchestrator

        report = get_orchestrator().run_learning_stage(result.context)
        log_event(
            logger, "learning.hook_ran",
            status=report.status,
            recommendations=len(
                result.context.get("learning_report", {}).get("recommendations", [])
            ),
        )


class AnalyticsPublishListener(PublishListener):
    """Measures publishes that execute outside a pipeline run (scheduled
    queue drains). Records deduplicate on `analytics_ref`."""

    key = "agent9-analytics"

    def on_publish_attempt(self, job: dict, attempt: dict) -> None:
        if attempt.get("status") != "published":
            return
        from services.analytics.collector import build_record_from_job

        store = get_analytics_store()
        ref = job.get("analytics_ref", "")
        if ref and store.find_by_ref(ref):
            return
        store.add_record(build_record_from_job(job, attempt))


def learning_context_extra() -> dict:
    """The `context_extra` payload for the NEXT pipeline run: everything
    learned so far, routed per engine — pass it to
    `run_full_pipeline(..., context_extra=learning_context_extra())` so
    new content automatically benefits from previous performance."""
    from services.learning.recommendations import (
        build_recommendations,
        recommendations_by_engine,
    )
    from services.learning.patterns import mine_patterns

    records = get_analytics_store().list_records()
    recommendations = build_recommendations(mine_patterns(records))
    return {"learning_recommendations": recommendations_by_engine(recommendations)}


_hooks: "list" = []
_listener: "AnalyticsPublishListener | None" = None


def enable_continuous_learning() -> dict:
    """Arm the full closed loop (idempotent): pipeline hooks + publish
    listener. After this, every run measures itself and learns."""
    global _listener
    from services.orchestrator import attach_hook

    if not _hooks:
        for hook in (AnalyticsHook(), LearningHook()):
            attach_hook(hook)
            _hooks.append(hook)
    if _listener is None:
        _listener = AnalyticsPublishListener()
        register_publish_listener(_listener)

    log_event(logger, "analytics.continuous_learning_enabled", hooks=len(_hooks))
    return {"hooks": [hook.name for hook in _hooks], "listener": _listener.key}


def disable_continuous_learning() -> None:
    """Detach everything `enable_continuous_learning()` attached."""
    global _listener
    from services.orchestrator import detach_hook
    from services.publishing.extensions import unregister_publish_listener

    while _hooks:
        detach_hook(_hooks.pop())
    if _listener is not None:
        unregister_publish_listener(_listener)
        _listener = None
