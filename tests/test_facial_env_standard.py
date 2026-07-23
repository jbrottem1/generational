"""Facial Performance + Environment Construction Standard tests."""

from __future__ import annotations

from pathlib import Path

from services.character_performance import (
    compute_eye_pose,
    face_rig_profile,
    validate_facial_performance_plan,
)
from services.character_world_studio import studio_place_candidate
from services.environment_department import build_environment_package, validate_environment_package
from services.shot_assembly import build_complete_shot
from services.studio_assets import ensure_doctor_001_asset


ROOT = Path(__file__).resolve().parents[1]


def test_face_rig_and_eye_math():
    rig = face_rig_profile("DOCTOR_001")
    assert "brow_inner_left" in rig["controls"]
    assert "jaw_open" in rig["controls"]
    pose = compute_eye_pose((0.0, 1.65, 0.0), (0.4, 1.6, -1.5))
    assert abs(pose.yaw_deg) > 0
    assert pose.convergence_deg > 0


def test_environment_package_has_three_layers():
    env = build_environment_package("LOC-GMRI", owner="DOCTOR_001")
    review = validate_environment_package(env)
    assert review["ok"] is True
    assert review["rendered_inspection_required"] is True
    assert len(env["foreground"]) >= 1
    assert len(env["midground"]) >= 1
    assert len(env["background"]) >= 1
    assert env["weather"]["affects"]


def test_complete_shot_contract():
    shot = build_complete_shot(
        shot_id="scene_004_shot_02",
        story_objective="The Doctor reveals the diagnosis",
        scene={
            "scene_number": 4,
            "narration": "This finding is concerning — and treatable when understood.",
            "subject": "diagnostic_hologram",
            "length_sec": 3.5,
        },
        character_id="DOCTOR_001",
        location="LOC-GMRI",
    )
    facial = shot["character_performance"]["facial_performance_plan"]
    assert validate_facial_performance_plan(facial)["ok"] is True
    assert facial["attention_target"]["attention_target_id"]
    assert facial["gaze_events"]
    assert facial["quality_caveat"]
    assert shot["validation"]["rendered_facial_inspection"]["status"].startswith("PENDING")
    assert "Inspect the final MP4" in shot["validation"]["quality_rule"]


def test_cws_attaches_facial_and_environment():
    out = studio_place_candidate(
        {
            "topic": "How Diagnosis Becomes Clarity",
            "visual_package": {
                "scenes": [
                    {
                        "scene_number": 1,
                        "narration": "Let's carefully examine what the scan reveals.",
                        "length_sec": 3.0,
                        "subject": "hologram_heart",
                    }
                ]
            },
        },
        write=False,
    )
    scene = out["visual_package"]["scenes"][0]
    assert scene.get("facial_performance_plan")
    assert scene.get("environment_package")
    assert scene.get("complete_shot")
    pkg = out["CHARACTER_WORLD_STUDIO_PACKAGE"]
    assert pkg["facial_performance_standard"]["plans_attached"] is True
    assert pkg["environment_construction_standard"]["packages_attached"] is True
    assert "plan_validation_is_not_mp4_quality_proof" in str(pkg["quality_gate"].get("warnings"))


def test_doctor_asset_writes_face_rig_and_env_package():
    ensure_doctor_001_asset(force=False)
    asset = ROOT / "data" / "studio_assets" / "DOCTOR_001"
    assert (asset / "FACE_RIG_PROFILE.json").is_file()
    assert (asset / "ENVIRONMENT_PACKAGE.json").is_file()
