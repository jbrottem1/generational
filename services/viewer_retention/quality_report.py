"""Module 10 — Quality Report: scores + performance predictions."""

from __future__ import annotations

from core.heuristics import clamp
from services.viewer_retention.models import EXCELLENCE_PASS_THRESHOLD, QUALITY_DIMENSIONS
from services.viewer_retention.pacing import pacing_variety_score


def _seo_score(candidate: dict) -> int:
    seo = candidate.get("seo") or candidate.get("seo_package") or {}
    if isinstance(seo, dict):
        if seo.get("score") is not None:
            return clamp(int(seo["score"]), 0, 100)
        title = str(seo.get("title") or candidate.get("title") or "")
        tags = seo.get("tags") or seo.get("hashtags") or []
        return clamp(50 + (15 if title else 0) + min(20, len(tags) * 2), 0, 100)
    return 70


def _psych_score(candidate: dict) -> int:
    p = candidate.get("psychology") or {}
    if isinstance(p, dict):
        if p.get("viral_score") is not None:
            return clamp(int(p["viral_score"]), 0, 100)
        if p.get("score") is not None:
            return clamp(int(p["score"]), 0, 100)
        dims = p.get("dimensions") if isinstance(p.get("dimensions"), dict) else p
        keys = ("retention_potential", "first_3_second_hook", "curiosity_gap", "share_likelihood")
        vals = [float(dims.get(k) or 0) for k in keys if isinstance(dims, dict)]
        if vals:
            return clamp(int(round(sum(vals) / len(vals))), 0, 100)
    return 72


def build_quality_report(
    candidate: dict,
    *,
    hook: dict,
    pacing,
    narration_plan: dict,
    sound_design: dict,
    caption_plan: dict,
    visual_ranking: dict,
    retention: dict,
    camera_plan,
    baseline: dict | None = None,
) -> dict:
    hook_score = int((hook.get("selected") or {}).get("score") or hook.get("score") or 70)
    visuals = int(visual_ranking.get("score") or 70)
    narration = int(narration_plan.get("score") or 70)
    psychology = _psych_score(candidate)
    ret = int(retention.get("score") or 70)
    sound = int(sound_design.get("score") or 70)
    captions = int(caption_plan.get("score") or 70)
    animation = clamp(
        55
        + min(30, len(camera_plan) * 4)
        + pacing_variety_score(pacing) * 0.15,
        0,
        100,
    )
    education = clamp(
        60
        + (12 if visuals >= 85 else 0)
        + (12 if narration >= 85 else 0)
        + (10 if psychology >= 80 else 0),
        0,
        100,
    )
    entertainment = clamp(
        50
        + hook_score * 0.2
        + ret * 0.15
        + sound * 0.1
        + animation * 0.1,
        0,
        100,
    )
    seo = _seo_score(candidate)

    scores = {
        "hook": hook_score,
        "visuals": visuals,
        "narration": narration,
        "psychology": psychology,
        "retention": ret,
        "sound_design": sound,
        "captions": captions,
        "animation": int(animation),
        "education": education,
        "entertainment": int(entertainment),
        "seo": seo,
    }
    overall = int(round(sum(scores[k] for k in QUALITY_DIMENSIONS) / len(QUALITY_DIMENSIONS)))
    scores["overall"] = overall

    # Performance predictions (heuristic, reproducible)
    ctr = clamp(2.5 + hook_score * 0.06 + visuals * 0.02, 1.0, 18.0)
    avd = clamp(retention.get("average_retention_pct") or (ret * 0.7), 10.0, 95.0)
    completion = clamp(retention.get("completion_rate") or (ret * 0.65), 5.0, 92.0)
    share = clamp(psychology * 0.35 + entertainment * 0.4 + hook_score * 0.15, 5.0, 90.0) / 100.0
    subscribe = clamp(education * 0.25 + completion * 0.4 + psychology * 0.2, 3.0, 70.0) / 100.0

    predictions = {
        "ctr_pct": round(ctr, 2),
        "average_view_duration_pct": round(avd, 1),
        "completion_rate_pct": round(completion, 1),
        "share_probability": round(share, 3),
        "subscribe_probability": round(subscribe, 3),
    }

    improvements = {}
    baseline = baseline or {}
    for key, val in scores.items():
        if key in baseline:
            improvements[key] = round(val - float(baseline[key]), 1)

    return {
        "scores": scores,
        "predictions": predictions,
        "improvements_vs_baseline": improvements,
        "passed": overall >= EXCELLENCE_PASS_THRESHOLD,
        "threshold": EXCELLENCE_PASS_THRESHOLD,
    }
