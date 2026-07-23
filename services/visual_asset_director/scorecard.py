"""Per-scene visual scorecard."""

from __future__ import annotations

from typing import Any

from services.visual_asset_director.models import SCORECARD_FIELDS
from services.visual_asset_director.styles import style_compatibility


def build_scorecard(
    inspection: dict[str, Any],
    composition: dict[str, Any],
    *,
    continuity_hint: float = 70.0,
    character_hint: float = 70.0,
    environment_hint: float = 70.0,
    style_profile: dict[str, Any] | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, float]:
    m = inspection.get("metrics") or {}
    meta = meta or inspection.get("meta") or {}
    style_profile = style_profile or {}

    w = int(m.get("width") or 0)
    h = int(m.get("height") or 0)
    # Resolution score
    if w >= 1080 and h >= 1080:
        resolution = 95.0
    elif w >= 720 and h >= 720:
        resolution = 75.0
    elif w >= 512:
        resolution = 45.0
    else:
        resolution = 25.0

    lum = float(m.get("luminance_mean") or 128)
    contrast = float(m.get("luminance_std") or 0)
    lighting = max(20.0, min(100.0, 40 + contrast * 1.2 - abs(lum - 128) * 0.15))

    composition_score = float(composition.get("composition_mean") or 50)
    edu = float(composition.get("educational_clarity") or 50)

    lap = float(m.get("laplacian_variance") or 0)
    motion = max(35.0, min(95.0, 40 + min(40, lap * 0.8) + float(m.get("edge_density") or 0) * 60))

    thumb = max(
        20.0,
        min(
            100.0,
            resolution * 0.35
            + composition_score * 0.25
            + edu * 0.2
            + lighting * 0.2
            - (15 if inspection.get("reject_reasons") else 0),
        ),
    )

    style_fit = style_compatibility(meta, style_profile) if style_profile else 70.0

    overall = (
        resolution * 0.12
        + lighting * 0.1
        + composition_score * 0.14
        + continuity_hint * 0.1
        + character_hint * 0.1
        + environment_hint * 0.1
        + edu * 0.12
        + motion * 0.08
        + thumb * 0.08
        + style_fit * 0.06
    )
    if inspection.get("reject_reasons"):
        overall *= 0.72

    card = {
        "resolution": round(resolution, 1),
        "lighting": round(lighting, 1),
        "composition": round(composition_score, 1),
        "continuity": round(continuity_hint, 1),
        "character_consistency": round(character_hint, 1),
        "environment_consistency": round(environment_hint, 1),
        "educational_clarity": round(edu, 1),
        "motion_potential": round(motion, 1),
        "thumbnail_appeal": round(thumb, 1),
        "style_fit": round(style_fit, 1),
        "overall_professional_quality": round(max(0.0, min(100.0, overall)), 1),
    }
    for f in SCORECARD_FIELDS:
        card.setdefault(f, 50.0)
    return card
