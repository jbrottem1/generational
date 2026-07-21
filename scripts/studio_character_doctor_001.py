#!/usr/bin/env python3
"""CLI — permanent Generational Studio Character DOCTOR_001."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    p = argparse.ArgumentParser(description="Studio Character DOCTOR_001 — The Doctor")
    p.add_argument("command", choices=["ensure", "status", "selftest"])
    p.add_argument("--force", action="store_true", help="Regenerate plates (intentional upgrades only)")
    args = p.parse_args()

    from services.studio_assets import ensure_doctor_001_asset, get_asset
    from services.character_world_studio import studio_place_candidate

    if args.command == "ensure":
        print(json.dumps(ensure_doctor_001_asset(force=args.force), indent=2))
        return 0

    if args.command == "status":
        ensure_doctor_001_asset(force=False)
        print(json.dumps(get_asset("DOCTOR_001"), indent=2))
        return 0

    manifest = ensure_doctor_001_asset(force=False)
    asset = ROOT / "data/studio_assets/DOCTOR_001"
    expr_n = len(list((asset / "EXPRESSIONS").glob("*.png")))
    out = studio_place_candidate(
        {
            "topic": "How Your Immune System Learns",
            "visual_package": {
                "scenes": [
                    {
                        "scene_number": 1,
                        "narration": "Medical science teaches the body carefully.",
                        "length_sec": 3.0,
                    }
                ]
            },
        },
        write=False,
    )
    primary = out.get("primary_host") or {}
    report = {
        "ok": primary.get("id") == "DOCTOR_001" and expr_n >= 50 and manifest.get("status") == "permanent",
        "character_id": "DOCTOR_001",
        "primary_cast_id": primary.get("id"),
        "expressions": expr_n,
        "orthographic": len(list((asset / "ORTHOGRAPHIC").glob("*.png"))),
        "animations": (manifest.get("counts") or {}).get("animations"),
        "root": str(asset),
    }
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
