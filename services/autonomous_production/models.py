"""Autonomous Production Executor state contracts (Agent 23).

Project-management objects that sit above WorkflowExecutor / Orchestrator.
Additive only — never rename or remove fields once shipped.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _uid(prefix: str = "") -> str:
    return f"{prefix}{uuid.uuid4().hex[:12]}" if prefix else uuid.uuid4().hex[:12]


class ExecutionState:
    """Lifecycle for ProductionJob / ExecutionContext."""

    PENDING = "pending"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL = "partial"


@dataclass
class StageResult:
    """Outcome of one pipeline stage within a production job."""

    stage: str = ""
    status: str = ExecutionState.PENDING
    duration_ms: int = 0
    confidence: int = 0
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    outputs: dict = field(default_factory=dict)
    attempt: int = 0
    started_at: str = ""
    finished_at: str = ""

    def to_dict(self) -> dict:
        return {
            "stage": self.stage,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "confidence": self.confidence,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "outputs": dict(self.outputs),
            "attempt": self.attempt,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }

    @classmethod
    def from_dict(cls, data: dict | None) -> "StageResult":
        data = data or {}
        return cls(
            stage=data.get("stage", ""),
            status=data.get("status", ExecutionState.PENDING),
            duration_ms=int(data.get("duration_ms", 0)),
            confidence=int(data.get("confidence", 0)),
            errors=list(data.get("errors", [])),
            warnings=list(data.get("warnings", [])),
            outputs=dict(data.get("outputs", {})),
            attempt=int(data.get("attempt", 0)),
            started_at=data.get("started_at", ""),
            finished_at=data.get("finished_at", ""),
        )


@dataclass
class Checkpoint:
    """Production-level resume point (mirrors workflow checkpoint + chapters)."""

    checkpoint_id: str = field(default_factory=lambda: _uid("apc_"))
    job_id: str = ""
    workflow_run_id: str = ""
    completed_stages: list = field(default_factory=list)
    current_stage: str = ""
    chapter_index: int = 0
    scene_group_index: int = 0
    context_snapshot: dict = field(default_factory=dict)
    status: str = ExecutionState.RUNNING
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "checkpoint_id": self.checkpoint_id,
            "job_id": self.job_id,
            "workflow_run_id": self.workflow_run_id,
            "completed_stages": list(self.completed_stages),
            "current_stage": self.current_stage,
            "chapter_index": self.chapter_index,
            "scene_group_index": self.scene_group_index,
            "context_snapshot": dict(self.context_snapshot),
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict | None) -> "Checkpoint":
        data = data or {}
        return cls(
            checkpoint_id=data.get("checkpoint_id", _uid("apc_")),
            job_id=data.get("job_id", ""),
            workflow_run_id=data.get("workflow_run_id", ""),
            completed_stages=list(data.get("completed_stages", [])),
            current_stage=data.get("current_stage", ""),
            chapter_index=int(data.get("chapter_index", 0)),
            scene_group_index=int(data.get("scene_group_index", 0)),
            context_snapshot=dict(data.get("context_snapshot", {})),
            status=data.get("status", ExecutionState.RUNNING),
            created_at=data.get("created_at", _now_iso()),
            updated_at=data.get("updated_at", _now_iso()),
            error=data.get("error", ""),
        )


@dataclass
class ExecutionContext:
    """Shared execution bag for a ProductionJob (prompt + options + runtime)."""

    command: str = ""
    production_mode: str = "single_video"
    options: dict = field(default_factory=dict)
    workflow_config: dict = field(default_factory=dict)
    chapters: list = field(default_factory=list)
    scene_groups: list = field(default_factory=list)
    budget_usd: float = 0.0
    estimated_cost_usd: float = 0.0
    estimated_runtime_sec: float = 0.0
    platform_targets: list = field(default_factory=list)
    quality_level: str = "standard"
    longform: bool = False
    parallel_units: bool = False
    provider_preferences: dict = field(default_factory=dict)
    extras: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "command": self.command,
            "production_mode": self.production_mode,
            "options": dict(self.options),
            "workflow_config": dict(self.workflow_config),
            "chapters": list(self.chapters),
            "scene_groups": list(self.scene_groups),
            "budget_usd": self.budget_usd,
            "estimated_cost_usd": self.estimated_cost_usd,
            "estimated_runtime_sec": self.estimated_runtime_sec,
            "platform_targets": list(self.platform_targets),
            "quality_level": self.quality_level,
            "longform": self.longform,
            "parallel_units": self.parallel_units,
            "provider_preferences": dict(self.provider_preferences),
            "extras": dict(self.extras),
        }

    @classmethod
    def from_dict(cls, data: dict | None) -> "ExecutionContext":
        data = data or {}
        return cls(
            command=data.get("command", ""),
            production_mode=data.get("production_mode", "single_video"),
            options=dict(data.get("options", {})),
            workflow_config=dict(data.get("workflow_config", {})),
            chapters=list(data.get("chapters", [])),
            scene_groups=list(data.get("scene_groups", [])),
            budget_usd=float(data.get("budget_usd", 0.0)),
            estimated_cost_usd=float(data.get("estimated_cost_usd", 0.0)),
            estimated_runtime_sec=float(data.get("estimated_runtime_sec", 0.0)),
            platform_targets=list(data.get("platform_targets", [])),
            quality_level=data.get("quality_level", "standard"),
            longform=bool(data.get("longform", False)),
            parallel_units=bool(data.get("parallel_units", False)),
            provider_preferences=dict(data.get("provider_preferences", {})),
            extras=dict(data.get("extras", {})),
        )


@dataclass
class ProductionManifest:
    """Declared plan for a production before / during execution."""

    manifest_id: str = field(default_factory=lambda: _uid("man_"))
    production_mode: str = "single_video"
    title: str = ""
    command: str = ""
    stages: list = field(default_factory=list)
    chapters: list = field(default_factory=list)
    scene_groups: list = field(default_factory=list)
    unit_count: int = 1
    estimated_cost_usd: float = 0.0
    estimated_runtime_sec: float = 0.0
    estimated_duration_sec: float = 0.0
    platform_targets: list = field(default_factory=list)
    quality_level: str = "standard"
    longform: bool = False
    dependencies: list = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "manifest_id": self.manifest_id,
            "production_mode": self.production_mode,
            "title": self.title,
            "command": self.command,
            "stages": list(self.stages),
            "chapters": list(self.chapters),
            "scene_groups": list(self.scene_groups),
            "unit_count": self.unit_count,
            "estimated_cost_usd": self.estimated_cost_usd,
            "estimated_runtime_sec": self.estimated_runtime_sec,
            "estimated_duration_sec": self.estimated_duration_sec,
            "platform_targets": list(self.platform_targets),
            "quality_level": self.quality_level,
            "longform": self.longform,
            "dependencies": list(self.dependencies),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict | None) -> "ProductionManifest":
        data = data or {}
        return cls(
            manifest_id=data.get("manifest_id", _uid("man_")),
            production_mode=data.get("production_mode", "single_video"),
            title=data.get("title", ""),
            command=data.get("command", ""),
            stages=list(data.get("stages", [])),
            chapters=list(data.get("chapters", [])),
            scene_groups=list(data.get("scene_groups", [])),
            unit_count=int(data.get("unit_count", 1)),
            estimated_cost_usd=float(data.get("estimated_cost_usd", 0.0)),
            estimated_runtime_sec=float(data.get("estimated_runtime_sec", 0.0)),
            estimated_duration_sec=float(data.get("estimated_duration_sec", 0.0)),
            platform_targets=list(data.get("platform_targets", [])),
            quality_level=data.get("quality_level", "standard"),
            longform=bool(data.get("longform", False)),
            dependencies=list(data.get("dependencies", [])),
            created_at=data.get("created_at", _now_iso()),
        )


@dataclass
class ProductionSummary:
    """Final (or partial) package summary for a completed production job."""

    status: str = ExecutionState.PENDING
    production_mode: str = "single_video"
    packages: list = field(default_factory=list)
    stage_results: list = field(default_factory=list)
    quality_score: float = 0.0
    quality_report: dict = field(default_factory=dict)
    provider_usage: dict = field(default_factory=dict)
    actual_cost_usd: float = 0.0
    estimated_cost_usd: float = 0.0
    elapsed_sec: float = 0.0
    estimated_runtime_sec: float = 0.0
    failures: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    chapter_summaries: list = field(default_factory=list)
    unit_results: list = field(default_factory=list)
    production_report: dict = field(default_factory=dict)
    partial: bool = False
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "production_mode": self.production_mode,
            "packages": list(self.packages),
            "stage_results": [
                s.to_dict() if isinstance(s, StageResult) else s for s in self.stage_results
            ],
            "quality_score": self.quality_score,
            "quality_report": dict(self.quality_report),
            "provider_usage": dict(self.provider_usage),
            "actual_cost_usd": self.actual_cost_usd,
            "estimated_cost_usd": self.estimated_cost_usd,
            "elapsed_sec": self.elapsed_sec,
            "estimated_runtime_sec": self.estimated_runtime_sec,
            "failures": list(self.failures),
            "warnings": list(self.warnings),
            "chapter_summaries": list(self.chapter_summaries),
            "unit_results": list(self.unit_results),
            "production_report": dict(self.production_report),
            "partial": self.partial,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict | None) -> "ProductionSummary":
        data = data or {}
        stages = [
            StageResult.from_dict(s) if isinstance(s, dict) else s
            for s in data.get("stage_results", [])
        ]
        return cls(
            status=data.get("status", ExecutionState.PENDING),
            production_mode=data.get("production_mode", "single_video"),
            packages=list(data.get("packages", [])),
            stage_results=stages,
            quality_score=float(data.get("quality_score", 0.0)),
            quality_report=dict(data.get("quality_report", {})),
            provider_usage=dict(data.get("provider_usage", {})),
            actual_cost_usd=float(data.get("actual_cost_usd", 0.0)),
            estimated_cost_usd=float(data.get("estimated_cost_usd", 0.0)),
            elapsed_sec=float(data.get("elapsed_sec", 0.0)),
            estimated_runtime_sec=float(data.get("estimated_runtime_sec", 0.0)),
            failures=list(data.get("failures", [])),
            warnings=list(data.get("warnings", [])),
            chapter_summaries=list(data.get("chapter_summaries", [])),
            unit_results=list(data.get("unit_results", [])),
            production_report=dict(data.get("production_report", {})),
            partial=bool(data.get("partial", False)),
            error=data.get("error", ""),
        )


@dataclass
class ProductionJob:
    """Top-level autonomous production job created from a single user request."""

    job_id: str = field(default_factory=lambda: _uid("job_"))
    command: str = ""
    production_mode: str = "single_video"
    state: str = ExecutionState.PENDING
    context: ExecutionContext = field(default_factory=ExecutionContext)
    manifest: ProductionManifest = field(default_factory=ProductionManifest)
    summary: ProductionSummary = field(default_factory=ProductionSummary)
    checkpoint: Checkpoint | None = None
    workflow_run_id: str = ""
    child_job_ids: list = field(default_factory=list)
    parent_job_id: str = ""
    scheduled_at: str = ""
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)
    started_at: str = ""
    finished_at: str = ""
    paused_at: str = ""
    log: list = field(default_factory=list)
    progress_pct: float = 0.0
    current_stage: str = ""
    remaining_sec: float = 0.0

    def append_log(self, event: str, **fields) -> dict:
        entry = {"at": _now_iso(), "event": event, **fields}
        self.log.append(entry)
        return entry

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "command": self.command,
            "production_mode": self.production_mode,
            "state": self.state,
            "context": self.context.to_dict(),
            "manifest": self.manifest.to_dict(),
            "summary": self.summary.to_dict(),
            "checkpoint": self.checkpoint.to_dict() if self.checkpoint else None,
            "workflow_run_id": self.workflow_run_id,
            "child_job_ids": list(self.child_job_ids),
            "parent_job_id": self.parent_job_id,
            "scheduled_at": self.scheduled_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "paused_at": self.paused_at,
            "log": list(self.log),
            "progress_pct": self.progress_pct,
            "current_stage": self.current_stage,
            "remaining_sec": self.remaining_sec,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProductionJob":
        checkpoint = data.get("checkpoint")
        return cls(
            job_id=data.get("job_id", _uid("job_")),
            command=data.get("command", ""),
            production_mode=data.get("production_mode", "single_video"),
            state=data.get("state", ExecutionState.PENDING),
            context=ExecutionContext.from_dict(data.get("context")),
            manifest=ProductionManifest.from_dict(data.get("manifest")),
            summary=ProductionSummary.from_dict(data.get("summary")),
            checkpoint=Checkpoint.from_dict(checkpoint) if checkpoint else None,
            workflow_run_id=data.get("workflow_run_id", ""),
            child_job_ids=list(data.get("child_job_ids", [])),
            parent_job_id=data.get("parent_job_id", ""),
            scheduled_at=data.get("scheduled_at", ""),
            created_at=data.get("created_at", _now_iso()),
            updated_at=data.get("updated_at", _now_iso()),
            started_at=data.get("started_at", ""),
            finished_at=data.get("finished_at", ""),
            paused_at=data.get("paused_at", ""),
            log=list(data.get("log", [])),
            progress_pct=float(data.get("progress_pct", 0.0)),
            current_stage=data.get("current_stage", ""),
            remaining_sec=float(data.get("remaining_sec", 0.0)),
        )
