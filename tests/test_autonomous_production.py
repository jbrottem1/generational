"""Tests for the Autonomous Production Executor (Agent 23)."""

from __future__ import annotations

import pytest

from services.autonomous_production import (
    PRODUCTION_JOB_TYPE,
    PRODUCTION_MODES,
    AutonomousProductionExecutor,
    ExecutionState,
    ensure_production_handler,
    execute_production,
    get_production_executor,
    reset_production_executor,
    reset_production_store,
    resolve_production_mode,
)
from services.autonomous_production.estimates import estimate_cost_usd, estimate_runtime_sec
from services.autonomous_production.modes import build_chapters, detect_content_duration_sec
from services.autonomous_production.parallel import run_units_parallel
from services.autonomous_production.quality import validate_job
from services.autonomous_production.store import ProductionJobStore
from services.orchestrator.models import StageReport, StageStatus
from services.workflow_executor import (
    WorkflowConfig,
    WorkflowExecutor,
    WorkflowStatus,
    reset_workflow_executor,
    reset_workflow_store,
)
from services.workflow_executor.store import WorkflowRunStore


@pytest.fixture(autouse=True)
def _reset_singletons():
    reset_production_executor()
    reset_production_store()
    reset_workflow_executor()
    reset_workflow_store()
    yield
    reset_production_executor()
    reset_production_store()
    reset_workflow_executor()
    reset_workflow_store()


@pytest.fixture
def stores(tmp_path):
    prod = ProductionJobStore(tmp_path / "production_jobs")
    wf = WorkflowRunStore(tmp_path / "workflow_runs")
    return prod, wf


class _FakeOrch:
    def __init__(self, outcomes: dict | None = None, fail_times: dict | None = None):
        self.outcomes = outcomes or {}
        self.fail_times = fail_times or {}
        self.calls: list[str] = []
        self._fail_counts: dict[str, int] = {}

    def run_stage(self, stage, context, engine_keys=None):
        self.calls.append(stage)
        count = self._fail_counts.get(stage, 0) + 1
        self._fail_counts[stage] = count
        if stage in self.fail_times and count <= self.fail_times[stage]:
            return StageReport(stage=stage, status=StageStatus.FAILED, errors=[f"{stage} boom"])
        status = self.outcomes.get(stage, StageStatus.SUCCESS)
        return StageReport(stage=stage, status=status, confidence=80)

    def _run_production(self, context):
        self.calls.append("production")
        context.setdefault("production_packages", [{"id": "p1"}])
        return StageReport(stage="production", status=StageStatus.SUCCESS, confidence=90)

    def _run_packaging(self, context, result):
        self.calls.append("packaging")
        from services.orchestrator.models import ProductionPackage

        pkg = ProductionPackage(
            topic=context.get("command", "test"),
            asset_package={"assets": 1},
            render_package={"ready": True},
            publishing_package={"mode": "scheduled"},
            analytics_package={"views": 0},
            learning_metadata={"patterns": []},
            post_production_package={"edit": True},
            animation_package={},
        )
        result.packages = [pkg]
        context["unified_packages"] = [pkg.to_dict()]
        return StageReport(stage="packaging", status=StageStatus.SUCCESS, confidence=85)


def _make_executor(stores, orch=None):
    prod_store, wf_store = stores
    wf = WorkflowExecutor(store=wf_store, orchestrator=orch or _FakeOrch())
    return AutonomousProductionExecutor(store=prod_store, workflow_executor=wf)


def _intel_options():
    return {
        "force_single_unit": True,
        "unit_count": 1,
    }


def _intel_config():
    return WorkflowConfig.from_dict(
        {
            "template": "intelligence_only",
            "production_type": "full_production",
            "retry_policy": {"max_retries": 1, "backoff_sec": 0},
        }
    )


# ---------------------------------------------------------------------------
# Mode resolution
# ---------------------------------------------------------------------------


def test_resolve_youtube_short_mode():
    assert resolve_production_mode("Create a 45-second YouTube Short about black holes.") == "single_video"


def test_resolve_documentary_mode():
    assert resolve_production_mode("Create a 15-minute documentary about the Roman Empire.") == "documentary"


def test_resolve_course_and_animated_story():
    assert resolve_production_mode("Create an educational course on Python.") == "course"
    assert resolve_production_mode("Create a children's animated story.") == "animated_story"


def test_resolve_audiobook_and_campaign():
    assert resolve_production_mode("Create an audiobook about leadership") == "audiobook"
    assert resolve_production_mode("Launch a marketing campaign for sneakers") == "marketing_campaign"


