"""Live + offline validation for Google News discovery integration."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.env import load_application_env
from providers.news.google_news_provider import get_google_news_provider
from providers.trend_sources.google_news import GoogleNewsProvider as TrendAdapter
from services.discovery.engine import run_discovery


def main() -> int:
    load_application_env()
    out_dir = ROOT / "data" / "productions" / "_validation" / "google_news"
    out_dir.mkdir(parents=True, exist_ok=True)

    gn = get_google_news_provider(refresh=True)
    validation = gn.validate()
    print("=== Google News Provider Validation ===")
    print(json.dumps(validation, indent=2))

    # Live pull — structured only (never print XML)
    items = gn.pull_latest(
        feeds=["top_stories", "science", "technology"],
        country="US",
        language="en",
        query="science education",
        limit=12,
        use_cache=True,
    )
    print(f"\nLive articles: {len(items)}")
    for it in items[:8]:
        print(
            f"- {it.title}\n"
            f"  publisher={it.publisher} category={it.category} "
            f"region={it.region} lang={it.language}\n"
            f"  published={it.publish_time or '(unknown)'}\n"
            f"  scores={it.scores.to_dict()}\n"
            f"  provider={it.provider}"
        )

    # Trend adapter
    adapter = TrendAdapter()
    trends = adapter.discover("science education", category="science", limit=3)
    print(f"\nTrend adapter trends: {len(trends)}")
    for t in trends:
        print(f"- [{t.source}] {t.topic} conf={t.confidence:.2f} fresh={t.freshness:.2f}")

    # Discovery engine pass (persist validation queue separately via persist=False)
    payload = run_discovery(
        "science education",
        category="science",
        country="US",
        language="en",
        limit_per_provider=2,
        top_n=15,
        persist=False,
    )
    gn_meta = payload.get("google_news") or {}
    print("\n=== Discovery Engine ===")
    print(
        f"discovered={payload.get('discovered')} ready={payload.get('ready')} "
        f"deferred={payload.get('deferred_count')}"
    )
    print(f"google_news.live={gn_meta.get('live')} articles={gn_meta.get('article_count')}")
    if gn_meta.get("sample"):
        print("Sample flowing into pipeline:")
        for row in gn_meta["sample"][:5]:
            print(f"  • {row.get('title')} ({row.get('publisher')})")

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "SUCCESS" if items and gn_meta.get("live") else "PARTIAL",
        "validation": validation,
        "live_count": len(items),
        "live_sample": [i.to_dict() for i in items[:10]],
        "trend_adapter_count": len(trends),
        "discovery": {
            "discovered": payload.get("discovered"),
            "ready": payload.get("ready"),
            "deferred": payload.get("deferred_count"),
            "google_news": {
                k: v
                for k, v in gn_meta.items()
                if k != "sample"
            },
            "google_news_sample": gn_meta.get("sample"),
            "top": payload.get("top"),
        },
        "last_pull": gn.last_pull_meta,
    }
    json_path = out_dir / "GOOGLE_NEWS_E2E.json"
    md_path = out_dir / "GOOGLE_NEWS_E2E_REPORT.md"
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    lines = [
        "# Google News — End-to-End Verification",
        "",
        f"Generated: {report['generated_at']}",
        f"**Status:** {report['status']}",
        "",
        "## Live pull (structured)",
        f"- Articles: {len(items)}",
        f"- Cache: {gn.last_pull_meta.get('cache')}",
        "",
    ]
    for it in items[:8]:
        lines.append(f"### {it.title}")
        lines.append(f"- Publisher: {it.publisher}")
        lines.append(f"- Category: {it.category} | Region: {it.region} | Lang: {it.language}")
        lines.append(f"- Published: {it.publish_time or '(unknown)'}")
        lines.append(f"- Scores: `{it.scores.to_dict()}`")
        lines.append(f"- Provider: {it.provider}")
        lines.append("")
    lines.extend(
        [
            "## Discovery Engine",
            f"- Discovered trends: {payload.get('discovered')}",
            f"- Ready: {payload.get('ready')}",
            f"- Google News live: {gn_meta.get('live')}",
            "",
            "Raw XML is never stored in this report — only DiscoveryItem dicts.",
            "",
            f"JSON: `{json_path}`",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nReport: {md_path}")
    print(f"JSON: {json_path}")

    ok = bool(items) and bool(trends)
    print("\n=== RESULT:", "SUCCESS" if ok else "FAILED", "===")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
