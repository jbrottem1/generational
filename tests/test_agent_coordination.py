"""Tests for agent coordination task contract."""

from services.agent_coordination.task_contract import AgentTask, TaskStatus, validate_task


def test_agent_task_round_trip():
    task = AgentTask(
        objective="Render benchmark",
        owner_agent="16",
        expected_outputs=["mp4", "qc_report"],
        project_id="proj_1",
    )
    restored = AgentTask.from_dict(task.to_dict())
    assert restored.objective == "Render benchmark"
    assert restored.owner_agent == "16"
    assert restored.status == TaskStatus.PENDING.value


def test_validate_task_requires_objective():
    report = validate_task(AgentTask(owner_agent="0"))
    assert report["valid"] is False
    assert "objective required" in report["errors"]
