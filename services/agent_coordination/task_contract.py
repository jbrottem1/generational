"""Shared agent task contract — Agent 0 coordinates; specialists execute.

Every delegated task must carry enough structure to track, retry, and verify.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    P0 = "p0"
    P1 = "p1"
    P2 = "p2"
    P3 = "p3"
    P4 = "p4"


@dataclass
class AgentTask:
    """Standard envelope for work assigned to any agent."""

    task_id: str = field(default_factory=lambda: f"task_{uuid.uuid4().hex[:12]}")
    project_id: str = ""
    objective: str = ""
    inputs: dict[str, Any] = field(default_factory=dict)
    expected_outputs: list[str] = field(default_factory=list)
    owner_agent: str = ""
    priority: str = TaskPriority.P2.value
    dependencies: list[str] = field(default_factory=list)
    status: str = TaskStatus.PENDING.value
    progress_pct: float = 0.0
    retry_count: int = 0
    max_retries: int = 2
    cost_estimate_usd: float = 0.0
    completion_evidence: dict[str, Any] = field(default_factory=dict)
    error_details: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "AgentTask":
        data = dict(data or {})
        return cls(
            task_id=str(data.get("task_id") or f"task_{uuid.uuid4().hex[:12]}"),
            project_id=str(data.get("project_id") or ""),
            objective=str(data.get("objective") or ""),
            inputs=dict(data.get("inputs") or {}),
            expected_outputs=list(data.get("expected_outputs") or []),
            owner_agent=str(data.get("owner_agent") or data.get("owner") or ""),
            priority=str(data.get("priority") or TaskPriority.P2.value),
            dependencies=list(data.get("dependencies") or []),
            status=str(data.get("status") or TaskStatus.PENDING.value),
            progress_pct=float(data.get("progress_pct") or 0.0),
            retry_count=int(data.get("retry_count") or 0),
            max_retries=int(data.get("max_retries") or 2),
            cost_estimate_usd=float(data.get("cost_estimate_usd") or 0.0),
            completion_evidence=dict(data.get("completion_evidence") or {}),
            error_details=list(data.get("error_details") or []),
            created_at=str(data.get("created_at") or _now_iso()),
            updated_at=str(data.get("updated_at") or _now_iso()),
        )


def validate_task(task: AgentTask | dict[str, Any]) -> dict[str, Any]:
    """Return validation report; does not mutate task."""
    t = task if isinstance(task, AgentTask) else AgentTask.from_dict(task)
    errors: list[str] = []
    warnings: list[str] = []
    if not t.objective.strip():
        errors.append("objective required")
    if not t.owner_agent.strip():
        warnings.append("owner_agent unset")
    if not t.expected_outputs:
        warnings.append("expected_outputs empty — verification may be weak")
    if t.retry_count > t.max_retries:
        errors.append("retry_count exceeds max_retries")
    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "task_id": t.task_id,
    }


def task_from_dict(data: dict[str, Any]) -> AgentTask:
    return AgentTask.from_dict(data)
