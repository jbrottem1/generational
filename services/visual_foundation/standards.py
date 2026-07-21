"""Load Visual Foundation V1 standards (machine-readable constitution)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
FOUNDATION_JSON = ROOT / "data" / "visual_foundation" / "VISUAL_FOUNDATION_V1.json"
FOUNDATION_MD = ROOT / "GENERATIONAL_VISUAL_FOUNDATION_V1.md"
FOUNDATION_VERSION = "1.0.0"


@lru_cache(maxsize=1)
def load_foundation() -> dict[str, Any]:
    if FOUNDATION_JSON.is_file():
        return json.loads(FOUNDATION_JSON.read_text(encoding="utf-8"))
    return {
        "version": FOUNDATION_VERSION,
        "visual_target": "feature_film_quality_cinematic_realism",
        "quality_gates": {"reject_if": [], "self_review": []},
    }


def visual_target() -> str:
    return str(load_foundation().get("visual_target") or "feature_film_quality_cinematic_realism")


def reject_list() -> list[str]:
    return list(load_foundation().get("reject") or [])


def style_modes() -> list[str]:
    return list(load_foundation().get("style_modes") or ["cinematic_realism"])
