"""Workflow Executor state contracts (Agent 21).

Durable run objects that sit above the Orchestrator. Additive only —
never rename or remove fields once shipped.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _uid(prefix: str = "") -> str:
    return f"{prefix}{uuid.uuid4().hex[:12]}" if prefix else uuid.uuid4().hex[:12]


class WorkflowStatus:
    """Lifecycle status for ProjectRun / WorkflowRun / WorkflowStep."""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WAITING = "waiting"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


# Stages the Studio UI and templates may reference. Maps to orchestrator
# stage names (plus production/packaging specials and post-publish).
CANONICAL_STAGES: tuple[str, ...] = (
    "trend",
    "research",
    "psychology",
    "script",
    "attention",
    "visual",
    "audio",
    "refinement",
    "quality",
    "production",
    "packaging",
    "ai_director",
    "creative",
    "character_universe",
    "asset_generation",
    "animation",
    "render",
    "post_production",
    "seo",
    "optimization",
    "publish",
    "analytics",
    "learning",
)

# Human-facing aliases used in production-type resolution.
STAGE_ALIASES = {
    "market_intelligence": "trend",
    "script_generation": "script",
    "voice_audio": "audio",
    "voice": "audio",
    "creative_studio": "creative",
    "character": "character_universe",
    "universe": "character_universe",
    "post": "post_production",
    "seo_optimization": "seo",
    "optimization_lab": "optimization",
    "optimization_laboratory": "optimization",
    "publishing": "publish",
}


@dataclass
class RetryPolicy:
    """Per-run / per-step retry configuration."""

    max_retries: int = 2
    backoff_sec: float = 0.0
    retry_on_failed: bool = True
    skip_optional_on_fail: bool = True
    degrade_distribution_failures: bool = True

    def to_dict(self) -> dict:
        return {
            "max_retries": self.max_retries,
            "backoff_sec": self.backoff_sec,
            "retry_on_failed": self.retry_on_failed,
            "skip_optional_on_fail": self.skip_optional_on_fail,
            "degrade_distribution_failures": self.degrade_distribution_failures,
        }

    @classmethod
    def from_dict(cls, data: dict | None) -> "RetryPolicy":
        data = data or {}
        return cls(
            max_retries=int(data.get("max_retries", 2)),
            backoff_sec=float(data.get("backoff_sec", 0.0)),
            retry_on_failed=bool(data.get("retry_on_failed", True)),
            skip_optional_on_fail=bool(data.get("skip_optional_on_fail", True)),
            degrade_distribution_failures=bool(
                data.get("degrade_distribution_failures", True)
            ),
        )


@dataclass
class WorkflowStep:
    """One stage in a workflow plan."""

    step_id: str = field(default_factory=lambda: _uid("step_"))
    stage: str = ""
    engine_keys: list = field(default_factory=list)
    required: bool = True
    optional: bool = False
    status: str = WorkflowStatus.PENDING
    attempt: int = 0
    max_attempts: int = 3
    started_at: str = ""
    finished_at: str = ""
    duration_ms: int = 0
    confidence: int = 0
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    diagnostics: dict = field(default_factory=dict)
    partial_outputs: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "stage": self.stage,
            "engine_keys": list(self.engine_keys),
            "required": self.required,
            "optional": self.optional,
            "status": self.status,
            "attempt": self.attempt,
            "max_attempts": self.max_attempts,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_ms": self.duration_ms,
            "confidence": self.confidence,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "diagnostics": dict(self.diagnostics),
            "partial_outputs": dict(self.partial_outputs),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WorkflowStep":
        return cls(
            step_id=data.get("step_id", _uid("step_")),
            stage=data.get("stage", ""),
            engine_keys=list(data.get("engine_keys", [])),
            required=bool(data.get("required", True)),
            optional=bool(data.get("optional", False)),
            status=data.get("status", WorkflowStatus.PENDING),
            attempt=int(data.get("attempt", 0)),
            max_attempts=int(data.get("max_attempts", 3)),
            started_at=data.get("started_at", ""),
            finished_at=data.get("finished_at", ""),
            duration_ms=int(data.get("duration_ms", 0)),
            confidence=int(data.get("confidence", 0)),
            errors=list(data.get("errors", [])),
            warnings=list(data.get("warnings", [])),
            diagnostics=dict(data.get("diagnostics", {})),
            partial_outputs=dict(data.get("partial_outputs", {})),
        )


@dataclass
class Checkpoint:
    """Persisted resume point for a ProjectRun."""

    checkpoint_id: str = field(default_factory=lambda: _uid("ckpt_"))
    run_id: str = ""
    completed_stages: list = field(default_factory=list)
    current_stage: str = ""
    context_snapshot: dict = field(default_factory=dict)
    step_states: list = field(default_factory=list)
    status: str = WorkflowStatus.RUNNING
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "checkpoint_id": self.checkpoint_id,
            "run_id": self.run_id,
            "completed_stages": list(self.completed_stages),
            "current_stage": self.current_stage,
            "context_snapshot": dict(self.context_snapshot),
            "step_states": list(self.step_states),
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Checkpoint":
        return cls(
            checkpoint_id=data.get("checkpoint_id", _uid("ckpt_")),
            run_id=data.get("run_id", ""),
            completed_stages=list(data.get("completed_stages", [])),
            current_stage=data.get("current_stage", ""),
            context_snapshot=dict(data.get("context_snapshot", {})),
            step_states=list(data.get("step_states", [])),
            status=data.get("status", WorkflowStatus.RUNNING),
            created_at=data.get("created_at", _now_iso()),
            updated_at=data.get("updated_at", _now_iso()),
            error=data.get("error", ""),
        )


@dataclass
class ExecutionLog:
    """Append-only event log for a run (Studio UI + debugging)."""

    entries: list = field(default_factory=list)

    def append(self, event: str, **fields) -> dict:
        entry = {"at": _now_iso(), "event": event, **fields}
        self.entries.append(entry)
        return entry

    def to_dict(self) -> dict:
        return {"entries": list(self.entries)}

    @classmethod
    def from_dict(cls, data: dict | None) -> "ExecutionLog":
        data = data or {}
        return cls(entries=list(data.get("entries", [])))


@dataclass
class FailureReport:
    """Structured failure details for a run or step."""

    stage: str = ""
    status: str = WorkflowStatus.FAILED
    message: str = ""
    errors: list = field(default_factory=list)
    attempt: int = 0
    recoverable: bool = True
    partial_outputs: dict = field(default_factory=dict)
    at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "stage": self.stage,
            "status": self.status,
            "message": self.message,
            "errors": list(self.errors),
            "attempt": self.attempt,
            "recoverable": self.recoverable,
            "partial_outputs": dict(self.partial_outputs),
            "at": self.at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FailureReport":
        return cls(
            stage=data.get("stage", ""),
            status=data.get("status", WorkflowStatus.FAILED),
            message=data.get("message", ""),
            errors=list(data.get("errors", [])),
            attempt=int(data.get("attempt", 0)),
            recoverable=bool(data.get("recoverable", True)),
            partial_outputs=dict(data.get("partial_outputs", {})),
            at=data.get("at", _now_iso()),
        )


@dataclass
class WorkflowConfig:
    """Configurable workflow execution options."""

    template: str = "full_production"
    production_type: str = "short"
    stage_order: list = field(default_factory=list)
    required_stages: list = field(default_factory=list)
    optional_stages: list = field(default_factory=list)
    skip_stages: list = field(default_factory=list)
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    timeout_sec: float = 0.0
    stage_timeout_sec: float = 0.0
    quality_level: str = "standard"
    budget_usd: float = 0.0
    platform_targets: list = field(default_factory=list)
    provider_preferences: dict = field(default_factory=dict)
    longform_mode: bool = False
    count: int = 3
    publish_mode: str = "scheduled"
    target_platform: str = "youtube_shorts"
    model: str = "demo"
    allow_partial_completion: bool = True

    def to_dict(self) -> dict:
        return {
            "template": self.template,
            "production_type": self.production_type,
            "stage_order": list(self.stage_order),
            "required_stages": list(self.required_stages),
            "optional_stages": list(self.optional_stages),
            "skip_stages": list(self.skip_stages),
            "retry_policy": self.retry_policy.to_dict(),
            "timeout_sec": self.timeout_sec,
            "stage_timeout_sec": self.stage_timeout_sec,
            "quality_level": self.quality_level,
            "budget_usd": self.budget_usd,
            "platform_targets": list(self.platform_targets),
            "provider_preferences": dict(self.provider_preferences),
            "longform_mode": self.longform_mode,
            "count": self.count,
            "publish_mode": self.publish_mode,
            "target_platform": self.target_platform,
            "model": self.model,
            "allow_partial_completion": self.allow_partial_completion,
        }

    @classmethod
    def from_dict(cls, data: dict | None) -> "WorkflowConfig":
        data = data or {}
        return cls(
            template=data.get("template", "full_production"),
            production_type=data.get("production_type", "short"),
            stage_order=list(data.get("stage_order", [])),
            required_stages=list(data.get("required_stages", [])),
            optional_stages=list(data.get("optional_stages", [])),
            skip_stages=list(data.get("skip_stages", [])),
            retry_policy=RetryPolicy.from_dict(data.get("retry_policy")),
            timeout_sec=float(data.get("timeout_sec", 0.0)),
            stage_timeout_sec=float(data.get("stage_timeout_sec", 0.0)),
            quality_level=data.get("quality_level", "standard"),
            budget_usd=float(data.get("budget_usd", 0.0)),
            platform_targets=list(data.get("platform_targets", [])),
            provider_preferences=dict(data.get("provider_preferences", {})),
            longform_mode=bool(data.get("longform_mode", False)),
            count=int(data.get("count", 3)),
            publish_mode=data.get("publish_mode", "scheduled"),
            target_platform=data.get("target_platform", "youtube_shorts"),
            model=data.get("model", "demo"),
            allow_partial_completion=bool(data.get("allow_partial_completion", True)),
        )


@dataclass
class WorkflowRun:
    """One execution attempt of a planned stage sequence."""

    workflow_id: str = field(default_factory=lambda: _uid("wf_"))
    template: str = "full_production"
    status: str = WorkflowStatus.PENDING
    steps: list = field(default_factory=list)
    current_step_index: int = 0
    started_at: str = ""
    finished_at: str = ""
    progress_pct: float = 0.0

    def to_dict(self) -> dict:
        return {
            "workflow_id": self.workflow_id,
            "template": self.template,
            "status": self.status,
            "steps": [s.to_dict() if isinstance(s, WorkflowStep) else s for s in self.steps],
            "current_step_index": self.current_step_index,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "progress_pct": self.progress_pct,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WorkflowRun":
        steps = [
            WorkflowStep.from_dict(s) if isinstance(s, dict) else s
            for s in data.get("steps", [])
        ]
        return cls(
            workflow_id=data.get("workflow_id", _uid("wf_")),
            template=data.get("template", "full_production"),
            status=data.get("status", WorkflowStatus.PENDING),
            steps=steps,
            current_step_index=int(data.get("current_step_index", 0)),
            started_at=data.get("started_at", ""),
            finished_at=data.get("finished_at", ""),
            progress_pct=float(data.get("progress_pct", 0.0)),
        )


@dataclass
class WorkflowResult:
    """Final (or partial) outcome of a ProjectRun."""

    status: str = WorkflowStatus.PENDING
    packages: list = field(default_factory=list)
    production_package: dict = field(default_factory=dict)
    asset_package: dict = field(default_factory=dict)
    animation_package: dict = field(default_factory=dict)
    post_production_package: dict = field(default_factory=dict)
    render_package: dict = field(default_factory=dict)
    publishing_package: dict = field(default_factory=dict)
    analytics_package: dict = field(default_factory=dict)
    learning_context: dict = field(default_factory=dict)
    production_report: dict = field(default_factory=dict)
    failure_reports: list = field(default_factory=list)
    provider_usage: dict = field(default_factory=dict)
    estimated_cost_usd: float = 0.0
    partial: bool = False
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "packages": list(self.packages),
            "production_package": dict(self.production_package),
            "asset_package": dict(self.asset_package),
            "animation_package": dict(self.animation_package),
            "post_production_package": dict(self.post_production_package),
            "render_package": dict(self.render_package),
            "publishing_package": dict(self.publishing_package),
            "analytics_package": dict(self.analytics_package),
            "learning_context": dict(self.learning_context),
            "production_report": dict(self.production_report),
            "failure_reports": [
                f.to_dict() if isinstance(f, FailureReport) else f
                for f in self.failure_reports
            ],
            "provider_usage": dict(self.provider_usage),
            "estimated_cost_usd": self.estimated_cost_usd,
            "partial": self.partial,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict | None) -> "WorkflowResult":
        data = data or {}
        failures = [
            FailureReport.from_dict(f) if isinstance(f, dict) else f
            for f in data.get("failure_reports", [])
        ]
        return cls(
            status=data.get("status", WorkflowStatus.PENDING),
            packages=list(data.get("packages", [])),
            production_package=dict(data.get("production_package", {})),
            asset_package=dict(data.get("asset_package", {})),
            animation_package=dict(data.get("animation_package", {})),
            post_production_package=dict(data.get("post_production_package", {})),
            render_package=dict(data.get("render_package", {})),
            publishing_package=dict(data.get("publishing_package", {})),
            analytics_package=dict(data.get("analytics_package", {})),
            learning_context=dict(data.get("learning_context", {})),
            production_report=dict(data.get("production_report", {})),
            failure_reports=failures,
            provider_usage=dict(data.get("provider_usage", {})),
            estimated_cost_usd=float(data.get("estimated_cost_usd", 0.0)),
            partial=bool(data.get("partial", False)),
            error=data.get("error", ""),
        )


@dataclass
class ProjectRun:
    """Top-level durable production run created from a user prompt."""

    run_id: str = field(default_factory=lambda: _uid("run_"))
    command: str = ""
    production_type: str = "short"
    status: str = WorkflowStatus.PENDING
    config: WorkflowConfig = field(default_factory=WorkflowConfig)
    workflow: WorkflowRun = field(default_factory=WorkflowRun)
    context: dict = field(default_factory=dict)
    result: WorkflowResult = field(default_factory=WorkflowResult)
    log: ExecutionLog = field(default_factory=ExecutionLog)
    checkpoint: Checkpoint | None = None
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)
    started_at: str = ""
    finished_at: str = ""
    estimated_completion_at: str = ""
    provider_usage: dict = field(default_factory=dict)
    estimated_cost_usd: float = 0.0

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "command": self.command,
            "production_type": self.production_type,
            "status": self.status,
            "config": self.config.to_dict(),
            "workflow": self.workflow.to_dict(),
            "context": dict(self.context),
            "result": self.result.to_dict(),
            "log": self.log.to_dict(),
            "checkpoint": self.checkpoint.to_dict() if self.checkpoint else None,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "estimated_completion_at": self.estimated_completion_at,
            "provider_usage": dict(self.provider_usage),
            "estimated_cost_usd": self.estimated_cost_usd,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectRun":
        checkpoint = data.get("checkpoint")
        return cls(
            run_id=data.get("run_id", _uid("run_")),
            command=data.get("command", ""),
            production_type=data.get("production_type", "short"),
            status=data.get("status", WorkflowStatus.PENDING),
            config=WorkflowConfig.from_dict(data.get("config")),
            workflow=WorkflowRun.from_dict(data.get("workflow") or {}),
            context=dict(data.get("context", {})),
            result=WorkflowResult.from_dict(data.get("result")),
            log=ExecutionLog.from_dict(data.get("log")),
            checkpoint=Checkpoint.from_dict(checkpoint) if checkpoint else None,
            created_at=data.get("created_at", _now_iso()),
            updated_at=data.get("updated_at", _now_iso()),
            started_at=data.get("started_at", ""),
            finished_at=data.get("finished_at", ""),
            estimated_completion_at=data.get("estimated_completion_at", ""),
            provider_usage=dict(data.get("provider_usage", {})),
            estimated_cost_usd=float(data.get("estimated_cost_usd", 0.0)),
        )
