"""Tests — Virtual Film Director (directs before Animation Engine)."""

from __future__ import annotations

from pathlib import Path

from services.animation_engine import attach_animation_package, build_animation_package
from services.virtual_film_director import (
    build_virtual_film_director_package,
    direct_candidate,
    review_shot_plan,
)


def _candidate() -> dict:
    return {
        "topic": "Why Fire Hydrants Are Different Colors",
        "world_package": {"world_type": "Suburban Neighborhood"},
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
    }


def test_vfd_artifacts(tmp_path):
    pkg = build_virtual_film_director_package(
        _candidate(), topic="Why Fire Hydrants Are Different Colors", write=True, out_dir=tmp_path
    )
    assert pkg["package_type"] == "VIRTUAL_FILM_DIRECTOR_PACKAGE"
    assert (tmp_path / "SHOT_PLAN.json").is_file()
    assert (tmp_path / "DIRECTOR_NOTES.md").is_file()
    assert (tmp_path / "CAMERA_SCRIPT.md").is_file()
    assert (tmp_path / "EMOTIONAL_TIMELINE.json").is_file()
    assert (tmp_path / "VISUAL_STORYBOARD.md").is_file()
    assert (tmp_path / "VIRTUAL_FILM_DIRECTOR_PACKAGE.json").is_file()
    assert len(pkg["shot_plan"]) == 4
    for s in pkg["shot_plan"]:
        assert s["scene_objective"]
        assert s["shot_language"]
        assert s["animation_seed"]["true_motion_camera"]
        assert s["animation_seed"]["narrative_purpose"]
        assert s["director_questions"]["ready"] is True
        assert s["composition"]["rule_of_thirds"] is True
    assert pkg["director_review"]["approved"] is True
    assert pkg["emotional_timeline"]["avoids_flatness"] is True


def test_direct_candidate_stamps_scenes():
    out = direct_candidate(_candidate(), write=False)
    assert out["directed_by_vfd"] is True
    assert out["prefer_vfd_shot_plan"] is True
    scene0 = out["visual_package"]["scenes"][0]
    assert scene0.get("vfd_seed")
    assert scene0.get("shot_language")
    assert scene0.get("vfd_camera_move")
    assert out["animation_handoff"]["virtual_film_director"] is True


def test_animation_engine_honors_vfd_seeds():
    directed = direct_candidate(_candidate(), write=False)
    pkg = build_animation_package(directed, topic=directed["topic"], write=False)
    out = attach_animation_package(directed, pkg)
    assert pkg.get("upstream_virtual_film_director", {}).get("present") is True
    assert pkg["upstream_virtual_film_director"]["honored_seeds"] >= 1
    # At least one scene should show VFD as camera source
    sources = [
        ((d.get("layers") or {}).get("camera") or {}).get("source")
        for d in pkg.get("scene_decisions") or []
    ]
    assert "virtual_film_director" in sources
    assert out["prefer_true_motion"] is True


def test_review_rejects_empty():
    gate = review_shot_plan([])
    assert gate["approved"] is False
    assert gate["decision"] == "REWRITE"
