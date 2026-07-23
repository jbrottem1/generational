"""Cinematic Direction Studio — intentional direction before render."""

from __future__ import annotations

from services.cinematic_direction_studio import (
    attach_cinematic_direction,
    build_director_package,
    build_episode_director_package,
    validate_director_package,
    validate_episode_direction,
)


def test_director_package_objectives():
    pkg = build_director_package(
        scene={
            "scene_number": 2,
            "narration": "Look through the microscope and explain what clarity means.",
            "length_sec": 4.0,
            "purpose": "story_beat",
            "studio_character_id": "DOCTOR_001",
        },
        scene_index=1,
        total_scenes=4,
        location="LOC-GMRI",
    )
    assert pkg["package_type"] == "DIRECTOR_PACKAGE"
    assert pkg["philosophy"]["not_a_renderer"] is True
    assert pkg["story_objective"]
    assert pkg["emotional_objective"]
    assert pkg["actor_objective"]
    assert pkg["camera_objective"]
    assert pkg["lighting_objective"]
    assert pkg["editing_objective"]
    assert pkg["music_objective"]
    assert len(pkg["actor_direction"]["beats"]) >= 3
    assert pkg["camera_language"]["motivated"] is True
    assert pkg["validation"]["ok"] is True


def test_episode_arc_and_variety():
    scenes = [
        {"purpose": "hook", "length_sec": 3.0, "narration": "Come see this."},
        {
            "purpose": "story_beat",
            "length_sec": 4.0,
            "narration": "Look through the microscope carefully.",
        },
        {
            "purpose": "story_beat",
            "length_sec": 3.5,
            "narration": "Pause and think about what this means.",
        },
        {
            "purpose": "payoff",
            "length_sec": 3.0,
            "narration": "Together we can choose hope.",
        },
    ]
    episode = build_episode_director_package(scenes, topic="Test", location="LOC-GMRI")
    assert episode["validation"]["ok"] is True
    shots = [s["shot_type"] for s in episode["scenes"]]
    assert len(set(shots)) >= 2
    assert episode["emotional_timeline"]["has_arc"] is True


def test_rejects_identical_framing():
    review = validate_episode_direction(
        {
            "scenes": [
                {"shot_type": "medium", "emotional_objective": "curiosity"},
                {"shot_type": "medium", "emotional_objective": "curiosity"},
                {"shot_type": "medium", "emotional_objective": "curiosity"},
            ],
            "emotional_timeline": {"has_arc": False},
        }
    )
    assert review["ok"] is False
    assert "identical_framing_every_scene" in review["rejects_hit"]


def test_attach_stamps_animation_seeds():
    scenes = attach_cinematic_direction(
        [
            {
                "scene_number": 1,
                "narration": "Walk to the bench and teach.",
                "length_sec": 3.5,
                "studio_character_id": "DOCTOR_001",
            }
        ],
        location="LOC-GMRI",
    )
    row = scenes[0]
    assert row["director_package"]["validation"]["ok"]
    assert row["director_emotion"]
    assert row["true_motion"]["cinematic_direction"] is True
    assert row["vfd_seed"]["cinematic_direction_studio"] is True
    assert validate_director_package(row["director_package"])["ok"]
