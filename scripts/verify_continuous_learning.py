#!/usr/bin/env python3
"""E2E validation for Continuous Learning & Self-Improvement Engine."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import engines  # noqa: F401
from engines import registry
from services.learning import (
    build_learning_dashboard,
    consult_context,
    for_script,
    get_optimization_api,
    predict_performance,
    record_productions_from_context,
)

OUT = ROOT / "data" / "productions" / "_validation" / "continuous_learning"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    consult = consult_context(
        "why cameras can see infrared",
        niche="science",
        platform="youtube_shorts",
        runtime_sec=60,
    )
    pred = predict_performance(
        topic="why cameras can see infrared",
        platform="youtube_shorts",
        runtime_sec=60,
        qa_score=94,
    )
    api = get_optimization_api()
    script_q = api.for_script("infrared")
    psych_q = api.for_psychology("infrared")

    ctx = {
        "subject": "infrared cameras",
        "target_platform": "youtube_shorts",
        "selected_ideas": [
            {
                "id": "e2e_ir",
                "title": "Why cameras can see infrared",
                "script": "Silicon sensors detect near-infrared…",
                "psychology_score": 90,
                "seo_score": 92,
                "visual_score": 93,
                "pqa_score": 95,
                "pqa_decision": "APPROVE",
                "human_attention_score": 91,
            }
        ],
    }
    saved = record_productions_from_context(ctx, pipeline_used="executive", run_id="e2e_cl")
    learning = registry.get_engine("learning").run({**ctx, "analytics_summary": {}})
    continuous = registry.get_engine("continuous_learning").run(
        {"subject": "infrared cameras", "target_platform": "youtube_shorts", "target_runtime_sec": 60}
    )
    dash = build_learning_dashboard()

    payload = {
        "status": "SUCCESS"
        if (
            consult.get("learning_consulted")
            and pred.get("expected_views") is not None
            and saved
            and continuous.get("learning_brief")
            and "top_performing_topics" in dash
            and script_q.get("question")
            and psych_q.get("question")
        )
        else "FAIL",
        "consult": {k: consult[k] for k in ("learning_consulted", "suggested_improvements") if k in consult},
        "predictions": pred,
        "self_optimization": {"script": script_q, "psychology": psych_q, "discovery": api.for_discovery()},
        "productions_saved": len(saved),
        "learning_report_status": (learning.get("learning_report") or {}).get("status"),
        "dashboard_keys": sorted(dash.keys()),
    }

    json_path = OUT / "CONTINUOUS_LEARNING_E2E.json"
    md_path = OUT / "CONTINUOUS_LEARNING_E2E_REPORT.md"
    json_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    md_path.write_text(
        "\n".join(
            [
                "# Continuous Learning — E2E",
                "",
                f"**Status:** {payload['status']}",
                "",
                f"Productions saved: {payload['productions_saved']}",
                f"Expected views: {pred.get('expected_views')} · CTR {pred.get('expected_ctr')} · confidence {pred.get('confidence')}",
                f"Script API: {script_q.get('question')}",
                f"Dashboard topics tracked: {len(dash.get('top_performing_topics') or [])}",
                "",
                f"JSON: `{json_path}`",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps({"status": payload["status"], "views": pred.get("expected_views"), "saved": len(saved)}, indent=2))
    print(f"Report: {md_path}")
    print(f"=== RESULT: {payload['status']} ===")
    return 0 if payload["status"] == "SUCCESS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
