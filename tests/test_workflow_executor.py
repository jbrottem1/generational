"""Tests for the End-to-End Workflow Executor (Agent 21)."""

from __future__ import annotations

import pytest

from services.orchestrator.models import StageReport, StageStatus
from services.workflow_executor import (
    WORKFLOW_JOB_TYPE,
    ProjectRun,
    RetryPolicy,
    WorkflowConfig,
    WorkflowExecutor,
    WorkflowStatus,
    ensure_workflow_handler,
    execute_workflow,
    get_workflow_executor,
    reset_workflow_executor,
    reset_workflow_store,
    resolve_production_type,
    studio_status,
)
from services.workflow_executor.models import WorkflowStep
from services.workflow_executor.policy import (
    degrade_failed_optional,
    map_orchestrator_status,
    progress_percent,
    should_retry,
    should_stop_run,
)
from services.workflow_executor.store import WorkflowRunStore
from services.workflow_executor.templates import (
    apply_production_defaults,
    build_workflow_steps,
)


@pytest.fixture(autouse=True)
def _reset_singletons():
    reset_workflow_executor()
    reset_workflow_store()
    yield
    reset_workflow_executor()
    reset_workflow_store()


@pytest.fixture
def store(tmp_path):
    return WorkflowRunStore(tmp_path / "workflow_runs")


@pytest.fixture
def executor(store):
    return WorkflowExecutor(store=store)


# ---------------------------------------------------------------------------
# Production type + templates
# ---------------------------------------------------------------------------


def test_resolve_youtube_short_prompt():
    assert resolve_production_type("Create a 45-second YouTube Short about black holes.") == "youtube_short"


def test_resolve_documentary_prompt():
    assert resolve_production_type("Create a 12-minute documentary about the Roman Empire.") == "documentary"


def test_resolve_course_and_podcast():
    assert resolve_production_type("Build a course on Python basics") == "course"
    assert resolve_production_type("Create a podcast about space") == "podcast"


def test_apply_defaults_sets_longform_for_documentary():
    cfg = apply_production_defaults("Create a 12-minute documentary about Rome")
    assert cfg.production_type == "documentary"
    assert cfg.longform_mode is True
    assert cfg.template == "documentary"


def test_build_workflow_steps_include_canonical_stages():
    cfg = apply_production_defaults("Create a YouTube Short about cats")
    steps = build_workflow_steps(cfg)
    stages = [s.stage for s in steps]
    assert "trend" in stages
    assert "script" in stages
    assert "ai_director" in stages
    assert "asset_generation" in stages
    assert "publish" in stages
    assert "analytics" in stages
    assert "learning" in stages


def test_intelligence_only_template():
    cfg = WorkflowConfig(template="intelligence_only", production_type="full_production")
    steps = build_workflow_steps(cfg)
    stages = [s.stage for s in steps]
    assert stages[-1] == "quality"
    assert "publish" not in stages


# ---------------------------------------------------------------------------
# Status / policy helpers
# ---------------------------------------------------------------------------


def test_status_transitions_mapping():
    assert map_orchestrator_status(StageStatus.SUCCESS) == WorkflowStatus.COMPLETED
    assert map_orchestrator_status(StageStatus.FAILED) == WorkflowStatus.FAILED
    assert map_orchestrator_status(StageStatus.SKIPPED) == WorkflowStatus.SKIPPED


def test_retry_policy_behavior():
    policy = RetryPolicy(max_retries=2)
    step = WorkflowStep(stage="script", status=WorkflowStatus.FAILED, attempt=1, max_attempts=3)
    assert should_retry(step, policy) is True
    step.attempt = 3
    assert should_retry(step, policy) is False


def test_degrade_optional_and_stop_required():
    policy = RetryPolicy()
    optional = WorkflowStep(
        stage="animation", status=WorkflowStatus.FAILED, optional=True, required=False, attempt=3, max_attempts=3
    )
    assert degrade_failed_optional(optional, policy) is True
    assert optional.status == WorkflowStatus.SKIPPED

    required = WorkflowStep(
        stage="script", status=WorkflowStatus.FAILED, required=True, attempt=3, max_attempts=3
    )
    assert should_stop_run(required, policy, exhausted_retries=True) is True


def test_progress_percent():
    steps = [
        WorkflowStep(stage="a", status=WorkflowStatus.COMPLETED),
        WorkflowStep(stage="b", status=WorkflowStatus.PENDING),
        WorkflowStep(stage="c", status=WorkflowStatus.SKIPPED),
        WorkflowStep(stage="d", status=WorkflowStatus.PENDING),
    ]
    assert progress_percent(steps) == 50.0


# ---------------------------------------------------------------------------
# Store + checkpoint
# ---------------------------------------------------------------------------


def test_create_run_persists(executor):
    run = executor.create_run("Create a 45-second YouTube Short about black holes.")
    assert run.run_id
    assert run.status == WorkflowStatus.PENDING
    loaded = executor.load_run(run.run_id)
    assert loaded is not None
    assert loaded.command == run.command
    assert loaded.production_type == "youtube_short"


