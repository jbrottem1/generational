#!/usr/bin/env python3
"""E2E validation for Executive Orchestrator (plan + optional live smoke)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import engines  # noqa: F401
from services.executive_orchestrator import create_video, parse_production_request, stage_plan
from services.executive_orchestrator.logging_store import persist_run_log

OUT = ROOT / "data" / "productions" / "_validation" / "executive_orchestrator"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    cmd_short = "Create a 60 second YouTube Short explaining why cameras can see infrared."
    cmd_doc = "Create a 12 minute documentary about black holes."

    brief_short = parse_production_request(cmd_short)
    brief_doc = parse_production_request(cmd_doc)

    run_short = create_video(cmd_short, plan_only=True, skip_publishing=True)
    run_doc = create_video(cmd_doc, plan_only=True, skip_publishing=True)

    payload = {
        "status": "SUCCESS"
        if (
            brief_short.runtime_sec == 60
            and "youtube_shorts" in brief_short.platforms
            and brief_doc.runtime_sec == 720
            and brief_doc.format == "documentary"
            and run_short.get("status") == "completed"
            and run_doc.get("status") == "completed"
            and run_short.get("export_paths")
        )
        else "FAIL",
        "briefs": {"short": brief_short.to_dict(), "documentary": brief_doc.to_dict()},
        "stage_plan": stage_plan(),
        "runs": {"short": run_short, "documentary": run_doc},
    }

    json_path = OUT / "EXECUTIVE_ORCHESTRATOR_E2E.json"
    md_path = OUT / "EXECUTIVE_ORCHESTRATOR_E2E_REPORT.md"
    json_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    md_path.write_text(
        "\n".join(
            [
                "# Executive Orchestrator — E2E",
                "",
                f"**Status:** {payload['status']}",
                "",
                "## Commands",
                f"- Short: `{cmd_short}` → {brief_short.runtime_sec}s · {brief_short.platforms}",
                f"- Doc: `{cmd_doc}` → {brief_doc.runtime_sec}s · {brief_doc.format}",
                "",
                "## Stages",
                *[f"- {s['label']} (η {s['eta_sec']}s)" for s in stage_plan()],
                "",
                f"Short run id: `{run_short.get('id')}` status={run_short.get('status')}",
                f"Export: `{run_short.get('export_paths')}`",
                "",
                f"JSON: `{json_path}`",
            ]
        ),
        encoding="utf-8",
    )
    persist_run_log(run_short)

    print(json.dumps({"status": payload["status"], "short_id": run_short.get("id"), "doc_id": run_doc.get("id")}, indent=2))
    print(f"Report: {md_path}")
    print(f"=== RESULT: {payload['status']} ===")
    return 0 if payload["status"] == "SUCCESS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
