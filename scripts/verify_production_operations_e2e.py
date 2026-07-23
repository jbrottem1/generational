#!/usr/bin/env python3
"""E2E — Production Operations Layer (prompt → packaged production)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import engines  # noqa: F401
from engines import registry
from services.production_operations import run_studio_ops, search_history, queue_summary

OUT = ROOT / "data" / "productions" / "_validation" / "production_operations"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> int:
    print("=== Production Operations E2E ===")
    eng = registry.get_engine("production_operations")
    assert eng and eng.is_ready()

    result = run_studio_ops(
        topic="Why Octopuses Have Three Hearts",
        platform="youtube_shorts",
        length_sec=45,
        style="educational",
        narrator="professor",
        voice="default",
        quality_target=98,
    )

    status = result["status"]
    report = result["report"]
    stages_done = sum(
        1 for s in status["stages"] if s["status"] in ("succeeded", "skipped", "degraded", "partial")
    )
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "production_id": result["production_id"],
        "succeeded": result["succeeded"],
        "elapsed_ms": result["elapsed_ms"],
        "stages_completed": stages_done,
        "stages_total": 16,
        "pipeline_health": status.get("pipeline_health"),
        "retry_count": status.get("retry_count"),
        "recommendation": report.get("final_recommendation"),
        "overall_quality_score": report.get("overall_quality_score"),
        "export_validation": result.get("export_validation"),
        "report_path": result.get("report_path"),
        "history_hits": len(search_history(query="Octopus")),
        "queue": queue_summary(),
        "passed": (
            result["succeeded"]
            and stages_done == 16
            and bool(result.get("report_path"))
            and report.get("final_recommendation") is not None
        ),
    }
    (OUT / "PRODUCTION_OPS_E2E.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (OUT / "PRODUCTION_OPS_E2E_REPORT.md").write_text(
        "\n".join(
            [
                "# Production Operations E2E",
                "",
                f"**Passed: {payload['passed']}**",
                f"- Production: `{payload['production_id']}`",
                f"- Stages: {payload['stages_completed']}/{payload['stages_total']}",
                f"- Quality: {payload['overall_quality_score']}",
                f"- Recommendation: {payload['recommendation']}",
                f"- Health: {payload['pipeline_health']}",
                f"- Retries: {payload['retry_count']}",
                f"- Report: `{payload['report_path']}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps({k: payload[k] for k in ("passed", "production_id", "stages_completed", "overall_quality_score", "recommendation", "report_path")}, indent=2))
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
