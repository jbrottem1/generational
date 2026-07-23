#!/usr/bin/env python3
"""Run the Trend Intelligence & Discovery Engine locally.

Usage:
  ./venv/bin/python scripts/run_discovery_engine.py
  ./venv/bin/python scripts/run_discovery_engine.py --subject "turtle evolution" --category science
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.env import load_application_env

load_application_env()

from services.discovery.engine import run_discovery
from services.discovery.queue import QUEUE_PATH, top_queue


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subject", default="science education")
    parser.add_argument("--category", default="science")
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--no-persist", action="store_true")
    args = parser.parse_args()

    result = run_discovery(
        subject=args.subject,
        category=args.category,
        top_n=max(args.top, 15),
        persist=not args.no_persist,
    )
    summary = {
        "ok": result.get("ok"),
        "subject": result.get("subject"),
        "discovered": result.get("discovered"),
        "ready": result.get("ready"),
        "deferred_count": result.get("deferred_count"),
        "series_count": len(result.get("series") or []),
        "top": result.get("top"),
        "series": result.get("series") or [],
        "queue_preview": top_queue(args.top) if not args.no_persist else (result.get("queue") or [])[: args.top],
        "queue_path": str(QUEUE_PATH),
    }
    print(json.dumps(summary, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