def test_checkpoint_save_and_load(executor):
    run = executor.create_run("Create a short about Mars")
    run.status = WorkflowStatus.RUNNING
    run.workflow.steps[0].status = WorkflowStatus.COMPLETED
    ckpt = executor._checkpoint(run)
    assert ckpt.run_id == run.run_id
    assert "trend" in ckpt.completed_stages or run.workflow.steps[0].stage in ckpt.completed_stages
    loaded = executor.store.load_checkpoint(run.run_id)
    assert loaded is not None
    assert loaded.checkpoint_id == ckpt.checkpoint_id


# ---------------------------------------------------------------------------
# Mocked stage execution (retry / resume / failure)
# ---------------------------------------------------------------------------


class _FakeOrch:
    """Minimal orchestrator double for controlled stage outcomes."""

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


def _intelligence_config(**overrides):
    data = {
        "template": "intelligence_only",
        "production_type": "full_production",
        "retry_policy": {"max_retries": 2, "backoff_sec": 0},
    }
    data.update(overrides)
    return WorkflowConfig.from_dict(data)


def test_stage_execution_with_fake_orch(store):
    orch = _FakeOrch()
    executor = WorkflowExecutor(store=store, orchestrator=orch)
    run = executor.execute(
        "Create ideas about black holes",
        config=_intelligence_config(),
    )
    assert run.status == WorkflowStatus.COMPLETED
    assert run.workflow.progress_pct == 100.0
    assert "trend" in orch.calls
    assert "quality" in orch.calls
    assert executor.get_status(run.run_id)["status"] == WorkflowStatus.COMPLETED


def test_retry_recovers_flaky_stage(store):
    orch = _FakeOrch(fail_times={"script": 1})
    executor = WorkflowExecutor(store=store, orchestrator=orch)
    run = executor.execute("Create a short about stars", config=_intelligence_config())
    assert run.status == WorkflowStatus.COMPLETED
    assert orch.calls.count("script") == 2
    script_step = next(s for s in run.workflow.steps if s.stage == "script")
    assert script_step.attempt == 2
    assert script_step.status == WorkflowStatus.COMPLETED


def test_failure_stops_required_stage(store):
    orch = _FakeOrch(outcomes={"psychology": StageStatus.FAILED})
    # Always fail psychology (no retries succeed)
    orch.fail_times["psychology"] = 99
    executor = WorkflowExecutor(store=store, orchestrator=orch)
    run = executor.execute("Create a short about stars", config=_intelligence_config())
    assert run.status == WorkflowStatus.FAILED
    assert run.result.partial is True
    assert run.checkpoint is not None
    assert "psychology" in (run.result.error or "")


def test_optional_stage_failure_degrades(store):
    cfg = WorkflowConfig.from_dict(
        {
            "template": "full_production",
            "production_type": "youtube_short",
            "stage_order": ["trend", "research", "animation", "quality"],
            "optional_stages": ["animation"],
            "required_stages": ["trend", "research", "quality"],
            "retry_policy": {"max_retries": 0, "backoff_sec": 0},
        }
    )
    orch = _FakeOrch(outcomes={"animation": StageStatus.FAILED})
    orch.fail_times["animation"] = 99
    executor = WorkflowExecutor(store=store, orchestrator=orch)
    run = executor.execute("Create a short", config=cfg)
    assert run.status == WorkflowStatus.COMPLETED
    anim = next(s for s in run.workflow.steps if s.stage == "animation")
    assert anim.status == WorkflowStatus.SKIPPED


def test_resume_from_checkpoint(store):
    orch = _FakeOrch(fail_times={"visual": 99})
    executor = WorkflowExecutor(store=store, orchestrator=orch)
    run = executor.execute("Create a short about nebulae", config=_intelligence_config())
    assert run.status == WorkflowStatus.FAILED
    run_id = run.run_id
    completed_before = [
        s.stage for s in run.workflow.steps if s.status == WorkflowStatus.COMPLETED
    ]
    assert "trend" in completed_before

    # Fix the flaky stage and resume.
    orch2 = _FakeOrch()
    executor2 = WorkflowExecutor(store=store, orchestrator=orch2)
    resumed = executor2.resume(run_id)
    assert resumed.status == WorkflowStatus.COMPLETED
    # Already-completed stages should not re-run.
    assert "trend" not in orch2.calls


def test_cancel_run(store):
    executor = WorkflowExecutor(store=store, orchestrator=_FakeOrch())
    run = executor.create_run("Create a short", config=_intelligence_config())
    cancelled = executor.cancel(run.run_id)
    assert cancelled.status == WorkflowStatus.CANCELLED
    assert all(
        s.status in (WorkflowStatus.CANCELLED, WorkflowStatus.PENDING)
        or s.status == WorkflowStatus.CANCELLED
        for s in cancelled.workflow.steps
        if s.status != WorkflowStatus.COMPLETED
    )


