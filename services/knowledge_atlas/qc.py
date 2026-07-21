"""Knowledge Atlas QC — reject low-quality or unlicensed assets."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from services.knowledge_atlas.models import AtlasAsset

ALLOWED_LICENSES = frozenset({
    "public_domain",
    "CC0",
    "CC-BY",
    "CC-BY-SA",
    "US-Gov",
    "NASA",
    "NOAA",
    "Unsplash",
})

MIN_SHORT_SIDE = 400
MIN_QUALITY_SCORE = 0.5


@dataclass
class AtlasQCResult:
    passed: bool
    hard_fails: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    quality_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "hard_fails": self.hard_fails,
            "warnings": self.warnings,
            "quality_score": self.quality_score,
        }


def validate_asset(asset: AtlasAsset, *, require_file: bool = True) -> AtlasQCResult:
    fails: list[str] = []
    warnings: list[str] = []

    if require_file:
        root = Path(__file__).resolve().parents[2]
        p = Path(asset.path)
        if not p.is_absolute():
            # Try data/reality and data/knowledge_atlas roots
            candidates = [
                root / asset.path,
                root / "data" / "reality" / asset.path.replace("data/reality/", ""),
                root / "data" / "knowledge_atlas" / asset.path.replace("data/knowledge_atlas/", ""),
            ]
            if not any(c.is_file() for c in candidates):
                fails.append(f"missing_file:{asset.asset_id}")

    lic = asset.license.strip()
    if lic not in ALLOWED_LICENSES:
        fails.append(f"license_not_allowed:{asset.asset_id}:{lic}")

    short = min(asset.width, asset.height) if asset.width and asset.height else 0
    if short and short < MIN_SHORT_SIDE:
        warnings.append(f"resolution_below_preferred:{short}")

    if asset.quality_score < MIN_QUALITY_SCORE:
        warnings.append(f"quality_score_low:{asset.quality_score}")

    if not asset.description.strip():
        warnings.append("missing_description")

    score = asset.quality_score
    passed = not fails
    return AtlasQCResult(passed=passed, hard_fails=fails, warnings=warnings, quality_score=score)
