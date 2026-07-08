import engines  # noqa: F401 - importing registers all engines
from core.workflows import WORKFLOW_JOB_TYPE, WorkflowEngine, ensure_workflow_handler
from engines import registry
from engines.base import Engine


class RecorderEngine(Engine):
    key = "recorder"
    label = "Recorder"

    def is_ready(self):
        return True

    def run(self, context):
        return {"recorded": context.get("value", 0) + 1}


class FailingEngine(Engine):
    key = "failing"
    label = "Failing"

    def is_ready(self):
        return True

    def run(self, context):
        raise RuntimeError("engine exploded")


def test_custom_workflow_merges_context():
    registry.register(RecorderEngine())
    run = WorkflowEngine().execute(["recorder"], {"value": 41})
    assert run.succeeded
    assert run.context["recorded"] == 42
    assert run.steps[0].status == "succeeded"


def test_unready_engines_are_skipped():
    run = WorkflowEngine().execute(["voice", "image"], {})
    assert run.succeeded
    assert [step.status for step in run.steps] == ["skipped", "skipped"]


def test_failing_step_stops_run_without_raising():
    registry.register(FailingEngine())
    registry.register(RecorderEngine())
    run = WorkflowEngine().execute(["failing", "recorder"], {})
    assert not run.succeeded
    assert run.steps[0].status == "failed"
    assert "engine exploded" in run.steps[0].error
    assert len(run.steps) == 1  # stopped before recorder


def test_workflow_runs_through_job_queue(job_queue):
    registry.register(RecorderEngine())
    ensure_workflow_handler(job_queue)
    job = job_queue.submit(WORKFLOW_JOB_TYPE, {"workflow": ["recorder"], "context": {"value": 1}})
    job = job_queue.run(job.id)
    assert job.status == "succeeded"
    assert job.result["context"]["recorded"] == 2
    assert job.result["run"]["succeeded"] is True
