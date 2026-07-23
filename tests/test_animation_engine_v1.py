"""Tests for Cinematic Animation Engine V2 — quality evolution of V1."""

from __future__ import annotations

from pathlib import Path

from engines.animation import AnimationEngine
from services.animation_engine import attach_animation_package, build_animation_package
from services.animation_engine.camera import choose_camera
from services.animation_engine.cinematic import plan_cinematic_intent
from services.animation_engine.intent import detect_characters, detect_world_type
from services.animation_engine.models import PACKAGE_VERSION
from services.animation_engine.score import quality_gate


def _candidate() -> dict:
    return {
        "topic": "Why Fire Hydrants Are Different Colors",
        "world_package": {"world_type": "Suburban Neighborhood", "theme": "irish countryside mist"},
        "visual_package": {
            "scenes": [
                {
                    "scene_number": 1,
                    "purpose": "hook",
                    "length_sec": 3.0,
                    "narration": "These colors could determine whether firefighters save your house.",
                    "subject": "fire hydrants",
                },
                {
                    "scene_number": 2,
                    "purpose": "story_beat",
                    "length_sec": 3.5,
                    "narration": "Each color indicates a flow rating firefighters read at a glance.",
                },
                {
                    "scene_number": 3,
                    "purpose": "story_beat",
                    "length_sec": 4.0,
                    "narration": "A forest of pipes under the street feeds two nearby hydrants differently.",
                },
                {
                    "scene_number": 4,
                    "purpose": "payoff",
                    "length_sec": 3.0,
                    "narration": "Flow rate matters when seconds decide if a house is saved.",
                },
            ]
        },
        "animation_handoff": {"provider": "Cinematography Engine", "scenes": []},
    }


def test_engine_is_ready_v2():
    eng = AnimationEngine()
    assert eng.is_ready() is True
    assert eng.key == "animation"
    assert eng.version.startswith("2.")


def test_build_package_cinematic_v2(tmp_path):
    cand = _candidate()
    pkg = build_animation_package(cand, topic=cand["topic"], write=True, out_path=tmp_path)
    assert pkg["package_type"] == "ANIMATION_PACKAGE"
    assert pkg["package_version"] == PACKAGE_VERSION
    assert pkg["package_version"].startswith("2.")
    assert pkg["scene_count"] == 4
    assert Path(pkg["path"]).is_file()
    for d in pkg["scene_decisions"]:
        assert d["layers"]["passes_motion_minimum"] is True
        assert "camera_movement" in d["layers"]["active_motion_classes"]
        assert d["layers"]["camera"]["forbid_static_lock"] is True
        assert d["layers"]["camera"]["narrative_purpose"]
        assert d["layers"]["camera"]["motivated"] is True
        assert d["layers"]["world"]["living_background"] is True
        assert d["layers"]["world"]["depth_layers"]
        assert d["layers"]["world"]["allow_abstract_geometry"] is False
        assert d["cinematic"]["emotion"]
        assert d["cinematic"]["lighting_mood"]
        assert d["cinematic"]["visual_moment"]
        assert d["layers"]["immersion"]["passed"] is True
        assert d["motion_effect"] != "static"
    cams = {d["layers"]["camera"]["camera_move"] for d in pkg["scene_decisions"]}
    assert len(cams) >= 3
    gate = pkg["quality_gate"]
    assert gate["passed"] is True
    assert gate["decision"] == "APPROVE"
    assert gate["engine_version"].startswith("2.")
    assert pkg["animation_excellence"]["animation_excellence_score"] >= 75
    assert (gate.get("metrics") or {}).get("immersion_pass_ratio", 0) >= 0.85


def test_cinematic_intent_and_motivated_camera():
    scene = {"purpose": "hook", "narration": "Wait — this secret could save your house."}
    cine = plan_cinematic_intent(scene, world_env="countryside", topic="hydrant")
    assert cine["emotion"] in {"curiosity", "tension", "focus", "awe"}
    assert cine["lighting_mood"]
    assert cine["shot_size"]
    cam = choose_camera(scene, scene_index=0, cinematic=cine)
    assert cam["narrative_purpose"]
    assert cam["forbid_purposeless_drift"] is True


def test_character_and_object_detection():
    scene = {
        "narration": "Firefighters open the hydrant valve as water pressure surges.",
        "subject": "hydrant",
    }
    chars = detect_characters(scene, topic="infrastructure")
    assert any(c["name"] == "firefighter" for c in chars)
    world = detect_world_type(
        {"world_package": {"world_type": "ocean research"}},
        {"narration": "Waves crash as the reef breathes."},
        topic="ocean currents",
    )
    assert world == "ocean"
    from services.animation_engine.intent import detect_object_animations

    objs = detect_object_animations(scene, topic="hydrant")
    assert objs and objs[0]["object"] == "hydrant"


def test_attach_enriches_visual_scenes_v2():
    cand = _candidate()
    pkg = build_animation_package(cand, topic=cand["topic"], write=False)
    out = attach_animation_package(cand, pkg)
    assert out["forbid_ken_burns_default"] is True
    assert out["prefer_true_motion"] is True
    assert out["cinematic_animation_v2"] is True
    scene0 = out["visual_package"]["scenes"][0]
    assert scene0["effect"]["effect"] == scene0["animation_effect"]
    assert scene0["effect"]["source"] == "animation_engine_v2"
    assert scene0["ken_burns"] is False
    assert scene0["true_motion"]["cinematic_v2"] is True
    assert scene0["true_motion"]["not_ken_burns_only"] is True
    assert out["animation_handoff"]["animation_engine_v2"] is True


def test_engine_run_attaches_package():
    ctx = {"candidates": [_candidate()], "topic": "Why Fire Hydrants Are Different Colors"}
    result = AnimationEngine().run(ctx)
    assert result["animation_summary"]["animation_status"] == "READY"
    assert result["animation_summary"]["version"].startswith("2.")
    assert ctx["candidates"][0].get("ANIMATION_PACKAGE")
    assert result.get("animation_excellence_score", 0) >= 70


def test_quality_gate_rejects_static_lock():
    decisions = [
        {
            "scene_number": 1,
            "duration_sec": 5,
            "layers": {
                "active_motion_classes": [],
                "passes_motion_minimum": False,
                "camera": {"camera_move": "static"},
                "world": {"living_background": False, "allow_abstract_geometry": True},
                "immersion": {"passed": False, "failing": ["world_feels_alive"]},
            },
        }
    ]
    gate = quality_gate(decisions)
    assert gate["passed"] is False
    assert gate["decision"] == "REJECT"
    assert gate.get("re_render_scenes")
