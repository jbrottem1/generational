"""Knowledge Atlas asset evaluator — resolution, license, educational value."""

from __future__ import annotations

from services.knowledge_atlas.models import AtlasAsset
from services.knowledge_atlas.qc import ALLOWED_LICENSES
from services.quality.visual_priority import priority_boost


def score_asset(asset: AtlasAsset) -> float:
    """0–1 quality score from resolution, license trust, metadata richness, visual priority.

    Authentic photographs outrank diagrams; AI/synthetic types receive no priority boost.
    """
    score = 0.0

    # License trust
    lic = asset.license.strip()
    if lic in ("public_domain", "CC0", "NASA", "NOAA", "US-Gov"):
        score += 0.28
    elif lic in ALLOWED_LICENSES:
        score += 0.22
    else:
        score += 0.05

    # Resolution
    short = min(asset.width, asset.height) if asset.width and asset.height else 0
    if short >= 900:
        score += 0.26
    elif short >= 600:
        score += 0.20
    elif short >= 400:
        score += 0.14
    elif short > 0:
        score += 0.08

    # Metadata richness
    if asset.scientific_name:
        score += 0.08
    if asset.description:
        score += 0.08
    if asset.concepts:
        score += 0.08
    if asset.suggested_uses:
        score += 0.04
    if asset.compare_with:
        score += 0.04

    # Visual priority ladder (photos win over AI)
    score += priority_boost(asset.visual_type)

    return round(min(1.0, score), 2)
