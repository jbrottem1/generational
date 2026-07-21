"""Live validation: YouTube Search Intelligence → Discovery → Agent 3 handoff."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.env import load_application_env
from services.discovery.engine import run_discovery
from services.discovery.script_handoff import queue_item_to_script_context
from services.providers.youtube_search_intelligence import get_youtube_search_intelligence


def _assert_no_raw_api(payload: dict) -> None:
    blob = json.dumps(payload, default=str)
    for banned in ("etag", '"kind": "youtube#', "pageInfo", "nextPageToken"):
        assert banned not in blob, f"raw API field leaked: {banned}"


def main() -> int:
    load_application_env()
    out_dir = ROOT / "data" / "productions" / "_validation" / "youtube_search_intelligence"
    out_dir.mkdir(parents=True, exist_ok=True)

    topic = "How cameras are made"
    intel = get_youtube_search_intelligence(refresh=True)
    print("=== YouTube Search Intelligence ===")
    print(f"configured={intel.is_configured()}")

    if not intel.is_configured():
        print("FAIL: YOUTUBE_API_KEY not configured — cannot run live validation.")
        return 1

    report = intel.analyze_topic(topic, category="science", country="US", language="en", limit=8)
    print(f"live={report.live} videos={len(report.videos)}")
    print(f"market={report.market.to_dict()}")
    print(f"brief={json.dumps(report.brief.to_dict(), indent=2)}")
    for v in report.videos[:5]:
        print(
            f"- {v.title}\n"
            f"  channel={v.channel} views={v.view_count} likes={v.like_count} "
            f"comments={v.comment_count} duration={v.duration_sec}s\n"
            f"  category={v.category} lang={v.language}\n"
            f"  scores={v.scores.to_dict()}\n"
            f"  thumb={v.thumbnail[:60]}…"
        )

    _assert_no_raw_api(report.to_dict())

    payload = run_discovery(
        topic,
        category="science",
        country="US",
        language="en",
        limit_per_provider=2,
        top_n=12,
        persist=False,
    )
    ysi = payload.get("youtube_search_intelligence") or {}
    print("\n=== Discovery Engine ===")
    print(
        f"discovered={payload.get('discovered')} ready={payload.get('ready')} "
        f"ysi.live={ysi.get('live')}"
    )
    top = payload.get("top") or {}
    if top:
        print(f"top.topic={top.get('topic')}")
        print(f"top.overall_opportunity_score={top.get('overall_opportunity_score')}")
        print(f"top.recommended_video_type={top.get('recommended_video_type')}")
        print(f"top.unified discovery_score={top.get('discovery_score')}")
        print(f"top.confidence={top.get('confidence_score')}")
        brief = top.get("production_brief") or {}
        print(f"reasoning={str(brief.get('reasoning') or '')[:240]}")
        print(f"cross_ref={brief.get('cross_reference')}")

    handoff = payload.get("script_handoff") or (queue_item_to_script_context(top) if top else {})
    print("\n=== Agent 3 Script Handoff ===")
    print(f"target_platform={handoff.get('target_platform')}")
    print(f"candidates={len(handoff.get('candidates') or [])}")
    print(f"research.opportunity_score={(handoff.get('research') or {}).get('opportunity_score')}")

    _assert_no_raw_api({"ysi": ysi, "top": top, "handoff": handoff})

    status = "SUCCESS" if report.live and report.videos and top else "PARTIAL"
    doc = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "topic": topic,
        "intelligence": report.to_dict(),
        "discovery": {
            "discovered": payload.get("discovered"),
            "ready": payload.get("ready"),
            "top": top,
            "youtube_search_intelligence_brief": ysi.get("brief"),
            "youtube_search_intelligence_market": ysi.get("market"),
        },
        "script_handoff": handoff,
    }
    json_path = out_dir / "YOUTUBE_SEARCH_INTELLIGENCE_E2E.json"
    md_path = out_dir / "YOUTUBE_SEARCH_INTELLIGENCE_E2E_REPORT.md"
    json_path.write_text(json.dumps(doc, indent=2, default=str), encoding="utf-8")

    lines = [
        "# YouTube Search Intelligence — E2E",
        "",
        f"Generated: {doc['generated_at']}",
        f"**Status:** {status}",
        "",
        f"Topic: **{topic}**",
        f"Videos analyzed: {len(report.videos)}",
        f"Avg views: {report.market.average_view_count}",
        f"Opportunity: {report.brief.overall_opportunity_score}",
        f"Unified discovery: {report.brief.unified_discovery_score}",
        f"Recommended type: {report.brief.recommended_video_type}",
        "",
        "## Sample watch signals (structured)",
        "",
    ]
    for v in report.videos[:6]:
        lines.append(f"### {v.title}")
        lines.append(f"- Channel: {v.channel}")
        lines.append(f"- Views / likes / comments: {v.view_count} / {v.like_count} / {v.comment_count}")
        lines.append(f"- Duration: {v.duration_sec}s | Category: {v.category} | Lang: {v.language}")
        lines.append(f"- Scores: `{v.scores.to_dict()}`")
        lines.append("")
    lines.extend(
        [
            "## Agent 3 handoff",
            f"- Platform: `{handoff.get('target_platform')}`",
            f"- Opportunity score: {(handoff.get('research') or {}).get('opportunity_score')}",
            "",
            "Raw YouTube API payloads are never stored in this report.",
            f"JSON: `{json_path}`",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nReport: {md_path}")
    print(f"=== RESULT: {status} ===")
    return 0 if status == "SUCCESS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
