"""Tests for Animation Studio storyboard + QC gate (additive pipeline expansion)."""

from __future__ import annotations

from services.asset_production.animation_qc import run_animation_qc
from services.asset_production.storyboard import build_storyboard_package


def test_storyboard_answers_required_questions():
    scenes = [
        {
            "scene_number": 1,
            "purpose": "hook",
            "narration": "The ocean is glowing.",
            "length_sec": 3.0,
            "emotion": "curious",
        },
        {
            "scene_number": 2,
            "purpose": "story_beat",
            "narration": "Life makes its own light.",
            "length_sec": 4.0,
        },
    ]
    pkg = build_storyboard_package(scenes, title="Test", character_id="CHAR-DASH")
    assert pkg["beat_count"] == 2
    beat = pkg["beats"][0]
    for key in ("who", "doing", "moving", "camera", "emotion", "transition_out"):
        assert key in beat and beat[key], key
    assert beat["camera"] == "push_in"
    assert "CHAR-DASH" in beat["who"]
    assert beat["environment_fx"]


def test_animation_qc_rejects_color_bed():
    report = run_animation_qc(
        {
            "scene_breakdown": [{"scene_number": 1, "length_sec": 2, "narration": "x", "camera_motion": "push"}],
            "storyboard_package": {"beats": [{"camera": "push_in", "environment_fx": ["ENVFX-particle-field"]}]},
            "generated_images": [{"path": "data/x.png", "placeholder": False}],
            "render_package": {"assembly": {"visual_count": 1, "color_bed": True}},
        }
    )
    assert report["passed"] is False
    assert any(c["name"] == "no_color_bed" and not c["ok"] for c in report["checks"])


def test_animation_qc_passes_motion_ready_asset():
    scenes = [
        {
            "scene_number": 1,
            "length_sec": 4.0,
            "narration": "Hello",
            "camera_motion": "follow walk",
            "animation_components": ["walk_cycle"],
            "environment_fx": ["ENVFX-particle-field"],
            "effect": {"effect": "cinematic_push_in"},
            "resolved_asset": {"path": "data/a.png", "placeholder": False},
        }
    ]
    board = build_storyboard_package(scenes)
    report = run_animation_qc(
        {
            "scene_breakdown": scenes,
            "storyboard_package": board,
            "character_id": "CHAR-DASH",
            "true_motion": {"motion_class": "true_layered_animation"},
            "generated_images": [{"path": "data/a.png", "placeholder": False}],
            "render_package": {
                "assembly": {
                    "visual_count": 3,
                    "color_bed": False,
                    "true_motion": {"motion_class": "true_layered_animation"},
                    "log": ["scene→clip a.png effect=cinematic_push_in d=4.00s"],
                }
            },
        }
    )
    assert report["passed"] is True, report.get("errors")
