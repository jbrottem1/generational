#!/usr/bin/env python3
"""Generational Launch Readiness Audit — public publishing go/no-go."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.launch_readiness import run_launch_readiness_audit  # noqa: E402


def main() -> int:
    print("=== Launch Readiness Audit ===")
    result = run_launch_readiness_audit()
    print(
        json.dumps(
            {
                "launch_readiness_score": result.get("launch_readiness_score"),
                "ready_for_public_launch": result.get("ready_for_public_launch"),
                "recommendation": result.get("recommendation"),
                "prioritized_blockers": result.get("prioritized_blockers") or [],
                "rollout_plan": bool(result.get("rollout_plan")),
                "json": str(ROOT / "data" / "productions" / "_validation" / "launch_readiness" / "LAUNCH_READINESS_AUDIT.json"),
                "markdown": str(ROOT / "LAUNCH_READINESS_AUDIT.md"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
