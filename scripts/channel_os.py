#!/usr/bin/env python3
"""Multi-Channel Media Operating System CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Generational Multi-Channel Media OS")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("templates", help="List channel profile templates")
    sub.add_parser("list", help="List installed channel profiles")
    sub.add_parser("dashboard", help="Write channel dashboard")
    sub.add_parser("install-samples", help="Install 3 sample channel profiles")

    route = sub.add_parser("route", help="Route an opportunity topic to a channel")
    route.add_argument("--topic", required=True)
    route.add_argument("--category", default="")
    route.add_argument("--platform", default="youtube_shorts")

    prod = sub.add_parser("produce", help="Produce one video for a channel via existing ops")
    prod.add_argument("channel_id")
    prod.add_argument("--topic", required=True)
    prod.add_argument("--category", default="")
    prod.add_argument("--length", type=int, default=45)
    prod.add_argument("--dry-run", action="store_true")

    val = sub.add_parser("validate", help="Install samples + produce one topic per sample channel")
    val.add_argument("--execute", action="store_true", help="Actually run studio ops (slow)")
    val.add_argument("--length", type=int, default=45)

    args = parser.parse_args()

    if args.cmd == "templates":
        from services.channel_os import CHANNEL_TEMPLATES, list_template_ids

        print(json.dumps({"templates": list_template_ids(), "count": len(CHANNEL_TEMPLATES)}, indent=2))
        return 0

    if args.cmd == "list":
        from services.channel_os import list_profiles

        rows = list_profiles(status=None)
        print(
            json.dumps(
                [
                    {
                        "channel_id": r.get("channel_id"),
                        "brand_name": r.get("brand_name"),
                        "narrator_profile": r.get("narrator_profile"),
                        "categories": r.get("topic_categories"),
                        "status": r.get("status"),
                        "metrics": r.get("metrics"),
                    }
                    for r in rows
                ],
                indent=2,
            )
        )
        return 0

    if args.cmd == "dashboard":
        from services.channel_os import write_channel_dashboard

        paths = write_channel_dashboard()
        print(json.dumps({k: str(v) for k, v in paths.items()}, indent=2))
        return 0

    if args.cmd == "install-samples":
        from services.channel_os import install_sample_profiles, write_channel_dashboard

        rows = install_sample_profiles()
        write_channel_dashboard()
        print(json.dumps([{"channel_id": r["channel_id"], "brand_name": r["brand_name"]} for r in rows], indent=2))
        return 0

    if args.cmd == "route":
        from services.channel_os import route_opportunity

        out = route_opportunity(
            {"topic": args.topic, "category": args.category, "platform": args.platform}
        )
        print(json.dumps({k: v for k, v in out.items() if k != "profile"}, indent=2, default=str))
        return 0 if out.get("ok") else 1

    if args.cmd == "produce":
        from services.channel_os import produce_for_channel, write_channel_dashboard

        out = produce_for_channel(
            args.channel_id,
            args.topic,
            category=args.category,
            length_sec=args.length,
            execute=not args.dry_run,
        )
        if not args.dry_run:
            write_channel_dashboard()
        print(json.dumps(out, indent=2, default=str))
        return 0 if out.get("ok") else 1

    if args.cmd == "validate":
        from services.channel_os import install_sample_profiles, produce_for_channel, write_channel_dashboard

        samples = install_sample_profiles()
        topics = {
            "science_daily": ("Why Leaves Change Color in Autumn", "biology"),
            "ai_explained": ("How Neural Networks Learn", "artificial_intelligence"),
            "space_explorer": ("Why Saturn Has Rings", "astronomy"),
        }
        results = []
        for p in samples:
            cid = p["channel_id"]
            topic, cat = topics[cid]
            out = produce_for_channel(
                cid,
                topic,
                category=cat,
                length_sec=args.length,
                execute=args.execute,
            )
            results.append(
                {
                    "channel_id": cid,
                    "brand_name": p["brand_name"],
                    "topic": topic,
                    "executed": out.get("executed"),
                    "production_id": out.get("production_id"),
                    "success": out.get("success"),
                    "verification": out.get("verification") or out.get("ops_kwargs_preview"),
                    "project_root": (out.get("packaged") or {}).get("project_root"),
                }
            )
        write_channel_dashboard()
        print(json.dumps({"results": results}, indent=2, default=str))
        ok = all(
            (r.get("verification") or {}).get("all_passed", True)
            if args.execute
            else r.get("executed") is False
            for r in results
        )
        return 0 if ok or not args.execute else 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
