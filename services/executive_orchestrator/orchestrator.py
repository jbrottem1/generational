"""Executive Orchestrator — one-command AI production studio entry point.

    result = create_video("Create a 60 second YouTube Short explaining why cameras can see infrared.")

Coordinates Discovery → Research → Script → Evidence → Visuals → Animation →
Voice → Assembly → Production QA (with auto-revision) → Export → Publishing.
"""

from __future__ import annotations

import time
from typing import Any

from core.log import get_logger, log_event
from core.workflows import WorkflowEngine
from services.discovery.script_handoff import queue_item_to_script_context
from services.executive_orchestrator.export_artifacts import package_export_artifacts
from services.executive_orchestrator.logging_store import persist_run_log
from services.executive_orchestrator.parallel import get_parallel_pool
from services.executive_orchestrator.request_parser import ProductionBrief, parse_production_request
from services.executive_orchestrator.revision_loop import run_revision_loop
from services.executive_orchestrator.stages import STAGE_ENGINES
from services.executive_orchestrator.state import (
    ProductionRun,
    get_run_registry,
    mark_stage,
)

logger = get_logger(__name__)


class ExecutiveOrchestrator:
    """Single entry point for the Generational AI Media Operating System."""

    def __init__(
        self,
        *,
        workflows: WorkflowEngine | None = None,
        max_revision_rounds: int = 2,
        max_parallel: int = 2,
    ) -> None:
        self._workflows = workflows or WorkflowEngine()
        self.max_revision_rounds = max_revision_rounds
        self.max_parallel = max_parallel

    # ------------------------------------------------------------------ API

    def create_video(
        self,
        command: str,
        *,
        category: str = "science",
        max_revision_rounds: int | None = None,
        publish_mode: str = "scheduled",
        plan_only: bool = False,
        skip_publishing: bool = False,
        context_extra: dict | None = None,
    ) -> dict[str, Any]:
        """One instruction → coordinated studio production."""
        brief = parse_production_request(command, category=category)
        run = ProductionRun(
            command=command,
            topic=brief.topic,
            platforms=list(brief.platforms),
            runtime_sec=brief.runtime_sec,
            brief=brief.to_dict(),
            notes=list(brief.notes),
        )
        get_run_registry().add(run)
        return self._execute_run(
            run,
            brief,
            max_revision_rounds=max_revision_rounds,
            publish_mode=publish_mode,
            plan_only=plan_only,
            skip_publishing=skip_publishing,
            context_extra=context_extra,
        )

    def submit_video(self, command: str, **kwargs) -> dict[str, Any]:
        """Queue a production on the parallel pool; returns run stub immediately."""
        brief = parse_production_request(command, category=kwargs.get("category", "science"))
        run = ProductionRun(
            command=command,
            topic=brief.topic,
            platforms=list(brief.platforms),
            runtime_sec=brief.runtime_sec,
            brief=brief.to_dict(),
            status="pending",
        )
        get_run_registry().add(run)
        pool = get_parallel_pool(max_workers=self.max_parallel)

        def _job():
            return self._execute_run(
                run,
                brief,
                max_revision_rounds=kwargs.get("max_revision_rounds"),
                publish_mode=kwargs.get("publish_mode", "scheduled"),
                plan_only=kwargs.get("plan_only", False),
                skip_publishing=kwargs.get("skip_publishing", False),
                context_extra=kwargs.get("context_extra"),
            )

        fut = pool.submit(run.id, _job)
        return {
            "submitted": True,
            "run_id": run.id,
            "status": "pending",
            "topic": brief.topic,
            "platforms": brief.platforms,
            "runtime_sec": brief.runtime_sec,
            "future_done": fut.done(),
            "dashboard": get_run_registry().dashboard(),
        }

    def get_run(self, run_id: str) -> dict | None:
        run = get_run_registry().get(run_id)
        return run.to_dict() if run else None

    def dashboard(self) -> dict[str, Any]:
        return get_run_registry().dashboard()

    # -------------------------------------------------------------- execute

    def _execute_run(
        self,
        run: ProductionRun,
        brief: ProductionBrief,
        *,
        max_revision_rounds: int | None,
        publish_mode: str,
        plan_only: bool,
        skip_publishing: bool,
        context_extra: dict | None,
    ) -> dict[str, Any]:
        started = time.time()
        run.status = "running"
        from datetime import datetime, timezone

        run.started_at = datetime.now(timezone.utc).isoformat()
        get_run_registry().update(run)

        context: dict[str, Any] = {
            "command": brief.raw_command or run.command,
            "subject": brief.topic,
            "topic": brief.topic,
            "niche": brief.category,
            "category": brief.category,
            "target_platform": brief.primary_platform,
            "platforms": list(brief.platforms),
            "target_runtime_sec": brief.runtime_sec,
            "video_format": brief.format,
            "publish_mode": publish_mode,
            "count": 1,
            "goal": brief.goal,
        }
        if context_extra:
            context.update(context_extra)

        log_event(
            logger,
            "executive.started",
            run_id=run.id,
            topic=brief.topic,
            platforms=brief.platforms,
            runtime_sec=brief.runtime_sec,
            plan_only=plan_only,
        )

        try:
            if plan_only:
                self._run_plan_only(run, brief, context)
            else:
                self._run_full(run, brief, context, max_revision_rounds or self.max_revision_rounds, skip_publishing)
            run.status = "completed" if not run.error else "failed"
        except Exception as exc:  # noqa: BLE001 — never crash the studio
            run.status = "failed"
            run.error = str(exc)
            log_event(logger, "executive.failed", run_id=run.id, error=str(exc))

        run.generation_time_ms = int((time.time() - started) * 1000)
        run.finished_at = datetime.now(timezone.utc).isoformat()
        get_run_registry().update(run)

        result = run.to_dict()
        result["context_keys"] = sorted(context.keys())
        result["pqa_summary"] = context.get("pqa_summary")
        result["discovery_top"] = context.get("discovery_top")
        try:
            result["log_path"] = str(persist_run_log(result))
        except Exception as exc:  # noqa: BLE001
            result["log_error"] = str(exc)

        log_event(
            logger,
            "executive.finished",
            run_id=run.id,
            status=run.status,
            qa=run.qa_score,
            ms=run.generation_time_ms,
        )
        return result

    def _run_plan_only(self, run: ProductionRun, brief: ProductionBrief, context: dict) -> None:
        """Parse + stage plan without invoking heavy engines (fast rehearsal)."""
        for key in STAGE_ENGINES:
            t0 = time.time()
            mark_stage(run, key, "running", message="plan_only")
            engines = list(STAGE_ENGINES.get(key) or [])
            mark_stage(
                run,
                key,
                "completed",
                message=f"planned engines={engines}",
                engines=engines,
                started=t0,
            )
        context["executive_plan_only"] = True
        manifest = package_export_artifacts(context, run_id=run.id, topic=brief.topic)
        run.export_paths = dict(manifest.get("paths") or {})
        run.export_size_bytes = int(manifest.get("export_size_bytes") or 0)
        run.publish_status = "plan_only"
        run.artifacts = {"export": manifest, "brief": brief.to_dict()}
        run.notes.append("plan_only")

    def _run_full(
        self,
        run: ProductionRun,
        brief: ProductionBrief,
        context: dict,
        max_revision_rounds: int,
        skip_publishing: bool,
    ) -> None:
        # 1) Discovery
        self._run_stage_engines(run, "discovery", context)
        self._seed_from_discovery(brief, context)

        # 2–8) Research → Direction → Script → Evidence → Visuals → Animation → Voice → Assembly
        for key in ("research", "direction", "script", "evidence", "visuals", "animation", "voice", "assembly"):
            ok = self._run_stage_engines(run, key, context)
            if not ok and key in ("research", "direction", "script"):
                # Soft-fail later stages; hard-fail early intelligence
                run.error = run.stages[key].error or f"Stage {key} failed"
                # Continue to record remaining as skipped
                for later in ("direction", "script", "evidence", "visuals", "animation", "voice", "assembly", "qa", "export", "publishing"):
                    if later == key:
                        continue
                    if run.stages.get(later) and run.stages[later].status == "pending":
                        mark_stage(run, later, "skipped", message="upstream_failed")
                return

        # Ensure selected_ideas exists for QA / publish collectors
        if not context.get("selected_ideas"):
            ideas = context.get("ideas") or context.get("candidates") or []
            if ideas:
                context["selected_ideas"] = list(ideas)

        # 9–11) QA + revision loop
        self._run_stage_engines(run, "qa", context)
        t_rev = time.time()
        mark_stage(run, "qa", "running", message="revision_loop")

        def _on_round(round_i: int, engines: list[str]) -> None:
            run.revision_rounds = round_i
            run.notes.append(f"revision_round_{round_i}:{','.join(engines)}")
            get_run_registry().update(run)

        rev = run_revision_loop(
            context,
            workflows=self._workflows,
            max_rounds=max_revision_rounds,
            on_round=_on_round,
        )
        run.revision_rounds = int(rev.get("rounds") or 0)
        run.qa_decision = str(rev.get("final_decision") or "")
        if rev.get("qa_score") is not None:
            run.qa_score = int(rev["qa_score"])
        elif context.get("pqa_reports"):
            run.qa_score = int((context["pqa_reports"][0] or {}).get("overall_score") or 0)
            run.qa_decision = str((context["pqa_reports"][0] or {}).get("decision") or run.qa_decision)

        qa_status = "completed" if rev.get("approved") else ("failed" if rev.get("blocked") else "completed")
        mark_stage(
            run,
            "qa",
            qa_status,
            message=f"decision={run.qa_decision} score={run.qa_score} rounds={run.revision_rounds}",
            engines=["production_qa"] + list(rev.get("engines_touched") or []),
            started=t_rev,
        )

        if rev.get("blocked") or (run.qa_decision == "BLOCK_EXPORT"):
            run.error = run.error or "PQA BLOCK_EXPORT"
            for later in ("export", "publishing"):
                mark_stage(run, later, "skipped", message="blocked_by_pqa")
            return

        if run.qa_decision == "REQUEST_REVISION":
            run.notes.append("qa_still_request_revision_after_loop")
            # Still export artifacts for review, but do not publish
            skip_publishing = True

        # 12–13) Export artifacts
        t0 = time.time()
        mark_stage(run, "export", "running")
        try:
            manifest = package_export_artifacts(context, run_id=run.id, topic=brief.topic)
            run.export_paths = dict(manifest.get("paths") or {})
            run.export_size_bytes = int(manifest.get("export_size_bytes") or 0)
            run.artifacts["export"] = manifest
            mark_stage(run, "export", "completed", message="artifacts_written", started=t0)
        except Exception as exc:  # noqa: BLE001
            mark_stage(run, "export", "failed", error=str(exc), started=t0)
            run.error = str(exc)
            mark_stage(run, "publishing", "skipped", message="export_failed")
            return

        # 14) Publishing queue
        if skip_publishing or publish_mode == "none":
            mark_stage(run, "publishing", "skipped", message="skip_publishing")
            run.publish_status = "skipped"
            return

        ok = self._run_stage_engines(run, "publishing", context)
        run.publish_status = "queued" if ok else "failed"
        if context.get("publishing_result"):
            run.artifacts["publishing_result"] = context["publishing_result"]
        if context.get("queued_count") is not None:
            run.artifacts["queued_count"] = context["queued_count"]

    def _seed_from_discovery(self, brief: ProductionBrief, context: dict) -> None:
        """Merge top discovery opportunity into script-ready context."""
        top = context.get("discovery_top") or context.get("discovery_queue") or []
        item = None
        if isinstance(top, list) and top:
            item = top[0]
        elif isinstance(context.get("discovery"), dict):
            queue = context["discovery"].get("queue") or context["discovery"].get("top") or []
            if queue:
                item = queue[0]

        if isinstance(item, dict):
            try:
                seeded = queue_item_to_script_context(item)
                # Prefer user topic / platform / runtime
                seeded["command"] = brief.raw_command
                seeded["subject"] = brief.topic
                seeded["target_platform"] = brief.primary_platform
                seeded["platforms"] = list(brief.platforms)
                seeded["target_runtime_sec"] = brief.runtime_sec
                for key, val in seeded.items():
                    if key == "candidates" and context.get("candidates"):
                        continue
                    if key not in context or context.get(key) in (None, "", [], {}):
                        context[key] = val
                    elif key == "research" and isinstance(val, dict):
                        merged = dict(val)
                        merged.update(context.get("research") or {})
                        context["research"] = merged
                if not context.get("candidates") and seeded.get("candidates"):
                    context["candidates"] = seeded["candidates"]
            except Exception as exc:  # noqa: BLE001
                log_event(logger, "executive.discovery_seed_failed", error=str(exc))

        # Always ensure at least one candidate for downstream engines
        if not context.get("candidates"):
            context["candidates"] = [
                {
                    "title": brief.topic[:120],
                    "hook": f"What if we looked closer at {brief.topic}?",
                    "angle": f"Educational explainer: {brief.topic}",
                    "estimated_runtime_hint_sec": brief.runtime_sec,
                    "recommended_video_format": brief.format,
                }
            ]
        # Stamp runtime / platform on candidates
        for c in context["candidates"]:
            if isinstance(c, dict):
                c.setdefault("estimated_runtime_hint_sec", brief.runtime_sec)
                c.setdefault("title", brief.topic[:120])

    def _run_stage_engines(self, run: ProductionRun, stage_key: str, context: dict) -> bool:
        engines = list(STAGE_ENGINES.get(stage_key) or [])
        t0 = time.time()
        mark_stage(run, stage_key, "running", message=f"engines={engines}")
        if not engines:
            mark_stage(run, stage_key, "completed", message="service_step", started=t0)
            return True
        try:
            result = self._workflows.execute(engines, context)
            steps = result.summary().get("steps") or []
            failed = [s for s in steps if s.get("status") == "failed"]
            used = [s.get("engine") for s in steps if s.get("engine")]
            # FutureEngine / not-ready → skipped is OK (WARNING, not fail)
            if failed:
                # Soft-fail non-critical stages (animation stub, publishing)
                critical = stage_key in ("discovery", "research", "direction", "script", "qa")
                err = "; ".join(f"{s.get('engine')}: {s.get('error')}" for s in failed)
                if critical:
                    mark_stage(run, stage_key, "failed", error=err, engines=used, started=t0)
                    return False
                mark_stage(
                    run,
                    stage_key,
                    "completed",
                    message=f"degraded:{err}",
                    engines=used,
                    started=t0,
                )
                run.notes.append(f"{stage_key}_degraded")
                return True
            mark_stage(
                run,
                stage_key,
                "completed",
                message=f"steps={len(steps)}",
                engines=used,
                started=t0,
            )
            return True
        except Exception as exc:  # noqa: BLE001
            mark_stage(run, stage_key, "failed", error=str(exc), engines=engines, started=t0)
            return False


_ORCH: ExecutiveOrchestrator | None = None


def get_executive_orchestrator(**kwargs) -> ExecutiveOrchestrator:
    global _ORCH
    if _ORCH is None or kwargs:
        _ORCH = ExecutiveOrchestrator(**kwargs) if kwargs else ExecutiveOrchestrator()
    return _ORCH


def create_video(command: str, **kwargs) -> dict[str, Any]:
    """Module-level one-command entry point."""
    return get_executive_orchestrator().create_video(command, **kwargs)
