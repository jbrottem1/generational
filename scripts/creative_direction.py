#!/usr/bin/env python3
"""Creative Direction CLI — Phase III visual identity."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Generational Creative Direction (Phase III)")
    parser.add_argument("--materialize", action="store_true", help="Write constitution packages")
    parser.add_argument("--review", nargs=2, metavar=("ASSET_ID", "JSON_PATH"), help="Review an asset JSON")
    parser.add_argument("--show-constitution", action="store_true")
    args = parser.parse_args()

    from services.creative_direction import load_constitution, materialize_creative_direction, review_asset

    if args.show_constitution:
        print(json.dumps(load_constitution(), indent=2))
        return 0

    if args.review:
        asset_id, path = args.review
        data = json.loads(Path(path).read_text())
        data.setdefault("asset_id", asset_id)
        print(json.dumps(review_asset(data), indent=2))
        return 0

    result = materialize_creative_direction(write=True)
    print(json.dumps({"ok": result.get("ok"), "path": result.get("path")}, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
