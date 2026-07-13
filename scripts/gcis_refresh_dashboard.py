#!/usr/bin/env python3
"""Refresh GCIS executive dashboard from validation reports."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.gcis import refresh_dashboard_from_validation


def main() -> None:
    dash = refresh_dashboard_from_validation()
    print(json.dumps({"ok": True, "updated_at": dash.get("updated_at"), "metrics": dash.get("metrics")}, indent=2))


if __name__ == "__main__":
    main()
