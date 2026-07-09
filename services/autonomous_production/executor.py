"""Autonomous Production Executor (Agent 23).

Coordinates complete media productions from a single user request by driving
WorkflowExecutor → Orchestrator → engines. Does not call engines or providers
directly. Does not replace the Orchestrator or WorkflowExecutor.
"""

from __future__ import annotations

import time
from pathlib import Path

from core.log import get_logger, log_event
from services.autonomous_production.estimates import (
    estimate_cost_usd,
    estimate_runtime_sec,
    remaining_runtime_sec,
)
from services.autonomous_production.longform import (
    chapter_summaries,
    mark_chapter_status,
    prepare_longform_plan,
    should_split_units,
)
from services.autonomous_production.models import (
    Checkpoint,
    ExecutionContext,
    ExecutionState,
    ProductionJob,
    ProductionManifest,
    ProductionSummary,
    _now_iso,
)
from services.autonomous_production.modes import (
    mode_defaults,
    resolve_production_mode,
    workflow_type_for_mode,
)
from services.autonomous_production.observability import execution_log
from services.autonomous_production.parallel import run_units_parallel
from services.autonomous_production.quality import stage_results_from_workflow, validate_job
from services.autonomous_production.store import ProductionJobStore, get_production_store
from services.workflow_executor import (
    WorkflowConfig,
    WorkflowExecutor,
    WorkflowStatus,
    get_workflow_executor,
)
from services.workflow_executor.templates import apply_production_defaults, build_workflow_steps

logger = get_logger(__name__)

PRODUCTION_JOB_TYPE = "autonomous_production"


