#!/usr/bin/env python3
"""Run Golden Motion Production via BlenderRuntime."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Golden Motion Production (BlenderRuntime)")
    parser.add_argument("--preview-only", action="store_true", help="Skip full-quality final pass")
    args = parser.parse_args()

    from services.animation_runtime.golden_production import run_golden_motion_production

    result = run_golden_motion_production(preview_only=args.preview_only)
    print(json.dumps({k: result.get(k) for k in ("ok", "production_dir", "final_mp4", "runtime")}, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
