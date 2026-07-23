"""Live production run state for the Executive Orchestrator dashboard."""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from services.executive_orchestrator.stages import (
    EXECUTIVE_STAGES,
    STAGE_ETA_SEC,
    STAGE_LABELS,
    remaining_eta_sec,
    stage_plan,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class StageState:
    key: str
    label: str
    status: str = "pending"  # pending | running | completed | failed | skipped
    started_at: str = ""
    finished_at: str = ""
    duration_ms: int = 0
    eta_sec: int = 0
    engines_used: list[str] = field(default_factory=list)
    message: str = ""
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProductionRun:
    """One end-to-end studio production."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    command: str = ""
    topic: str = ""
    platforms: list[str] = field(default_factory=list)
    runtime_sec: int = 60
    status: str = "pending"  # pending | running | completed | failed | cancelled
    stages: dict[str, StageState] = field(default_factory=dict)
    engines_used: list[str] = field(default_factory=list)
    qa_score: int | None = None
    qa_decision: str = ""
    revision_rounds: int = 0
    export_paths: dict[str, str] = field(default_factory=dict)
    export_size_bytes: int = 0
    publish_status: str = "not_queued"
    generation_time_ms: int = 0
    created_at: str = field(default_factory=_now)
    started_at: str = ""
    finished_at: str = ""
    error: str = ""
    notes: list[str] = field(default_factory=list)
    brief: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.stages:
            for key in EXECUTIVE_STAGES:
                self.stages[key] = StageState(
                    key=key,
                    label=STAGE_LABELS[key],
                    eta_sec=STAGE_ETA_SEC.get(key, 30),
                )

    def stage_status_map(self) -> dict[str, str]:
        return {k: v.status for k, v in self.stages.items()}

    def estimated_remaining_sec(self) -> int:
        return remaining_eta_sec(self.stage_status_map())

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "command": self.command,
            "topic": self.topic,
            "platforms": list(self.platforms),
            "runtime_sec": self.runtime_sec,
            "status": self.status,
            "stages": {k: v.to_dict() for k, v in self.stages.items()},
            "stage_plan": stage_plan(),
            "engines_used": list(self.engines_used),
            "qa_score": self.qa_score,
            "qa_decision": self.qa_decision,
            "revision_rounds": self.revision_rounds,
            "export_paths": dict(self.export_paths),
            "export_size_bytes": self.export_size_bytes,
            "publish_status": self.publish_status,
            "generation_time_ms": self.generation_time_ms,
            "estimated_remaining_sec": self.estimated_remaining_sec(),
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "error": self.error,
            "notes": list(self.notes),
            "brief": dict(self.brief),
            "artifacts": dict(self.artifacts),
        }


class RunRegistry:
    """Thread-safe in-memory registry of live + recent production runs."""

    def __init__(self, *, maxlen: int = 100) -> None:
        self._lock = threading.RLock()
        self._runs: dict[str, ProductionRun] = {}
        self._order: list[str] = []
        self._maxlen = maxlen

    def add(self, run: ProductionRun) -> ProductionRun:
        with self._lock:
            self._runs[run.id] = run
            self._order.append(run.id)
            while len(self._order) > self._maxlen:
                old = self._order.pop(0)
                self._runs.pop(old, None)
        return run

    def get(self, run_id: str) -> ProductionRun | None:
        with self._lock:
            return self._runs.get(run_id)

    def update(self, run: ProductionRun) -> None:
        with self._lock:
            self._runs[run.id] = run

    def list_runs(self, *, limit: int = 50) -> list[ProductionRun]:
        with self._lock:
            ids = list(reversed(self._order))[:limit]
            return [self._runs[i] for i in ids if i in self._runs]

    def dashboard(self) -> dict[str, Any]:
        with self._lock:
            runs = [self._runs[i] for i in reversed(self._order) if i in self._runs]
            active = [r for r in runs if r.status == "running"]
            pending = [r for r in runs if r.status == "pending"]
            failed = [r for r in runs if r.status == "failed"]
            completed = [r for r in runs if r.status == "completed"]
            stage_rollup: dict[str, dict[str, int]] = {
                k: {"pending": 0, "running": 0, "completed": 0, "failed": 0, "skipped": 0}
                for k in EXECUTIVE_STAGES
            }
            for run in active + pending:
                for key, st in run.stages.items():
                    bucket = stage_rollup.get(key)
                    if bucket is not None:
                        bucket[st.status] = bucket.get(st.status, 0) + 1
            return {
                "generated_at": _now(),
                "active_count": len(active),
                "pending_count": len(pending),
                "completed_count": len(completed),
                "failed_count": len(failed),
                "active_runs": [r.to_dict() for r in active[:20]],
                "recent_runs": [r.to_dict() for r in runs[:20]],
                "stage_rollup": stage_rollup,
                "stages": [
                    {
                        "key": k,
                        "label": STAGE_LABELS[k],
                        **stage_rollup[k],
                        "eta_sec": STAGE_ETA_SEC.get(k, 30),
                    }
                    for k in EXECUTIVE_STAGES
                ],
            }


_REGISTRY = RunRegistry()


def get_run_registry() -> RunRegistry:
    return _REGISTRY


def mark_stage(
    run: ProductionRun,
    key: str,
    status: str,
    *,
    message: str = "",
    error: str = "",
    engines: list[str] | None = None,
    started: float | None = None,
) -> None:
    stage = run.stages.get(key)
    if not stage:
        return
    stage.status = status
    if status == "running":
        stage.started_at = _now()
        stage.message = message
        stage.error = ""
    elif status in ("completed", "failed", "skipped"):
        stage.finished_at = _now()
        stage.message = message
        stage.error = error
        if started is not None:
            stage.duration_ms = int((time.time() - started) * 1000)
        if engines:
            stage.engines_used = list(engines)
            for e in engines:
                if e not in run.engines_used:
                    run.engines_used.append(e)
    get_run_registry().update(run)
