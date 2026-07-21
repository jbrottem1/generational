#!/usr/bin/env python3
"""CLI — Generational Physics & Interaction Engine."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    p = argparse.ArgumentParser(description="Physics & Interaction Engine")
    p.add_argument(
        "command",
        choices=["ensure", "build", "interact", "validate", "selftest"],
    )
    p.add_argument("--character", default="DOCTOR_001")
    p.add_argument("--type", default="using_microscopes")
    p.add_argument("--target", default="microscope")
    args = p.parse_args()

    from services.physics_interaction import (
        build_interaction_package,
        build_physics_profile,
        ensure_physics_library,
        materialize_interaction,
        materialize_physics_profile,
        validate_interaction_package,
        validate_physics_profile,
    )

    if args.command == "ensure":
        lib = ensure_physics_library(write_packages=True)
        print(
            json.dumps(
                {
                    "ok": True,
                    "library": str(ROOT / "data/physics_interaction/PHYSICS_LIBRARY.json"),
                    "count": lib.get("count"),
                    "profiles": lib.get("profiles"),
                },
                indent=2,
            )
        )
        return 0

    if args.command == "interact":
        ix = build_interaction_package(
            actor=args.character,
            target=args.target,
            interaction_type=args.type,
            physics_state="manipulating",
            world_id="WORLD-GMRI-MEDICAL-LAB",
        )
        path = materialize_interaction(ix)
        review = validate_interaction_package(ix)
        print(json.dumps({"ok": review.get("ok"), "path": path, "package": ix, "validation": review}, indent=2))
        return 0 if review.get("ok") else 1

    stage = None
    try:
        from services.stage_world_simulation import resolve_world_package

        stage = resolve_world_package("WORLD-GMRI-MEDICAL-LAB")
    except Exception:  # noqa: BLE001
        pass

    profile = build_physics_profile(
        args.character,
        world_id="WORLD-GMRI-MEDICAL-LAB",
        stage_world=stage,
        interactions=[
            build_interaction_package(
                actor=args.character,
                target=args.target,
                interaction_type=args.type,
                physics_state="manipulating",
            )
        ],
    )

    if args.command == "build":
        paths = materialize_physics_profile(profile)
        print(
            json.dumps(
                {
                    "ok": bool((profile.get("validation") or {}).get("ok")),
                    "character_id": profile.get("character_id"),
                    "validation": profile.get("validation"),
                    "paths": paths,
                },
                indent=2,
            )
        )
        return 0 if (profile.get("validation") or {}).get("ok") else 1

    if args.command == "validate":
        print(json.dumps(validate_physics_profile(profile), indent=2))
        return 0 if (profile.get("validation") or {}).get("ok") else 1

    # selftest
    lib = ensure_physics_library(write_packages=True)
    doctor = build_physics_profile("DOCTOR_001", stage_world=stage, world_id="WORLD-GMRI-MEDICAL-LAB")
    bad_ix = validate_interaction_package({"interaction_id": "x"})
    bad_profile = validate_physics_profile(
        {
            "hand_physics": {},
            "foot_physics": {"planting": {"no_slide": False}},
            "body_physics": {"forbid": [], "balance": {}},
            "collision": {"enabled": False},
            "clothing_physics": {},
            "hair_physics": {},
            "objects": [],
        }
    )
    ok = (
        bool((doctor.get("validation") or {}).get("ok"))
        and not bad_ix.get("ok")
        and not bad_profile.get("ok")
        and int(lib.get("count") or 0) >= 4
    )
    print(
        json.dumps(
            {
                "ok": ok,
                "library_count": lib.get("count"),
                "doctor_ok": (doctor.get("validation") or {}).get("ok"),
                "incomplete_interaction_rejected": not bad_ix.get("ok"),
                "broken_physics_rejected": not bad_profile.get("ok"),
                "supported_interactions": len(doctor.get("supported_interactions") or []),
                "object_count": len(doctor.get("objects") or []),
                "philosophy": doctor.get("philosophy"),
            },
            indent=2,
        )
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
