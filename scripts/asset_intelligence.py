#!/usr/bin/env python3
"""Universal Asset Intelligence CLI — search, package, validate (no render engine)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.env import load_application_env  # noqa: E402

load_application_env(create_if_missing=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="Universal Asset Intelligence")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("seed", help="Index reality / cache / asset_generation into library")

    p = sub.add_parser("search", help="Semantic search over the asset library")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=8)
    p.add_argument("--collection", default="")
    p.add_argument("--kind", default="")

    p = sub.add_parser("package", help="Build Asset Intelligence package for a topic")
    p.add_argument("--topic", required=True)
    p.add_argument("--keywords", default="", help="Comma-separated keywords")
    p.add_argument("--collection", default="")
    p.add_argument("--platform", default="youtube_shorts")
    p.add_argument("--audience", default="general_public")
    p.add_argument("--channel", default="")
    p.add_argument("--needed", type=int, default=6)
    p.add_argument("--out", default="")

    p = sub.add_parser("validate", help="Validate an existing package JSON")
    p.add_argument("path")

    p = sub.add_parser("collections", help="List niche collections and counts")
    p.add_argument("--name", default="", help="Show assets in one collection")

    p = sub.add_parser("score", help="Score one asset_id")
    p.add_argument("asset_id")
    p.add_argument("--query", default="")

    args = parser.parse_args()

    if args.cmd == "seed":
        from services.asset_intelligence import seed_from_existing_sources

        print(json.dumps(seed_from_existing_sources(), indent=2))
        return 0

    if args.cmd == "search":
        from services.asset_intelligence import semantic_search

        hits = semantic_search(
            args.query, limit=args.limit, collection=args.collection, kind=args.kind
        )
        slim = [
            {
                "asset_id": h.get("asset_id"),
                "topic": h.get("topic"),
                "kind": h.get("kind"),
                "collection": h.get("collection"),
                "rank_score": h.get("rank_score"),
                "scores": h.get("scores"),
                "uri": h.get("uri"),
            }
            for h in hits
        ]
        print(json.dumps(slim, indent=2))
        return 0

    if args.cmd == "package":
        from services.asset_intelligence import build_asset_intelligence_package

        keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
        pkg = build_asset_intelligence_package(
            topic=args.topic,
            keywords=keywords,
            collection=args.collection,
            platform=args.platform,
            audience=args.audience,
            channel=args.channel,
            needed=args.needed,
        )
        if args.out:
            out = Path(args.out)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(pkg, indent=2) + "\n", encoding="utf-8")
            pkg["path"] = str(out)
        summary = {
            "path": pkg.get("path"),
            "topic": pkg.get("topic"),
            "selected_count": len(pkg.get("selected_media") or []),
            "backup_count": len(pkg.get("backup_choices") or []),
            "visual_diversity_score": pkg.get("visual_diversity_score"),
            "validation": pkg.get("validation"),
            "selected_ids": [a.get("asset_id") for a in pkg.get("selected_media") or []],
        }
        print(json.dumps(summary, indent=2))
        return 0 if (pkg.get("validation") or {}).get("ok") else 1

    if args.cmd == "validate":
        from services.asset_intelligence import validate_asset_intelligence_package

        data = json.loads(Path(args.path).read_text(encoding="utf-8"))
        result = validate_asset_intelligence_package(data)
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok") else 1

    if args.cmd == "collections":
        from services.asset_intelligence import COLLECTIONS, collection_assets, seed_from_existing_sources

        seed_from_existing_sources(limit_per_source=40)
        if args.name:
            rows = collection_assets(args.name)
            print(json.dumps([{"asset_id": r.get("asset_id"), "topic": r.get("topic"), "kind": r.get("kind")} for r in rows], indent=2))
            return 0
        counts = {c: len(collection_assets(c)) for c in COLLECTIONS}
        print(json.dumps(counts, indent=2))
        return 0

    if args.cmd == "score":
        from services.asset_intelligence import get_asset, score_asset_quality

        asset = get_asset(args.asset_id)
        if not asset:
            print(json.dumps({"ok": False, "error": "asset_not_found"}))
            return 1
        print(json.dumps(score_asset_quality(asset, query=args.query), indent=2))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
