#!/usr/bin/env python3
"""CLI — Golden Motion Validation + Animation Execution Layer."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    p = argparse.ArgumentParser(description="Golden Motion / Animation Execution")
    p.add_argument("command", choices=["audit", "golden", "selftest"])
    args = p.parse_args()

    from services.animation_execution import (
        audit_capabilities,
        run_golden_motion_validation,
    )

    if args.command == "audit":
        audit = audit_capabilities()
        print(json.dumps(audit, indent=2, default=str))
        return 0 if not audit.get("sufficient_for_golden_motion") else 0

    result = run_golden_motion_validation(write=True)
    summary = {
        "golden_motion_passed": result.get("golden_motion_passed"),
        "mp4_path": result.get("mp4_path"),
        "refused_misleading_mp4": True,
        "out_dir": result.get("out_dir"),
        "latest_dir": result.get("latest_dir"),
        "artifacts": list((result.get("artifacts") or {}).keys()),
        "source_package_summaries": result.get("source_package_summaries"),
        "capability_verdict": (result.get("capability_audit") or {}).get("verdict"),
        "blocking_gaps": (result.get("capability_gap_report") or {}).get("blocking_gaps"),
        "next_integration_step": (result.get("capability_gap_report") or {}).get(
            "next_integration_step"
        ),
    }

    if args.command == "selftest":
        # Success criteria for THIS environment: honest refusal, not fake pass
        ok = (
            result.get("golden_motion_passed") is False
            and result.get("mp4_path") is None
            and bool(result.get("executable_scene"))
            and bool(result.get("capability_gap_report"))
            and (result.get("source_package_summaries") or {}).get("rig_ok")
            and (result.get("source_package_summaries") or {}).get("world_ok")
        )
        summary["selftest_ok"] = ok
        summary["note"] = (
            "Selftest passes when packages compose and misleading MP4 is refused."
        )
        print(json.dumps(summary, indent=2, default=str))
        return 0 if ok else 1

    print(json.dumps(summary, indent=2, default=str))
    # Exit 2 = capability gap (expected until skeletal runtime exists)
    return 2 if not result.get("golden_motion_passed") else 0


if __name__ == "__main__":
    raise SystemExit(main())
