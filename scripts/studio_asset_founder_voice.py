#!/usr/bin/env python3
"""CLI — permanent Studio Voice Asset #0001: Founder Voice."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    p = argparse.ArgumentParser(description="Generational Studio Asset VOICE-0001 — Founder Voice")
    p.add_argument("command", choices=["ensure", "status", "qa", "selftest", "resolve"])
    p.add_argument("--narrator", default="", help="Narrator key to resolve (default=founder)")
    args = p.parse_args()

    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env", override=True)

    from services.studio_assets.founder_voice import (
        ensure_founder_voice_asset,
        get_founder_voice_id,
        run_founder_voice_qa,
    )
    from services.elevenlabs.voices import resolve_narrator_profile

    if args.command == "ensure":
        print(json.dumps(ensure_founder_voice_asset(), indent=2))
        return 0

    if args.command == "status":
        ensure_founder_voice_asset(sync_env=False)
        vid = get_founder_voice_id()
        print(
            json.dumps(
                {
                    "asset_id": "VOICE-0001",
                    "name": "Founder Voice",
                    "default": True,
                    "provider": "elevenlabs",
                    "voice_id_suffix": f"…{vid[-6:]}",
                    "path": "data/studio_assets/VOICE-0001-FOUNDER-VOICE/",
                },
                indent=2,
            )
        )
        return 0

    if args.command == "qa":
        ensure_founder_voice_asset()
        report = run_founder_voice_qa(live_probe=True, write_report=True)
        print(json.dumps(report, indent=2))
        return 0 if report.get("production_ready") else 1

    if args.command == "resolve":
        ensure_founder_voice_asset(sync_env=False)
        r = resolve_narrator_profile(args.narrator or "founder")
        print(
            json.dumps(
                {
                    "profile_key": r.get("profile_key"),
                    "label": r.get("label"),
                    "permanent_default": r.get("permanent_default"),
                    "studio_asset_id": r.get("studio_asset_id"),
                    "voice_id_suffix": f"…{str(r.get('voice_id') or '')[-6:]}",
                    "provider": r.get("provider"),
                },
                indent=2,
            )
        )
        return 0

    # selftest
    ensure_founder_voice_asset()
    r = resolve_narrator_profile("")
    founder = get_founder_voice_id()
    ok = str(r.get("voice_id") or "") == founder and bool(r.get("permanent_default"))
    qa = run_founder_voice_qa(live_probe=True, write_report=True)
    out = {
        "ok": ok and bool(qa.get("production_ready")),
        "unspecified_narrator_uses_founder": ok,
        "qa_production_ready": qa.get("production_ready"),
        "voice_id_suffix": f"…{founder[-6:]}",
    }
    print(json.dumps(out, indent=2))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
