"""Creative Excellence — attention craft reviews (not engineering QA)."""

from __future__ import annotations

from services.creative_excellence import review_production_creative_excellence
from services.creative_excellence.recommendation import pick_single_recommendation
from services.creative_excellence.scorecard import build_creative_excellence_scorecard


def test_scorecard_separates_engineering_from_creative():
    card = build_creative_excellence_scorecard(
        {
            "topic": "What gravity actually does",
            "hook": "Stop — gravity is not what you were taught.",
            "script": "Wait — before you disagree. The truth most videos skip. Share this myth.",
            "psychology": {"dimensions": {"curiosity_gap": 88, "emotional_intensity": 80, "share_likelihood": 82}},
            "visual_package": {
                "scenes": [
                    {"n": 1, "camera": "push_in", "lighting": "documentary", "environment": "lab"},
                    {"n": 2, "camera": "orbit", "lighting": "scientific"},
                    {"n": 3, "camera": "macro"},
                ]
            },
            "world_package": {"world_id": "WORLD-SCIENCE_LAB", "continuity": {"single_world": True}},
            "cinematic_direction_package": {
                "shot_list": [
                    {"movement_score": 80},
                    {"movement_score": 70},
                    {"movement_score": 75},
                ]
            },
            "voice_package": {"provider": "elevenlabs", "placeholder": False, "path": "x.mp3"},
            "structured_script": {"call_to_action": "Share the myth you believed — tag a friend"},
        },
        production_report={
            "hook_score": 92,
            "visual_score": 88,
            "narration_score": 85,
            "audio_score": 84,
            "retention_prediction": 86,
            "shareability": 88,
            "educational_accuracy": 90,
            "animation_score": 90,
            "length_sec": 45,
            "export_validation": {"ok": True, "hard_fails": []},
            "platform_readiness": True,
            "stages_completed": 16,
        },
    )
    assert "engineering_quality" in card["dimensions"]
    assert "creative_excellence_score" in card
    assert isinstance(card["creative_excellence_score"], (int, float))
    assert set(card["timeline"]) >= {
        "first_3_seconds",
        "first_6_seconds",
        "first_15_seconds",
        "middle_pacing",
        "ending",
    }
    assert "would_stop_scrolling" in card["viewer_outcomes"]
    v2 = card["v2_quality"]["scores"]
    for key in (
        "visual_quality",
        "motion_quality",
        "storytelling",
        "educational_clarity",
        "hook",
        "viewer_retention",
        "audio_quality",
        "overall_professionalism",
    ):
        assert key in v2


def test_exactly_one_recommendation():
    rec = pick_single_recommendation(
        segments={
            "first_3_seconds": 60,
            "first_6_seconds": 70,
            "first_15_seconds": 75,
            "middle_pacing": 80,
            "ending": 85,
        },
        craft={
            "viewer_emotion": 70,
            "curiosity": 68,
            "payoff": 72,
            "visual_movement": 65,
            "narration_energy": 74,
        },
    )
    assert rec["element"]
    assert rec["recommendation"]
    assert "expected_retention_gain" in rec
    assert rec.get("principle") or rec.get("mode")


def test_full_review_writes_history(tmp_path, monkeypatch):
    import services.creative_excellence.review as rev

    monkeypatch.setattr(rev, "HISTORY_PATH", tmp_path / "history.json")
    monkeypatch.setattr(rev, "OUT_ROOT", tmp_path / "out")
    result = review_production_creative_excellence(
        {"topic": "Black holes", "hook": "Stop — this is not empty space.", "script": "Wait. The secret most people miss."},
        production_report={
            "hook_score": 70,
            "visual_score": 65,
            "narration_score": 70,
            "retention_prediction": 68,
            "shareability": 60,
            "educational_accuracy": 80,
            "animation_score": 60,
            "export_validation": {"ok": False, "hard_fails": ["missing_audio"]},
        },
        production_id="test_ce_1",
        topic="Black holes",
    )
    assert result["single_recommendation"]["element"]
    assert (tmp_path / "history.json").exists()
    assert result.get("markdown_path")
