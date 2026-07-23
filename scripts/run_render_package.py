#!/usr/bin/env python3
"""Execute RENDER_PACKAGE.json on local Mac — Generational OS V2.5 Layer 3."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.env import load_application_env

load_application_env()

# Delegate to run_local_render_job with package → job field mapping
from scripts.run_local_render_job import execute_job  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute RENDER_PACKAGE.json (OS V2.5)")
    parser.add_argument("--package", default="RENDER_PACKAGE.json")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    path = Path(args.package)
    if not path.is_file():
        print(json.dumps({"ok": False, "error": f"missing package: {path}"}))
        return 1
    payload = execute_job(path, smoke=args.smoke)
    print(json.dumps(payload, indent=2))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
