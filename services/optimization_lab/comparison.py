"""Module 2 — Automatic Comparison & leaderboard."""

from __future__ import annotations

from core.heuristics import clamp
from services.optimization_lab.models import SCORE_DIMENSIONS


def _psych(candidate: dict) -> dict:
    p = candidate.get("psychology") or {}
    if isinstance(p, dict) and isinstance(p.get("dimensions"), dict):
        return p["dimensions"]
    return p if isinstance(p, dict) else {}


def score_variant(variant: dict, candidate: dict) -> dict:
    """Score one variant across mission metrics (0–100)."""
    axes = variant.get("axes") or {}
    psych = _psych(candidate)
    vr = candidate.get("viewer_retention_package") or {}
    studio = candidate.get("studio_render_package") or {}

    hook = str(axes.get("hook") or "")
    hook_quality = 55
    if "?" in hook:
        hook_quality += 8
    if "—" in hook or ":" in hook:
        hook_quality += 5
    if 8 <= len(hook.split()) <= 24:
        hook_quality += 12
    if any(w in hook.lower() for w in ("secret", "wrong", "hidden", "changing", "nobody")):
        hook_quality += 10
    hook_quality += int(round((float(psych.get("first_3_second_hook") or 50) - 50) * 0.25))
    # Prefer non-baseline experimental hooks slightly when psychology is strong
    if not variant.get("baseline") and float(psych.get("curiosity_gap") or 0) >= 70:
        hook_quality += 4

    psychology = clamp(
        int(
            float(psych.get("viral_score") or candidate.get("psychology_score") or 0)
            or (
                sum(
                    float(psych.get(k) or 50)
                    for k in ("curiosity_gap", "retention_potential", "share_likelihood")
                )
                / 3
            )
        ),
        0,
        100,
    )
    # Axis affinity boosts
    if axes.get("narration") == "curious_storyteller":
        psychology = clamp(psychology + 3, 0, 100)
    if axes.get("narration") == "high_energy_host" and psychology >= 70:
        psychology = clamp(psychology + 4, 0, 100)

    retention = int(
        vr.get("overall_score")
        or (vr.get("quality_scores") or {}).get("retention")
        or psych.get("retention_potential")
        or 62
    )
    if axes.get("camera_movement"):
        retention = clamp(retention + 3, 0, 100)
    if axes.get("caption_style") in ("kinetic_bold", "highlight_pop"):
        retention = clamp(retention + 2, 0, 100)

    educational = clamp(
        60
        + (10 if "explained" in str(axes.get("title") or "").lower() else 0)
        + (8 if axes.get("visual_style") in ("science_documentary", "kinetic_infographic") else 0)
        + (6 if axes.get("narration") in ("authoritative_educator", "calm_documentary") else 0),
        0,
        100,
    )

    entertainment = clamp(
        55
        + (12 if axes.get("music") in ("cinematic_rise", "urgent_beat") else 4)
        + (10 if axes.get("thumbnail") in ("question_overlay", "before_after_split") else 4)
        + int(hook_quality * 0.15),
        0,
        100,
    )

    seo_pkg = axes.get("seo") or {}
    seo = clamp(
        50
        + (15 if seo_pkg.get("title") else 0)
        + min(20, len(seo_pkg.get("tags") or []) * 4)
        + min(10, len(seo_pkg.get("hashtags") or []) * 3)
        + (8 if len(str(axes.get("title") or "")) >= 20 else 0),
        0,
        100,
    )

    visual = int(
        studio.get("overall_score")
        or candidate.get("studio_render_score")
        or candidate.get("visual_score")
        or 70
    )
    if axes.get("visual_style"):
        visual = clamp(visual + 4, 0, 100)

    narration = clamp(
        58
        + (12 if axes.get("narration") else 0)
        + (10 if axes.get("narration") == "authoritative_educator" else 0)
        + int((vr.get("quality_scores") or {}).get("narration") or 0) * 0.15,
        0,
        100,
    )

    professional = clamp(
        60
        + (10 if studio.get("passed") or studio.get("overall_score", 0) >= 90 else 0)
        + (8 if vr.get("passed") or vr.get("overall_score", 0) >= 90 else 0)
        + (8 if axes.get("visual_style") == "science_documentary" else 4),
        0,
        100,
    )

    platform = clamp(
        65
        + (10 if seo_pkg.get("tags") else 0)
        + (8 if axes.get("caption_style") else 0)
        + (8 if axes.get("thumbnail") else 0)
        + (5 if len(str(axes.get("description") or "")) > 40 else 0),
        0,
        100,
    )

    scores = {
        "hook_quality": clamp(hook_quality, 0, 100),
        "psychology": psychology,
        "retention": clamp(retention, 0, 100),
        "educational_value": educational,
        "entertainment": entertainment,
        "seo": seo,
        "visual_quality": clamp(visual, 0, 100),
        "narration": narration,
        "professional_appearance": professional,
        "platform_readiness": platform,
    }
    overall = int(round(sum(scores[k] for k in SCORE_DIMENSIONS) / len(SCORE_DIMENSIONS)))
    scores["overall"] = overall
    return scores


def compare_variants(variants: list[dict], candidate: dict) -> dict:
    """Score all variants and return ranked leaderboard."""
    scored = []
    for v in variants:
        row = dict(v)
        row["scores"] = score_variant(v, candidate)
        row["overall_score"] = row["scores"]["overall"]
        scored.append(row)
    scored.sort(key=lambda r: (r["overall_score"], r["scores"].get("hook_quality", 0)), reverse=True)
    for i, row in enumerate(scored):
        row["rank"] = i + 1
    winner = scored[0] if scored else {}
    return {
        "variants": scored,
        "leaderboard": [
            {
                "rank": r["rank"],
                "label": r["label"],
                "variant_id": r["variant_id"],
                "overall": r["overall_score"],
                "hook_quality": r["scores"]["hook_quality"],
                "retention": r["scores"]["retention"],
                "seo": r["scores"]["seo"],
                "title": (r.get("axes") or {}).get("title"),
            }
            for r in scored
        ],
        "winner": winner,
    }
