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


def _resolve_export_bytes(production: dict[str, Any], export_path: str) -> int:
    """Prefer explicit bytes; otherwise read the verified local file."""
    explicit = production.get("export_bytes")
    if explicit is None:
        explicit = production.get("bytes")
    if explicit is not None:
        try:
            return int(explicit)
        except (TypeError, ValueError):
            pass
    ver = production.get("verification") or production.get("verify") or {}
    probe = ver.get("probe") if isinstance(ver, dict) else None
    if isinstance(probe, dict) and probe.get("bytes") is not None:
        try:
            return int(probe["bytes"])
        except (TypeError, ValueError):
            pass
    if ver.get("bytes") is not None:
        try:
            return int(ver["bytes"])
        except (TypeError, ValueError):
            pass
    if export_path:
        from pathlib import Path

        path = Path(export_path)
        if path.is_file():
            return int(path.stat().st_size)
    return 0


def _export_is_technically_verified(production: dict[str, Any], export_path: str) -> bool:
    ver = production.get("verification") or production.get("verify") or {}
    if isinstance(ver, dict) and ver.get("ok") is True:
        return True
    if not export_path:
        return False
    from pathlib import Path

    path = Path(export_path)
    if not path.is_file() or path.stat().st_size <= 0:
        return False
    # Prefer live probe when available; avoid false fails from omitted metadata
    try:
        from services.media_production.verified_export import assess_export_technical_validity

        return bool(assess_export_technical_validity(path).get("ok"))
    except Exception:  # noqa: BLE001
        return path.stat().st_size > 0


def hard_fail_reasons(
    production: dict[str, Any],
    *,
    foundation: bool = False,
    scores: dict[str, float] | None = None,
) -> list[str]:
    """Non-negotiable blockers.

    Foundation path: animation QC fail-closed; lipsync floor 70 hard-fails.
    Raw file size alone is never a hard fail when the MP4 verifies technically.
    Missing animation-QC metadata is reported separately as a warning when the
    export itself is valid (see soft_warning_reasons).
    """
    fails: list[str] = []
    qc = production.get("qc") or {}
    export_path = str(production.get("export_path") or production.get("output_path") or "")
    bytes_ = _resolve_export_bytes(production, export_path)
    foundation = foundation or bool(production.get("foundation")) or str(
        production.get("demo_id") or ""
    ).startswith("foundation_")
    verified = _export_is_technically_verified(production, export_path)

    if not export_path:
        fails.append("missing_export_path")
    elif bytes_ <= 0 and not production.get("mock") and not verified:
        fails.append("export_zero_bytes")
    elif not production.get("mock") and not verified:
        # Context-aware size/bitrate — only hard-fail truncated / implausible outputs
        duration = float(
            production.get("duration_sec")
            or (production.get("verification") or {}).get("duration_sec")
            or (production.get("verify") or {}).get("duration_sec")
            or 0
        )
        bitrate = int((bytes_ * 8) / duration) if duration > 0 else 0
        if bytes_ < 2_048:
            fails.append("export_truncated")
        elif duration > 0 and bitrate and bitrate < 40_000:
            fails.append("implausible_bitrate")
    if qc.get("passed") is False:
        fails.append("animation_qc_failed")
    # Missing QC report is NOT a hard fail when the final MP4 verifies — see warnings
    if production.get("placeholder_assets"):
        fails.append("placeholder_assets_remain")
    ver = production.get("verification") or production.get("verify") or {}
    if ver and ver.get("ok") is False and not verified:
        fails.append("export_verification_failed")
    if ver.get("has_audio") is False:
        fails.append("missing_audio")
    if ver.get("has_video") is False:
        fails.append("missing_video")
    if foundation and scores is not None:
        # Only apply lipsync/animation floors when QC metrics exist
        if qc and "passed" in qc:
            lipsync = float(scores.get(QualityDimension.LIPSYNC.value) or 0)
            if lipsync < 70.0:
                fails.append("lipsync_below_foundation_floor")
            anim = float(scores.get(QualityDimension.ANIMATION.value) or 0)
            if anim < 70.0:
                fails.append("animation_below_foundation_floor")
    return fails


def soft_warning_reasons(
    production: dict[str, Any],
    *,
    foundation: bool = False,
) -> list[str]:
    """Non-blocking issues — valid MP4s stay SUCCESS_WITH_WARNINGS."""
    warnings: list[str] = []
    qc = production.get("qc") or {}
    export_path = str(production.get("export_path") or production.get("output_path") or "")
    bytes_ = _resolve_export_bytes(production, export_path)
    foundation = foundation or bool(production.get("foundation")) or str(
        production.get("demo_id") or ""
    ).startswith("foundation_")
    verified = _export_is_technically_verified(production, export_path)

    if foundation and not qc and not production.get("mock"):
        if production.get("require_full_qc", True) and "passed" not in qc:
            if verified:
                warnings.append("animation_qc_missing")
            else:
                # Still surface as warning here; foundation_gate may escalate if no export
                warnings.append("animation_qc_missing")
    if export_path and bytes_ and bytes_ < 50_000 and verified:
        # Legacy gate demoted: short educational clips may be under 50KB yet valid
        warnings.append("export_size_below_legacy_threshold")
    elif export_path and bytes_ < 50_000 and not verified and not production.get("mock"):
        warnings.append("export_too_small")
    return warnings


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
    warnings: list[str] = list(soft_warning_reasons(production, foundation=is_foundation))
    for dim, min_score in thresholds.items():
        if dim in scores and scores[dim] < min_score:
            # Foundation: lipsync / animation threshold breaches are hard fails when QC present
            if is_foundation and dim in (
                QualityDimension.LIPSYNC.value,
                QualityDimension.ANIMATION.value,
            ):
                continue
            warnings.append(f"{dim}_below_threshold")

    overall = round(sum(scores.values()) / max(len(scores), 1), 1)
    min_overall = 70.0 if is_foundation else 65.0
    # Soft dimension warnings must not alone block a technically verified export
    verified = _export_is_technically_verified(
        production,
        str(production.get("export_path") or production.get("output_path") or ""),
    )
    if verified and not hard_fails:
        passed = True
    else:
        passed = not hard_fails and not warnings and overall >= min_overall

    return QualityReport(
        scores=scores,
        overall=overall,
        passed=passed and not hard_fails,
        hard_fails=hard_fails,
        warnings=warnings,
        thresholds=thresholds,
    )
