#!/usr/bin/env python3
"""Trend & Opportunity Intelligence CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    p = argparse.ArgumentParser(description="Trend & Opportunity Intelligence")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="Discover + rank + briefs + reports")
    r.add_argument("--subject", default="science education")
    r.add_argument("--category", default="science")
    r.add_argument("--top", type=int, default=25)
    r.add_argument("--briefs", type=int, default=10)
    r.add_argument("--high-confidence", type=int, default=5)
    r.add_argument("--no-discovery", action="store_true")

    h = sub.add_parser("handoff", help="Handoff a PRODUCTION_BRIEF JSON to pipeline")
    h.add_argument("--brief-json", required=True)
    h.add_argument("--execute-ops", action="store_true")
    h.add_argument("--enqueue", action="store_true", default=True)
    h.add_argument("--no-enqueue", action="store_true")
    h.add_argument("--run-immediately", action="store_true")

    sub.add_parser("providers", help="List modular data-source interfaces")
    sub.add_parser("library", help="List opportunity library rows")

    s = sub.add_parser("selftest", help="Science category self-test + #1 handoff")
    s.add_argument("--execute-ops", action="store_true", help="Actually run studio ops for #1 (slow)")
    s.add_argument("--run-immediately", action="store_true")

    args = p.parse_args()

    if args.cmd == "providers":
        from services.trend_opportunity import list_provider_interfaces

        print(json.dumps(list_provider_interfaces(), indent=2))
        return 0

    if args.cmd == "library":
        from services.trend_opportunity import list_opportunities

        print(json.dumps(list_opportunities(limit=40), indent=2, default=str))
        return 0

    if args.cmd == "run":
        from services.trend_opportunity import run_trend_opportunity

        out = run_trend_opportunity(
            args.subject,
            category=args.category,
            top_n=args.top,
            brief_count=args.briefs,
            high_confidence_count=args.high_confidence,
            use_discovery_engine=not args.no_discovery,
        )
        summary = {
            "ok": out.get("ok"),
            "ranked": len(out.get("top_opportunities") or []),
            "briefs": len(out.get("production_briefs") or []),
            "highest_confidence": len(out.get("highest_confidence") or []),
            "number_one": (out.get("number_one") or {}).get("topic"),
            "score": (out.get("number_one") or {}).get("overall_opportunity_score"),
            "paths": out.get("paths"),
            "db": out.get("opportunity_library_db"),
        }
        print(json.dumps(summary, indent=2))
        return 0

    if args.cmd == "handoff":
        from services.trend_opportunity import handoff_pipeline

        brief = json.loads(Path(args.brief_json).read_text(encoding="utf-8"))
        if "production_brief" in brief and "topic" not in brief:
            brief = brief["production_brief"]
        out = handoff_pipeline(
            brief,
            execute_ops=args.execute_ops,
            enqueue=not args.no_enqueue,
            run_immediately=args.run_immediately,
        )
        print(json.dumps(out, indent=2, default=str))
        return 0 if out.get("ok") else 1

    if args.cmd == "selftest":
        from services.trend_opportunity import handoff_pipeline, run_trend_opportunity

        result = run_trend_opportunity(
            "science education",
            category="science",
            top_n=25,
            brief_count=10,
            high_confidence_count=5,
        )
        number_one = result.get("number_one") or {}
        brief = number_one.get("production_brief") or {}
        handoff = handoff_pipeline(
            brief,
            execute_ops=args.execute_ops,
            enqueue=True,
            run_immediately=args.run_immediately,
        )
        # Persist self-test report
        report_dir = Path(ROOT) / "data" / "trend_opportunity" / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        selftest = {
            "category": "science",
            "top_25_count": len(result.get("top_opportunities") or []),
            "top_10_briefs": len(result.get("production_briefs") or []),
            "top_5_high_confidence": [
                {"topic": c.get("topic"), "confidence": c.get("confidence"), "score": c.get("overall_opportunity_score")}
                for c in (result.get("highest_confidence") or [])
            ],
            "number_one": {
                "topic": number_one.get("topic"),
                "score": number_one.get("overall_opportunity_score"),
                "working_title": (number_one.get("strategy") or {}).get("working_title"),
                "manual_editing_required": brief.get("manual_editing_required"),
            },
            "handoff": {
                "ok": handoff.get("ok"),
                "manual_editing_required": handoff.get("manual_editing_required"),
                "research_ok": (handoff.get("research") or {}).get("ok"),
                "studio_ok": (handoff.get("studio_ops") or {}).get("ok"),
                "verification": (handoff.get("research") or {}).get("verification"),
                "enqueue": handoff.get("enqueue"),
                "executed_ops": (handoff.get("studio_ops") or {}).get("executed"),
            },
            "paths": result.get("paths"),
            "db": result.get("opportunity_library_db"),
        }
        path = report_dir / "SCIENCE_SELFTEST.json"
        path.write_text(json.dumps(selftest, indent=2, default=str) + "\n", encoding="utf-8")
        print(json.dumps(selftest, indent=2, default=str))
        return 0 if selftest["handoff"]["ok"] and selftest["top_25_count"] >= 25 else 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
