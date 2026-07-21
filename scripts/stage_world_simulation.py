#!/usr/bin/env python3
"""CLI — Generational Stage & World Simulation Engine."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    p = argparse.ArgumentParser(description="Stage & World Simulation Engine")
    p.add_argument(
        "command",
        choices=["ensure", "build", "validate", "list", "selftest"],
    )
    p.add_argument("--world", default="WORLD-GMRI-MEDICAL-LAB")
    args = p.parse_args()

    from services.stage_world_simulation import (
        build_world_package,
        ensure_world_library,
        list_worlds,
        materialize_world_package,
        validate_world_package,
    )

    if args.command == "ensure":
        lib = ensure_world_library(write_packages=True)
        print(
            json.dumps(
                {
                    "ok": True,
                    "library": str(ROOT / "data/world_simulation/WORLD_LIBRARY.json"),
                    "count": lib.get("count"),
                    "worlds": [
                        {
                            "id": w.get("world_id"),
                            "name": w.get("display_name"),
                            "validation_ok": w.get("validation_ok"),
                        }
                        for w in lib.get("worlds") or []
                    ],
                },
                indent=2,
            )
        )
        return 0

    if args.command == "list":
        print(json.dumps(list_worlds(), indent=2))
        return 0

    pkg = build_world_package(args.world)

    if args.command == "build":
        paths = materialize_world_package(pkg)
        print(
            json.dumps(
                {
                    "ok": bool((pkg.get("validation") or {}).get("ok")),
                    "world_id": pkg.get("world_id"),
                    "validation": pkg.get("validation"),
                    "paths": paths,
                    "scene_ref": pkg.get("scene_ref"),
                },
                indent=2,
            )
        )
        return 0 if (pkg.get("validation") or {}).get("ok") else 1

    if args.command == "validate":
        review = validate_world_package(pkg)
        print(json.dumps(review, indent=2))
        return 0 if review.get("ok") else 1

    # selftest
    lib = ensure_world_library(write_packages=True)
    lab = build_world_package("WORLD-GMRI-MEDICAL-LAB")
    forest = build_world_package("Forest")
    bad = validate_world_package(
        {
            "flat_image_background": True,
            "geometry": {"not_a_flat_image": False},
            "navigation": {},
            "interaction_points": {"count": 0, "points": []},
            "living_world": {"living": False, "channels": []},
            "camera": {"follows_performance": False, "camera_replaces_actor_motion": True},
            "persistent": False,
        }
    )
    ok = (
        bool((lab.get("validation") or {}).get("ok"))
        and bool((forest.get("validation") or {}).get("ok"))
        and not bad.get("ok")
        and int(lib.get("count") or 0) >= 10
    )
    print(
        json.dumps(
            {
                "ok": ok,
                "library_count": lib.get("count"),
                "lab_ok": (lab.get("validation") or {}).get("ok"),
                "forest_ok": (forest.get("validation") or {}).get("ok"),
                "flat_photo_rejected": not bad.get("ok"),
                "lab_interactions": (lab.get("interaction_points") or {}).get("count"),
                "lab_nav_waypoints": len(
                    ((lab.get("navigation") or {}).get("nav_mesh") or {}).get("waypoints") or []
                ),
                "philosophy": lab.get("philosophy"),
            },
            indent=2,
        )
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
