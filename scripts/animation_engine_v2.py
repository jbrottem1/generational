#!/usr/bin/env python3
"""CLI — Cinematic Animation Engine V2 (quality evolution of V1)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _demo() -> dict:
    return {
        "topic": "Are Leprechauns Real? The Truth Behind Ireland's Tiny Tricksters",
        "world_package": {"world_type": "Irish misty countryside"},
        "visual_package": {
            "scenes": [
                {
                    "scene_number": 1,
                    "purpose": "hook",
                    "length_sec": 3,
                    "narration": "What if I told you millions know the name leprechaun?",
                    "subject": "leprechaun legend",
                },
                {
                    "scene_number": 2,
                    "purpose": "story_beat",
                    "length_sec": 3.5,
                    "narration": "In Irish folklore a solitary fairy often works as a shoemaker.",
                },
                {
                    "scene_number": 3,
                    "purpose": "story_beat",
                    "length_sec": 3.5,
                    "narration": "Celtic traditions place otherworld beings among the mounds of the forest.",
                },
                {
                    "scene_number": 4,
                    "purpose": "payoff",
                    "length_sec": 3,
                    "narration": "The word likely comes from Old Irish luchorpán — a little body.",
                },
            ]
        },
    }


def cmd_selftest(_: argparse.Namespace) -> int:
    from engines.animation import AnimationEngine
    from services.animation_engine import build_animation_package

    eng = AnimationEngine()
    assert eng.is_ready()
    assert eng.version.startswith("2.")
    pkg = build_animation_package(_demo(), write=True)
    print(
        json.dumps(
            {
                "ok": True,
                "engine_ready": True,
                "version": eng.version,
                "label": eng.label,
                "path": pkg.get("path"),
                "excellence": (pkg.get("animation_excellence") or {}).get("animation_excellence_score"),
                "gate": (pkg.get("quality_gate") or {}).get("decision"),
                "immersion_pass_ratio": ((pkg.get("quality_gate") or {}).get("metrics") or {}).get(
                    "immersion_pass_ratio"
                ),
                "summary": pkg.get("summary"),
                "scenes": [
                    {
                        "n": d.get("scene_number"),
                        "emotion": d.get("emotion"),
                        "lighting": d.get("lighting_mood"),
                        "camera": (d.get("layers") or {}).get("camera", {}).get("camera_move"),
                        "purpose": (d.get("layers") or {}).get("camera", {}).get("narrative_purpose"),
                    }
                    for d in pkg.get("scene_decisions") or []
                ],
            },
            indent=2,
        )
    )
    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    from services.animation_engine import build_animation_package

    cand = _demo()
    if args.candidate and Path(args.candidate).is_file():
        cand = json.loads(Path(args.candidate).read_text(encoding="utf-8"))
    if args.topic:
        cand["topic"] = args.topic
    pkg = build_animation_package(cand, topic=str(cand.get("topic") or ""), write=True)
    print(json.dumps(pkg.get("summary"), indent=2))
    print(f"Wrote {pkg.get('path')}")
    print(f"Report {pkg.get('report_markdown_path')}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Cinematic Animation Engine V2")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("selftest")
    s.set_defaults(func=cmd_selftest)
    plan = sub.add_parser("plan")
    plan.add_argument("--topic", default="")
    plan.add_argument("--candidate", default="")
    plan.set_defaults(func=cmd_plan)
    args = p.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
