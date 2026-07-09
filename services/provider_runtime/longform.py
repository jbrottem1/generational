"""Long-form runtime execution — checkpointed multi-hour productions."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from core.log import get_logger, log_event

if TYPE_CHECKING:
    from services.orchestrator.models import PipelineResult

logger = get_logger(__name__)

LONGFORM_JOB_TYPE = "longform_pipeline"
CHECKPOINT_DIR = Path(__file__).resolve().parents[2] / "data" / "provider_runtime" / "checkpoints"


@dataclass
class ProductionCheckpoint:
    """Serializable checkpoint for resumable long-form jobs."""

    job_id: str
    command: str
    completed_stages: list = field(default_factory=list)
    context_snapshot: dict = field(default_factory=dict)
    status: str = "running"
    created_at: str = ""
    updated_at: str = ""
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "command": self.command,
            "completed_stages": list(self.completed_stages),
            "context_snapshot": self.context_snapshot,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProductionCheckpoint":
        return cls(
            job_id=data["job_id"],
            command=data["command"],
            completed_stages=list(data.get("completed_stages", [])),
            context_snapshot=dict(data.get("context_snapshot", {})),
            status=data.get("status", "running"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            error=data.get("error", ""),
        )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class RuntimeExecutionEngine:
    """Executes the full pipeline with checkpoints for long-form content.

    Supports documentaries, podcasts, courses, feature-length videos, series,
    books, audiobooks, and multi-hour marketing campaigns. Does not modify
    engine internals — delegates to the orchestrator at each stage boundary.
    """

    def __init__(self, checkpoint_dir: "Path | None" = None) -> None:
        self._checkpoint_dir = checkpoint_dir or CHECKPOINT_DIR
        self._checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def start_production(
        self,
        command: str,
        production_type: str = "documentary",
        options: "dict | None" = None,
    ) -> ProductionCheckpoint:
        job_id = uuid.uuid4().hex[:12]
        checkpoint = ProductionCheckpoint(
            job_id=job_id,
            command=command,
            created_at=_now(),
            updated_at=_now(),
            context_snapshot={
                "production_type": production_type,
                "options": options or {},
                "longform": True,
            },
        )
        self._save(checkpoint)
        log_event(logger, "runtime.longform_started", job_id=job_id, production_type=production_type)
        return checkpoint

    def resume_production(self, job_id: str) -> "ProductionCheckpoint | None":
        path = self._checkpoint_dir / f"{job_id}.json"
        if not path.exists():
            return None
        return ProductionCheckpoint.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def pause_production(self, job_id: str) -> "ProductionCheckpoint | None":
        """Request pause — honored between stages on the next loop check."""
        checkpoint = self.resume_production(job_id)
        if checkpoint is None:
            return None
        if checkpoint.status in ("completed", "failed", "cancelled", "paused"):
            return checkpoint
        snapshot = dict(checkpoint.context_snapshot or {})
        snapshot["_pause_requested"] = True
        checkpoint.context_snapshot = snapshot
        if checkpoint.status != "running":
            checkpoint.status = "paused"
        checkpoint.updated_at = _now()
        self._save(checkpoint)
        log_event(logger, "runtime.longform_pause_requested", job_id=job_id)
        return checkpoint

    def cancel_production(self, job_id: str) -> "ProductionCheckpoint | None":
        """Cancel a long-form job and persist terminal cancelled status."""
        checkpoint = self.resume_production(job_id)
        if checkpoint is None:
            return None
        if checkpoint.status in ("completed", "cancelled"):
            return checkpoint
        snapshot = dict(checkpoint.context_snapshot or {})
        snapshot.pop("_pause_requested", None)
        snapshot["_cancel_requested"] = True
        checkpoint.context_snapshot = snapshot
        checkpoint.status = "cancelled"
        checkpoint.updated_at = _now()
        checkpoint.error = checkpoint.error or "Cancelled"
        self._save(checkpoint)
        log_event(logger, "runtime.longform_cancelled", job_id=job_id)
        return checkpoint

    def run(
        self,
        command: str,
        production_type: str = "documentary",
        options: "dict | None" = None,
        resume_job_id: str = "",
    ) -> dict:
        """Run full pipeline with checkpointing after each stage group."""
        from services.orchestrator import get_orchestrator
        from services.orchestrator.stages import build_pipeline_plan
        from services.orchestrator.models import StageStatus

        if resume_job_id:
            checkpoint = self.resume_production(resume_job_id)
            if not checkpoint:
                return {"error": f"Checkpoint {resume_job_id!r} not found", "status": "failed"}
            if checkpoint.status == "cancelled":
                return {
                    "job_id": checkpoint.job_id,
                    "status": "cancelled",
                    "checkpoint": checkpoint.to_dict(),
                }
            # Clear control flags so resume can proceed.
            snap = dict(checkpoint.context_snapshot or {})
            snap.pop("_pause_requested", None)
            snap.pop("_cancel_requested", None)
            checkpoint.context_snapshot = snap
            checkpoint.status = "running"
            checkpoint.error = ""
            self._save(checkpoint)
        else:
            checkpoint = self.start_production(command, production_type, options)

        context = dict(checkpoint.context_snapshot)
        context.setdefault("command", command)
        context.setdefault("count", (options or {}).get("count", 3))
        context.update((options or {}).get("context_extra", {}))

        orchestrator = get_orchestrator()
        plan = build_pipeline_plan()
        completed = set(checkpoint.completed_stages)

        from services.orchestrator.models import PipelineResult
        from services.orchestrator.stages import distribution_stage_names
        from services.orchestrator.report import build_production_report

        result = PipelineResult(status=StageStatus.SUCCESS, context=context)
        all_stages = list(plan) + [("production", None), ("packaging", None)]
        all_stages += [(stage, None) for stage in distribution_stage_names()]

        for stage, engine_keys in all_stages:
            # Reload control flags from disk so pause/cancel from another
            # process is honored between stages.
            latest = self.resume_production(checkpoint.job_id)
            if latest is not None:
                flags = latest.context_snapshot or {}
                if flags.get("_cancel_requested") or latest.status == "cancelled":
                    checkpoint.status = "cancelled"
                    checkpoint.updated_at = _now()
                    checkpoint.context_snapshot = self._snapshot_context(context)
                    checkpoint.error = checkpoint.error or "Cancelled"
                    self._save(checkpoint)
                    return {
                        "job_id": checkpoint.job_id,
                        "status": "cancelled",
                        "paused_before_stage": stage,
                        "checkpoint": checkpoint.to_dict(),
                    }
                if flags.get("_pause_requested"):
                    snap = dict(flags)
                    snap.pop("_pause_requested", None)
                    checkpoint.context_snapshot = {**self._snapshot_context(context), **snap}
                    checkpoint.status = "paused"
                    checkpoint.updated_at = _now()
                    self._save(checkpoint)
                    return {
                        "job_id": checkpoint.job_id,
                        "status": "paused",
                        "paused_before_stage": stage,
                        "checkpoint": checkpoint.to_dict(),
                    }

            if stage in completed:
                continue
            if stage == "production":
                report = orchestrator._run_production(context)  # noqa: SLF001
            elif stage == "packaging":
                report = orchestrator._run_packaging(context, result)  # noqa: SLF001
            else:
                report = orchestrator.run_stage(stage, context, engine_keys=engine_keys)
            result.stage_reports.append(report)
            checkpoint.completed_stages.append(stage)
            checkpoint.updated_at = _now()
            checkpoint.context_snapshot = self._snapshot_context(context)

            if report.status == StageStatus.FAILED and stage not in distribution_stage_names():
                checkpoint.status = "failed"
                checkpoint.error = "; ".join(report.errors) or f"Stage {stage} failed"
                self._save(checkpoint)
                return {
                    "job_id": checkpoint.job_id,
                    "status": "failed",
                    "failed_stage": stage,
                    "checkpoint": checkpoint.to_dict(),
                }
            self._save(checkpoint)

        if any(r.status in (StageStatus.WARNING, StageStatus.FAILED) for r in result.stage_reports):
            result.status = StageStatus.WARNING
        result.production_report = build_production_report(result)

        checkpoint.status = "completed"
        checkpoint.updated_at = _now()
        self._save(checkpoint)

        return {
            "job_id": checkpoint.job_id,
            "status": checkpoint.status,
            "packages": len(result.packages),
            "production_report": result.production_report,
            "checkpoint": checkpoint.to_dict(),
        }

    def list_checkpoints(self) -> list[dict]:
        checkpoints = []
        for path in sorted(self._checkpoint_dir.glob("*.json")):
            try:
                checkpoints.append(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError):
                continue
        return checkpoints

    def _save(self, checkpoint: ProductionCheckpoint) -> None:
        path = self._checkpoint_dir / f"{checkpoint.job_id}.json"
        path.write_text(json.dumps(checkpoint.to_dict(), indent=2), encoding="utf-8")

    @staticmethod
    def _snapshot_context(context: dict) -> dict:
        """Store JSON-safe context subset for resume."""
        safe = {}
        for key, value in context.items():
            try:
                json.dumps(value)
                safe[key] = value
            except (TypeError, ValueError):
                safe[key] = str(value)
        return safe


def _longform_job_handler(payload: dict) -> dict:
    engine = RuntimeExecutionEngine()
    return engine.run(
        payload["command"],
        production_type=payload.get("production_type", "documentary"),
        options=payload.get("options"),
        resume_job_id=payload.get("resume_job_id", ""),
    )


def ensure_longform_handler(queue) -> None:
    """Register long-form pipeline handler on job queue (idempotent)."""
    if not queue.has_handler(LONGFORM_JOB_TYPE):
        queue.register_handler(LONGFORM_JOB_TYPE, _longform_job_handler)
