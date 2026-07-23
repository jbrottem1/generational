#!/usr/bin/env python3
"""CLI — permanent Studio Asset #0001: The Doctor."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    p = argparse.ArgumentParser(description="Generational Studio Asset #0001 — The Doctor")
    p.add_argument("command", choices=["ensure", "status", "cast-check", "selftest"])
    p.add_argument("--force", action="store_true", help="Regenerate procedural plates (use carefully)")
    args = p.parse_args()

    from services.studio_assets import ensure_the_doctor_asset, get_asset, the_doctor_host_profile
    from services.character_world_studio import studio_place_candidate

    if args.command == "ensure":
        manifest = ensure_the_doctor_asset(force=args.force)
        print(json.dumps(manifest, indent=2))
        return 0

    if args.command == "status":
        ensure_the_doctor_asset(force=False)
        row = get_asset("CHAR-0001")
        print(json.dumps(row, indent=2))
        return 0

    if args.command == "cast-check":
        host = the_doctor_host_profile()
        print(json.dumps({"id": host["id"], "name": host["name"], "domains": host["domains"]}, indent=2))
        return 0

    # selftest — science topic should cast The Doctor
    ensure_the_doctor_asset(force=False)
    cand = {
        "topic": "How Vaccines Train Your Immune System",
        "visual_package": {
            "scenes": [
                {
                    "scene_number": 1,
                    "narration": "Inside your body, immune cells learn to recognize invaders.",
                    "purpose": "hook",
                    "length_sec": 3.0,
                },
                {
                    "scene_number": 2,
                    "narration": "Medical science uses vaccines to teach that memory safely.",
                    "purpose": "story_beat",
                    "length_sec": 3.5,
                },
            ]
        },
    }
    out = studio_place_candidate(cand, write=False)
    primary = out.get("primary_host") or {}
    loc = out.get("studio_location") or {}
    report = {
        "ok": primary.get("id") == "CHAR-0001",
        "primary_host": primary.get("name"),
        "primary_id": primary.get("id"),
        "location": loc.get("name"),
        "location_id": loc.get("id"),
        "permanent_ip": bool(primary.get("permanent_ip")),
        "asset": str(ROOT / "data/studio_assets/CHAR-0001-THE-DOCTOR"),
    }
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
