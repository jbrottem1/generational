"""Tests for AI Cinematic Director — no render engine duplication."""

from __future__ import annotations

from services.cinematic_director import (
    CAMERA_MOVES,
    COLOR_PALETTES,
    build_cinematic_direction_package,
    direct_candidate,
    validate_cinematic_direction,
)


def test_vocabularies_cover_mission():
    for cam in ("push_in", "pull_out", "dolly", "orbit", "handheld", "static", "macro", "overhead", "tracking"):
        assert cam in CAMERA_MOVES
    for niche in ("science", "biology", "history", "psychology", "finance", "nature", "technology"):
        assert niche in COLOR_PALETTES


def test_package_has_required_sections():
    pkg = build_cinematic_direction_package(
        {
            "title": "Why Octopuses Have Three Hearts",
            "script": (
                "Stop. An octopus has three hearts. "
                "Two push blood through the gills. The third feeds the body. "
                "When it swims, one heart nearly pauses. Follow for more."
            ),
            "niche": "biology",
        }
    )
    for key in (
        "shot_list",
        "camera_plan",
        "timing",
        "motion_plan",
        "lighting",
        "color",
        "transition_plan",
        "emotional_pacing",
        "director_notes",
        "validation",
    ):
        assert key in pkg
    assert pkg["shot_list"]
    assert pkg["validation"]["ok"] is True
    # Opening should be high intensity / non-static
    assert pkg["shot_list"][0]["camera"] != "static"
    assert pkg["shot_list"][0]["movement_score"] >= 50


def test_rejects_flat_plan():
    bad = {
        "shot_list": [
            {
                "scene_id": "s1",
                "camera": "static",
                "movement_score": 10,
                "duration_sec": 8,
                "emotional_pacing": {"intensity_pct": 10},
                "emphasis": {},
            }
        ]
    }
    v = validate_cinematic_direction(bad)
    assert v["ok"] is False
    assert v["hard_fails"]


def test_apply_enriches_visual_package_fields():
    directed = direct_candidate(
        {
            "title": "AI Explainer",
            "script": "Stop. AI is pattern matching. That claim survives the hype. Follow along.",
            "niche": "technology",
            "platform": "youtube_shorts",
        }
    )
    scenes = (directed.get("visual_package") or {}).get("scenes") or []
    assert scenes
    s0 = scenes[0]
    assert s0.get("camera_motion") or s0.get("camera")
    assert s0.get("lighting")
    assert s0.get("motion_intensity") is not None
    assert directed.get("cinematic_direction_package")
