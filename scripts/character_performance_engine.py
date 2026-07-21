#!/usr/bin/env python3
"""CLI — Generational Character Performance Engine."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    p = argparse.ArgumentParser(description="Character Performance Engine")
    p.add_argument(
        "command",
        choices=["build", "validate", "selftest", "doctor"],
        help="build scene package | validate | selftest | doctor sample",
    )
    p.add_argument("--narration", default="Walk with me — let's examine the evidence together.")
    p.add_argument("--duration", type=float, default=4.0)
    p.add_argument("--character", default="DOCTOR_001")
    p.add_argument("--location", default="LOC-GMRI")
    p.add_argument("--write", action="store_true")
    args = p.parse_args()

    from services.character_performance_engine import (
        build_character_performance,
        build_episode_performance_package,
        validate_character_performance,
    )

    scene = {
        "scene_number": 1,
        "narration": args.narration,
        "length_sec": args.duration,
        "studio_expression": "teaching",
        "subject": "diagnostic hologram",
        "prop": "microscope",
    }

    if args.command == "doctor":
        scene["narration"] = (
            "Walk through the lab with me. Point to the hologram — "
            "then look through the microscope."
        )
        scene["length_sec"] = 5.0

    pkg = build_character_performance(
        character_id=args.character,
        scene=scene,
        scene_index=0,
        location=args.location,
    )

    out_dir = ROOT / "data" / "character_performance_engine" / "packages"
    if args.command in {"build", "doctor"} or args.write:
        out_dir.mkdir(parents=True, exist_ok=True)
        slug = "DOCTOR_001_LAB_WALK" if args.command == "doctor" else "SCENE_SAMPLE"
        path = out_dir / f"{slug}.json"
        path.write_text(json.dumps(pkg, indent=2, default=str) + "\n", encoding="utf-8")
        episode = build_episode_performance_package(
            [{"character_performance_package": pkg}],
            topic=slug,
            production_id=slug.lower(),
            write=True,
            out_dir=out_dir / slug.lower(),
        )
        print(
            json.dumps(
                {
                    "ok": bool((pkg.get("validation") or {}).get("ok")),
                    "path": str(path),
                    "episode_path": episode.get("path"),
                    "validation": pkg.get("validation"),
                    "camera_follow": pkg.get("camera_follow"),
                    "path_keyframes": len((pkg.get("simulation") or {}).get("keyframes") or []),
                    "travel_norm": (pkg.get("locomotion") or {}).get("path_distance_norm"),
                },
                indent=2,
            )
        )
        return 0 if (pkg.get("validation") or {}).get("ok") else 1

    if args.command == "validate":
        review = validate_character_performance(pkg)
        print(json.dumps(review, indent=2))
        return 0 if review.get("ok") else 1

    # selftest
    review = validate_character_performance(pkg)
    path_ok = len((pkg.get("simulation") or {}).get("keyframes") or []) >= 3
    actor = bool((pkg.get("true_motion") or {}).get("actor_driven"))
    ken = pkg.get("ken_burns") is True
    ok = bool(review.get("ok") and path_ok and actor and not ken)
    # Negative: camera-only stub must fail
    bad = validate_character_performance(
        {
            "ken_burns": True,
            "motion_class": "ken_burns",
            "blocking": {},
            "locomotion": {"waypoints": [], "path_distance_norm": 0},
            "body_performance": {"continuous": False, "body_actions_present": []},
            "interactions": {"count": 0, "events": []},
            "environment_life": {"living": False, "channels": []},
            "camera_follow": {"follows_actor_path": False, "camera_replaces_action": True},
            "simulation": {"actor_driven": False, "keyframes": []},
        }
    )
    print(
        json.dumps(
            {
                "ok": ok and not bad.get("ok"),
                "positive_validation": review,
                "negative_ken_burns_rejected": not bad.get("ok"),
                "negative_failures": bad.get("failures"),
                "path_keyframes": len((pkg.get("simulation") or {}).get("keyframes") or []),
                "philosophy": pkg.get("philosophy"),
            },
            indent=2,
            default=str,
        )
    )
    return 0 if ok and not bad.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