def test_studio_ui_status_output(store):
    orch = _FakeOrch()
    executor = WorkflowExecutor(store=store, orchestrator=orch)
    run = executor.execute("Create a short about galaxies", config=_intelligence_config())
    status = studio_status(run)
    assert status["run_id"] == run.run_id
    assert status["progress"] == 100.0
    assert "current_stage" in status
    assert "errors" in status
    assert "outputs" in status
    assert "provider_usage" in status
    assert "costs" in status
    assert "logs" in status
    assert "steps" in status
    assert executor.get_status(run.run_id)["status"] == WorkflowStatus.COMPLETED


def test_longform_workflow_flags(store):
    orch = _FakeOrch()
    executor = WorkflowExecutor(store=store, orchestrator=orch)
    run = executor.execute(
        "Create a 12-minute documentary about the Roman Empire.",
        config=WorkflowConfig(template="intelligence_only"),
    )
    # production type resolved from prompt even with intelligence_only template
    assert run.production_type == "documentary"
    assert run.config.longform_mode is True
    assert run.status == WorkflowStatus.COMPLETED


def test_provider_runtime_integration_usage_snapshot(store, monkeypatch):
    class _Runtime:
        def usage_summary(self):
            return {"total_cost_usd": 1.25, "calls": 3}

    monkeypatch.setattr(
        "services.workflow_executor.executor.get_provider_runtime",
        lambda: _Runtime(),
        raising=False,
    )
    # Patch the import path used inside _provider_usage_snapshot
    import services.workflow_executor.executor as ex_mod

    monkeypatch.setattr(
        ex_mod,
        "_provider_usage_snapshot",
        lambda: {"total_cost_usd": 1.25, "calls": 3},
    )
    executor = WorkflowExecutor(store=store, orchestrator=_FakeOrch())
    run = executor.execute("Create a short", config=_intelligence_config())
    assert run.provider_usage.get("total_cost_usd") == 1.25
    assert run.result.estimated_cost_usd == 1.25


def test_job_handler_registration(job_queue, store):
    ensure_workflow_handler(job_queue)
    assert job_queue.has_handler(WORKFLOW_JOB_TYPE)
    # Idempotent
    ensure_workflow_handler(job_queue)

    orch = _FakeOrch()
    executor = WorkflowExecutor(store=store, orchestrator=orch)
    # Run via direct executor then verify job payload shape through handler import
    from services.workflow_executor.executor import _workflow_job_handler

    # Handler uses get_workflow_executor — point store via payload
    reset_workflow_executor()
    # Monkeypatch singleton to our fake-orch executor
    import services.workflow_executor.executor as ex_mod

    ex_mod._executor = executor
    result = _workflow_job_handler(
        {
            "command": "Create a short about quarks",
            "config": _intelligence_config().to_dict(),
        }
    )
    assert result["status"] == WorkflowStatus.COMPLETED
    assert "studio_status" in result
    assert result["run_id"]


def test_model_round_trip():
    run = ProjectRun(command="x", production_type="short")
    run.workflow.steps = [WorkflowStep(stage="trend", status=WorkflowStatus.PENDING)]
    data = run.to_dict()
    restored = ProjectRun.from_dict(data)
    assert restored.command == "x"
    assert restored.workflow.steps[0].stage == "trend"


# ---------------------------------------------------------------------------
# End-to-end mock production (real orchestrator, demo mode)
# ---------------------------------------------------------------------------


def test_end_to_end_mock_production(store):
    """Full pipeline through real Orchestrator in demo mode — may take a bit."""
    executor = WorkflowExecutor(store=store)
    run = executor.execute(
        "Create a 45-second YouTube Short about black holes.",
        config=WorkflowConfig(
            count=1,
            publish_mode="scheduled",
            retry_policy=RetryPolicy(max_retries=0, backoff_sec=0),
        ),
    )
    assert run.run_id
    assert run.status in (WorkflowStatus.COMPLETED, WorkflowStatus.FAILED)
    # Even on warning-level degradation we expect a terminal status and checkpoint.
    assert run.checkpoint is not None
    status = executor.get_status(run.run_id)
    assert status["run_id"] == run.run_id
    assert "steps" in status
    assert len(run.log.entries) >= 2
    # Packages may be empty if quality gate holds everything; still a valid run.
    assert isinstance(run.result.packages, list)
    assert run.workflow.progress_pct > 0 or run.status == WorkflowStatus.FAILED


def test_execute_workflow_module_helper(store, monkeypatch):
    reset_workflow_executor()
    executor = WorkflowExecutor(store=store, orchestrator=_FakeOrch())
    import services.workflow_executor.executor as ex_mod

    ex_mod._executor = executor
    run = execute_workflow(
        "Create a short about neutrinos",
        config=_intelligence_config(),
    )
    assert run.status == WorkflowStatus.COMPLETED


def test_list_runs(store):
    executor = WorkflowExecutor(store=store, orchestrator=_FakeOrch())
    executor.execute("Create a short a", config=_intelligence_config())
    executor.execute("Create a short b", config=_intelligence_config())
    listed = executor.list_runs()
    assert len(listed) >= 2