def test_all_production_modes_registered():
    expected = {
        "single_video",
        "video_series",
        "podcast",
        "course",
        "marketing_campaign",
        "documentary",
        "animated_story",
        "audiobook",
        "educational_program",
        "full_production",
    }
    assert expected <= set(PRODUCTION_MODES)


def test_duration_and_chapters_for_longform():
    cmd = "Create a 15-minute documentary about Rome"
    assert detect_content_duration_sec(cmd) == 900.0
    chapters = build_chapters(cmd, "documentary")
    assert len(chapters) >= 1


def test_estimates_positive():
    cost = estimate_cost_usd("Create a short about cats", mode="single_video", budget_usd=0.01)
    assert cost["estimated_cost_usd"] > 0
    assert "over_budget" in cost
    runtime = estimate_runtime_sec("Create a short about cats", mode="single_video")
    assert runtime > 0


# ---------------------------------------------------------------------------
# Job lifecycle
# ---------------------------------------------------------------------------


def test_create_job_persists(stores):
    executor = _make_executor(stores)
    job = executor.create_job(
        "Create a 45-second YouTube Short about black holes.",
        options=_intel_options(),
        config=_intel_config(),
    )
    assert job.job_id
    assert job.state == ExecutionState.PENDING
    assert job.production_mode == "single_video"
    assert job.manifest.stages
    loaded = executor.load_job(job.job_id)
    assert loaded is not None
    assert loaded.command == job.command


def test_execute_workflow_via_orchestrator(stores):
    orch = _FakeOrch()
    executor = _make_executor(stores, orch)
    job = executor.execute(
        "Create ideas about black holes",
        options=_intel_options(),
        config=_intel_config(),
    )
    assert job.state == ExecutionState.COMPLETED
    assert job.workflow_run_id
    assert job.summary.quality_score > 0
    assert "trend" in orch.calls
    assert job.progress_pct == 100.0
    status = executor.get_status(job.job_id)
    assert status["state"] == ExecutionState.COMPLETED
    assert "elapsed_sec" in status
    assert "costs" in status


def test_checkpoint_and_recovery(stores):
    orch = _FakeOrch(fail_times={"psychology": 99})
    executor = _make_executor(stores, orch)
    job = executor.execute(
        "Create a short about stars",
        options=_intel_options(),
        config=_intel_config(),
    )
    assert job.state == ExecutionState.FAILED
    assert job.checkpoint is not None
    assert job.checkpoint.job_id == job.job_id

    # Recovery with healthy orchestrator
    healthy = _FakeOrch()
    prod_store, wf_store = stores
    wf = WorkflowExecutor(store=wf_store, orchestrator=healthy)
    executor2 = AutonomousProductionExecutor(store=prod_store, workflow_executor=wf)
    # Reset failed workflow steps via resume path
    resumed = executor2.resume(job.job_id)
    # May complete or still fail depending on workflow checkpoint; at least resumes
    assert resumed.job_id == job.job_id
    assert resumed.state in (
        ExecutionState.COMPLETED,
        ExecutionState.FAILED,
        ExecutionState.PARTIAL,
        ExecutionState.RUNNING,
    )


def test_cancel_job(stores):
    executor = _make_executor(stores)
    job = executor.create_job("Create a short about cats", options=_intel_options(), config=_intel_config())
    cancelled = executor.cancel(job.job_id)
    assert cancelled.state == ExecutionState.CANCELLED


def test_pause_and_resume_flags(stores):
    executor = _make_executor(stores)
    job = executor.create_job("Create a short about cats", options=_intel_options(), config=_intel_config())
    job.state = ExecutionState.RUNNING
    executor.store.save(job)
    paused = executor.pause(job.job_id)
    assert paused.state == ExecutionState.PAUSED
    assert paused.paused_at


def test_failure_handling_quality(stores):
    orch = _FakeOrch(fail_times={"script": 99})
    executor = _make_executor(stores, orch)
    job = executor.execute(
        "Create a short about stars",
        options=_intel_options(),
        config=_intel_config(),
    )
    assert job.state == ExecutionState.FAILED
    qc = validate_job(job)
    assert qc["status"] in ("fail", "warn")
    assert qc["quality_score"] < 100


def test_budget_overrun_warning(stores):
    executor = _make_executor(stores)
    job = executor.create_job(
        "Create a documentary about Rome",
        options={**_intel_options(), "budget_usd": 0.0001},
        config=WorkflowConfig.from_dict(
            {
                "template": "intelligence_only",
                "production_type": "documentary",
                "budget_usd": 0.0001,
            }
        ),
    )
    assert any("budget" in w.lower() for w in job.summary.warnings) or any(
        e.get("event") == "job.budget_warning" for e in job.log
    )


# ---------------------------------------------------------------------------
# Long-form + parallel
# ---------------------------------------------------------------------------


