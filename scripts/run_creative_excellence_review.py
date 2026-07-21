#!/usr/bin/env python3
"""Creative Excellence review — attention craft scorecard + ONE recommendation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.creative_excellence import review_production_creative_excellence  # noqa: E402


def _load_gold_standard() -> tuple[dict, dict, str]:
    base = ROOT / "data" / "productions" / "_validation" / "gold_standard" / "ai_what_it_actually_is"
    report = {}
    candidate = {"topic": "What Artificial Intelligence Actually Is", "platform": "youtube_shorts"}
    pid = ""
    if (base / "PRODUCTION_REPORT.json").exists():
        report = json.loads((base / "PRODUCTION_REPORT.json").read_text(encoding="utf-8"))
        pid = str(report.get("production_id") or "")
    if (base / "SCRIPT.json").exists():
        script = json.loads((base / "SCRIPT.json").read_text(encoding="utf-8"))
        if isinstance(script, dict):
            candidate["structured_script"] = script
            candidate["script"] = script.get("full_script") or script.get("script") or ""
    if (base / "SCRIPT.md").exists() and not candidate.get("script"):
        candidate["script"] = (base / "SCRIPT.md").read_text(encoding="utf-8")
    if (base / "GOLD_STANDARD_MANIFEST.json").exists():
        man = json.loads((base / "GOLD_STANDARD_MANIFEST.json").read_text(encoding="utf-8"))
        pid = pid or str(man.get("production_id") or "")
        candidate["topic"] = man.get("topic") or candidate["topic"]
    # Enrich from ops context if present
    if pid:
        ops = ROOT / "data" / "productions" / "_ops" / pid / "PRODUCTION_REPORT.json"
        if ops.exists() and not report:
            report = json.loads(ops.read_text(encoding="utf-8"))
    return candidate, report, pid


def main() -> int:
    parser = argparse.ArgumentParser(description="Creative Excellence review")
    parser.add_argument("--topic", default="")
    parser.add_argument("--production-id", default="")
    parser.add_argument("--report", default="", help="Path to PRODUCTION_REPORT.json")
    parser.add_argument("--gold-standard", action="store_true", help="Review the AI gold-standard flagship")
    parser.add_argument("--script", default="", help="Optional script text/file")
    args = parser.parse_args()

    candidate: dict = {}
    report: dict = {}
    pid = args.production_id

    if args.gold_standard or (not args.report and not args.topic):
        candidate, report, pid = _load_gold_standard()
    if args.report:
        report = json.loads(Path(args.report).read_text(encoding="utf-8"))
        pid = pid or str(report.get("production_id") or "")
        candidate.setdefault("topic", report.get("topic"))
    if args.topic:
        candidate["topic"] = args.topic
    if args.script:
        p = Path(args.script)
        candidate["script"] = p.read_text(encoding="utf-8") if p.exists() else args.script

    print("=== Creative Excellence Review ===")
    result = review_production_creative_excellence(
        candidate,
        production_report=report,
        production_id=pid,
        topic=str(candidate.get("topic") or report.get("topic") or ""),
    )
    gold = ROOT / "data" / "productions" / "_validation" / "gold_standard" / "ai_what_it_actually_is"
    if args.gold_standard and gold.exists():
        (gold / "CREATIVE_EXCELLENCE.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        if result.get("markdown_path") and Path(result["markdown_path"]).exists():
            (gold / "CREATIVE_EXCELLENCE.md").write_text(
                Path(result["markdown_path"]).read_text(encoding="utf-8"),
                encoding="utf-8",
            )

    sc = result.get("scorecard") or {}
    rec = result.get("single_recommendation") or {}
    print(
        json.dumps(
            {
                "creative_excellence_score": sc.get("creative_excellence_score"),
                "engineering_quality": (sc.get("dimensions") or {}).get("engineering_quality"),
                "timeline": sc.get("timeline"),
                "viewer_outcomes": (sc.get("viewer_outcomes") or {}).get("judgments"),
                "single_recommendation": {
                    "element": rec.get("element"),
                    "expected_retention_gain": rec.get("expected_retention_gain"),
                    "recommendation": rec.get("recommendation"),
                },
                "vs_previous": result.get("vs_previous"),
                "markdown": result.get("markdown_path"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
