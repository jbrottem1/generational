#!/usr/bin/env python3
"""Run Continuous Learning & Publishing Intelligence cycle (V2.0)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.publishing_intelligence import run_intelligence_cycle  # noqa: E402
from services.launch_readiness import run_launch_readiness_audit  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Publishing Intelligence V2.0 cycle")
    parser.add_argument("--topic", default="How bees pollinate flowers")
    parser.add_argument("--platform", default="youtube_shorts")
    parser.add_argument("--seed-demo-actuals", action="store_true", help="Seed demo metrics for offline calibration")
    parser.add_argument("--audit", action="store_true", help="Run Launch Readiness Audit after cycle")
    parser.add_argument("--mp4", default="", help="Optional path to final MP4")
    args = parser.parse_args()

    candidate = {
        "topic": args.topic,
        "title": args.topic,
        "platform": args.platform,
        "hook": "Most people get this wrong about nature.",
        "niche": "Education",
        "quality_score": 91,
    }
    if args.mp4:
        candidate["video_path"] = args.mp4
        candidate["render_package"] = {"mp4_path": args.mp4, "file_uri": args.mp4}

    print("=== Publishing Intelligence Cycle ===")
    result = run_intelligence_cycle(
        candidate,
        platforms=None,
        quality_scores={
            "hook_strength": 88,
            "overall_production_score": 91,
            "visual_quality": 90,
            "retention_prediction": 86,
            "shareability": 84,
            "seo_quality": 88,
        },
        seed_demo_actuals=args.seed_demo_actuals,
    )
    summary = {
        "topic": result.get("topic"),
        "platforms": list((result.get("publish_packages") or {}).get("platforms") or {}),
        "seo_title": (result.get("publish_packages") or {}).get("seo_title"),
        "suggested_publish_time": (result.get("publish_packages") or {}).get("suggested_publish_time"),
        "analytics_record_id": result.get("analytics_record_id"),
        "prediction_accuracy_pct": (result.get("calibration") or {}).get("average_prediction_accuracy_pct"),
        "highest_impact_improvement": (result.get("highest_impact_improvement") or {}).get("recommendation"),
        "confidence_score": (result.get("dashboard_snapshot") or {}).get("confidence_score"),
        "business_monthly_earnings_usd": (result.get("business_intelligence") or {}).get(
            "estimated_monthly_earnings_usd"
        ),
        "cycle_path": result.get("cycle_path"),
    }
    print(json.dumps(summary, indent=2))

    if args.audit:
        print("\n=== Launch Readiness Audit ===")
        audit = run_launch_readiness_audit()
        print(
            json.dumps(
                {
                    "launch_readiness_score": audit.get("launch_readiness_score"),
                    "recommendation": audit.get("recommendation"),
                    "blockers": audit.get("prioritized_blockers") or audit.get("blockers") or [],
                    "report": str(ROOT / "LAUNCH_READINESS_AUDIT.md"),
                },
                indent=2,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
