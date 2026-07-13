"""Echoer Communication Protocol (ECP v1).

All agents exchange structured messages through Echoer — the executive
coordination bus. Agent 0 owns routing; specialists execute; QC stays independent.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class MessageType(str, Enum):
    TASK = "task"
    STATUS = "status"
    RESULT = "result"
    ERROR = "error"
    LESSON = "lesson"
    QUERY = "query"


@dataclass
class EchoerMessage:
    """Outbound message to Echoer (from any agent) or from Agent 0 to agents."""

    msg_id: str = field(default_factory=lambda: f"ecp_{uuid.uuid4().hex[:12]}")
    msg_type: str = MessageType.TASK.value
    from_agent: str = "0"
    to_agent: str = ""
    project_id: str = ""
    cycle_id: str = ""
    objective: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    priority: str = "p2"
    retry_count: int = 0
    max_retries: int = 2
    created_at: str = field(default_factory=_now_iso)

    def to_json(self) -> str:
        return json.dumps(asdict(self), separators=(",", ":"), default=str)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_json(cls, raw: str) -> "EchoerMessage":
        return cls.from_dict(json.loads(raw))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EchoerMessage":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class EchoerResponse:
    """Expected reply shape from any agent via Echoer."""

    msg_id: str = ""
    in_reply_to: str = ""
    from_agent: str = ""
    status: str = "ok"  # ok | partial | failed | blocked
    summary: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    evidence: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    cost_estimate_usd: float = 0.0
    duration_sec: float = 0.0
    completed_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_message(
    *,
    msg_type: str | MessageType,
    from_agent: str,
    to_agent: str,
    objective: str,
    payload: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
    project_id: str = "",
    cycle_id: str = "",
    priority: str = "p2",
) -> EchoerMessage:
    mt = msg_type.value if isinstance(msg_type, MessageType) else str(msg_type)
    return EchoerMessage(
        msg_type=mt,
        from_agent=str(from_agent),
        to_agent=str(to_agent),
        objective=objective,
        payload=dict(payload or {}),
        context=dict(context or {}),
        project_id=project_id,
        cycle_id=cycle_id,
        priority=priority,
    )


def parse_response(raw: str | dict[str, Any]) -> EchoerResponse:
    """Parse agent reply; tolerate partial JSON."""
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return EchoerResponse(status="failed", summary=raw[:500], errors=["invalid_json"])
    else:
        data = dict(raw)
    return EchoerResponse(
        msg_id=str(data.get("msg_id") or ""),
        in_reply_to=str(data.get("in_reply_to") or data.get("reply_to") or ""),
        from_agent=str(data.get("from_agent") or data.get("agent") or ""),
        status=str(data.get("status") or "ok"),
        summary=str(data.get("summary") or data.get("message") or ""),
        data=dict(data.get("data") or data.get("payload") or {}),
        evidence=dict(data.get("evidence") or {}),
        errors=list(data.get("errors") or []),
        warnings=list(data.get("warnings") or []),
        cost_estimate_usd=float(data.get("cost_estimate_usd") or 0.0),
        duration_sec=float(data.get("duration_sec") or 0.0),
        completed_at=str(data.get("completed_at") or _now_iso()),
    )


# Agent 0 routing table (specialist → default owner)
AGENT_ROUTES: dict[str, str] = {
    "research": "11",
    "seo": "8",
    "script": "3",
    "education": "24",
    "animation": "16",
    "voice": "5",
    "render": "6",
    "qc": "17",
    "publish": "7",
    "engagement": "24",
    "gcis": "0",
}


def route_to_agent(task_kind: str) -> str:
    return AGENT_ROUTES.get(task_kind.lower(), "0")
