"""Voice Studio unit tests — no live API credits."""

from __future__ import annotations

from services.voice_studio.content_routing import select_narrator_profile
from services.voice_studio.profiles import NARRATOR_PROFILE_CATALOG, normalize_profile_key
from services.voice_studio.recommend import recommend_voices_for_profiles
from services.voice_studio.scoring import educational_shorts_score, score_voice_dimensions


def test_all_suggested_profiles_exist():
    expected = {
        "professor",
        "documentary",
        "storyteller",
        "science_educator",
        "technology_explainer",
        "history_narrator",
        "calm_instructor",
        "energetic_presenter",
    }
    assert expected.issubset(set(NARRATOR_PROFILE_CATALOG))


def test_aliases_and_content_routing():
    assert normalize_profile_key("Calm Instructor") == "calm_instructor"
    assert normalize_profile_key("energetic_explainer") == "energetic_explainer"
    assert normalize_profile_key("Energetic Presenter") == "energetic_presenter"
    sel = select_narrator_profile(content_type="science")
    assert sel["profile_key"] == "science_educator"
    sel2 = select_narrator_profile(content_type="ai", niche="technology")
    assert sel2["profile_key"] == "technology_explainer"


def test_scoring_and_shorts_recommendations():
    voices = [
        {"voice_id": "a", "name": "Alice - Clear, Engaging Educator", "category": "premade"},
        {"voice_id": "b", "name": "Liam - Energetic, Social Media Creator", "category": "premade"},
        {"voice_id": "c", "name": "Bill - Wise, Mature, Balanced", "category": "premade"},
    ]
    scored = [score_voice_dimensions(v) for v in voices]
    assert all("dimensions" in s for s in scored)
    assert all(0 <= s["overall"] <= 10 for s in scored)
    recs = recommend_voices_for_profiles(scored, top_n=2)
    assert "professor" in recs["by_profile"]
    assert len(recs["educational_youtube_shorts_top3"]) <= 3
    assert educational_shorts_score(scored[0]) > 0


def test_profile_catalog_has_no_hardcoded_voice_ids():
    for key, meta in NARRATOR_PROFILE_CATALOG.items():
        assert "voice_id" not in meta
        assert meta.get("env_key")
