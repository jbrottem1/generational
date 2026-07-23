"""Validate Audience Intelligence enrichment + Agent 3 handoff."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.env import load_application_env
from services.audience_intelligence import analyze_topic
from services.discovery.engine import run_discovery


def main() -> int:
    load_application_env()
    out_dir = ROOT / "data" / "productions" / "_validation" / "audience_intelligence"
    out_dir.mkdir(parents=True, exist_ok=True)

    topic = "How cameras are made"
    print("=== Audience Intelligence (standalone) ===")
    report = analyze_topic(
        topic,
        category="science",
        angle="Manufacturing process explained — surprising precision inside modern cameras",
    )
    print(json.dumps(report.to_dict(), indent=2)[:2000])
    print(f"\nHuman Attention Score: {report.human_attention_score}")
    print(f"Opening hook: {report.creative.suggested_opening_hook}")
    print(f"Format: {report.creative.recommended_video_format}")
    print(f"Thumbnail: {report.creative.best_thumbnail_style}")

    print("\n=== Discovery → Audience enrichment ===")
    payload = run_discovery(
        topic,
        category="science",
        country="US",
        language="en",
        limit_per_provider=2,
        top_n=10,
        persist=False,
    )
    top = payload.get("top") or {}
    ai = top.get("audience_intelligence") or payload.get("audience_intelligence") or {}
    handoff = payload.get("script_handoff") or {}
    print(f"discovered={payload.get('discovered')} ready={payload.get('ready')}")
    print(f"top.human_attention_score={top.get('human_attention_score')}")
    print(f"top.audience drivers curiosity={(ai.get('psychological_drivers') or {}).get('curiosity_potential')}")
    print(f"handoff.hook={(handoff.get('candidates') or [{}])[0].get('hook')}")
    print(f"handoff.human_attention_score={handoff.get('human_attention_score')}")
    print(f"handoff.target_platform={handoff.get('target_platform')}")

    blob = json.dumps({"ai": ai, "handoff": handoff}, default=str)
    assert "youtube#" not in blob and "etag" not in blob

    status = "SUCCESS" if ai.get("human_attention_score") and handoff.get("candidates") else "PARTIAL"
    doc = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "standalone": report.to_dict(),
        "discovery_top_audience": ai,
        "script_handoff": {
            "target_platform": handoff.get("target_platform"),
            "human_attention_score": handoff.get("human_attention_score"),
            "hook": (handoff.get("candidates") or [{}])[0].get("hook"),
            "audience_script_guidance": handoff.get("audience_script_guidance"),
        },
    }
    json_path = out_dir / "AUDIENCE_INTELLIGENCE_E2E.json"
    md_path = out_dir / "AUDIENCE_INTELLIGENCE_E2E_REPORT.md"
    json_path.write_text(json.dumps(doc, indent=2, default=str), encoding="utf-8")
    md_path.write_text(
        "\n".join(
            [
                "# Audience Intelligence — E2E",
                "",
                f"Generated: {doc['generated_at']}",
                f"**Status:** {status}",
                "",
                f"## Topic: {topic}",
                f"- Human Attention Score: **{ai.get('human_attention_score') or report.human_attention_score}**",
                f"- Opening hook: {(handoff.get('candidates') or [{}])[0].get('hook') or report.creative.suggested_opening_hook}",
                f"- Format: {(ai.get('creative') or {}).get('recommended_video_format') or report.creative.recommended_video_format}",
                f"- Thumbnail: {(ai.get('creative') or {}).get('best_thumbnail_style') or report.creative.best_thumbnail_style}",
                "",
                "## Agent 3 handoff",
                f"- Platform: `{handoff.get('target_platform')}`",
                f"- Attention: {handoff.get('human_attention_score')}",
                "",
                "Structured JSON only — Discovery Engine unchanged as opportunity layer.",
                f"JSON: `{json_path}`",
            ]
        ),
        encoding="utf-8",
    )
    print(f"\nReport: {md_path}")
    print(f"=== RESULT: {status} ===")
    return 0 if status == "SUCCESS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
