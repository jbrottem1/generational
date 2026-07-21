#!/usr/bin/env python3
"""Run Version 1 launch checklist verification."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.launch_plan import run_launch_checklist  # noqa: E402


def main() -> int:
    print("=== Version 1 Launch Checklist ===")
    report = run_launch_checklist()
    print(
        json.dumps(
            {
                "ready_to_publish": report.get("ready_to_publish"),
                "passed": report.get("passed"),
                "total": report.get("total"),
                "blockers": [
                    {"id": b["id"], "label": b["label"], "detail": b.get("detail")}
                    for b in (report.get("blockers") or [])
                ],
                "report": str(ROOT / "LAUNCH_CHECKLIST.md"),
            },
            indent=2,
        )
    )
    return 0 if report.get("ready_to_publish") else 1


if __name__ == "__main__":
    raise SystemExit(main())
