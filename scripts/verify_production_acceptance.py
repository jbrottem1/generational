#!/usr/bin/env python3
"""CLI / CI entry for Production Acceptance Testing System V1.0."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.production_acceptance import run_acceptance_suite  # noqa: E402

OUT = ROOT / "data" / "productions" / "_validation" / "production_acceptance"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Production Acceptance Testing System V1.0")
    parser.add_argument("--mode", default="smoke", choices=["smoke", "full", "stress"])
    parser.add_argument(
        "--include",
        nargs="*",
        default=None,
        help="Optional category subset (pipeline_integrity video_generation duration platform stress quality recovery output_validation)",
    )
    args = parser.parse_args()

    print(f"=== Production Acceptance ({args.mode}) ===")
    result = run_acceptance_suite(mode=args.mode, include=args.include)
    summary = result["summary"]
    (OUT / f"ACCEPTANCE_{args.mode.upper()}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    lines = [
        f"# Production Acceptance — {args.mode}",
        "",
        f"**Passed: {result['passed']}**",
        f"- Run: `{result['run_id']}`",
        f"- Pass %: {summary.get('pass_pct')}",
        f"- Failure %: {summary.get('failure_pct')}",
        f"- Average quality: {summary.get('average_quality')}",
        f"- Avg render ms: {summary.get('average_render_time_ms')}",
        f"- Recovery success %: {summary.get('recovery_success_pct')}",
        f"- Report: `{result['run_path']}`",
        "",
        "## Failures",
    ]
    for r in result.get("results") or []:
        if not r.get("passed"):
            lines.append(f"- `{r.get('category')}/{r.get('name')}`: {r.get('message')}")
    if summary.get("ok"):
        lines.append("- none")
    (OUT / f"ACCEPTANCE_{args.mode.upper()}_REPORT.md").write_text("\n".join(lines), encoding="utf-8")

    print(
        json.dumps(
            {
                "passed": result["passed"],
                "run_id": result["run_id"],
                "pass_pct": summary.get("pass_pct"),
                "average_quality": summary.get("average_quality"),
                "total": summary.get("total"),
                "failed": summary.get("failed"),
            },
            indent=2,
        )
    )
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
