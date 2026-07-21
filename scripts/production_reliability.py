#!/usr/bin/env python3
"""CLI — Production Reliability Initiative validation + reports."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="V1 Production Reliability Initiative")
    parser.add_argument("--limit", type=int, default=10, help="Number of validation productions")
    parser.add_argument("--reports-only", action="store_true", help="Rewrite reports from last summary")
    args = parser.parse_args()

    from services.production_reliability.reports import write_all_reports
    from services.production_reliability.runner import run_reliability_batch

    if args.reports_only:
        paths = write_all_reports()
        print(json.dumps({"reports": paths}, indent=2))
        return 0

    summary = run_reliability_batch(limit=args.limit)
    paths = write_all_reports(summary)
    print(
        json.dumps(
            {
                "mp4_success_rate": summary.get("mp4_success_rate"),
                "mission_mp4_gate_passed": summary.get("mission_mp4_gate_passed"),
                "publication_ready_rate": summary.get("publication_ready_rate"),
                "count": summary.get("count"),
                "reports": paths,
                "library_root": summary.get("library_root"),
            },
            indent=2,
        )
    )
    return 0 if summary.get("mission_mp4_gate_passed") else 2


if __name__ == "__main__":
    raise SystemExit(main())
