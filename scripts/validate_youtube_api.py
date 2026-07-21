#!/usr/bin/env python3
"""Validate YouTube Data API v3 integration (Agent 0 startup check).

Usage:
  ./venv/bin/python scripts/validate_youtube_api.py

Never prints the API key. Paste your key into .env as:
  YOUTUBE_API_KEY=your_key_here
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.env import load_application_env, startup_credential_report

load_application_env()

from services.providers.youtube_provider import get_youtube_provider, validate_youtube_startup


def main() -> int:
    report = validate_youtube_startup()
    cred = startup_credential_report(keys=("YOUTUBE_API_KEY",))
    print("=== YouTube Data API v3 — Startup Validation ===")
    for line in report.get("lines") or []:
        print(line)
    print()
    print(
        json.dumps(
            {
                "ok": report.get("ok"),
                "detected": report.get("detected"),
                "authenticated": report.get("authenticated"),
                "quota_accessible": report.get("quota_accessible"),
                "trending_search_ok": report.get("trending_search_ok"),
                "masked_key": report.get("masked_key"),
                "error": report.get("error"),
                "quota": report.get("quota"),
                "env_path": cred.get("env_path"),
            },
            indent=2,
        )
    )
    if not report.get("ok"):
        print(
            "\nFix: set YOUTUBE_API_KEY in the project .env (never commit it), then re-run.",
            file=sys.stderr,
        )
        return 1

    # Smoke methods without dumping payloads that could leak keys
    yt = get_youtube_provider()
    smoke = {
        "search_videos": bool(yt.search_videos("science explained", max_results=1).get("ok")),
        "search_channels": bool(yt.search_channels("NASA", max_results=1).get("ok")),
        "quota_after": yt.quota.snapshot(),
    }
    print("\nMethod smoke:", json.dumps(smoke, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
