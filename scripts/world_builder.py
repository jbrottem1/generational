#!/usr/bin/env python3
"""Persistent World & Environment System CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.env import load_application_env  # noqa: E402

load_application_env(create_if_missing=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="Persistent World & Environment System")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="List available worlds")
    sub.add_parser("seed", help="Seed library from catalog templates")

    p = sub.add_parser("search", help="Search reusable worlds")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=6)

    p = sub.add_parser("inspect", help="Inspect a world by id or type")
    p.add_argument("world")

    p = sub.add_parser("select", help="Select best world for a topic")
    p.add_argument("--topic", required=True)
    p.add_argument("--niche", default="")
    p.add_argument("--location-type", default="")

    p = sub.add_parser("package", help="Generate World + Environment Packages")
    p.add_argument("--topic", required=True)
    p.add_argument("--niche", default="")
    p.add_argument("--world-type", default="")
    p.add_argument("--world-id", default="")
    p.add_argument("--scenes", type=int, default=4)
    p.add_argument("--platform", default="youtube_shorts")
    p.add_argument("--audience", default="general_public")
    p.add_argument("--production-id", default="")
    p.add_argument("--out", default="")

    p = sub.add_parser("validate", help="Validate a world/production package JSON")
    p.add_argument("path")

    p = sub.add_parser("validate-continuity", help="Validate continuity block in a package")
    p.add_argument("path")

    p = sub.add_parser("reset-state", help="Reset world state for a production")
    p.add_argument("--world-id", required=True)
    p.add_argument("--production-id", default="default")

    p = sub.add_parser("state", help="Show world state")
    p.add_argument("--world-id", required=True)
    p.add_argument("--production-id", default="default")

    p = sub.add_parser("extend", help="Add a zone to a library world")
    p.add_argument("--world-id", required=True)
    p.add_argument("--zone-id", required=True)
    p.add_argument("--zone-name", default="")

    p = sub.add_parser("usage", help="Show world usage history")
    p.add_argument("--limit", type=int, default=20)

    p = sub.add_parser("preview", help="Preview world zones/objects")
    p.add_argument("world")

    args = parser.parse_args()

    if args.cmd == "list":
        from services.world_builder import WORLD_TYPES, seed_library_from_catalog
        from services.world_builder.library import load_index

        seed_library_from_catalog()
        idx = load_index()
        rows = list((idx.get("worlds") or {}).values())
        print(json.dumps({"templates": list(WORLD_TYPES), "library_count": len(rows), "worlds": rows}, indent=2))
        return 0

    if args.cmd == "seed":
        from services.world_builder import seed_library_from_catalog

        print(json.dumps(seed_library_from_catalog(), indent=2))
        return 0

    if args.cmd == "search":
        from services.world_builder import search_worlds

        print(json.dumps(search_worlds(args.query, limit=args.limit), indent=2))
        return 0

    if args.cmd in ("inspect", "preview"):
        from services.world_builder import get_library_world, get_world

        w = get_library_world(args.world) or get_world(world_id=args.world) or get_world(world_type=args.world)
        if not w:
            print(json.dumps({"ok": False, "error": "not_found"}))
            return 1
        if args.cmd == "preview":
            print(
                json.dumps(
                    {
                        "world_id": w.get("world_id"),
                        "name": w.get("name"),
                        "zones": [z.get("id") for z in (w.get("zones") or [])],
                        "objects": [o.get("object_id") or o.get("name") for o in (w.get("objects") or [])],
                        "scale": w.get("scale"),
                        "ambience": w.get("sound_ambience"),
                    },
                    indent=2,
                )
            )
            return 0
        print(json.dumps(w, indent=2))
        return 0

    if args.cmd == "select":
        from services.world_builder import select_best_world

        print(
            json.dumps(
                select_best_world(topic=args.topic, niche=args.niche, location_type=args.location_type),
                indent=2,
            )
        )
        return 0

    if args.cmd == "package":
        from services.world_builder import build_world_package, empty_world_request

        req = empty_world_request(
            topic=args.topic,
            location_type=args.world_type,
            existing_world_id=args.world_id,
            platform=args.platform,
            audience=args.audience,
        )
        pkg = build_world_package(
            {"topic": args.topic, "niche": args.niche, "platform": args.platform, "audience": args.audience},
            topic=args.topic,
            niche=args.niche,
            world_type=args.world_type,
            world_id=args.world_id,
            scene_count=args.scenes,
            request=req,
            production_id=args.production_id or args.topic.replace(" ", "_")[:40],
            platform=args.platform,
            audience=args.audience,
        )
        if args.out:
            out = Path(args.out)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(pkg, indent=2) + "\n", encoding="utf-8")
            pkg["path"] = str(out)
        summary = {
            "path": pkg.get("path"),
            "world_id": pkg.get("world_id"),
            "world_type": pkg.get("world_type"),
            "zones_used": [e.get("selected_zone") for e in pkg.get("environment_packages") or []],
            "environment_package_count": len(pkg.get("environment_packages") or []),
            "validation": pkg.get("validation"),
            "continuity_validation": pkg.get("continuity_validation"),
            "selection_reasoning": (pkg.get("selection") or {}).get("selection_reasoning"),
            "cinematic_prescriptions_in_env": any(
                e.get("cinematic_prescriptions") for e in pkg.get("environment_packages") or []
            ),
        }
        print(json.dumps(summary, indent=2))
        return 0 if (pkg.get("validation") or {}).get("ok") else 1

    if args.cmd == "validate":
        from services.world_builder import validate_world_package

        data = json.loads(Path(args.path).read_text(encoding="utf-8"))
        result = validate_world_package(data)
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok") else 1

    if args.cmd == "validate-continuity":
        from services.world_builder import validate_production_continuity

        data = json.loads(Path(args.path).read_text(encoding="utf-8"))
        result = validate_production_continuity(
            (data.get("continuity") or {}).get("scene_bindings") or [],
            data.get("environment_packages") or [],
            (data.get("continuity") or {}).get("state") or {},
        )
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok") else 1

    if args.cmd == "reset-state":
        from services.world_builder import reset_world_state

        print(json.dumps(reset_world_state(args.world_id, args.production_id), indent=2))
        return 0

    if args.cmd == "state":
        from services.world_builder import load_state

        print(json.dumps(load_state(args.world_id, args.production_id), indent=2))
        return 0

    if args.cmd == "extend":
        from services.world_builder import extend_world

        zone = {
            "id": args.zone_id,
            "name": args.zone_name or args.zone_id,
            "description": args.zone_name or args.zone_id,
            "connections": [],
            "landmarks": [],
        }
        w = extend_world(args.world_id, zone=zone)
        print(json.dumps({"world_id": w.get("world_id"), "zones": [z.get("id") for z in w.get("zones") or []]}, indent=2))
        return 0

    if args.cmd == "usage":
        from services.world_builder.library import USAGE_PATH

        if not USAGE_PATH.exists():
            print(json.dumps([]))
            return 0
        hist = json.loads(USAGE_PATH.read_text(encoding="utf-8"))
        print(json.dumps(hist[-args.limit :], indent=2))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
