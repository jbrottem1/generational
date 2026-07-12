"""Multidimensional quality scoring — not just 'MP4 plays'.

Scores 0–100 per dimension with hard-fail conditions and minimum thresholds.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class QualityDimension(str, Enum):
    HOOK = "hook_quality"
    STORY = "story_structure"
    EDUCATION = "educational_clarity"
    ACCURACY = "factual_accuracy"
    ANIMATION = "animation_quality"
    CHARACTER = "character_consistency"
    VISUAL = "visual_clarity"
    AUDIO = "audio_quality"
    LIPSYNC = "lip_synchronization"
    PACING = "pacing"
    DELIVERY = "emotional_delivery"
    ENDING = "ending_quality"
    BRAND = "brand_consistency"
    PLATFORM = "platform_readiness"
    TECHNICAL = "technical_validity"


# Minimum per-dimension threshold (0–100) for ship consideration
DEFAULT_THRESHOLDS: dict[str, float] = {
    QualityDimension.TECHNICAL.value: 70.0,
    QualityDimension.EDUCATION.value: 65.0,
    QualityDimension.ACCURACY.value: 70.0,
    QualityDimension.ANIMATION.value: 60.0,
    QualityDimension.LIPSYNC.value: 55.0,
    QualityDimension.HOOK.value: 50.0,
    QualityDimension.ENDING.value: 50.0,
}

# PROJECT FOUNDATION — hard ship gates (lipsync floor 70; animation QC fail-closed)
FOUNDATION_THRESHOLDS: dict[str, float] = {
    QualityDimension.TECHNICAL.value: 75.0,
    QualityDimension.EDUCATION.value: 70.0,
    QualityDimension.ACCURACY.value: 70.0,
    QualityDimension.ANIMATION.value: 70.0,
    QualityDimension.LIPSYNC.value: 70.0,
    QualityDimension.HOOK.value: 55.0,
    QualityDimension.ENDING.value: 55.0,
}


@dataclass
class QualityReport:
    scores: dict[str, float] = field(default_factory=dict)
    overall: float = 0.0
    passed: bool = False
    hard_fails: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    thresholds: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_THRESHOLDS))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def hard_fail_reasons(
    production: dict[str, Any],
    *,
    foundation: bool = False,
    scores: dict[str, float] | None = None,
) -> list[str]:
    """Non-negotiable blockers.

    Foundation path: animation QC fail-closed; lipsync floor 70 hard-fails.
    """
    fails: list[str] = []
    qc = production.get("qc") or {}
    export_path = str(production.get("export_path") or production.get("output_path") or "")
    bytes_ = int(production.get("export_bytes") or production.get("bytes") or 0)
    foundation = foundation or bool(production.get("foundation")) or str(
        production.get("demo_id") or ""
    ).startswith("foundation_")

    if not export_path:
        fails.append("missing_export_path")
    elif bytes_ < 50_000 and not production.get("mock"):
        fails.append("export_too_small")
    if qc.get("passed") is False:
        fails.append("animation_qc_failed")
    if foundation and not qc and not production.get("mock"):
        # Recovered / stub QC without metrics is not enough to ship Foundation
        if production.get("require_full_qc", True) and "passed" not in qc:
            fails.append("animation_qc_missing")
    if production.get("placeholder_assets"):
        fails.append("placeholder_assets_remain")
    ver = production.get("verification") or production.get("verify") or {}
    if ver and ver.get("ok") is False:
        fails.append("export_verification_failed")
    if ver.get("has_audio") is False:
        fails.append("missing_audio")
    if ver.get("has_video") is False:
        fails.append("missing_video")
    if foundation and scores is not None:
        lipsync = float(scores.get(QualityDimension.LIPSYNC.value) or 0)
        if lipsync < 70.0:
            fails.append("lipsync_below_foundation_floor")
        anim = float(scores.get(QualityDimension.ANIMATION.value) or 0)
        if anim < 70.0:
            fails.append("animation_below_foundation_floor")
    return fails


def _score_from_qc(qc: dict[str, Any], *, foundation: bool = False) -> dict[str, float]:
    """Derive dimension scores from performer / pipeline QC when present."""
    idle = float(qc.get("idle_ratio") or 0)
    walk = float(qc.get("walk_ratio") or 0)
    purposeful = bool(qc.get("purposeful_gestures", True))
    mouth = bool(qc.get("mouth_varies", True))
    speaking = float(qc.get("speaking_ratio") or 0.5)
    silence_ok = bool(qc.get("has_silence_closed", True))

    animation = 72.0
    if purposeful:
        animation += 8.0
    if idle >= 0.2:
        animation += 5.0
    if foundation and 0.22 <= idle <= 0.55:
        animation += 4.0
    if walk > 0.25:
        animation -= 10.0
    elif foundation and walk <= 0.20:
        animation += 2.0
    if not qc.get("blink_programmed", True):
        animation -= 5.0
    if foundation and qc.get("interactive_teaching"):
        animation += 2.0

    lipsync = 70.0 if mouth else 40.0
    if speaking > 0.15:
        lipsync += min(15.0, speaking * 20)
    if foundation and silence_ok and mouth:
        lipsync += 3.0
    if foundation and speaking >= 0.55:
        lipsync += 2.0

    return {
        QualityDimension.ANIMATION.value: min(100.0, animation),
        QualityDimension.LIPSYNC.value: min(100.0, lipsync),
        QualityDimension.CHARACTER.value: 78.0 if (qc.get("grounded") and foundation) else (
            75.0 if qc.get("grounded") else 55.0
        ),
        QualityDimension.TECHNICAL.value: 88.0 if (qc.get("passed") and foundation) else (
            85.0 if qc.get("passed") else 45.0
        ),
    }


def score_production(
    production: dict[str, Any],
    *,
    script: dict[str, Any] | None = None,
    educational: dict[str, Any] | None = None,
    thresholds: dict[str, float] | None = None,
    foundation: bool | None = None,
) -> QualityReport:
    """Score a finished or in-progress production package."""
    is_foundation = (
        foundation
        if foundation is not None
        else (
            bool(production.get("foundation"))
            or str(production.get("demo_id") or "").startswith("foundation_")
        )
    )
    thresholds = thresholds or (
        dict(FOUNDATION_THRESHOLDS) if is_foundation else dict(DEFAULT_THRESHOLDS)
    )
    qc = production.get("qc") or {}
    script = script or production.get("script") or {}
    educational = educational or production.get("educational_review") or {}

    scores = _score_from_qc(qc, foundation=is_foundation)

    hook = str(script.get("hook") or production.get("hook") or "")
    scores[QualityDimension.HOOK.value] = 75.0 if len(hook) > 20 else 45.0

    takeaway = str(script.get("takeaway") or script.get("cta") or "")
    scores[QualityDimension.ENDING.value] = 70.0 if takeaway else 50.0

    scores[QualityDimension.STORY.value] = float(production.get("story_score") or 68.0)
    scores[QualityDimension.EDUCATION.value] = float(
        educational.get("score") or production.get("education_score") or 65.0
    )
    scores[QualityDimension.ACCURACY.value] = float(
        educational.get("accuracy_score") or 70.0
    )
    default_visual = 78.0 if is_foundation else 70.0
    scores[QualityDimension.VISUAL.value] = float(
        production.get("visual_score") or default_visual
    )
    scores[QualityDimension.AUDIO.value] = float(production.get("audio_score") or 72.0)
    scores[QualityDimension.PACING.value] = float(
        production.get("pacing_score") or (72.0 if is_foundation else 68.0)
    )
    scores[QualityDimension.DELIVERY.value] = float(
        production.get("delivery_score") or (74.0 if is_foundation else 70.0)
    )
    scores[QualityDimension.BRAND.value] = float(production.get("brand_score") or 75.0)
    scores[QualityDimension.PLATFORM.value] = float(production.get("platform_score") or 70.0)

    hard_fails = hard_fail_reasons(production, foundation=is_foundation, scores=scores)
    warnings: list[str] = []
    for dim, min_score in thresholds.items():
        if dim in scores and scores[dim] < min_score:
            # Foundation: lipsync / animation threshold breaches are hard fails (already)
            if is_foundation and dim in (
                QualityDimension.LIPSYNC.value,
                QualityDimension.ANIMATION.value,
            ):
                continue
            warnings.append(f"{dim}_below_threshold")

    overall = round(sum(scores.values()) / max(len(scores), 1), 1)
    min_overall = 70.0 if is_foundation else 65.0
    passed = not hard_fails and not warnings and overall >= min_overall

    return QualityReport(
        scores=scores,
        overall=overall,
        passed=passed and not hard_fails,
        hard_fails=hard_fails,
        warnings=warnings,
        thresholds=thresholds,
    )
