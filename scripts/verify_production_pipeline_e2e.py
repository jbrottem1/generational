#!/usr/bin/env python3
"""E2E verification — Production Pipeline Integration Layer."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import engines  # noqa: F401
from engines import registry
from services.production_pipeline import run_production_pipeline, verify_agents

OUT = ROOT / "data" / "productions" / "_validation" / "production_pipeline"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> int:
    print("=== Production Pipeline Integration E2E ===")
    verification = verify_agents()
    engine = registry.get_engine("production_pipeline")
    assert engine and engine.is_ready()

    result = run_production_pipeline(
        "Artificial Intelligence Explained in 60 Seconds",
        production_id="e2e_production_pipeline",
        platform="youtube_shorts",
        stop_on_failure=False,
    )

    status = result.get("pipeline_status") or {}
    stages = status.get("stages") or []
    succeeded_stages = [s for s in stages if s.get("status") == "succeeded"]
    failed_stages = [s for s in stages if s.get("status") == "failed"]

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "agent_verification_ok": verification.get("ok"),
        "engine_ready": True,
        "production_id": result.get("production_id"),
        "status_path": result.get("status_path"),
        "overall_success": result.get("succeeded"),
        "elapsed_ms": result.get("elapsed_ms"),
        "validation_score": result.get("validation_score"),
        "current_stage": result.get("current_stage"),
        "stages_succeeded": len(succeeded_stages),
        "stages_failed": len(failed_stages),
        "stage_summaries": result.get("stage_summaries"),
        "contracts": verification.get("contracts"),
        "passed": bool(result.get("status_path")) and len(stages) == 10 and len(succeeded_stages) >= 3,
    }

    (OUT / "PIPELINE_INTEGRATION_E2E.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    lines = [
        "# Production Pipeline Integration — E2E Report",
        "",
        f"Generated: {payload['generated_at']}",
        f"**Passed: {payload['passed']}**",
        "",
        f"- Status file: `{payload['status_path']}`",
        f"- Elapsed: {payload['elapsed_ms']} ms",
        f"- Validation score: {payload['validation_score']}",
        f"- Stages succeeded: {payload['stages_succeeded']} / 10",
        f"- Stages failed: {payload['stages_failed']}",
        "",
        "## Stage results",
    ]
    for s in stages:
        lines.append(
            f"- **{s.get('label') or s.get('key')}**: {s.get('status')} "
            f"(score={s.get('validation_score')}, {s.get('elapsed_ms')} ms)"
        )
    (OUT / "PIPELINE_INTEGRATION_E2E_REPORT.md").write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({
        "passed": payload["passed"],
        "status_path": payload["status_path"],
        "stages_succeeded": payload["stages_succeeded"],
        "validation_score": payload["validation_score"],
        "report": str(OUT / "PIPELINE_INTEGRATION_E2E_REPORT.md"),
    }, indent=2))
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
