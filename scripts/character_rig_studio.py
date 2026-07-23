#!/usr/bin/env python3
"""CLI — Generational Character Rig Studio."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    p = argparse.ArgumentParser(description="Character Rig Studio")
    p.add_argument(
        "command",
        choices=["ensure", "build", "validate", "list", "selftest"],
    )
    p.add_argument("--character", default="DOCTOR_001")
    args = p.parse_args()

    from services.character_rig_studio import (
        build_character_rig,
        ensure_library,
        list_actors,
        materialize_character_rig,
        validate_character_rig,
    )

    if args.command == "ensure":
        lib = ensure_library(write_packages=True)
        print(
            json.dumps(
                {
                    "ok": True,
                    "library": str(ROOT / "data/character_rig_studio/CHARACTER_LIBRARY.json"),
                    "count": lib.get("count"),
                    "actors": [
                        {
                            "id": a.get("character_id"),
                            "name": a.get("canonical_name"),
                            "status": a.get("status"),
                            "validation_ok": a.get("validation_ok"),
                        }
                        for a in lib.get("actors") or []
                    ],
                },
                indent=2,
            )
        )
        return 0

    if args.command == "list":
        print(json.dumps(list_actors(), indent=2))
        return 0

    pkg = build_character_rig(args.character)

    if args.command == "build":
        paths = materialize_character_rig(pkg)
        print(
            json.dumps(
                {
                    "ok": bool((pkg.get("validation") or {}).get("ok")),
                    "character_id": pkg.get("character_id"),
                    "validation": pkg.get("validation"),
                    "paths": paths,
                    "scene_ref": pkg.get("scene_ref"),
                },
                indent=2,
            )
        )
        return 0 if (pkg.get("validation") or {}).get("ok") else 1

    if args.command == "validate":
        review = validate_character_rig(pkg)
        print(json.dumps(review, indent=2))
        return 0 if review.get("ok") else 1

    # selftest
    lib = ensure_library(write_packages=True)
    doctor = build_character_rig("DOCTOR_001")
    founder = build_character_rig("FOUNDER_001")
    bad = validate_character_rig({"identity": {"character_id": "X"}})
    ok = (
        bool((doctor.get("validation") or {}).get("ok"))
        and bool((founder.get("validation") or {}).get("ok"))
        and not bad.get("ok")
        and int(lib.get("count") or 0) >= 7
    )
    print(
        json.dumps(
            {
                "ok": ok,
                "library_count": lib.get("count"),
                "doctor_ok": (doctor.get("validation") or {}).get("ok"),
                "founder_ok": (founder.get("validation") or {}).get("ok"),
                "incomplete_rejected": not bad.get("ok"),
                "doctor_joint_count": (doctor.get("body_rig") or {}).get("joint_count"),
                "doctor_clips": (doctor.get("performance_system") or {}).get("clip_count"),
                "philosophy": doctor.get("philosophy"),
            },
            indent=2,
        )
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
