#!/usr/bin/env python3
"""Run Production Validation Suite — real multi-domain content via existing ops."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.production_validation import run_validation_suite  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Production Validation Suite")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of domain productions")
    parser.add_argument("--domains", nargs="*", default=None, help="Subset of domains")
    args = parser.parse_args()

    print("=== Production Validation Suite (real content) ===")
    result = run_validation_suite(domains=args.domains, limit=args.limit)
    print(
        json.dumps(
            {
                "productions": result.get("productions"),
                "publish_ready_pct": result.get("publish_ready_pct"),
                "average_overall": (result.get("average_scores") or {}).get("overall_production_score"),
                "top_weaknesses": [
                    {"rank": w.get("rank"), "label": w.get("label"), "count": w.get("count")}
                    for w in (result.get("weakness_ranking") or [])[:5]
                ],
                "report": result.get("report_path"),
                "roadmap": result.get("roadmap_path"),
            },
            indent=2,
        )
    )
    # Success = suite ran and produced roadmap (content may still need work)
    return 0 if result.get("productions") else 1


if __name__ == "__main__":
    raise SystemExit(main())
