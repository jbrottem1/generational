#!/usr/bin/env python3
"""Audience Intelligence CLI — brief, review, search, lessons, analytics interfaces."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    p = argparse.ArgumentParser(description="Audience Intelligence System")
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("brief", help="Generate pre-production Creative Brief")
    b.add_argument("--topic", required=True)
    b.add_argument("--niche", default="")
    b.add_argument("--platform", default="youtube_shorts")
    b.add_argument("--length-sec", type=int, default=45)
    b.add_argument("--narrator", default="professor")
    b.add_argument("--production-id", default="")

    r = sub.add_parser("review", help="Post-production review + record one lesson")
    r.add_argument("--topic", default="")
    r.add_argument("--niche", default="")
    r.add_argument("--platform", default="youtube_shorts")
    r.add_argument("--production-id", default="")
    r.add_argument("--candidate-json", default="")
    r.add_argument("--report-json", default="")
    r.add_argument("--ce-json", default="")
    r.add_argument("--video-id", default="")

    s = sub.add_parser("search", help="Search creative memory lessons")
    s.add_argument("query", nargs="?", default="")
    s.add_argument("--category", default="")
    s.add_argument("--platform", default="")
    s.add_argument("--niche", default="")
    s.add_argument("--min-confidence", type=float, default=0.0)
    s.add_argument("--limit", type=int, default=12)

    sub.add_parser("lessons", help="List production lessons")
    sub.add_parser("seed", help="Seed bootstrap lessons")
    sub.add_parser("interfaces", help="List future analytics interfaces")

    a = sub.add_parser("analyze", help="Topic analysis report (existing enricher)")
    a.add_argument("--topic", required=True)
    a.add_argument("--category", default="general")

    args = p.parse_args()

    if args.cmd == "brief":
        from services.audience_intelligence.brief import build_creative_brief

        out = build_creative_brief(
            topic=args.topic,
            niche=args.niche,
            platform=args.platform,
            length_sec=args.length_sec,
            narrator=args.narrator,
            production_id=args.production_id,
        )
        print(json.dumps(out, indent=2))
        return 0

    if args.cmd == "review":
        from services.audience_intelligence.post_review import review_production_audience

        def _load(path: str) -> dict:
            if not path:
                return {}
            return json.loads(Path(path).read_text(encoding="utf-8"))

        out = review_production_audience(
            topic=args.topic,
            niche=args.niche,
            platform=args.platform,
            production_id=args.production_id,
            candidate=_load(args.candidate_json),
            production_report=_load(args.report_json),
            creative_excellence=_load(args.ce_json) or None,
            published_video_id=args.video_id,
        )
        print(json.dumps(out, indent=2))
        return 0

    if args.cmd == "search":
        from services.audience_intelligence.memory import search_lessons

        rows = search_lessons(
            args.query,
            category=args.category,
            platform=args.platform,
            niche=args.niche,
            min_confidence=args.min_confidence,
            limit=args.limit,
        )
        print(json.dumps(rows, indent=2))
        return 0

    if args.cmd == "lessons":
        from services.audience_intelligence.memory import load_knowledge

        kb = load_knowledge()
        print(json.dumps({"count": len(kb.get("lessons") or []), "lessons": kb.get("lessons") or []}, indent=2))
        return 0

    if args.cmd == "seed":
        from services.audience_intelligence.memory import seed_bootstrap_lessons

        print(json.dumps(seed_bootstrap_lessons(), indent=2))
        return 0

    if args.cmd == "interfaces":
        from services.audience_intelligence.analytics_interfaces import list_analytics_interfaces

        print(json.dumps(list_analytics_interfaces(), indent=2))
        return 0

    if args.cmd == "analyze":
        from services.audience_intelligence import analyze_topic

        print(json.dumps(analyze_topic(args.topic, category=args.category).to_dict(), indent=2))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
