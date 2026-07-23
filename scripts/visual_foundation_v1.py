#!/usr/bin/env python3
"""CLI — Generational Visual Foundation V1."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    p = argparse.ArgumentParser(description="Visual Foundation V1 — permanent constitution")
    p.add_argument("command", choices=["show", "gate", "selftest"])
    p.add_argument("--topic", default="Generational Visual Foundation check")
    args = p.parse_args()

    from services.visual_foundation import load_foundation, review_visual_foundation, visual_target

    if args.command == "show":
        data = load_foundation()
        print(
            json.dumps(
                {
                    "version": data.get("version"),
                    "visual_target": visual_target(),
                    "default_style_mode": data.get("default_style_mode"),
                    "document": "GENERATIONAL_VISUAL_FOUNDATION_V1.md",
                    "reject_count": len(data.get("reject") or []),
                    "integrations": data.get("integrations"),
                },
                indent=2,
            )
        )
        return 0

    candidate = {
        "topic": args.topic,
        "style_mode": "cinematic_realism",
        "studio_cast": [
            {
                "id": "CHAR-0001",
                "name": "The Doctor",
                "silhouette": "white_cyborg_doctor_blue_glow",
                "permanent_ip": True,
                "facial_range": ["teaching", "concerned"],
            }
        ],
        "studio_location": {
            "id": "LOC-GMRI",
            "ambient_life": ["researchers"],
            "detail_dressing": ["equipment"],
            "environmental_animation": ["screens"],
        },
        "visual_package": {
            "scenes": [
                {
                    "scene_number": 1,
                    "studio_character_id": "CHAR-0001",
                    "studio_expression": "teaching",
                }
            ]
        },
    }

    if args.command == "gate":
        print(json.dumps(review_visual_foundation(candidate), indent=2))
        return 0

    report = review_visual_foundation(candidate)
    empty = review_visual_foundation({"topic": "x", "visual_package": {"scenes": [{}]}})
    out = {
        "ok": bool(report.get("approved")) and not empty.get("approved"),
        "visual_target": visual_target(),
        "sample_decision": report.get("decision"),
        "empty_rejected": empty.get("decision") == "REJECT",
    }
    print(json.dumps(out, indent=2))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
