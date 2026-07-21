#!/usr/bin/env python3
"""CLI — Generational Character & World Studio."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _demo(topic: str = "Why Fire Hydrants Are Different Colors") -> dict:
    return {
        "topic": topic,
        "world_package": {"world_type": "Suburban Neighborhood"},
        "visual_package": {
            "scenes": [
                {
                    "scene_number": 1,
                    "purpose": "hook",
                    "length_sec": 3,
                    "narration": "These colors could determine whether firefighters save your house.",
                    "subject": "fire hydrants",
                },
                {
                    "scene_number": 2,
                    "purpose": "story_beat",
                    "length_sec": 3.5,
                    "narration": "Each color indicates a flow rating engineers read at a glance.",
                },
                {
                    "scene_number": 3,
                    "purpose": "payoff",
                    "length_sec": 3,
                    "narration": "Flow rate matters when seconds decide if a house is saved.",
                },
            ]
        },
    }


def cmd_selftest(_: argparse.Namespace) -> int:
    from services.character_world_studio import list_hosts, list_locations, studio_place_candidate

    out = studio_place_candidate(_demo(), write=True)
    pkg = out["CHARACTER_WORLD_STUDIO_PACKAGE"]
    print(
        json.dumps(
            {
                "ok": True,
                "hosts": len(list_hosts()),
                "locations": len(list_locations()),
                "primary_host": (out.get("primary_host") or {}).get("name"),
                "location": (out.get("studio_location") or {}).get("name"),
                "gate": (pkg.get("quality_gate") or {}).get("decision"),
                "feels_like_series": (pkg.get("summary") or {}).get("feels_like_series"),
                "path": pkg.get("path"),
                "plates": list((pkg.get("character_plates") or {}).keys()),
                "scene0_character": out["visual_package"]["scenes"][0].get("studio_character_name"),
            },
            indent=2,
        )
    )
    return 0 if (pkg.get("quality_gate") or {}).get("approved") else 2


def cmd_cast(_: argparse.Namespace) -> int:
    from services.character_world_studio import list_hosts

    for h in list_hosts():
        print(f"{h['id']}: {h['name']} — {h['role']}")
    return 0


def cmd_locations(_: argparse.Namespace) -> int:
    from services.character_world_studio import list_locations

    for loc in list_locations():
        print(f"{loc['id']}: {loc['name']}")
    return 0


def cmd_place(args: argparse.Namespace) -> int:
    from services.character_world_studio import studio_place_candidate

    cand = _demo(args.topic or "Why Fire Hydrants Are Different Colors")
    if args.candidate and Path(args.candidate).is_file():
        cand = json.loads(Path(args.candidate).read_text(encoding="utf-8"))
    if args.topic:
        cand["topic"] = args.topic
    out = studio_place_candidate(
        cand,
        topic=str(cand.get("topic") or ""),
        write=True,
        out_dir=Path(args.out_dir) if args.out_dir else None,
    )
    pkg = out["CHARACTER_WORLD_STUDIO_PACKAGE"]
    print(json.dumps(pkg.get("summary"), indent=2))
    print(f"Package: {pkg.get('path')}")
    return 0 if (pkg.get("quality_gate") or {}).get("approved") else 2


def main() -> int:
    p = argparse.ArgumentParser(description="Character & World Studio")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("selftest")
    s.set_defaults(func=cmd_selftest)
    c = sub.add_parser("cast")
    c.set_defaults(func=cmd_cast)
    loc = sub.add_parser("locations")
    loc.set_defaults(func=cmd_locations)
    place = sub.add_parser("place")
    place.add_argument("--topic", default="")
    place.add_argument("--candidate", default="")
    place.add_argument("--out-dir", default="")
    place.set_defaults(func=cmd_place)
    args = p.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
