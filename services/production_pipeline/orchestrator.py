"""Production Pipeline Integration orchestrator.

Executes:
  Research → Psychology → Studio Director → Script Generator → Scene Builder
  → Media Generation → Voice Generation → Video Assembly → Quality Control → Export

Uses existing engines via WorkflowEngine. Does not rewrite agents.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Any

from core.log import get_logger, log_event
from core.workflows import StepStatus, WorkflowEngine
from services.production_pipeline.bridges import (
    bridge_before_stage,
    validation_score,
    verify_stage_io,
)
from services.production_pipeline.stages import PRODUCTION_STAGES, flat_engine_order, stage_contract_table
from services.production_pipeline.status import (
    mark_stage_finished,
    mark_stage_running,
    mark_stage_skipped,
    new_status,
    status_path,
    write_status,
)

logger = get_logger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def verify_agents() -> dict[str, Any]:
    """Verify every production stage engine is registered and report I/O contracts."""
    import engines  # noqa: F401
    from engines import registry

    rows = []
    all_ok = True
    for stage in PRODUCTION_STAGES:
        engine_rows = []
        for key in stage["engines"]:
            eng = registry.get_engine(key)
            ready = bool(eng and eng.is_ready())
            if eng is None:
                all_ok = False
            engine_rows.append(
                {
                    "key": key,
                    "registered": eng is not None,
                    "ready": ready,
                    "version": getattr(eng, "version", "") if eng else "",
                    "input_contract": list(getattr(eng, "input_contract", []) or []) if eng else [],
                    "output_contract": list(getattr(eng, "output_contract", []) or []) if eng else [],
                }
            )
        rows.append(
            {
                "stage": stage["key"],
                "label": stage["label"],
                "declared_inputs": list(stage["inputs"]),
                "declared_outputs": list(stage["outputs"]),
                "engines": engine_rows,
            }
        )
    return {
        "ok": all_ok,
        "stages": rows,
        "engine_order": flat_engine_order(),
        "contracts": stage_contract_table(),
        "verified_at": _now(),
    }


def run_production_pipeline(
    command: str,
    *,
    production_id: str = "",
    platform: str = "youtube_shorts",
    context: dict | None = None,
    stop_on_failure: bool = True,
) -> dict[str, Any]:
    """Execute the full integrated production pipeline with live PIPELINE_STATUS.json."""
    import engines  # noqa: F401

    pid = production_id or f"pipeline_{uuid.uuid4().hex[:10]}"
    ctx: dict[str, Any] = dict(context or {})
    ctx.setdefault("command", command)
    ctx.setdefault("platform", platform)
    ctx.setdefault("project_id", pid)
    ctx.setdefault("project_name", pid)

    status = new_status(pid, command=command, platform=platform)
    path = write_status(pid, status)
    log_event(
        logger,
        "production_pipeline.started",
        production_id=pid,
        stages=len(PRODUCTION_STAGES),
        status_path=str(path),
    )

    workflow = WorkflowEngine()
    stage_summaries: list[dict] = []
    overall_ok = True
    t0 = time.time()

    for stage in PRODUCTION_STAGES:
        stage_key = stage["key"]
        ctx = bridge_before_stage(stage_key, ctx)
        pre_io = verify_stage_io(stage, ctx)

        status = mark_stage_running(status, stage_key)
        write_status(pid, status)
        log_event(
            logger,
            "production_pipeline.stage_started",
            production_id=pid,
            stage=stage_key,
            engines=",".join(stage["engines"]),
            missing_inputs=",".join(pre_io.get("missing_inputs") or []),
        )

        started = time.time()
        engine_results: list[dict] = []
        stage_ok = True
        stage_error = ""

        # Run stage engines as a mini-workflow (skip missing / unready)
        run = workflow.execute(list(stage["engines"]), ctx)
        ctx = run.context

        for step in run.steps:
            engine_results.append(
                {
                    "engine": step.engine_key,
                    "status": step.status,
                    "duration_ms": step.duration_ms,
                    "error": step.error,
                    "problems": list(step.problems or []),
                }
            )
            if step.status == StepStatus.FAILED:
                stage_ok = False
                stage_error = step.error or f"{step.engine_key} failed"
                overall_ok = False

        # If every engine skipped and stage required research/script, soft-skip
        if run.steps and all(s.status == StepStatus.SKIPPED for s in run.steps):
            status = mark_stage_skipped(status, stage_key, reason="all_engines_skipped")
            write_status(pid, status)
            log_event(
                logger,
                "production_pipeline.stage_skipped",
                production_id=pid,
                stage=stage_key,
            )
            stage_summaries.append(
                {
                    "stage": stage_key,
                    "status": "skipped",
                    "elapsed_ms": 0,
                    "validation_score": 0,
                }
            )
            continue

        elapsed_ms = int((time.time() - started) * 1000)
        score = validation_score(ctx, stage_key)
        out_loc = str(status_path(pid).parent)

        status = mark_stage_finished(
            status,
            stage_key,
            success=stage_ok,
            elapsed_ms=elapsed_ms,
            output_location=out_loc,
            validation_score=score,
            error=stage_error,
            engine_results=engine_results,
        )
        write_status(pid, status)

        log_event(
            logger,
            "production_pipeline.stage_finished",
            production_id=pid,
            stage=stage_key,
            success=stage_ok,
            elapsed_ms=elapsed_ms,
            validation_score=score,
            error=stage_error[:160] if stage_error else "",
        )

        stage_summaries.append(
            {
                "stage": stage_key,
                "status": "succeeded" if stage_ok else "failed",
                "elapsed_ms": elapsed_ms,
                "validation_score": score,
                "engines": engine_results,
            }
        )

        if not stage_ok and stop_on_failure:
            break

    total_ms = int((time.time() - t0) * 1000)
    status["elapsed_ms"] = total_ms
    if status.get("overall_status") == "running":
        # Incomplete because stop_on_failure broke early
        if not overall_ok:
            status["overall_status"] = "failed"
            status["success"] = False
        else:
            # Mark remaining pending as skipped
            for stage in status.get("stages") or []:
                if stage.get("status") == "pending":
                    stage["status"] = "skipped"
                    stage["error"] = "not_reached"
            status["overall_status"] = "succeeded" if overall_ok else "failed"
            status["success"] = overall_ok
        status["finished_at"] = _now()
    path = write_status(pid, status)

    log_event(
        logger,
        "production_pipeline.finished",
        production_id=pid,
        success=status.get("success"),
        elapsed_ms=total_ms,
        validation_score=status.get("validation_score"),
        status_path=str(path),
    )

    return {
        "production_id": pid,
        "succeeded": bool(status.get("success")),
        "elapsed_ms": total_ms,
        "validation_score": status.get("validation_score"),
        "current_stage": status.get("current_stage"),
        "status_path": str(path),
        "pipeline_status": status,
        "stage_summaries": stage_summaries,
        "context": ctx,
        "agent_verification": verify_agents(),
    }
