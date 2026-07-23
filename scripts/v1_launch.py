#!/usr/bin/env python3
"""V1 Launch Program CLI — COO operations (no new engines)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    p = argparse.ArgumentParser(description="Generational V1 Launch Program")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("health", help="Phase 1 — health checks + readiness report")
    sub.add_parser("catalog", help="Show 25-video pilot catalog")
    sub.add_parser("dashboard", help="Phase 3 — executive dashboard")
    sub.add_parser("recommend", help="Phase 4 — launch recommendation")

    pilot = sub.add_parser("pilot", help="Phase 2 — run pilot productions")
    pilot.add_argument("--limit", type=int, default=None)
    pilot.add_argument("--offset", type=int, default=0)
    pilot.add_argument("--categories", nargs="*", default=None)
    pilot.add_argument("--no-skip", action="store_true")

    full = sub.add_parser("run-program", help="Phases 1→2→3→4 in sequence")
    full.add_argument("--limit", type=int, default=25, help="Pilot batch size (default 25)")

    args = p.parse_args()

    if args.cmd == "health":
        from services.v1_launch import write_launch_readiness_report

        paths = write_launch_readiness_report()
        print(json.dumps({k: str(v) for k, v in paths.items()}, indent=2))
        return 0

    if args.cmd == "catalog":
        from services.v1_launch import build_pilot_catalog

        cat = build_pilot_catalog()
        print(json.dumps({"total": len(cat), "pilot": [{"launch_id": r["launch_id"], "category": r["launch_category"], "topic": r["topic"]} for r in cat]}, indent=2))
        return 0

    if args.cmd == "pilot":
        from services.v1_launch import run_pilot_batch, write_executive_artifacts

        out = run_pilot_batch(
            limit=args.limit,
            offset=args.offset,
            categories=args.categories,
            skip_completed=not args.no_skip,
        )
        write_executive_artifacts()
        print(json.dumps({"library_total": out.get("library_total"), "executed": out.get("executed_this_batch"), "results": out.get("results")}, indent=2, default=str))
        return 0

    if args.cmd == "dashboard":
        from services.v1_launch import write_executive_artifacts

        paths = write_executive_artifacts()
        print(json.dumps({k: str(v) for k, v in paths.items()}, indent=2))
        return 0

    if args.cmd == "recommend":
        from services.v1_launch import decide_launch_recommendation, write_executive_artifacts

        write_executive_artifacts()
        rec = decide_launch_recommendation()
        print(json.dumps(rec, indent=2, default=str))
        return 0 if rec.get("decision") != "NOT_READY" else 2

    if args.cmd == "run-program":
        from services.v1_launch import (
            run_pilot_batch,
            write_executive_artifacts,
            write_launch_readiness_report,
        )

        health_paths = write_launch_readiness_report()
        pilot = run_pilot_batch(limit=args.limit, skip_completed=True)
        dash_paths = write_executive_artifacts()
        from services.v1_launch import decide_launch_recommendation

        rec = decide_launch_recommendation()
        print(
            json.dumps(
                {
                    "phase1": {k: str(v) for k, v in health_paths.items()},
                    "phase2": {"executed": pilot.get("executed_this_batch"), "library_total": pilot.get("library_total")},
                    "phase3": {k: str(v) for k, v in dash_paths.items()},
                    "phase4": {"decision": rec.get("decision"), "rationale": rec.get("rationale")},
                },
                indent=2,
                default=str,
            )
        )
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
