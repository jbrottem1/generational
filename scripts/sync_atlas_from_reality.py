#!/usr/bin/env python3
"""Sync Project Reality catalog entries into the Knowledge Atlas."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.knowledge_atlas.ingest import ingest_from_reality_catalog


def main() -> int:
    added, skipped = ingest_from_reality_catalog()
    print(f"Atlas sync: added={added} skipped={skipped}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
