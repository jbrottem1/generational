"""Resilient stage execution — retry / repair / fallback / continue."""

from __future__ import annotations

import time
from typing import Any

from core.log import get_logger, log_event
from core.workflows import StepStatus, WorkflowEngine
from engines import registry

logger = get_logger(__name__)


def run_engine_with_retries(
    engine_key: str,
    context: dict,
    *,
    max_retries: int = 2,
) -> dict[str, Any]:
    """Run one engine; retry on failure. Never raises — returns structured result."""
    engine = registry.get_engine(engine_key)
    attempts: list[dict] = []
    if engine is None or not engine.is_ready():
        return {
            "engine": engine_key,
            "status": "skipped",
            "attempts": 1,
            "retries": 0,
            "error": "not_registered_or_not_ready",
            "warnings": [f"{engine_key} unavailable — continued"],
            "duration_ms": 0,
            "fallback": True,
        }

    last_error = ""
    for attempt in range(max_retries + 1):
        started = time.time()
        try:
            updates = engine.run(context) or {}
            context.update(updates)
            duration = int((time.time() - started) * 1000)
            attempts.append({"attempt": attempt + 1, "status": "succeeded", "duration_ms": duration})
            log_event(
                logger,
                "ops.engine_succeeded",
                engine=engine_key,
                attempt=attempt + 1,
                duration_ms=duration,
            )
            return {
                "engine": engine_key,
                "status": "succeeded",
                "attempts": attempt + 1,
                "retries": attempt,
                "error": "",
                "warnings": [],
                "duration_ms": duration,
                "fallback": False,
                "attempt_log": attempts,
            }
        except Exception as exc:  # noqa: BLE001 — resilience: never terminate
            duration = int((time.time() - started) * 1000)
            last_error = str(exc)[:300]
            attempts.append(
                {
                    "attempt": attempt + 1,
                    "status": "failed",
                    "duration_ms": duration,
                    "error": last_error,
                }
            )
            log_event(
                logger,
                "ops.engine_retry",
                level=30,
                engine=engine_key,
                attempt=attempt + 1,
                error=last_error,
            )
            time.sleep(min(0.05 * (attempt + 1), 0.25))

    return {
        "engine": engine_key,
        "status": "failed_continued",
        "attempts": len(attempts),
        "retries": max(0, len(attempts) - 1),
        "error": last_error,
        "warnings": [f"{engine_key} failed after retries — production continued"],
        "duration_ms": sum(int(a.get("duration_ms") or 0) for a in attempts),
        "fallback": True,
        "attempt_log": attempts,
    }


def run_stage_engines(
    stage: dict,
    context: dict,
    *,
    workflow: WorkflowEngine | None = None,
) -> dict[str, Any]:
    """Execute all engines for a stage with retries; always continues."""
    _ = workflow  # reserved for batching; per-engine control is more resilient
    engine_results = []
    warnings: list[str] = []
    errors: list[str] = []
    retries = 0
    total_ms = 0
    max_retries = int(stage.get("max_retries") or 0)

    for key in stage.get("engines") or []:
        result = run_engine_with_retries(key, context, max_retries=max_retries)
        engine_results.append(result)
        retries += int(result.get("retries") or 0)
        total_ms += int(result.get("duration_ms") or 0)
        warnings.extend(result.get("warnings") or [])
        if result.get("status") == "failed_continued" and result.get("error"):
            errors.append(f"{key}: {result['error']}")

    # Stage succeeds if no hard engine crash remains, OR all skipped (degraded ok)
    hard_fails = [r for r in engine_results if r.get("status") == "failed_continued"]
    all_skipped = bool(engine_results) and all(r.get("status") == "skipped" for r in engine_results)
    if all_skipped:
        status = "skipped"
        success = True  # continue production
        warnings.append(f"{stage['key']}: all engines skipped — fallback continue")
    elif hard_fails and not any(r.get("status") == "succeeded" for r in engine_results):
        status = "degraded"
        success = True  # NEVER terminate
        warnings.append(f"{stage['key']}: degraded — continuing pipeline")
    elif hard_fails:
        status = "partial"
        success = True
    else:
        status = "succeeded"
        success = True

    return {
        "status": status,
        "success": success,
        "engine_results": engine_results,
        "warnings": warnings,
        "errors": errors,
        "retries": retries,
        "duration_ms": total_ms,
        "escalated": False,
    }
