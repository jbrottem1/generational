"""Knowledge Atlas asset evaluator — resolution, license, educational value."""

from __future__ import annotations

from services.knowledge_atlas.models import AtlasAsset
from services.knowledge_atlas.qc import ALLOWED_LICENSES


def score_asset(asset: AtlasAsset) -> float:
    """0–1 quality score from resolution, license trust, metadata richness."""
    score = 0.0

    # License trust
    lic = asset.license.strip()
    if lic in ("public_domain", "CC0", "NASA", "NOAA", "US-Gov"):
        score += 0.30
    elif lic in ALLOWED_LICENSES:
        score += 0.25
    else:
        score += 0.05

    # Resolution
    short = min(asset.width, asset.height) if asset.width and asset.height else 0
    if short >= 900:
        score += 0.30
    elif short >= 600:
        score += 0.22
    elif short >= 400:
        score += 0.15
    elif short > 0:
        score += 0.08

    # Metadata richness
    if asset.scientific_name:
        score += 0.10
    if asset.description:
        score += 0.10
    if asset.concepts:
        score += 0.10
    if asset.suggested_uses:
        score += 0.05
    if asset.compare_with:
        score += 0.05

    return round(min(1.0, score), 2)
