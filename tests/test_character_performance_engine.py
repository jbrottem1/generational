"""Character Performance Engine — blocking, simulation, anti-Ken-Burns gate."""

from __future__ import annotations

from services.character_performance_engine import (
    attach_character_performances,
    build_character_performance,
    path_to_ffmpeg_exprs,
    simulation_to_true_motion_path,
    validate_character_performance,
)
from services.character_performance_engine.true_motion_bridge import package_true_motion_fields
from services.media_production.true_motion import _character_motion_exprs


def test_build_doctor_lab_performance_passes_gate():
    pkg = build_character_performance(
        character_id="DOCTOR_001",
        scene={
            "scene_number": 1,
            "narration": "Walk through the laboratory and point toward the hologram.",
            "length_sec": 4.5,
            "studio_expression": "teaching",
            "subject": "hologram",
            "prop": "microscope",
        },
        scene_index=0,
        location="LOC-GMRI",
    )
    assert pkg["package_type"] == "CHARACTER_PERFORMANCE_PACKAGE"
    assert pkg["ken_burns"] is False
    assert pkg["philosophy"]["not_a_renderer"] is True
    assert len(pkg["blocking"]["questions_answered"]) == 6
    assert len(pkg["locomotion"]["waypoints"]) >= 2
    assert pkg["locomotion"]["path_distance_norm"] >= 0.08
    assert pkg["environment_life"]["living"] is True
    assert pkg["camera_follow"]["follows_actor_path"] is True
    assert pkg["camera_follow"]["camera_replaces_action"] is False
    assert len(pkg["simulation"]["keyframes"]) >= 3
    assert pkg["validation"]["ok"] is True


def test_ken_burns_stub_rejected():
    review = validate_character_performance(
        {
            "ken_burns": True,
            "motion_class": "ken_burns",
            "blocking": {},
            "locomotion": {"waypoints": [{"t": 0, "x": 0.5, "y": 0.5}], "path_distance_norm": 0.01},
            "body_performance": {"continuous": False, "body_actions_present": ["blink"]},
            "interactions": {"count": 0, "events": []},
            "environment_life": {"living": False, "channels": []},
            "camera_follow": {"follows_actor_path": False, "camera_replaces_action": True},
            "simulation": {"actor_driven": False, "keyframes": []},
        }
    )
    assert review["ok"] is False
    assert "ken_burns" in review["rejects_hit"] or "ken_burns_flag" in review["failures"]


def test_true_motion_bridge_piecewise_exprs():
    pkg = build_character_performance(
        character_id="DOCTOR_001",
        scene={"narration": "Explain while walking.", "length_sec": 3.0},
        scene_index=1,
        location="lab",
    )
    path = simulation_to_true_motion_path(pkg["simulation"])
    x, y, scale = path_to_ffmpeg_exprs(path, duration_sec=3.0, shot_size="dynamic_medium")
    assert "if(lt(t" in x or "(W-w)" in x
    assert "(H-h)" in y
    assert float(scale) > 0.4

    # Consumed by true_motion helper
    x2, y2, s2 = _character_motion_exprs(
        "walk_explain",
        duration_sec=3.0,
        performance_path=path,
    )
    assert x2 == x
    assert y2 == y
    assert s2 == scale


def test_attach_to_scenes_stamps_true_motion():
    scenes = attach_character_performances(
        [
            {
                "scene_number": 1,
                "studio_character_id": "DOCTOR_001",
                "narration": "Open the door and walk toward the patient.",
                "length_sec": 4.0,
            }
        ],
        location="clinic",
    )
    row = scenes[0]
    assert row["character_performance_package"]["validation"]["ok"]
    assert row["true_motion"]["actor_driven"] is True
    assert row["true_motion"]["performance_path"]["keyframes"]
    fields = package_true_motion_fields(row["character_performance_package"])
    assert fields["not_ken_burns_only"] is True
