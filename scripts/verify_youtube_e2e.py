#!/usr/bin/env python3
"""End-to-end YouTube API verification — live only, no demos.

Usage (after pasting key into .env):
  ./venv/bin/python scripts/verify_youtube_e2e.py

Stops on first hard failure. Never prints the API key.
"""

from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.env import load_application_env

load_application_env()

QUERY = "How cameras are made"
REPORT_PATH = ROOT / "data" / "productions" / "_validation" / "youtube_e2e" / "YOUTUBE_E2E_REPORT.json"
MD_PATH = ROOT / "data" / "productions" / "_validation" / "youtube_e2e" / "YOUTUBE_E2E_REPORT.md"


def _fail(step: str, message: str, report: dict) -> int:
    report["ok"] = False
    report["failed_at"] = step
    report["error"] = message
    _write_report(report)
    print(f"\n✗ STOPPED at [{step}]: {message}", file=sys.stderr)
    return 1


def _write_report(report: dict) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    lines = [
        "# YouTube API — End-to-End Verification Report",
        "",
        f"Generated: {report.get('completed_at')}",
        f"**Status:** {'SUCCESS' if report.get('ok') else 'FAILED'}",
        "",
        "## Checklist",
        "",
    ]
    for item in report.get("checklist") or []:
        mark = "✓" if item.get("ok") else "✗"
        lines.append(f"- {mark} {item.get('label')}")
        if item.get("detail"):
            lines.append(f"  - {item['detail']}")
    if report.get("error"):
        lines.extend(["", "## Error", "", report["error"]])
    if report.get("results"):
        lines.extend(["", "## Sample results", ""])
        for row in report["results"][:5]:
            lines.append(f"- **{row.get('title')}**")
            lines.append(f"  - Channel: {row.get('channel')}")
            lines.append(f"  - Views: {row.get('view_count')}")
            lines.append(f"  - Published: {row.get('publish_date')}")
            lines.append(f"  - Video ID: {row.get('video_id')}")
            lines.append(f"  - Thumbnail: {row.get('thumbnail_url')}")
    if report.get("discovery"):
        lines.extend(["", "## Discovery / SEO", "", "```json", json.dumps(report["discovery"], indent=2)[:4000], "```", ""])
    lines.extend(
        [
            "",
            "## Security",
            "",
            f"- Hardcoded credentials detected: {report.get('hardcoded_credentials_detected')}",
            f"- Secret leak in logs/report: {report.get('secret_leak_detected')}",
            "",
        ]
    )
    MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def _scan_for_hardcoded_keys() -> list[str]:
    hits: list[str] = []
    patterns = [
        re.compile(r"AIza[0-9A-Za-z\-_]{20,}"),
        re.compile(r"YOUTUBE_API_KEY\s*=\s*['\"][^'\"]+['\"]"),
    ]
    roots = [
        ROOT / "services" / "providers",
        ROOT / "providers" / "trend_sources",
        ROOT / "scripts" / "validate_youtube_api.py",
        ROOT / "scripts" / "verify_youtube_e2e.py",
    ]
    for root in roots:
        paths = [root] if root.is_file() else list(root.rglob("*.py"))
        for path in paths:
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for pat in patterns:
                if pat.search(text):
                    # Allow empty assignment in comments/docs only if not a real key
                    if "AIza" in text or re.search(r"YOUTUBE_API_KEY\s*=\s*['\"][^'\"]{8,}['\"]", text):
                        hits.append(str(path.relative_to(ROOT)))
                        break
    return sorted(set(hits))


