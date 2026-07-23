#!/usr/bin/env python3
"""CLI — Generational Cinematic Direction Studio."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    p = argparse.ArgumentParser(description="Cinematic Direction Studio")
    p.add_argument("command", choices=["direct", "validate", "selftest"])
    p.add_argument("--topic", default="Directed Teaching Demo")
    args = p.parse_args()

    from services.cinematic_direction_studio import (
        build_episode_director_package,
        validate_director_package,
        validate_episode_direction,
    )

    scenes = [
        {
            "scene_number": 1,
            "purpose": "hook",
            "length_sec": 3.5,
            "narration": "Walk with me into the lab — something important is waiting.",
            "studio_character_id": "DOCTOR_001",
        },
        {
            "scene_number": 2,
            "purpose": "story_beat",
            "length_sec": 4.0,
            "narration": "Look through the microscope. Notice how clarity changes everything.",
            "studio_character_id": "DOCTOR_001",
        },
        {
            "scene_number": 3,
            "purpose": "story_beat",
            "length_sec": 3.8,
            "narration": "Pause. Think about what this means for the patient.",
            "studio_character_id": "DOCTOR_001",
        },
        {
            "scene_number": 4,
            "purpose": "payoff",
            "length_sec": 3.5,
            "narration": "When we understand, we can choose hope — and act.",
            "studio_character_id": "DOCTOR_001",
        },
    ]

    episode = build_episode_director_package(
        scenes,
        topic=args.topic,
        production_id="cds_demo",
        location="LOC-GMRI",
        write=args.command == "direct",
    )

    if args.command == "direct":
        print(
            json.dumps(
                {
                    "ok": bool((episode.get("validation") or {}).get("ok")),
                    "path": episode.get("path"),
                    "validation": episode.get("validation"),
                    "emotional_timeline": episode.get("emotional_timeline"),
                    "shots": [s.get("shot_type") for s in episode.get("scenes") or []],
                },
                indent=2,
            )
        )
        return 0 if (episode.get("validation") or {}).get("ok") else 1

    if args.command == "validate":
        print(json.dumps(validate_episode_direction(episode), indent=2))
        return 0 if (episode.get("validation") or {}).get("ok") else 1

    # selftest
    scene_ok = all(validate_director_package(s).get("ok") for s in episode["scenes"])
    ep_ok = bool((episode.get("validation") or {}).get("ok"))
    shots = [s.get("shot_type") for s in episode["scenes"]]
    varied = len(set(shots)) >= 2
    # Negative: identical framing episode
    bad = validate_episode_direction(
        {
            "scenes": [
                {"shot_type": "medium", "emotional_objective": "curiosity"},
                {"shot_type": "medium", "emotional_objective": "curiosity"},
                {"shot_type": "medium", "emotional_objective": "curiosity"},
            ],
            "emotional_timeline": {"has_arc": False},
        }
    )
    ok = scene_ok and ep_ok and varied and not bad.get("ok")
    print(
        json.dumps(
            {
                "ok": ok,
                "scene_ok": scene_ok,
                "episode_ok": ep_ok,
                "shot_variety": shots,
                "identical_framing_rejected": not bad.get("ok"),
                "actor_beats_scene2": len(
                    ((episode["scenes"][1].get("actor_direction") or {}).get("beats") or [])
                ),
                "philosophy": episode.get("philosophy"),
            },
            indent=2,
        )
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
