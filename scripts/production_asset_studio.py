#!/usr/bin/env python3
"""Production Asset Studio CLI — Phase II asset catalogs + Blender bootstrap."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Generational Production Asset Studio (Phase II)")
    parser.add_argument("--bootstrap", action="store_true", help="Materialize catalogs + build Blender assets")
    parser.add_argument("--catalog-only", action="store_true", help="Write department catalogs only")
    parser.add_argument("--list-departments", action="store_true")
    args = parser.parse_args()

    if args.list_departments:
        from services.production_asset_studio import list_departments

        print(json.dumps(list_departments(), indent=2))
        return 0

    if args.catalog_only:
        from services.production_asset_studio import materialize_phase_ii_catalog

        print(json.dumps(materialize_phase_ii_catalog(write=True), indent=2))
        return 0

    from services.production_asset_studio import run_phase_ii_bootstrap

    result = run_phase_ii_bootstrap(write=True)
    print(
        json.dumps(
            {
                "ok": result.get("ok"),
                "catalog_ok": (result.get("catalog") or {}).get("ok"),
                "blender_ok": (result.get("blender_build") or {}).get("ok"),
                "report": str(ROOT / "data" / "production_asset_studio" / "PHASE_II_BOOTSTRAP_REPORT.json"),
            },
            indent=2,
        )
    )
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
