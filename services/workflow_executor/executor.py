"""End-to-End Workflow Executor (Agent 21).

Turns one user prompt into a durable ProjectRun that drives the Orchestrator
stage-by-stage with checkpoints, retries, and Studio UI status.

Does NOT reimplement engines or call provider APIs directly — all stage work
goes through the Orchestrator; external AI calls stay behind ProviderRuntime.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from core.log import get_logger, log_event
from services.orchestrator.models import PipelineResult, ProductionPackage, StageStatus
from services.orchestrator.report import build_production_report
from services.workflow_executor.models import (
    Checkpoint,
    ProjectRun,
    WorkflowConfig,
    WorkflowResult,
    WorkflowRun,
    WorkflowStatus,
    WorkflowStep,
    _now_iso,
)
from services.workflow_executor.policy import (
    DISTRIBUTION_SET,
    build_failure_report,
    degrade_failed_optional,
    estimate_completion_iso,
    map_orchestrator_status,
    progress_percent,
    should_retry,
    should_stop_run,
)
from services.workflow_executor.status import studio_status
from services.workflow_executor.store import WorkflowRunStore, get_workflow_store
from services.workflow_executor.templates import (
    apply_production_defaults,
    build_workflow_steps,
)

if TYPE_CHECKING:
    from services.orchestrator.orchestrator import Orchestrator

logger = get_logger(__name__)

WORKFLOW_JOB_TYPE = "workflow_run"


def _json_safe(context: dict) -> dict:
    safe = {}
    for key, value in context.items():
        try:
            json.dumps(value)
            safe[key] = value
        except (TypeError, ValueError):
            safe[key] = str(value)
    return safe


def _provider_usage_snapshot() -> dict:
    try:
        from services.provider_runtime import get_provider_runtime

        runtime = get_provider_runtime()
        summary = runtime.usage_summary() if hasattr(runtime, "usage_summary") else {}
        return summary if isinstance(summary, dict) else {"raw": summary}
    except Exception:  # noqa: BLE001 - provider layer optional during tests
        return {}


class WorkflowExecutor:
    """Durable run controller over the Orchestrator + ProviderRuntime."""

    def __init__(
        self,
        store: "WorkflowRunStore | None" = None,
        orchestrator: "Orchestrator | None" = None,
    ) -> None:
        self._store = store or get_workflow_store()
        self._orchestrator = orchestrator

    @property
    def store(self) -> WorkflowRunStore:
        return self._store

    def _orch(self) -> "Orchestrator":
        if self._orchestrator is not None:
            return self._orchestrator
        from services.orchestrator import get_orchestrator

        return get_orchestrator()

    # ----------------------------------------------------------- create

    def create_run(
        self,
        command: str,
        config: "WorkflowConfig | dict | None" = None,
        *,
        context_extra: "dict | None" = None,
    ) -> ProjectRun:
        """Accept a production request and create a durable ProjectRun."""
        if isinstance(config, dict):
            cfg = WorkflowConfig.from_dict(config)
        elif config is None:
            cfg = WorkflowConfig()
        else:
            cfg = config

        cfg = apply_production_defaults(command, cfg)
        steps = build_workflow_steps(cfg)
        workflow = WorkflowRun(
            template=cfg.template,
            status=WorkflowStatus.PENDING,
            steps=steps,
        )
        context = {
            "command": command,
            "count": cfg.count,
            "model": cfg.model,
            "target_platform": cfg.target_platform,
            "publish_mode": cfg.publish_mode,
            "quality_level": cfg.quality_level,
            "budget_usd": cfg.budget_usd,
            "platform_targets": list(cfg.platform_targets),
            "provider_preferences": dict(cfg.provider_preferences),
            "longform": cfg.longform_mode,
            "production_type": cfg.production_type,
            "workflow_template": cfg.template,
        }
        if context_extra:
            context.update(context_extra)
        run = ProjectRun(
            command=command,
            production_type=cfg.production_type,
            status=WorkflowStatus.PENDING,
            config=cfg,
            workflow=workflow,
            context=context,
        )
        run.log.append(
            "run.created",
            production_type=cfg.production_type,
            template=cfg.template,
            stages=len(steps),
            longform=cfg.longform_mode,
        )
        self._persist(run)
        log_event(
            logger,
            "workflow.run_created",
            run_id=run.run_id,
            production_type=cfg.production_type,
            stages=len(steps),
        )
        return run

    # ----------------------------------------------------------- execute

    def execute(
        self,
        command: str = "",
        config: "WorkflowConfig | dict | None" = None,
        *,
        run_id: str = "",
        resume: bool = False,
        context_extra: "dict | None" = None,
    ) -> ProjectRun:
        """Create (or load) a run and execute until complete / failed / cancelled."""
        if resume or run_id:
            run = self.load_run(run_id)
            if run is None:
                raise ValueError(f"Workflow run {run_id!r} not found")
            return self.resume(run.run_id)

        if not command:
            raise ValueError("command is required to start a new workflow run")
        run = self.create_run(command, config, context_extra=context_extra)
        return self._execute_run(run)

    def resume(self, run_id: str) -> ProjectRun:
        """Resume a failed or interrupted run from its last checkpoint."""
        run = self.load_run(run_id)
        if run is None:
            raise ValueError(f"Workflow run {run_id!r} not found")
        if run.status == WorkflowStatus.CANCELLED:
            run.log.append("run.resume_blocked", reason="cancelled")
            self._persist(run)
            return run
        if run.status == WorkflowStatus.COMPLETED:
            return run

        checkpoint = self._store.load_checkpoint(run_id) or run.checkpoint
        if checkpoint:
            run.context.update(checkpoint.context_snapshot or {})
            completed = set(checkpoint.completed_stages or [])
            for step in run.workflow.steps:
                if step.stage in completed and step.status not in (
                    WorkflowStatus.FAILED,
                    WorkflowStatus.RETRYING,
                ):
                    if step.status == WorkflowStatus.PENDING:
                        step.status = WorkflowStatus.COMPLETED
                elif step.status in (
                    WorkflowStatus.RUNNING,
                    WorkflowStatus.FAILED,
                    WorkflowStatus.RETRYING,
                ):
                    # Reset so resume can re-attempt from this stage.
                    step.status = WorkflowStatus.PENDING
                    step.attempt = 0
                    step.errors = []
                    step.warnings.append("Resumed — stage reset for retry")
        run.status = WorkflowStatus.RUNNING
        run.result.error = ""
        run.result.partial = False
        run.log.append("run.resumed", from_stage=self._next_pending_stage(run))
        self._persist(run)
        return self._execute_run(run, resuming=True)

    def cancel(self, run_id: str) -> ProjectRun:
        run = self.load_run(run_id)
        if run is None:
            raise ValueError(f"Workflow run {run_id!r} not found")
        run.status = WorkflowStatus.CANCELLED
        run.finished_at = _now_iso()
        run.updated_at = run.finished_at
        for step in run.workflow.steps:
            if step.status in (WorkflowStatus.PENDING, WorkflowStatus.WAITING, WorkflowStatus.RUNNING):
                step.status = WorkflowStatus.CANCELLED
        run.workflow.status = WorkflowStatus.CANCELLED
        run.log.append("run.cancelled")
        self._checkpoint(run, status=WorkflowStatus.CANCELLED)
        self._persist(run)
        return run

    def load_run(self, run_id: str) -> "ProjectRun | None":
        return self._store.load(run_id)

    def list_runs(self, status: str = "") -> list[dict]:
        return self._store.list_runs(status=status)

    def get_status(self, run_id: str) -> dict:
        run = self.load_run(run_id)
        if run is None:
            return {"error": f"run {run_id!r} not found", "status": "missing"}
        return studio_status(run)

    # -------------------------------------------------------- internals

    def _execute_run(self, run: ProjectRun, *, resuming: bool = False) -> ProjectRun:
        orch = self._orch()
        if not resuming or not run.started_at:
            run.started_at = _now_iso()
        run.status = WorkflowStatus.RUNNING
        run.workflow.status = WorkflowStatus.RUNNING
        run.workflow.started_at = run.workflow.started_at or run.started_at
        run.log.append("run.started", resuming=resuming)
        self._persist(run)

        pipeline_result = PipelineResult(status=StageStatus.SUCCESS, context=run.context)
        # Restore packages already produced before interruption.
        if run.context.get("unified_packages"):
            try:
                pipeline_result.packages = [
                    ProductionPackage.from_dict(p) for p in run.context["unified_packages"]
                ]
            except Exception:  # noqa: BLE001
                pass

        deadline = None
        if run.config.timeout_sec and run.config.timeout_sec > 0:
            deadline = time.time() + run.config.timeout_sec

        for index, step in enumerate(run.workflow.steps):
            run.workflow.current_step_index = index
            if run.status == WorkflowStatus.CANCELLED:
                break
            if step.status in (
                WorkflowStatus.COMPLETED,
                WorkflowStatus.SKIPPED,
                WorkflowStatus.CANCELLED,
            ):
                continue

            if deadline is not None and time.time() > deadline:
                run.status = WorkflowStatus.FAILED
                run.result.error = "Workflow timeout exceeded"
                run.result.failure_reports.append(
                    build_failure_report(
                        WorkflowStep(
                            stage=step.stage,
                            status=WorkflowStatus.FAILED,
                            errors=["Workflow timeout exceeded"],
                        ),
                        recoverable=True,
                    )
                )
                run.log.append("run.timeout", stage=step.stage)
                break

            ok = self._run_step(run, step, orch, pipeline_result)
            run.workflow.progress_pct = progress_percent(run.workflow.steps)
            run.estimated_completion_at = estimate_completion_iso(
                run.started_at,
                run.workflow.progress_pct,
                longform=run.config.longform_mode,
            )
            self._checkpoint(run)
            self._persist(run)

            if not ok:
                # Hard stop — preserve partial outputs.
                run.status = WorkflowStatus.FAILED
                run.result.partial = True
                run.result.error = "; ".join(step.errors) or f"Stage {step.stage} failed"
                run.result.failure_reports.append(
                    build_failure_report(step, recoverable=True)
                )
                run.log.append("run.failed", stage=step.stage, error=run.result.error)
                break
        else:
            # Completed all steps without break.
            self._finalize_success(run, pipeline_result)

        if run.status == WorkflowStatus.RUNNING:
            # Loop exited via break on failure/timeout/cancel already set status,
            # or all steps were already done on resume.
            if all(
                s.status
                in (
                    WorkflowStatus.COMPLETED,
                    WorkflowStatus.SKIPPED,
                    WorkflowStatus.CANCELLED,
                )
                for s in run.workflow.steps
            ):
                self._finalize_success(run, pipeline_result)
            elif run.status == WorkflowStatus.RUNNING:
                run.status = WorkflowStatus.FAILED
                run.result.partial = True

        run.finished_at = _now_iso()
        run.updated_at = run.finished_at
        run.workflow.finished_at = run.finished_at
        run.workflow.progress_pct = progress_percent(run.workflow.steps)
        run.workflow.status = run.status
        self._attach_outputs(run, pipeline_result)
        self._attach_provider_usage(run)
        self._checkpoint(run, status=run.status)
        self._persist(run)
        log_event(
            logger,
            "workflow.run_finished",
            run_id=run.run_id,
            status=run.status,
            progress=run.workflow.progress_pct,
        )
        return run

    def _run_step(
        self,
        run: ProjectRun,
        step: WorkflowStep,
        orch: "Orchestrator",
        pipeline_result: PipelineResult,
    ) -> bool:
        """Execute one step with retries. Returns False on hard failure."""
        policy = run.config.retry_policy
        while True:
            if step.attempt >= step.max_attempts and step.status == WorkflowStatus.FAILED:
                break

            step.attempt += 1
            step.status = (
                WorkflowStatus.RETRYING if step.attempt > 1 else WorkflowStatus.RUNNING
            )
            step.started_at = step.started_at or _now_iso()
            step.errors = []
            run.log.append(
                "step.started",
                stage=step.stage,
                attempt=step.attempt,
                optional=step.optional,
            )
            self._persist(run)

            started = time.time()
            try:
                report = self._invoke_stage(orch, step, run.context, pipeline_result)
            except Exception as exc:  # noqa: BLE001 - never crash the executor
                from services.orchestrator.models import StageReport

                report = StageReport(
                    stage=step.stage,
                    status=StageStatus.FAILED,
                    errors=[str(exc)],
                    started_at=step.started_at,
                    finished_at=_now_iso(),
                )

            step.duration_ms = int((time.time() - started) * 1000)
            step.finished_at = _now_iso()
            step.confidence = getattr(report, "confidence", 0) or 0
            step.diagnostics = dict(getattr(report, "diagnostics", {}) or {})
            step.warnings = list(getattr(report, "warnings", []) or [])
            orch_status = getattr(report, "status", StageStatus.FAILED)
            step.errors = list(getattr(report, "errors", []) or [])
            pipeline_result.stage_reports.append(report)

            if orch_status == StageStatus.FAILED:
                step.status = WorkflowStatus.FAILED
            elif orch_status == StageStatus.SKIPPED:
                step.status = WorkflowStatus.SKIPPED
            elif orch_status == StageStatus.WARNING:
                # Optional / not-ready engines → completed with warnings.
                step.status = WorkflowStatus.COMPLETED
            else:
                step.status = map_orchestrator_status(orch_status, step.optional)

            run.log.append(
                "step.finished",
                stage=step.stage,
                status=step.status,
                attempt=step.attempt,
                duration_ms=step.duration_ms,
            )

            if step.status != WorkflowStatus.FAILED:
                return True

            if should_retry(step, policy):
                run.log.append("step.retrying", stage=step.stage, attempt=step.attempt)
                step.status = WorkflowStatus.RETRYING
                if policy.backoff_sec:
                    time.sleep(policy.backoff_sec)
                continue

            # Retries exhausted.
            if degrade_failed_optional(step, policy):
                run.result.failure_reports.append(
                    build_failure_report(step, recoverable=True)
                )
                run.log.append("step.degraded", stage=step.stage)
                return True

            if should_stop_run(step, policy, exhausted_retries=True):
                return False

            # Non-required failure that wasn't degraded — treat as skip.
            step.status = WorkflowStatus.SKIPPED
            return True

        return False

    def _invoke_stage(
        self,
        orch: "Orchestrator",
        step: WorkflowStep,
        context: dict,
        pipeline_result: PipelineResult,
    ):
        stage = step.stage
        if stage == "production":
            return orch._run_production(context)  # noqa: SLF001 — same seam as longform
        if stage == "packaging":
            return orch._run_packaging(context, pipeline_result)  # noqa: SLF001
        engine_keys = step.engine_keys if step.engine_keys else None
        return orch.run_stage(stage, context, engine_keys=engine_keys)

    def _finalize_success(self, run: ProjectRun, pipeline_result: PipelineResult) -> None:
        # Refresh packages from unified_packages if distribution enriched them.
        unified = run.context.get("unified_packages")
        if unified:
            try:
                pipeline_result.packages = [
                    ProductionPackage.from_dict(p) for p in unified
                ]
            except Exception:  # noqa: BLE001
                pass

        if any(
            r.status in (StageStatus.WARNING, StageStatus.FAILED)
            for r in pipeline_result.stage_reports
        ):
            pipeline_result.status = StageStatus.WARNING
        else:
            pipeline_result.status = StageStatus.SUCCESS

        pipeline_result.production_report = build_production_report(pipeline_result)
        run.context["production_report"] = pipeline_result.production_report
        run.context["pipeline_steps"] = [
            step
            for report in pipeline_result.stage_reports
            for step in report.diagnostics.get("steps", [])
        ]

        failed_required = any(
            s.status == WorkflowStatus.FAILED and s.required for s in run.workflow.steps
        )
        if failed_required:
            run.status = WorkflowStatus.FAILED
            run.result.partial = True
        else:
            run.status = WorkflowStatus.COMPLETED
            # Partial if any optional stage was skipped due to failure.
            run.result.partial = any(
                s.status == WorkflowStatus.SKIPPED and s.errors for s in run.workflow.steps
            )
        run.workflow.status = run.status
        run.log.append("run.completed", status=run.status, partial=run.result.partial)

    def _attach_outputs(self, run: ProjectRun, pipeline_result: PipelineResult) -> None:
        packages = [
            p.to_dict() if hasattr(p, "to_dict") else p for p in pipeline_result.packages
        ]
        run.result.packages = packages
        run.result.status = run.status
        run.result.production_report = dict(pipeline_result.production_report or {})
        first = packages[0] if packages else {}
        run.result.production_package = dict(first) if first else {}
        run.result.asset_package = dict(first.get("asset_package") or {})
        run.result.animation_package = dict(first.get("animation_package") or {})
        run.result.post_production_package = dict(
            first.get("post_production_package") or {}
        )
        run.result.render_package = dict(first.get("render_package") or {})
        run.result.publishing_package = dict(first.get("publishing_package") or {})
        run.result.analytics_package = dict(first.get("analytics_package") or {})
        run.result.learning_context = dict(
            first.get("learning_metadata")
            or run.context.get("learning_metadata")
            or {}
        )
        if not run.result.error and run.status == WorkflowStatus.FAILED:
            run.result.error = "Workflow failed"

    def _attach_provider_usage(self, run: ProjectRun) -> None:
        usage = _provider_usage_snapshot()
        run.provider_usage = usage
        run.result.provider_usage = usage
        cost = 0.0
        if isinstance(usage, dict):
            cost = float(usage.get("total_cost_usd") or usage.get("estimated_cost_usd") or 0)
        run.estimated_cost_usd = cost
        run.result.estimated_cost_usd = cost

    def _checkpoint(self, run: ProjectRun, status: str = "") -> Checkpoint:
        completed = [
            s.stage
            for s in run.workflow.steps
            if s.status
            in (WorkflowStatus.COMPLETED, WorkflowStatus.SKIPPED, WorkflowStatus.CANCELLED)
        ]
        current = ""
        for s in run.workflow.steps:
            if s.status in (
                WorkflowStatus.RUNNING,
                WorkflowStatus.RETRYING,
                WorkflowStatus.PENDING,
                WorkflowStatus.FAILED,
            ):
                current = s.stage
                break
        ckpt = Checkpoint(
            run_id=run.run_id,
            completed_stages=completed,
            current_stage=current,
            context_snapshot=_json_safe(run.context),
            step_states=[s.to_dict() for s in run.workflow.steps],
            status=status or run.status,
            created_at=(run.checkpoint.created_at if run.checkpoint else _now_iso()),
            updated_at=_now_iso(),
            error=run.result.error,
        )
        if run.checkpoint:
            ckpt.checkpoint_id = run.checkpoint.checkpoint_id
        run.checkpoint = ckpt
        self._store.save_checkpoint(ckpt)
        return ckpt

    def _persist(self, run: ProjectRun) -> None:
        run.updated_at = _now_iso()
        self._store.save(run)

    @staticmethod
    def _next_pending_stage(run: ProjectRun) -> str:
        for step in run.workflow.steps:
            if step.status in (
                WorkflowStatus.PENDING,
                WorkflowStatus.FAILED,
                WorkflowStatus.RETRYING,
            ):
                return step.stage
        return ""


# ------------------------------------------------------- module interface

_executor: "WorkflowExecutor | None" = None


def get_workflow_executor(
    store_dir: "str | Path | None" = None,
) -> WorkflowExecutor:
    global _executor
    if store_dir is not None:
        return WorkflowExecutor(store=WorkflowRunStore(store_dir))
    if _executor is None:
        _executor = WorkflowExecutor()
    return _executor


def reset_workflow_executor() -> None:
    global _executor
    _executor = None


def execute_workflow(command: str, **kwargs) -> ProjectRun:
    """Module-level convenience: create + execute a production workflow."""
    config = kwargs.pop("config", None)
    context_extra = kwargs.pop("context_extra", None)
    return get_workflow_executor().execute(
        command, config=config, context_extra=context_extra, **kwargs
    )


def _workflow_job_handler(payload: dict) -> dict:
    executor = get_workflow_executor(payload.get("store_dir"))
    if payload.get("resume_run_id"):
        run = executor.resume(payload["resume_run_id"])
    else:
        run = executor.execute(
            payload.get("command", ""),
            config=payload.get("config"),
            context_extra=payload.get("context_extra"),
        )
    return {
        "run_id": run.run_id,
        "status": run.status,
        "studio_status": studio_status(run),
        "result": run.result.to_dict(),
    }


def ensure_workflow_handler(queue) -> None:
    """Register workflow_run job handler (idempotent)."""
    if not queue.has_handler(WORKFLOW_JOB_TYPE):
        queue.register_handler(WORKFLOW_JOB_TYPE, _workflow_job_handler)
