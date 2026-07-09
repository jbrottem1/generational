"""The Orchestrator — the single entry point of the AI Content Operating System.

Coordinates every subsystem (trend discovery → opportunity ranking →
psychology → script → visual → audio → refinement → quality gate → media
production → packaging) into one production pipeline behind ONE interface:

    result = get_orchestrator().run_full_pipeline("Create 3 science shorts...")

Design rules:
- The orchestrator never contains engine logic. It executes stage groups
  (see stages.py) through the existing WorkflowEngine and folds the final
  context into ProductionPackage objects (see packager.py).
- Every stage returns SUCCESS / WARNING / FAILED plus diagnostics, and a
  failure stops the run gracefully — partial results are preserved.
- Future subsystems plug in via `register_stage()` and autonomy agents via
  `hooks.attach_hook()` — never by editing this module.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

from core.constants import DEFAULT_MODEL, DEFAULT_PUBLISH_THRESHOLD, IDEAS_PER_BATCH
from core.log import get_logger, log_event
from core.workflows import WorkflowEngine
from services.orchestrator.hooks import notify_hooks
from services.orchestrator.models import PipelineResult, StageReport, StageStatus
from services.orchestrator.packager import build_packages
from services.orchestrator.stages import build_pipeline_plan, get_stage

logger = get_logger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _average(values: list) -> int:
    return int(round(sum(values) / len(values))) if values else 0


def _stage_confidence(stage: str, context: dict) -> int:
    """0-100 confidence signal per stage, read from what the stage produced."""
    candidates = context.get("candidates", [])
    if stage == "trend":
        return int(context.get("top_opportunity", {}).get("opportunity_score", 0))
    if stage == "research":
        return int(context.get("research", {}).get("research_confidence", 0) * 100)
    if stage == "psychology":
        return _average([c.get("psychology_score", 0) for c in candidates])
    if stage == "script":
        return _average([c.get("script_score", 0) for c in candidates])
    if stage == "visual":
        return int(context.get("visual_intelligence_summary", {}).get("average_visual_score", 0))
    if stage == "audio":
        return int(context.get("voice_audio_summary", {}).get("average_audio_score", 0))
    if stage == "attention":
        return int(context.get("attention_graph_summary", {}).get("average_attention_score", 0))
    if stage == "refinement":
        selected = context.get("selected_ideas", [])
        return _average([idea.get("seo_score", 0) for idea in selected])
    if stage == "quality":
        ideas = context.get("ideas", [])
        return _average([idea.get("scores", {}).get("publish", 0) for idea in ideas])
    return 0


class Orchestrator:
    """One clean interface over the whole pipeline; engines plug in underneath."""

    def __init__(self, workflow_engine: "WorkflowEngine | None" = None) -> None:
        self._workflows = workflow_engine or WorkflowEngine()

    # ------------------------------------------------------------- stages

    def run_stage(self, stage: str, context: dict, engine_keys: "list | None" = None) -> StageReport:
        """Execute one named stage group against a shared context."""
        engine_keys = engine_keys if engine_keys is not None else get_stage(stage)
        report = StageReport(stage=stage, started_at=_now_iso())
        started = time.time()
        log_event(logger, "orchestrator.stage_started", stage=stage, engines=len(engine_keys))

        if not engine_keys:
            report.status = StageStatus.FAILED
            report.errors.append(f"Unknown stage: {stage!r}")
        else:
            run = self._workflows.execute(engine_keys, context)
            steps = run.summary()["steps"]
            report.diagnostics["steps"] = steps
            skipped = [s["engine"] for s in steps if s["status"] == "skipped"]
            failed = [s for s in steps if s["status"] == "failed"]

            if failed:
                report.status = StageStatus.FAILED
                report.errors = [f"{s['engine']}: {s['error']}" for s in failed]
            elif skipped:
                report.status = StageStatus.WARNING
                report.warnings.append(f"Engines not ready, skipped: {', '.join(skipped)}")
            if context.get("error"):
                report.warnings.append(str(context["error"]))
                if report.status == StageStatus.SUCCESS:
                    report.status = StageStatus.WARNING

        report.finished_at = _now_iso()
        report.duration_ms = int((time.time() - started) * 1000)
        report.confidence = _stage_confidence(stage, context)
        log_event(
            logger,
            "orchestrator.stage_finished",
            stage=stage,
            status=report.status,
            duration_ms=report.duration_ms,
            confidence=report.confidence,
            warnings=len(report.warnings),
            errors=len(report.errors),
        )
        return report

    # Named stage runners — the stable public surface. Each runs its group
    # against the provided context (from a prior stage or a fixture).

    def run_trend_stage(self, context: dict) -> StageReport:
        return self.run_stage("trend", context)

    def run_script_stage(self, context: dict) -> StageReport:
        return self.run_stage("script", context)

    def run_visual_stage(self, context: dict) -> StageReport:
        return self.run_stage("visual", context)

    def run_audio_stage(self, context: dict) -> StageReport:
        return self.run_stage("audio", context)

    def run_quality_stage(self, context: dict) -> StageReport:
        return self.run_stage("quality", context)

    # Future stages (Agents 6-10) — wired now, light up when their engines
    # become ready (until then their engines are skipped and the report is
    # a WARNING with diagnostics — never a crash).

    def run_render_stage(self, context: dict) -> StageReport:
        return self.run_stage("render", context)

    def run_seo_stage(self, context: dict) -> StageReport:
        return self.run_stage("seo", context)

    def run_publish_stage(self, context: dict) -> StageReport:
        return self.run_stage("publish", context)

    def run_analytics_stage(self, context: dict) -> StageReport:
        return self.run_stage("analytics", context)

    def run_learning_stage(self, context: dict) -> StageReport:
        return self.run_stage("learning", context)

    def run_brand_stage(self, context: dict) -> StageReport:
        return self.run_stage("brand_management", context)

    # ------------------------------------------------------- full pipeline

    def run_full_pipeline(
        self,
        command: str,
        count: int = IDEAS_PER_BATCH,
        model: str = DEFAULT_MODEL,
        threshold: int = DEFAULT_PUBLISH_THRESHOLD,
        research_settings: "dict | None" = None,
        project_name: "str | None" = None,
        target_platform: str = "youtube_shorts",
        context_extra: "dict | None" = None,
    ) -> PipelineResult:
        """User command → ProductionPackage list, through every subsystem."""
        context = {
            "command": command,
            "count": count,
            "model": model,
            "threshold": threshold,
            "research_settings": research_settings,
            "project_name": project_name,
            "target_platform": target_platform,
        }
        context.update(context_extra or {})
        result = PipelineResult(status=StageStatus.SUCCESS, context=context)
        plan = build_pipeline_plan()
        log_event(logger, "orchestrator.pipeline_started", command=command[:80], stages=len(plan))

        for stage, engine_keys in plan:
            report = self.run_stage(stage, context, engine_keys=engine_keys)
            result.stage_reports.append(report)
            if report.status == StageStatus.FAILED:
                result.status = StageStatus.FAILED
                result.error = "; ".join(report.errors) or f"Stage '{stage}' failed."
                log_event(logger, "orchestrator.pipeline_stopped", stage=stage, error=result.error)
                notify_hooks(result)
                return result

        # Engine-level step results (same shape the UI dashboard has always
        # consumed) — set before production so its dashboard is accurate.
        context["pipeline_steps"] = [
            step
            for report in result.stage_reports
            for step in report.diagnostics.get("steps", [])
        ]

        result.stage_reports.append(self._run_production(context))
        result.stage_reports.append(self._run_packaging(context, result))

        if any(r.status == StageStatus.WARNING for r in result.stage_reports):
            result.status = StageStatus.WARNING

        log_event(
            logger,
            "orchestrator.pipeline_finished",
            status=result.status,
            packages=len(result.packages),
            publish_ready=sum(1 for p in result.packages if p.publish_ready),
        )
        notify_hooks(result)
        return result

    # ------------------------------------------------ internal final steps

    def _run_production(self, context: dict) -> StageReport:
        """Media production + publishing queue for quality-approved ideas.

        Reuses services/production.py wholesale — the orchestrator adds
        status/diagnostics, not a second production path.
        """
        from services.production import run_media_production

        report = StageReport(stage="production", started_at=_now_iso())
        started = time.time()
        log_event(logger, "orchestrator.stage_started", stage="production")

        try:
            production = run_media_production(context)
            context.update(production)
            report.diagnostics["packages"] = len(production.get("production_packages", []))
            report.diagnostics["queued"] = production.get("queued_count", 0)
            if production.get("production_error"):
                report.status = StageStatus.FAILED
                report.errors.append(str(production["production_error"]))
            elif production.get("production_skipped"):
                report.status = StageStatus.WARNING
                report.warnings.append("No publishable ideas — media production skipped.")
            report.confidence = 100 if production.get("production_packages") else 0
        except Exception as exc:  # noqa: BLE001 - graceful stop, never crash
            report.status = StageStatus.FAILED
            report.errors.append(str(exc))

        report.finished_at = _now_iso()
        report.duration_ms = int((time.time() - started) * 1000)
        log_event(
            logger, "orchestrator.stage_finished", stage="production",
            status=report.status, duration_ms=report.duration_ms,
        )
        return report

    def _run_packaging(self, context: dict, result: PipelineResult) -> StageReport:
        """Fold the final context into standardized ProductionPackage objects."""
        report = StageReport(stage="packaging", started_at=_now_iso())
        started = time.time()
        try:
            result.packages = build_packages(context)
            context["unified_packages"] = [pkg.to_dict() for pkg in result.packages]
            report.diagnostics["packages"] = len(result.packages)
            report.confidence = _average([pkg.quality_score for pkg in result.packages])
            if not result.packages:
                report.status = StageStatus.WARNING
                report.warnings.append("Pipeline produced no ideas to package.")
        except Exception as exc:  # noqa: BLE001 - graceful stop, never crash
            report.status = StageStatus.FAILED
            report.errors.append(str(exc))
        report.finished_at = _now_iso()
        report.duration_ms = int((time.time() - started) * 1000)
        log_event(
            logger, "orchestrator.stage_finished", stage="packaging",
            status=report.status, duration_ms=report.duration_ms, confidence=report.confidence,
        )
        return report


# ------------------------------------------------------- module interface

_orchestrator: "Orchestrator | None" = None


def get_orchestrator() -> Orchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator


def run_full_pipeline(command: str, **kwargs) -> PipelineResult:
    """Convenience module-level entry point (see Orchestrator.run_full_pipeline)."""
    return get_orchestrator().run_full_pipeline(command, **kwargs)


# Job-queue integration — autonomy preparation. A future Scheduler agent
# submits ORCHESTRATOR_JOB_TYPE jobs instead of calling engines directly.
ORCHESTRATOR_JOB_TYPE = "run_pipeline"


def _run_pipeline_job(payload: dict) -> dict:
    result = get_orchestrator().run_full_pipeline(payload["command"], **payload.get("options", {}))
    return result.to_dict()


def ensure_orchestrator_handler(queue) -> None:
    """Register the orchestrator job handler on a queue (idempotent)."""
    if not queue.has_handler(ORCHESTRATOR_JOB_TYPE):
        queue.register_handler(ORCHESTRATOR_JOB_TYPE, _run_pipeline_job)