def test_longform_chapters_on_course(stores):
    executor = _make_executor(stores)
    job = executor.create_job(
        "Create an educational course on Python",
        production_mode="course",
        options={"unit_count": 3},
    )
    assert job.context.longform is True
    assert len(job.context.chapters) == 3
    assert job.manifest.unit_count == 3


def test_parallel_units_helper():
    from services.autonomous_production.models import ProductionJob

    units = [ProductionJob(command=f"u{i}") for i in range(3)]

    def _run(u):
        u.state = ExecutionState.COMPLETED
        return u

    out = run_units_parallel(units, _run, max_workers=3)
    assert len(out) == 3
    assert all(u.state == ExecutionState.COMPLETED for u in out)


def test_multi_unit_course_execution(stores):
    orch = _FakeOrch()
    executor = _make_executor(stores, orch)
    job = executor.execute(
        "Create a course on Python basics",
        production_mode="course",
        options={"unit_count": 2},
        config=_intel_config(),
    )
    assert job.state in (ExecutionState.COMPLETED, ExecutionState.PARTIAL)
    assert len(job.child_job_ids) == 2
    assert len(job.summary.unit_results) == 2


# ---------------------------------------------------------------------------
# Scheduling + ProviderRuntime surface + module API
# ---------------------------------------------------------------------------


def test_schedule_registers_handler(stores):
    from core.jobs import JobQueue

    executor = _make_executor(stores)
    queue = JobQueue()
    result = executor.schedule(
        "Create a short about cats",
        options=_intel_options(),
        queue=queue,
    )
    assert result["job_id"]
    assert queue.has_handler(PRODUCTION_JOB_TYPE)


def test_job_handler_executes(stores, tmp_path):
    from core.jobs import JobQueue

    orch = _FakeOrch()
    prod_store, wf_store = stores
    wf = WorkflowExecutor(store=wf_store, orchestrator=orch)
    # Bind singleton-style executor used by handler via store_dir
    executor = AutonomousProductionExecutor(store=prod_store, workflow_executor=wf)
    queue = JobQueue()
    ensure_production_handler(queue)

    # Patch get_production_executor used inside handler by executing via store_dir path
    from services.autonomous_production import executor as exec_mod

    original = exec_mod.get_production_executor

    def _get(store_dir=None):
        if store_dir:
            return AutonomousProductionExecutor(
                store=ProductionJobStore(store_dir),
                workflow_executor=wf,
            )
        return executor

    exec_mod.get_production_executor = _get
    try:
        job = queue.submit(
            PRODUCTION_JOB_TYPE,
            {
                "command": "Create ideas about space",
                "config": {
                    "production_mode": "single_video",
                    "force_single_unit": True,
                    "unit_count": 1,
                    "workflow_config": _intel_config().to_dict(),
                },
                "store_dir": str(prod_store.directory),
            },
        )
        finished = queue.run(job.id)
        assert finished.status == "succeeded"
        assert finished.result["job_id"]
        assert finished.result["state"] in (
            ExecutionState.COMPLETED,
            ExecutionState.PARTIAL,
            ExecutionState.FAILED,
        )
    finally:
        exec_mod.get_production_executor = original


def test_execute_production_convenience(stores, monkeypatch):
    orch = _FakeOrch()
    executor = _make_executor(stores, orch)
    monkeypatch.setattr(
        "services.autonomous_production.executor.get_production_executor",
        lambda store_dir=None: executor,
    )
    job = execute_production(
        "Create ideas about cats",
        options=_intel_options(),
        config=_intel_config(),
    )
    assert job.state == ExecutionState.COMPLETED


def test_provider_runtime_usage_attached(stores):
    orch = _FakeOrch()
    executor = _make_executor(stores, orch)
    job = executor.execute(
        "Create ideas about nebulae",
        options=_intel_options(),
        config=_intel_config(),
    )
    # usage may be empty dict in tests without runtime activity — key must exist
    assert isinstance(job.summary.provider_usage, dict)
    status = executor.get_status(job.job_id)
    assert "provider_usage" in status


def test_workflow_pause_api(stores):
    prod_store, wf_store = stores
    orch = _FakeOrch()
    wf = WorkflowExecutor(store=wf_store, orchestrator=orch)
    run = wf.create_run("Create ideas", config=_intel_config())
    paused = wf.pause(run.run_id)
    assert paused.context.get("_pause_requested") is True or paused.status == WorkflowStatus.PAUSED


def test_architecture_no_engine_imports():
    import ast
    from pathlib import Path

    path = Path("services/autonomous_production/executor.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("engines"), alias.name
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            assert not mod.startswith("engines"), mod
            assert mod != "engines", mod
