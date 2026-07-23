#!/usr/bin/env python3
"""CLI — Human Realism Framework V1."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Human Realism Framework")
    parser.add_argument("command", choices=["ensure", "show", "selftest", "plan"])
    parser.add_argument("character_id", nargs="?", default="CHAR-0001")
    args = parser.parse_args()

    from services.human_realism import (
        GOLD_STANDARD_CHARACTER_ID,
        build_performance_plan,
        list_character_ids,
        materialize_framework,
        resolve_character,
    )

    if args.command == "ensure":
        index = materialize_framework(include_characters=True)
        print(json.dumps(index, indent=2))
        return 0

    if args.command == "show":
        pkg = resolve_character(args.character_id)
        print(
            json.dumps(
                {
                    "character_id": pkg.get("character_id"),
                    "name": pkg.get("name"),
                    "is_gold_standard": pkg.get("is_gold_standard"),
                    "inherits_from": pkg.get("inherits_from"),
                    "reference_implementation": pkg.get("reference_implementation"),
                    "style_mode": pkg.get("style_mode"),
                    "gait": pkg.get("gait"),
                    "gestures_favorites": (pkg.get("gestures") or {}).get("favorites"),
                    "systems": [
                        "anatomy",
                        "skeleton",
                        "muscles",
                        "face",
                        "eyes",
                        "blinking",
                        "breathing",
                        "locomotion",
                        "hands",
                        "clothing",
                        "hair",
                        "emotion",
                        "quality_validation",
                    ],
                },
                indent=2,
            )
        )
        return 0

    if args.command == "plan":
        plan = build_performance_plan(
            character_id=args.character_id,
            scene={
                "scene_number": 1,
                "narration": "Let me show you how careful observation keeps people safe.",
                "length_sec": 4.0,
                "studio_expression": "teaching",
            },
        )
        print(json.dumps(plan, indent=2))
        return 0

    # selftest
    index = materialize_framework(include_characters=True)
    doctor = resolve_character(GOLD_STANDARD_CHARACTER_ID)
    atlas = resolve_character("CHAR-ATLAS")
    assert doctor.get("is_gold_standard") is True
    assert atlas.get("reference_implementation") == GOLD_STANDARD_CHARACTER_ID
    assert "skeleton" in doctor and "skeleton" in atlas
    assert doctor["skeleton"]["hierarchy"] == atlas["skeleton"]["hierarchy"]
    assert doctor.get("visual_identity", {}).get("silhouette") != atlas.get("visual_identity", {}).get(
        "silhouette"
    )
    ids = set(list_character_ids())
    assert "DOCTOR_001" in ids
    assert {"CHAR-ATLAS", "CHAR-NOVA", "CHAR-ORION", "CHAR-PIPER", "CHAR-LUNA"} <= ids
    plan = build_performance_plan(
        character_id="CHAR-0001",
        scene={"scene_number": 1, "narration": "We will heal understanding.", "studio_expression": "compassion"},
    )
    assert plan["emotion"]["primary"]
    assert plan["foot_contact_required"] is True
    print(
        json.dumps(
            {
                "ok": True,
                "gold_standard": GOLD_STANDARD_CHARACTER_ID,
                "characters": len(index.get("characters") or []),
                "shared_skeleton": True,
                "distinct_identity": True,
                "sample_emotion": plan["emotion"]["primary"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
