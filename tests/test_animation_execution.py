"""Animation Execution Layer — honest skeletal gate + executable scene."""

from __future__ import annotations

from services.animation_execution import (
    audit_capabilities,
    build_executable_animation_scene,
    run_golden_motion_validation,
    select_runtime,
)


def test_capability_audit_marks_true_motion_insufficient():
    audit = audit_capabilities()
    assert audit["sufficient_for_golden_motion"] is False
    assert audit["true_motion"]["insufficient_for_golden_motion"] is True
    assert audit["true_motion"]["supports"]["skeletal_animation"] is False
    assert audit["skeletal_assets"]["has_skinned_mesh"] is False


def test_executable_scene_composes_packages():
    scene = build_executable_animation_scene(duration_sec=14.0)
    assert scene["package_type"] == "EXECUTABLE_ANIMATION_SCENE"
    assert scene["character_id"] == "DOCTOR_001"
    assert len(scene["joint_tracks"]) >= 10
    assert scene["phoneme_timeline"]
    assert len(scene["camera_plan"]) == 4
    assert "pelvis_translation" in scene["true_motion_requirements"]["evidence_required"]
    assert scene["true_motion_requirements"]["camera_alone_does_not_count"] is True


def test_insufficient_runtime_refuses_mp4():
    adapter, sel = select_runtime()
    assert adapter.supports_skeletal is False
    scene = build_executable_animation_scene()
    result = adapter.execute_scene(scene)
    assert result["ok"] is False
    assert result["encode"]["refused"] is True
    assert result["encode"]["mp4_path"] is None


def test_golden_motion_writes_gap_report_not_fake_pass():
    result = run_golden_motion_validation(write=True)
    assert result["golden_motion_passed"] is False
    assert result["mp4_path"] is None
    assert result["executable_scene"]["package_type"] == "EXECUTABLE_ANIMATION_SCENE"
    assert result["capability_gap_report"]["mp4_produced"] is False
    assert result["honest_capability_report"]["fallback_used"] is None
    assert result["artifacts"]["CAPABILITY_GAP_REPORT.json"]
    assert (result.get("source_package_summaries") or {}).get("world_ok") is True