class AutonomousProductionExecutor:
    """Project manager over WorkflowExecutor for complete productions."""

    def __init__(
        self,
        store: "ProductionJobStore | None" = None,
        workflow_executor: "WorkflowExecutor | None" = None,
    ) -> None:
        self._store = store or get_production_store()
        self._workflow = workflow_executor

    @property
    def store(self) -> ProductionJobStore:
        return self._store

    def _wf(self) -> WorkflowExecutor:
        if self._workflow is not None:
            return self._workflow
        return get_workflow_executor()

    # ----------------------------------------------------------- create

    def create_job(
        self,
        command: str,
        *,
        production_mode: str = "",
        options: "dict | None" = None,
        config: "dict | WorkflowConfig | None" = None,
    ) -> ProductionJob:
        """Accept a production request and create a durable ProductionJob."""
        options = dict(options or {})
        mode = resolve_production_mode(command, production_mode or options.get("production_mode", ""))
        defaults = mode_defaults(mode)
        wf_type = workflow_type_for_mode(mode)

        if config is None and isinstance(options.get("workflow_config"), dict):
            config = options.get("workflow_config")

        if isinstance(config, WorkflowConfig):
            wf_cfg = config
        elif isinstance(config, dict):
            wf_cfg = WorkflowConfig.from_dict(config)
        else:
            wf_cfg = WorkflowConfig(
                production_type=wf_type,
                budget_usd=float(options.get("budget_usd", 0) or 0),
                quality_level=options.get("quality_level", defaults.get("quality_level", "standard")),
                platform_targets=list(options.get("platform_targets") or []),
                provider_preferences=dict(options.get("provider_preferences") or {}),
                longform_mode=bool(defaults.get("longform", False)),
                count=int(options.get("count") or defaults.get("unit_count", 1)),
                skip_stages=list(defaults.get("skip_stages") or []),
            )
        if not wf_cfg.production_type or wf_cfg.production_type == "short":
            wf_cfg.production_type = wf_type
        wf_cfg = apply_production_defaults(command, wf_cfg)

        steps = build_workflow_steps(wf_cfg)
        stages = [s.stage for s in steps]
        unit_count = int(options.get("unit_count") or defaults.get("unit_count", 1))
        cost = estimate_cost_usd(
            command,
            mode=mode,
            stages=stages,
            unit_count=unit_count,
            quality_level=wf_cfg.quality_level,
            budget_usd=wf_cfg.budget_usd,
        )
        runtime = estimate_runtime_sec(
            command,
            mode=mode,
            stages=stages,
            unit_count=unit_count,
            longform=wf_cfg.longform_mode,
        )

        ctx = ExecutionContext(
            command=command,
            production_mode=mode,
            options=options,
            workflow_config=wf_cfg.to_dict(),
            budget_usd=wf_cfg.budget_usd,
            estimated_cost_usd=float(cost["estimated_cost_usd"]),
            estimated_runtime_sec=runtime,
            platform_targets=list(wf_cfg.platform_targets),
            quality_level=wf_cfg.quality_level,
            longform=bool(wf_cfg.longform_mode),
            parallel_units=bool(defaults.get("parallel_units", False)),
            provider_preferences=dict(wf_cfg.provider_preferences),
        )
        manifest = ProductionManifest(
            production_mode=mode,
            title=(command[:80] + "…") if len(command) > 80 else command,
            command=command,
            stages=stages,
            unit_count=unit_count,
            estimated_cost_usd=float(cost["estimated_cost_usd"]),
            estimated_runtime_sec=runtime,
            estimated_duration_sec=runtime,
            platform_targets=list(wf_cfg.platform_targets),
            quality_level=wf_cfg.quality_level,
            longform=bool(wf_cfg.longform_mode),
            dependencies=[
                {"from": stages[i], "to": stages[i + 1]}
                for i in range(len(stages) - 1)
            ],
        )
        job = ProductionJob(
            command=command,
            production_mode=mode,
            state=ExecutionState.PENDING,
            context=ctx,
            manifest=manifest,
            summary=ProductionSummary(
                production_mode=mode,
                estimated_cost_usd=float(cost["estimated_cost_usd"]),
                estimated_runtime_sec=runtime,
            ),
        )
        prepare_longform_plan(job)
        job.append_log(
            "job.created",
            production_mode=mode,
            stages=len(stages),
            longform=job.context.longform,
            estimated_cost_usd=job.context.estimated_cost_usd,
            estimated_runtime_sec=runtime,
        )
        if cost.get("over_budget"):
            job.append_log("job.budget_warning", **cost)
            job.summary.warnings.append(
                f"Estimated cost {cost['estimated_cost_usd']} exceeds budget {cost['budget_usd']}"
            )
        self._persist(job)
        log_event(
            logger,
            "autonomous_production.job_created",
            job_id=job.job_id,
            production_mode=mode,
            stages=len(stages),
        )
        return job

    # ----------------------------------------------------------- execute

    def execute(
        self,
        command: str = "",
        *,
        production_mode: str = "",
        options: "dict | None" = None,
        config: "dict | WorkflowConfig | None" = None,
        job_id: str = "",
        resume: bool = False,
    ) -> ProductionJob:
        """Create (or load) a job and execute until complete / failed / cancelled / paused."""
        if resume or job_id:
            job = self.load_job(job_id)
            if job is None:
                raise ValueError(f"Production job {job_id!r} not found")
            return self.resume(job.job_id)

        if not command:
            raise ValueError("command is required to start a new production job")
        job = self.create_job(
            command,
            production_mode=production_mode,
            options=options,
            config=config,
        )
        return self._execute_job(job)

    def estimate(
        self,
        command: str,
        *,
        production_mode: str = "",
        options: "dict | None" = None,
    ) -> dict:
        """Cost + runtime estimate without executing."""
        job = self.create_job(command, production_mode=production_mode, options=options)
        return {
            "job_id": job.job_id,
            "production_mode": job.production_mode,
            "manifest": job.manifest.to_dict(),
            "estimated_cost_usd": job.context.estimated_cost_usd,
            "estimated_runtime_sec": job.context.estimated_runtime_sec,
            "chapters": list(job.context.chapters),
            "over_budget": bool(
                job.context.budget_usd
                and job.context.estimated_cost_usd > job.context.budget_usd
            ),
        }

    def resume(self, job_id: str) -> ProductionJob:
        job = self.load_job(job_id)
        if job is None:
            raise ValueError(f"Production job {job_id!r} not found")
        if job.state == ExecutionState.CANCELLED:
            job.append_log("job.resume_blocked", reason="cancelled")
            self._persist(job)
            return job
        if job.state == ExecutionState.COMPLETED:
            return job

        job.state = ExecutionState.RUNNING
        job.paused_at = ""
        job.append_log("job.resumed", workflow_run_id=job.workflow_run_id)
        self._persist(job)

        if job.child_job_ids and should_split_units(job):
            return self._resume_units(job)
        return self._execute_job(job, resuming=True)

    def pause(self, job_id: str) -> ProductionJob:
        job = self.load_job(job_id)
        if job is None:
            raise ValueError(f"Production job {job_id!r} not found")
        if job.state not in (ExecutionState.RUNNING, ExecutionState.SCHEDULED, ExecutionState.PENDING):
            return job
        job.state = ExecutionState.PAUSED
        job.paused_at = _now_iso()
        job.append_log("job.paused", stage=job.current_stage)
        if job.workflow_run_id:
            try:
                self._wf().pause(job.workflow_run_id)
            except Exception as exc:  # noqa: BLE001
                job.append_log("job.pause_workflow_warning", error=str(exc))
        self._checkpoint(job)
        self._persist(job)
        return job

    def cancel(self, job_id: str) -> ProductionJob:
        job = self.load_job(job_id)
        if job is None:
            raise ValueError(f"Production job {job_id!r} not found")
        job.state = ExecutionState.CANCELLED
        job.finished_at = _now_iso()
        job.append_log("job.cancelled")
        if job.workflow_run_id:
            try:
                self._wf().cancel(job.workflow_run_id)
            except Exception as exc:  # noqa: BLE001
                job.append_log("job.cancel_workflow_warning", error=str(exc))
        for child_id in list(job.child_job_ids):
            try:
                self.cancel(child_id)
            except Exception:  # noqa: BLE001
                pass
        self._checkpoint(job, status=ExecutionState.CANCELLED)
        self._persist(job)
        return job

    def schedule(
        self,
        command: str,
        *,
        production_mode: str = "",
        options: "dict | None" = None,
        run_at: str = "",
        queue=None,
    ) -> dict:
        from services.autonomous_production.scheduler import schedule_job

        job = self.create_job(command, production_mode=production_mode, options=options)
        result = schedule_job(
            job,
            queue=queue,
            run_at=run_at,
            store_dir=str(self._store.directory),
        )
        self._persist(job)
        return {**result, "job": job.to_dict()}

    def load_job(self, job_id: str) -> "ProductionJob | None":
        return self._store.load(job_id)

    def list_jobs(self, state: str = "") -> list[dict]:
        return self._store.list_jobs(state=state)

    def get_status(self, job_id: str) -> dict:
        job = self.load_job(job_id)
        if job is None:
            return {"error": f"job {job_id!r} not found", "state": "missing"}
        return execution_log(job)

    # -------------------------------------------------------- internals

    def _execute_job(self, job: ProductionJob, *, resuming: bool = False) -> ProductionJob:
        if job.state == ExecutionState.PAUSED:
            return job

        if not resuming or not job.started_at:
            job.started_at = _now_iso()
        job.state = ExecutionState.RUNNING
        job.append_log("job.started", resuming=resuming)
        self._persist(job)

        # Multi-unit fan-out (course / series / campaign).
        if should_split_units(job) and not job.parent_job_id:
            return self._execute_units(job)

        return self._execute_single(job, resuming=resuming)

    def _execute_single(self, job: ProductionJob, *, resuming: bool = False) -> ProductionJob:
        wf = self._wf()
        wf_cfg = WorkflowConfig.from_dict(job.context.workflow_config)

        started = time.time()
        try:
            if resuming and job.workflow_run_id:
                run = wf.resume(job.workflow_run_id)
            else:
                context_extra = {
                    "production_job_id": job.job_id,
                    "production_mode": job.production_mode,
                    "autonomous_production": True,
                    "chapters": list(job.context.chapters),
                    "scene_groups": list(job.context.scene_groups),
                    **dict(job.context.extras),
                    **dict(job.context.options.get("context_extra") or {}),
                }
                run = wf.execute(
                    job.command,
                    config=wf_cfg,
                    context_extra=context_extra,
                )
        except Exception as exc:  # noqa: BLE001
            job.state = ExecutionState.FAILED
            job.summary.error = str(exc)
            job.summary.failures.append(
                {"code": "workflow_exception", "message": str(exc)}
            )
            job.append_log("job.failed", error=str(exc))
            job.finished_at = _now_iso()
            self._checkpoint(job, status=ExecutionState.FAILED)
            self._persist(job)
            return job

        # Pause requested mid-flight (workflow returned paused).
        if run.status == WorkflowStatus.PAUSED or getattr(run, "status", "") == "paused":
            job.workflow_run_id = run.run_id
            job.state = ExecutionState.PAUSED
            job.paused_at = _now_iso()
            self._sync_from_run(job, run)
            job.append_log("job.paused_from_workflow")
            self._checkpoint(job, status=ExecutionState.PAUSED)
            self._persist(job)
            return job

        job.workflow_run_id = run.run_id
        self._sync_from_run(job, run)
        self._finalize(job, run, elapsed=time.time() - started)
        return job

    def _execute_units(self, job: ProductionJob) -> ProductionJob:
        chapters = list(job.context.chapters)
        child_jobs: list[ProductionJob] = []
        for ch in chapters:
            child = self.create_job(
                ch.get("command") or job.command,
                production_mode=job.production_mode,
                options={
                    **job.context.options,
                    "force_single_unit": True,
                    "unit_count": 1,
                    "parent_job_id": job.job_id,
                    "chapter_index": ch.get("index", 0),
                },
                config=WorkflowConfig.from_dict(job.context.workflow_config),
            )
            child.parent_job_id = job.job_id
            child.context.longform = job.context.longform
            child.context.chapters = [ch]
            self._persist(child)
            child_jobs.append(child)
            ch["job_id"] = child.job_id
            mark_chapter_status(job, int(ch.get("index", 0)), "running")

        job.child_job_ids = [c.job_id for c in child_jobs]
        job.append_log("job.units_spawned", count=len(child_jobs))
        self._persist(job)

        def _run_child(child: ProductionJob) -> ProductionJob:
            return self._execute_single(child)

        if job.context.parallel_units:
            finished = run_units_parallel(child_jobs, _run_child, max_workers=4)
        else:
            finished = [_run_child(c) for c in child_jobs]

        # Refresh children from store (persisted state).
        finished = [self.load_job(c.job_id) or c for c in finished]
        for child in finished:
            idx = int(child.context.options.get("chapter_index", 0))
            status = (
                "completed"
                if child.state == ExecutionState.COMPLETED
                else "failed"
                if child.state == ExecutionState.FAILED
                else child.state
            )
            mark_chapter_status(job, idx, status)

        self._finalize_parent(job, finished)
        return job

    def _resume_units(self, job: ProductionJob) -> ProductionJob:
        children = []
        for cid in job.child_job_ids:
            child = self.load_job(cid)
            if child is None:
                continue
            if child.state in (ExecutionState.COMPLETED, ExecutionState.CANCELLED):
                children.append(child)
                continue
            children.append(self.resume(cid))
        self._finalize_parent(job, children)
        return job

    def _sync_from_run(self, job: ProductionJob, run) -> None:
        from services.workflow_executor.status import studio_status

        snap = studio_status(run)
        job.progress_pct = float(snap.get("progress") or run.workflow.progress_pct or 0)
        job.current_stage = str(snap.get("current_stage") or "")
        job.remaining_sec = remaining_runtime_sec(
            job.context.estimated_runtime_sec, job.progress_pct
        )
        job.summary.stage_results = stage_results_from_workflow(run)
        job.summary.packages = list(run.result.packages or [])
        job.summary.provider_usage = dict(run.provider_usage or run.result.provider_usage or {})
        job.summary.actual_cost_usd = float(
            run.estimated_cost_usd or run.result.estimated_cost_usd or 0
        )
        job.summary.production_report = dict(run.result.production_report or {})
        job.summary.partial = bool(run.result.partial)
        job.summary.error = run.result.error or ""
        for fr in run.result.failure_reports or []:
            if hasattr(fr, "to_dict"):
                job.summary.failures.append(fr.to_dict())
            elif isinstance(fr, dict):
                job.summary.failures.append(fr)
        job.summary.chapter_summaries = chapter_summaries(job)

    def _finalize(self, job: ProductionJob, run, *, elapsed: float) -> None:
        if run.status == WorkflowStatus.COMPLETED:
            job.state = ExecutionState.PARTIAL if run.result.partial else ExecutionState.COMPLETED
        elif run.status == WorkflowStatus.CANCELLED:
            job.state = ExecutionState.CANCELLED
        elif run.status == WorkflowStatus.FAILED:
            job.state = ExecutionState.FAILED
        else:
            job.state = ExecutionState.FAILED if run.result.error else ExecutionState.COMPLETED

        job.summary.status = job.state
        job.summary.elapsed_sec = round(elapsed, 2)
        job.summary.estimated_cost_usd = job.context.estimated_cost_usd
        qc = validate_job(job)
        job.summary.quality_score = float(qc["quality_score"])
        job.summary.quality_report = qc
        job.summary.warnings = list(dict.fromkeys(job.summary.warnings + list(qc.get("warnings") or [])))
        job.finished_at = _now_iso()
        job.progress_pct = float(run.workflow.progress_pct or job.progress_pct)
        job.remaining_sec = 0.0 if job.state in (
            ExecutionState.COMPLETED,
            ExecutionState.FAILED,
            ExecutionState.CANCELLED,
            ExecutionState.PARTIAL,
        ) else job.remaining_sec
        job.append_log(
            "job.finished",
            state=job.state,
            quality_score=job.summary.quality_score,
            elapsed_sec=job.summary.elapsed_sec,
        )
        self._checkpoint(job, status=job.state)
        self._persist(job)
        log_event(
            logger,
            "autonomous_production.job_finished",
            job_id=job.job_id,
            state=job.state,
            quality_score=job.summary.quality_score,
        )

    def _finalize_parent(self, job: ProductionJob, children: list[ProductionJob]) -> None:
        job.summary.unit_results = [
            {
                "job_id": c.job_id,
                "state": c.state,
                "quality_score": c.summary.quality_score,
                "error": c.summary.error,
                "packages": len(c.summary.packages),
            }
            for c in children
        ]
        job.summary.packages = [
            pkg for c in children for pkg in (c.summary.packages or [])
        ]
        job.summary.stage_results = [
            sr for c in children for sr in (c.summary.stage_results or [])
        ]
        job.summary.actual_cost_usd = sum(c.summary.actual_cost_usd for c in children)
        job.summary.elapsed_sec = sum(c.summary.elapsed_sec for c in children)
        job.summary.chapter_summaries = chapter_summaries(job)
        job.summary.provider_usage = {
            "units": len(children),
            "per_unit": [c.summary.provider_usage for c in children],
        }

        failed = [c for c in children if c.state == ExecutionState.FAILED]
        cancelled = [c for c in children if c.state == ExecutionState.CANCELLED]
        completed = [
            c
            for c in children
            if c.state in (ExecutionState.COMPLETED, ExecutionState.PARTIAL)
        ]
        if cancelled and not completed and not failed:
            job.state = ExecutionState.CANCELLED
        elif failed and not completed:
            job.state = ExecutionState.FAILED
            job.summary.error = "; ".join(c.summary.error for c in failed if c.summary.error)
        elif failed or any(c.state == ExecutionState.PARTIAL for c in children):
            job.state = ExecutionState.PARTIAL
            job.summary.partial = True
        else:
            job.state = ExecutionState.COMPLETED

        job.summary.status = job.state
        job.progress_pct = 100.0 if job.state in (
            ExecutionState.COMPLETED,
            ExecutionState.PARTIAL,
        ) else round(100.0 * len(completed) / max(len(children), 1), 1)
        qc = validate_job(job)
        job.summary.quality_score = float(qc["quality_score"])
        job.summary.quality_report = qc
        job.finished_at = _now_iso()
        job.append_log("job.units_finished", state=job.state, units=len(children))
        self._checkpoint(job, status=job.state)
        self._persist(job)

    def _checkpoint(self, job: ProductionJob, status: str = "") -> Checkpoint:
        completed = [
            sr.stage if hasattr(sr, "stage") else sr.get("stage", "")
            for sr in job.summary.stage_results
            if (getattr(sr, "status", None) or (sr.get("status") if isinstance(sr, dict) else ""))
            in (ExecutionState.COMPLETED, "completed", "skipped")
        ]
        chapter_index = 0
        for ch in job.context.chapters:
            if ch.get("status") in ("running", "pending", "failed"):
                chapter_index = int(ch.get("index", 0))
                break
            chapter_index = int(ch.get("index", 0))
        ckpt = Checkpoint(
            job_id=job.job_id,
            workflow_run_id=job.workflow_run_id,
            completed_stages=completed,
            current_stage=job.current_stage,
            chapter_index=chapter_index,
            scene_group_index=chapter_index,
            context_snapshot={
                "command": job.command,
                "production_mode": job.production_mode,
                "chapters": list(job.context.chapters),
                "options": dict(job.context.options),
            },
            status=status or job.state,
            created_at=(job.checkpoint.created_at if job.checkpoint else _now_iso()),
            updated_at=_now_iso(),
            error=job.summary.error,
        )
        if job.checkpoint:
            ckpt.checkpoint_id = job.checkpoint.checkpoint_id
        job.checkpoint = ckpt
        self._store.save_checkpoint(ckpt)
        return ckpt

    def _persist(self, job: ProductionJob) -> None:
        job.updated_at = _now_iso()
        self._store.save(job)


