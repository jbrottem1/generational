"""Tests for PROJECT FOUNDATION hard export gate."""

from __future__ import annotations

from pathlib import Path

from services.animation.foundation_gate import (
    LIPSYNC_FLOOR,
    evaluate_foundation_export,
    validate_performer_qc,
)
from services.quality.content_score import FOUNDATION_THRESHOLDS, score_production


def _good_qc(**overrides):
    qc = {
        "passed": True,
        "purposeful_gestures": True,
        "idle_ratio": 0.34,
        "walk_ratio": 0.08,
        "mouth_varies": True,
        "has_silence_closed": True,
        "has_speech_open": True,
        "speaking_ratio": 0.68,
        "grounded": True,
        "interactive_teaching": True,
        "blink_programmed": True,
        "gesture_counts": {"idle": 200, "write": 100, "point": 80, "wave": 0},
    }
    qc.update(overrides)
    return qc


def _good_production(tmp_path: Path | None = None, **overrides):
    if tmp_path is not None:
        export = tmp_path / "Physics_001_F_Equals_MA_ES001.mp4"
        export.write_bytes(b"\x00\x00\x00\x18ftypisom" + b"\x00" * 400_000)
        export_path = str(export)
    else:
        export_path = "/tmp/Physics_001_F_Equals_MA_ES001.mp4"
    prod = {
        "demo_id": "foundation_f_equals_ma",
        "foundation": True,
        "export_path": export_path,
        "export_bytes": 400_000,
        "qc": _good_qc(),
        "verify": {"ok": True, "has_audio": True, "has_video": True},
        "verification": {"ok": True, "has_audio": True, "has_video": True},
        "hook": "What does F equals m a actually mean?",
        "script": {
            "hook": "What does F equals m a actually mean?",
            "takeaway": "Force causes acceleration.",
        },
        "education_score": 86.0,
        "educational_review": {"score": 86.0, "accuracy_score": 82.0},
        "story_score": 76.0,
        "visual_score": 80.0,
        "audio_score": 78.0,
        "pacing_score": 76.0,
        "delivery_score": 78.0,
        "board_actions": [
            {"kind": "equation", "text": "F = m × a", "start": 0.22, "end": 0.36},
        ],
        "write_gesture_window": {"start": 0.22, "end": 0.42},
    }
    prod.update(overrides)
    return prod


def test_foundation_thresholds_lipsync_floor_70():
    assert FOUNDATION_THRESHOLDS["lip_synchronization"] == 70.0
    assert LIPSYNC_FLOOR == 70.0


def test_validate_performer_qc_rejects_failed():
    fails = validate_performer_qc({"passed": False, "idle_ratio": 0.3, "walk_ratio": 0.05})
    assert "animation_qc_failed" in fails


def test_validate_performer_qc_rejects_wave_and_idle_range():
    fails = validate_performer_qc(
        _good_qc(idle_ratio=0.70, gesture_counts={"idle": 500, "wave": 12})
    )
    assert any("idle_ratio_out_of_range" in f for f in fails)
    assert "wave_gesture_forbidden" in fails


def test_foundation_gate_passes_good_export(tmp_path):
    gate = evaluate_foundation_export(_good_production(tmp_path))
    assert gate.passed
    assert gate.hard_fails == []
    assert gate.quality is not None
    assert gate.quality.scores["lip_synchronization"] >= 70.0
    assert gate.quality.overall >= 70.0


def test_foundation_gate_hard_fails_animation_qc(tmp_path):
    gate = evaluate_foundation_export(_good_production(tmp_path, qc=_good_qc(passed=False)))
    assert not gate.passed
    assert "animation_qc_failed" in gate.hard_fails


def test_foundation_score_hard_fails_low_lipsync(tmp_path):
    # Force low lipsync via mouth_varies=False
    prod = _good_production(tmp_path, qc=_good_qc(mouth_varies=False, passed=True, speaking_ratio=0.05))
    report = score_production(prod, foundation=True)
    assert "lipsync_below_foundation_floor" in report.hard_fails or report.scores[
        "lip_synchronization"
    ] < 70
    gate = evaluate_foundation_export(prod)
    assert not gate.passed


def test_foundation_gate_flags_equation_outside_write_beat(tmp_path):
    gate = evaluate_foundation_export(
        _good_production(
            tmp_path,
            board_actions=[{"kind": "equation", "text": "F = m × a", "start": 0.05, "end": 0.12}],
            write_gesture_window={"start": 0.22, "end": 0.42},
        )
    )
    assert gate.passed  # sync is warning, not hard fail
    assert "equation_outside_write_beat" in gate.warnings


def test_foundation_gate_accepts_keyword_board_metadata(tmp_path):
    """Foundation V2 keyword boards must not be treated as missing equation metadata."""
    gate = evaluate_foundation_export(
        _good_production(
            tmp_path,
            demo_id="foundation_v2_turtle_202",
            board_actions=[
                {"kind": "write", "text": "Gradual shell", "start": 0.42, "end": 0.52, "row": 0},
                {"kind": "underline", "text": "Gradual shell", "start": 0.52, "end": 0.58, "row": 0},
            ],
            write_gesture_window={"start": 0.42, "end": 0.52},
        )
    )
    assert gate.passed
    assert "whiteboard_sync_metadata_missing" not in gate.warnings
    assert "no_equation_board_action" not in gate.warnings
    assert "no_board_write_actions" not in gate.warnings
