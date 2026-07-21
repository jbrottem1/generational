#!/usr/bin/env python3
"""CLI — Visual Source Intelligence (selection layer, no renderer)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _demo_candidate(topic: str) -> dict:
    return {
        "topic": topic,
        "visual_package": {
            "scenes": [
                {
                    "scene_number": 1,
                    "purpose": "hook",
                    "narration": "These colors could determine whether firefighters save your house.",
                    "visual_description": "Three differently colored fire hydrants on one corner",
                    "stock_footage_query": "suburban fire hydrants different colors",
                    "ai_video_prompt": "cinematic push toward three painted fire hydrants",
                    "ai_image_prompt": "three fire hydrants red yellow green",
                },
                {
                    "scene_number": 2,
                    "purpose": "story_beat",
                    "narration": "Each major color indicates a flow rating firefighters use.",
                    "visual_description": "color legend diagram",
                    "stock_footage_query": "fire hydrant color code chart",
                },
                {
                    "scene_number": 3,
                    "purpose": "story_beat",
                    "narration": "Flow rate matters when water supply decides whether a house is saved.",
                    "ai_video_prompt": "water flow visualization from hydrant",
                    "stock_footage_query": "fire hose water flow",
                },
                {
                    "scene_number": 4,
                    "purpose": "payoff",
                    "narration": "Two nearby hydrants can carry different ratings on the same street.",
                    "visual_description": "map of water main between hydrants",
                },
            ]
        },
    }


def cmd_selftest(_: argparse.Namespace) -> int:
    from services.visual_source_intelligence import build_visual_source_package

    pkg = build_visual_source_package(
        _demo_candidate("Why Fire Hydrants Are Different Colors"),
        topic="Why Fire Hydrants Are Different Colors",
        write=True,
    )
    summary = {
        "ok": True,
        "path": pkg.get("path"),
        "scene_count": pkg.get("scene_count"),
        "fallback_summary": pkg.get("fallback_summary"),
        "creative_review": (pkg.get("creative_review") or {}).get("answers"),
        "selections": [
            {
                "scene": d.get("scene_number"),
                "source": (d.get("selected") or {}).get("source_key"),
                "tier": d.get("tier_label"),
                "fallback_reason": d.get("fallback_reason"),
                "camera_motion": d.get("camera_motion"),
            }
            for d in pkg.get("scene_decisions") or []
        ],
    }
    print(json.dumps(summary, indent=2))
    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    from services.visual_source_intelligence import build_visual_source_package

    topic = args.topic or "Untitled topic"
    candidate = _demo_candidate(topic)
    if args.candidate and Path(args.candidate).is_file():
        candidate = json.loads(Path(args.candidate).read_text(encoding="utf-8"))
    pkg = build_visual_source_package(candidate, topic=topic, write=True)
    print(json.dumps(pkg, indent=2, default=str)[:12000])
    print(f"\nWrote: {pkg.get('path')}")
    print(f"Review: {pkg.get('review_markdown_path')}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Visual Source Intelligence")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_self = sub.add_parser("selftest", help="Run demo selection + write package")
    p_self.set_defaults(func=cmd_selftest)

    p_plan = sub.add_parser("plan", help="Plan sources for a topic or candidate JSON")
    p_plan.add_argument("--topic", default="Why Fire Hydrants Are Different Colors")
    p_plan.add_argument("--candidate", default="", help="Optional candidate JSON path")
    p_plan.set_defaults(func=cmd_plan)

    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
