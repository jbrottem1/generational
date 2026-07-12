"""PROJECT FOUNDATION — hard export gate (fail closed).

Validates performer QC + QualityReport before accepting a Foundation export.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from services.quality.content_score import (
    FOUNDATION_THRESHOLDS,
    QualityDimension,
    QualityReport,
    score_production,
)

# Performer QC floors for white-studio professor exports
IDLE_RATIO_MIN = 0.22
IDLE_RATIO_MAX = 0.55
WALK_RATIO_MAX = 0.20
LIPSYNC_FLOOR = 70.0
OVERALL_TARGET = 78.0


@dataclass
class FoundationGateResult:
    passed: bool
    hard_fails: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    quality: QualityReport | None = None
    qc_checks: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        if self.quality is not None:
            d["quality"] = self.quality.to_dict()
        return d


def validate_performer_qc(qc: dict[str, Any] | None) -> list[str]:
    """Hard-fail reasons from animation performer QC."""
    fails: list[str] = []
    qc = qc or {}
    if not qc:
        fails.append("missing_animation_qc")
        return fails
    if qc.get("passed") is False:
        fails.append("animation_qc_failed")
    idle = float(qc.get("idle_ratio") or -1)
    walk = float(qc.get("walk_ratio") or -1)
    if idle >= 0 and not (IDLE_RATIO_MIN <= idle <= IDLE_RATIO_MAX):
        fails.append(f"idle_ratio_out_of_range:{idle}")
    if walk >= 0 and walk > WALK_RATIO_MAX:
        fails.append(f"walk_ratio_too_high:{walk}")
    wave = int((qc.get("gesture_counts") or {}).get("wave") or 0)
    if wave > 0:
        fails.append("wave_gesture_forbidden")
    if qc.get("mouth_varies") is False:
        fails.append("mouth_does_not_vary")
    if qc.get("has_speech_open") is False:
        fails.append("speech_mouth_missing")
    if qc.get("has_silence_closed") is False:
        fails.append("silence_mouth_not_closed")
    return fails


def validate_whiteboard_sync(
    production: dict[str, Any],
    *,
    demo_id: str | None = None,
) -> list[str]:
    """Ensure equation write window overlaps choreography write beat (documented check)."""
    warnings: list[str] = []
    demo = demo_id or production.get("demo_id") or ""
    if not str(demo).startswith("foundation_"):
        return warnings
    # Board actions expose equation timing when attached to the production package
    board = production.get("board_actions") or []
    write_window = production.get("write_gesture_window") or {}
    if not board or not write_window:
        # Soft: missing metadata is a warning, not a ship blocker for recovered exports
        warnings.append("whiteboard_sync_metadata_missing")
        return warnings
    w_start = float(write_window.get("start") or 0)
    w_end = float(write_window.get("end") or 0)
    eq = next((a for a in board if str(a.get("kind")) == "equation"), None)
    if eq is None:
        warnings.append("no_equation_board_action")
        return warnings
    e_start = float(eq.get("start") or 0)
    e_end = float(eq.get("end") or 0)
    # Equation reveal must fall inside the write choreography beat
    if e_start < w_start - 0.02 or e_end > w_end + 0.05:
        warnings.append("equation_outside_write_beat")
    overlap = max(0.0, min(e_end, w_end) - max(e_start, w_start))
    if overlap < 0.08:
        warnings.append("equation_write_overlap_too_small")
    return warnings


def evaluate_foundation_export(
    production: dict[str, Any],
    *,
    script: dict[str, Any] | None = None,
    educational: dict[str, Any] | None = None,
    require_overall: float = OVERALL_TARGET,
) -> FoundationGateResult:
    """Fail-closed gate for Foundation exports.

    Hard-fails: animation QC, lipsync floor 70, missing/broken export.
    Soft warnings: whiteboard sync metadata, overall below stretch target.
    """
    qc = production.get("qc") or {}
    hard_fails = validate_performer_qc(qc)

    quality = score_production(
        production,
        script=script,
        educational=educational,
        thresholds=FOUNDATION_THRESHOLDS,
        foundation=True,
    )
    for reason in quality.hard_fails:
        if reason not in hard_fails:
            hard_fails.append(reason)

    lipsync = float(quality.scores.get(QualityDimension.LIPSYNC.value) or 0)
    if lipsync < LIPSYNC_FLOOR:
        reason = f"lipsync_below_foundation_floor:{lipsync}"
        if reason not in hard_fails:
            hard_fails.append(reason)

    warnings = list(quality.warnings)
    warnings.extend(validate_whiteboard_sync(production))
    if quality.overall < require_overall:
        warnings.append(f"overall_below_target:{quality.overall}<{require_overall}")

    passed = not hard_fails
    return FoundationGateResult(
        passed=passed,
        hard_fails=hard_fails,
        warnings=warnings,
        quality=quality,
        qc_checks={
            "idle_ratio": qc.get("idle_ratio"),
            "walk_ratio": qc.get("walk_ratio"),
            "lipsync": lipsync,
            "overall": quality.overall,
            "animation_qc_passed": qc.get("passed"),
        },
    )