# ------------------------------------------------------- module interface

_executor: "AutonomousProductionExecutor | None" = None


def get_production_executor(
    store_dir: "str | Path | None" = None,
) -> AutonomousProductionExecutor:
    global _executor
    if store_dir is not None:
        return AutonomousProductionExecutor(store=ProductionJobStore(store_dir))
    if _executor is None:
        _executor = AutonomousProductionExecutor()
    return _executor


def reset_production_executor() -> None:
    global _executor
    _executor = None


def execute_production(command: str, **kwargs) -> ProductionJob:
    """Module-level convenience: create + execute a production job."""
    return get_production_executor().execute(command, **kwargs)


def _production_job_handler(payload: dict) -> dict:
    executor = get_production_executor(payload.get("store_dir"))
    if payload.get("resume_job_id"):
        job = executor.resume(payload["resume_job_id"])
    elif payload.get("job_id") and not payload.get("command"):
        job = executor.resume(payload["job_id"])
    else:
        job = executor.execute(
            payload.get("command", ""),
            production_mode=(payload.get("config") or {}).get("production_mode", ""),
            options=payload.get("config"),
        )
    return {
        "job_id": job.job_id,
        "state": job.state,
        "status": execution_log(job),
        "summary": job.summary.to_dict(),
    }


def ensure_production_handler(queue) -> None:
    """Register autonomous_production job handler (idempotent)."""
    if not queue.has_handler(PRODUCTION_JOB_TYPE):
        queue.register_handler(PRODUCTION_JOB_TYPE, _production_job_handler)
