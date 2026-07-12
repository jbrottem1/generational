#!/usr/bin/env python3
"""Refresh Generational OS V2.5 executive operating dashboard."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.env import load_application_env

load_application_env()

from services.generational_os.dashboard import write_dashboard


def main() -> int:
    path = write_dashboard()
    print(json.dumps({"ok": True, "dashboard_path": str(path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