def main() -> int:
    report: dict = {
        "ok": False,
        "query": QUERY,
        "checklist": [],
        "results": [],
        "discovery": {},
        "latency_ms": None,
        "quota": None,
        "hardcoded_credentials_detected": False,
        "secret_leak_detected": False,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }

    from services.provider_runtime.config import get_credential, has_credential
    from services.providers.youtube_provider import get_youtube_provider, mask_secret

    # 1. Env load
    if not has_credential("YOUTUBE_API_KEY"):
        return _fail(
            "env_load",
            "YOUTUBE_API_KEY is empty or missing in .env. "
            "Paste your real key into the project-root .env as YOUTUBE_API_KEY=... then re-run. "
            "Do not commit .env.",
            report,
        )
    key = get_credential("YOUTUBE_API_KEY") or ""
    report["checklist"].append(
        {
            "ok": True,
            "label": "Authentication / env load",
            "detail": f"Key loaded from environment (masked={mask_secret(key)})",
        }
    )

    # 7 / 10 security scan before live calls
    hardcoded = _scan_for_hardcoded_keys()
    report["hardcoded_credentials_detected"] = bool(hardcoded)
    if hardcoded:
        return _fail("security_scan", f"Hardcoded credentials found in: {hardcoded}", report)
    report["checklist"].append({"ok": True, "label": "No hardcoded credentials detected", "detail": ""})

    yt = get_youtube_provider(refresh=True)
    validation = yt.validate()
    if not validation.get("ok"):
        return _fail(
            "auth_validate",
            validation.get("error") or "YouTube authentication / trending probe failed",
            report,
        )
    report["checklist"].append({"ok": True, "label": "Authentication successful", "detail": "Trending probe OK"})
    report["checklist"].append(
        {
            "ok": True,
            "label": "API quota accessible",
            "detail": json.dumps(validation.get("quota") or {}),
        }
    )

    # 2–6 Live search
    t0 = time.perf_counter()
    search = yt.search_videos(QUERY, max_results=5, order="relevance", region_code="US")
    search_ms = (time.perf_counter() - t0) * 1000
    if not search.get("ok"):
        return _fail("live_search", search.get("error") or "search_videos failed", report)

    ids = []
    for item in search.get("items") or []:
        vid = (item.get("id") or {}).get("videoId")
        if vid:
            ids.append(vid)
    if not ids:
        return _fail("live_search", "Search returned zero video IDs", report)

    t1 = time.perf_counter()
    stats = yt.video_statistics(ids)
    stats_ms = (time.perf_counter() - t1) * 1000
    if not stats.get("ok"):
        return _fail("video_statistics", stats.get("error") or "video_statistics failed", report)

    by_id = {str(it.get("id")): it for it in (stats.get("items") or [])}
    results = []
    for item in search.get("items") or []:
        vid = (item.get("id") or {}).get("videoId")
        if not vid or vid not in by_id:
            continue
        full = by_id[vid]
        snippet = full.get("snippet") or item.get("snippet") or {}
        statistics = full.get("statistics") or {}
        thumbs = (snippet.get("thumbnails") or {})
        thumb = (
            (thumbs.get("high") or {}).get("url")
            or (thumbs.get("medium") or {}).get("url")
            or (thumbs.get("default") or {}).get("url")
            or ""
        )
        results.append(
            {
                "title": snippet.get("title") or "",
                "channel": snippet.get("channelTitle") or "",
                "view_count": int(statistics.get("viewCount") or 0),
                "publish_date": snippet.get("publishedAt") or "",
                "thumbnail_url": thumb,
                "video_id": vid,
                "url": f"https://www.youtube.com/watch?v={vid}",
            }
        )

    if not results:
        return _fail("live_search", "No enriched video results after statistics fetch", report)

    latency = {
        "search_ms": round(search_ms, 1),
        "statistics_ms": round(stats_ms, 1),
        "total_ms": round(search_ms + stats_ms, 1),
    }
    report["latency_ms"] = latency
    report["results"] = results
    report["quota"] = yt.quota.snapshot()
    report["checklist"].append(
        {
            "ok": True,
            "label": "Live request successful",
            "detail": f"Query={QUERY!r} results={len(results)} latency_ms={latency['total_ms']}",
        }
    )

    # Secret leak check on report payload
    blob = json.dumps(report)
    if key and key in blob:
        report["secret_leak_detected"] = True
        return _fail("secret_leak", "API key appeared in report payload — blocked", report)
    report["checklist"].append({"ok": True, "label": "No secrets in report/logs payload", "detail": "Key not present in report JSON"})

    # 8–9 Discovery + SEO / trend scoring
    from services.discovery.engine import run_discovery
    from services.discovery.scoring import score_discovery_opportunity
    from services.seo.titles import generate_title_candidates
    from services.trends.models import Trend

    top = results[0]
    trend = Trend(
        topic=QUERY,
        keywords=["camera", "manufacturing", "how it's made", "factory"],
        search_volume=max(int(top["view_count"]), 1),
        growth_pct=55.0,
        velocity=0.62,
        competition=0.45,
        freshness=0.9,
        category="engineering",
        country="US",
        language="en",
        platform="youtube",
        source="youtube_e2e_live",
        confidence=0.9,
    )
    opportunity, discovery_score = score_discovery_opportunity(trend)
    titles = generate_title_candidates(QUERY, keywords=list(trend.keywords), base_psychology=75)
    discovery_run = run_discovery(
        QUERY,
        category="engineering",
        country="US",
        limit_per_provider=1,
        top_n=10,
        persist=False,
    )

    report["discovery"] = {
        "topic": QUERY,
        "seed_video": top,
        "discovery_score": discovery_score.to_dict() if hasattr(discovery_score, "to_dict") else dict(discovery_score.__dict__),
        "opportunity_score": opportunity.opportunity_score if hasattr(opportunity, "opportunity_score") else None,
        "seo_title_candidates": [
            {"title": c.get("title"), "archetype": c.get("archetype"), "score": c.get("score")}
            for c in (titles or [])[:5]
            if isinstance(c, dict)
        ],
        "engine_ok": bool(discovery_run.get("ok")),
        "engine_discovered": discovery_run.get("discovered"),
        "engine_youtube": discovery_run.get("youtube"),
        "engine_top_topic": (discovery_run.get("top") or {}).get("topic"),
    }
    # Ensure key not in discovery blob
    if key in json.dumps(report["discovery"]):
        report["secret_leak_detected"] = True
        return _fail("secret_leak", "API key leaked into discovery payload", report)

    if not discovery_run.get("ok"):
        return _fail("discovery_engine", "Discovery Engine run failed", report)

    report["checklist"].append(
        {
            "ok": True,
            "label": "Discovery Engine consumed results",
            "detail": f"discovered={discovery_run.get('discovered')} youtube_live={((discovery_run.get('youtube') or {}).get('live'))}",
        }
    )
    report["checklist"].append(
        {
            "ok": True,
            "label": "SEO / trend score generated",
            "detail": f"discovery_total={getattr(discovery_score, 'total', None)} titles={len(titles or [])}",
        }
    )
    report["checklist"].append({"ok": True, "label": "No errors", "detail": ""})

    report["ok"] = True
    report["failed_at"] = None
    report["error"] = None
    report["completed_at"] = datetime.now(timezone.utc).isoformat()
    _write_report(report)

    print("=== YouTube E2E Verification — SUCCESS ===")
    for item in report["checklist"]:
        print(f"✓ {item['label']}" + (f" — {item['detail']}" if item.get("detail") else ""))
    print(f"\nLatency: {latency['total_ms']} ms")
    print(f"Quota snapshot: {report['quota']}")
    print("\nTop results:")
    for row in results[:3]:
        print(f"- {row['title']}")
        print(f"  channel={row['channel']} views={row['view_count']} id={row['video_id']}")
        print(f"  published={row['publish_date']}")
        print(f"  thumb={row['thumbnail_url']}")
    print(f"\nReport: {MD_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
