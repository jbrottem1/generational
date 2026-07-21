"""Composition scoring — rule of thirds, hierarchy, educational clarity, etc."""

from __future__ import annotations

from typing import Any

from services.visual_asset_director.models import COMPOSITION_FIELDS


def score_composition(inspection: dict[str, Any], *, scene: dict[str, Any] | None = None) -> dict[str, float]:
    """Heuristic composition scores 0–100 from inspection metrics + scene intent."""
    m = inspection.get("metrics") or {}
    scene = scene or {}
    dens = float(m.get("edge_density") or 0)
    contrast = float(m.get("luminance_std") or 0)
    center_std = float(m.get("center_luminance_std") or contrast)
    aspect = m.get("aspect") or {}
    w = int(m.get("width") or 0)
    h = int(m.get("height") or 0)

    # Rule of thirds proxy: prefer non-dead-center imbalance in detail (edge vs center)
    thirds = 70.0
    if dens > 0 and contrast > 0:
        imbalance = abs(center_std - contrast) / max(1.0, contrast)
        thirds = max(40.0, min(95.0, 55 + imbalance * 80))
    if aspect.get("ok"):
        thirds = min(100.0, thirds + 5)

    subject_clarity = max(30.0, min(100.0, dens * 420 + contrast * 0.9))
    if dens < 0.02:
        subject_clarity = min(subject_clarity, 45.0)

    eye_direction = 68.0
    purpose = str(scene.get("purpose") or scene.get("beat") or "").lower()
    if any(k in purpose for k in ("hook", "reveal", "payoff", "diagram", "label")):
        eye_direction = 78.0
    if dens > 0.35:
        eye_direction -= 12

    leading_lines = max(45.0, min(90.0, 50 + dens * 80))
    depth = max(40.0, min(95.0, 48 + contrast * 0.7 + dens * 40))
    # World layered scenes often declare layers
    if scene.get("layers") or scene.get("environment_layers") or scene.get("foreground"):
        depth = min(100.0, depth + 12)
        layering = 82.0
    else:
        layering = max(50.0, min(88.0, depth - 5))

    bg_sep = max(40.0, min(95.0, contrast * 1.1 + (12 if dens < 0.25 else 0)))
    hierarchy = (subject_clarity * 0.45 + eye_direction * 0.25 + thirds * 0.3)
    negative = max(35.0, min(95.0, 100 - dens * 160))
    if dens < 0.015:
        negative = min(negative, 50.0)  # empty ≠ good negative space

    edu = 70.0
    if any(k in purpose for k in ("teach", "explain", "diagram", "science", "fact", "heart", "chamber")):
        edu = 80.0
    if "educational" in str(scene.get("style") or "").lower():
        edu = min(100.0, edu + 8)
    if dens < 0.015 or dens > 0.4:
        edu -= 15
    if inspection.get("reject_reasons"):
        edu -= 8 * min(3, len(inspection["reject_reasons"]))

    scores = {
        "rule_of_thirds": round(thirds, 1),
        "subject_clarity": round(subject_clarity, 1),
        "eye_direction": round(eye_direction, 1),
        "leading_lines": round(leading_lines, 1),
        "depth": round(depth, 1),
        "layering": round(layering, 1),
        "background_separation": round(bg_sep, 1),
        "visual_hierarchy": round(hierarchy, 1),
        "negative_space": round(negative, 1),
        "educational_clarity": round(max(0.0, min(100.0, edu)), 1),
    }
    for f in COMPOSITION_FIELDS:
        scores.setdefault(f, 50.0)
    scores["composition_mean"] = round(sum(scores[f] for f in COMPOSITION_FIELDS) / len(COMPOSITION_FIELDS), 1)
    # Aspect usability soft
    scores["frame_aspect_fit"] = 90.0 if aspect.get("ok") else 40.0
    scores["pixel_area"] = float(w * h)
    return scores
