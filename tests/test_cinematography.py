"""Tests for Cinematography Engine — narration-driven motion, never random."""

from __future__ import annotations

import engines  # noqa: F401
from core.workflows import WORKFLOWS
from engines import registry
from services.cinematography import (
    CAMERA_MOVEMENTS,
    build_cinematography_plan,
    choose_movement,
    cinematography_to_motion_planner_scenes,
    cinematography_to_true_motion_cameras,
    direct_scene,
)
from services.cinematography.models import CinematographyPlan


def test_tilt_narration_selects_orbit():
    movement, angle, framing, zoom, pan, reason = choose_movement("The Earth tilts on its axis.")
    assert movement == "orbit"
    assert "orbit" in reason.lower() or "tilt" in reason.lower()


def test_notice_fossil_selects_push_in():
    movement, *_ = choose_movement("Notice this fossil in the rock layer.")
    assert movement == "slow_push_in"


def test_tiny_transistor_selects_macro():
    movement, angle, framing, zoom, *_ = choose_movement("This tiny transistor switches billions of times.")
    assert movement == "macro_push_in"
    assert framing == "extreme_close_up"
    assert zoom == "in"


def test_factory_selects_establishing():
    movement, angle, framing, *_ = choose_movement("Inside the factory, assembly lines stretch for miles.")
    assert movement == "establishing_wide"
    assert framing == "extreme_wide"


def test_movement_is_deterministic():
    a = choose_movement("The Earth tilts toward the Sun.")
    b = choose_movement("The Earth tilts toward the Sun.")
    assert a == b


def test_direct_scene_outputs_full_contract():
    shot = direct_scene(
        {
            "scene_number": 1,
            "scene_id": "s1",
            "narration": "The Earth tilts on its axis.",
            "length_sec": 5.0,
            "expected_attention_score": 70,
            "motion_plan": {"camera_motion": "ken_burns_in"},
            "annotation_plan": [
                {
                    "narration_cue": "Earth",
                    "highlight_region": {"x0": 0.4, "y0": 0.3, "x1": 0.6, "y1": 0.5},
                }
            ],
        }
    )
    data = shot.to_dict()
    assert data["movement"] == "orbit"
    assert data["camera_angle"]
    assert data["framing"]
    assert data["easing"]
    assert data["focus_coordinates"]["x"] == data["focus_point"]["x"]
    assert data["motion_graph"]
    assert data["timeline"]
    assert data["attention_score"] > 0
    assert data["camera_plan"]["movement"] == "orbit"
    assert data["animation_effect"]
    assert data["movement"] in CAMERA_MOVEMENTS


def test_build_plan_from_evidence_package():
    candidate = {
        "title": "Seasons Explained",
        "evidence_package": {
            "scenes": [
                {
                    "scene_number": 1,
                    "scene_id": "s1",
                    "narration": "The Earth tilts on its axis.",
                    "length_sec": 4,
                    "expected_attention_score": 80,
                    "motion_plan": {"camera_motion": "ken_burns_in"},
                },
                {
                    "scene_number": 2,
                    "scene_id": "s2",
                    "narration": "Notice this fossil near the equator.",
                    "length_sec": 4,
                    "expected_attention_score": 75,
                },
                {
                    "scene_number": 3,
                    "scene_id": "s3",
                    "narration": "This tiny transistor changed computing.",
                    "length_sec": 4,
                },
                {
                    "scene_number": 4,
                    "scene_id": "s4",
                    "narration": "Inside the factory, cameras are assembled.",
                    "length_sec": 5,
                },
            ]
        },
    }
    plan = build_cinematography_plan(candidate)
    assert len(plan.scenes) == 4
    assert plan.scenes[0].movement == "orbit"
    assert plan.scenes[1].movement == "slow_push_in"
    assert plan.scenes[2].movement == "macro_push_in"
    assert plan.scenes[3].movement == "establishing_wide"
    payload = plan.to_dict()
    assert payload["animation_handoff"]["scenes"]
    assert payload["motion_graph"]
    assert payload["timeline"]
    restored = CinematographyPlan.from_dict(payload)
    assert restored.scenes[0].movement == "orbit"


def test_animation_adapter_shapes():
    plan = build_cinematography_plan(
        {
            "title": "Orbit",
            "evidence_package": {
                "scenes": [{"scene_number": 1, "narration": "Earth orbits the Sun.", "length_sec": 4}]
            },
        }
    )
    mp_scenes = cinematography_to_motion_planner_scenes(plan)
    assert mp_scenes[0]["camera_motion"]
    assert mp_scenes[0]["easing"]
    cams = cinematography_to_true_motion_cameras(plan)
    assert cams[0]


def test_engine_attaches_cinematography_and_animation_handoff():
    engine = registry.get_engine("cinematography")
    assert engine is not None
    updates = engine.run(
        {
            "candidates": [
                {
                    "title": "Earth tilt",
                    "evidence_package": {
                        "scenes": [
                            {
                                "scene_number": 1,
                                "narration": "The Earth tilts toward the Sun.",
                                "length_sec": 5,
                                "expected_attention_score": 72,
                            }
                        ]
                    },
                    "visual_package": {
                        "scenes": [{"scene_number": 1, "narration": "The Earth tilts toward the Sun.", "asset_type": "atlas_image"}],
                        "visual_score": 70,
                    },
                }
            ],
            "subject": "seasons",
        }
    )
    cand = updates["candidates"][0]
    assert cand["cinematography_plan"]
    assert cand["animation_handoff"]["scenes"]
    assert cand["visual_package"]["scenes"][0].get("cinematography")
    assert updates["cinematography_summary"]["animation_ready"] is True


def test_workflow_order():
    for key in ("intelligence", "full_content"):
        steps = WORKFLOWS[key]
        assert steps.index("visual_intelligence") < steps.index("cinematography")
        assert steps.index("cinematography") < steps.index("voice_audio")
