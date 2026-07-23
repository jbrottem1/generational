#!/usr/bin/env python3
"""V1 Validation Program CLI — real pipeline validation at scale."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Generational V1 Validation Program")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("catalog", help="Show 100-video catalog summary")
    sub.add_parser("dashboard", help="Write executive validation dashboard")
    sub.add_parser("bottlenecks", help="Print bottleneck analysis")

    lib = sub.add_parser("library", help="List/search Validation Library")
    lib.add_argument("--category", default="")
    lib.add_argument("--query", default="")
    lib.add_argument("--limit", type=int, default=20)

    run = sub.add_parser("run", help="Run validation productions via existing ops")
    run.add_argument("--limit", type=int, default=1)
    run.add_argument("--offset", type=int, default=0)
    run.add_argument("--categories", nargs="*", default=None)
    run.add_argument("--no-skip", action="store_true")
    run.add_argument("--ingest", default="", help="Also ingest existing ops production_id")

    ing = sub.add_parser("ingest", help="Ingest existing ops production into library")
    ing.add_argument("production_id")
    ing.add_argument("--category", default="biology")
    ing.add_argument("--validation-id", default="")

    args = parser.parse_args()

    if args.cmd == "catalog":
        from services.validation_program import CATEGORIES, build_validation_catalog

        cat = build_validation_catalog()
        by: dict[str, int] = {}
        for row in cat:
            by[row["category"]] = by.get(row["category"], 0) + 1
        print(json.dumps({"total": len(cat), "categories": list(CATEGORIES), "per_category": by, "sample": cat[:3]}, indent=2))
        return 0

    if args.cmd == "dashboard":
        from services.validation_program import write_executive_dashboard

        paths = write_executive_dashboard()
        print(json.dumps({k: str(v) for k, v in paths.items()}, indent=2))
        return 0

    if args.cmd == "library":
        from services.validation_program import list_validations

        rows = list_validations(category=args.category, query=args.query, limit=args.limit)
        print(json.dumps(rows, indent=2, default=str))
        return 0

    if args.cmd == "bottlenecks":
        from services.validation_program.bottlenecks import build_recommendations, detect_bottlenecks

        b = detect_bottlenecks()
        print(json.dumps({"bottlenecks": b, "recommendations": build_recommendations(b)}, indent=2, default=str))
        return 0

    if args.cmd == "ingest":
        from services.validation_program import ingest_existing_production, write_executive_dashboard

        out = ingest_existing_production(
            args.production_id,
            validation_id=args.validation_id or "",
            category=args.category,
        )
        write_executive_dashboard()
        print(json.dumps(out, indent=2, default=str))
        return 0

    if args.cmd == "run":
        from services.validation_program import run_validation_program

        out = run_validation_program(
            limit=args.limit,
            offset=args.offset,
            categories=args.categories,
            skip_completed=not args.no_skip,
            dry_ingest_ops_id=args.ingest or None,
        )
        print(
            json.dumps(
                {
                    "library_total": out.get("library_total"),
                    "executed_this_batch": out.get("executed_this_batch"),
                    "results": out.get("results"),
                    "highest_priority": (out.get("recommendations") or [None])[0],
                    "dashboard": out.get("dashboard"),
                    "library_root": out.get("library_root"),
                },
                indent=2,
                default=str,
            )
        )
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
