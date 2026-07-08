"""Tests for the Psychology & Virality Engine (18-dimension ViralScore + report)."""

import engines  # noqa: F401 - importing registers all engines
from core.workflows import WorkflowEngine
from engines import registry
from engines.psychology import (
    VIRAL_SCORE_WEIGHTS,
    build_report,
    score_dimensions,
    viral_score,
)

EXPECTED_DIMENSIONS = {
    "curiosity_gap",
    "emotional_intensity",
    "surprise",
    "novelty",
    "fear",
    "humor",
    "satisfaction",
    "retention_potential",
    "replay_value",
    "comment_likelihood",
    "share_likelihood",
    "controversy",
    "visual_hook_strength",
    "first_3_second_hook",
    "dopamine_curve",
    "information_density",
    "audience_identity",
    "community_appeal",
}

COMMAND = "Create 5 psychology shorts about procrastination"


def test_all_18_dimensions_present_and_bounded():
    scores = score_dimensions("The secret truth about procrastination — a study proves you were wrong")
    assert set(scores) == EXPECTED_DIMENSIONS == set(VIRAL_SCORE_WEIGHTS)
    for value in scores.values():
        assert 0 <= value <= 100


def test_weights_sum_to_one():
    assert round(sum(VIRAL_SCORE_WEIGHTS.values()), 6) == 1.0


def test_scoring_is_deterministic():
    text = "Why does procrastination happen to smart people?"
    assert score_dimensions(text) == score_dimensions(text)


def test_viral_score_bounded_0_to_100():
    for text in (
        "The secret truth nobody tells you — a shocking study you won't believe",
        "A plain statement about a topic.",
        "",
    ):
        score = viral_score(score_dimensions(text))
        assert 0 <= score <= 100


def test_curiosity_and_hook_words_raise_curiosity_gap():
    bland = score_dimensions("A video about procrastination habits and daily routines")
    curious = score_dimensions("The hidden secret nobody tells you about why you procrastinate")
    assert curious["curiosity_gap"] > bland["curiosity_gap"]


def test_fear_words_raise_fear_dimension():
    bland = score_dimensions("A calm explanation of a normal daily habit")
    fearful = score_dimensions("Warning: this deadly habit is destroying you and it's too late to avoid it")
    assert fearful["fear"] > bland["fear"]


def test_humor_words_raise_humor_dimension():
    bland = score_dimensions("A serious explanation of a scientific concept")
    funny = score_dimensions("This hilarious and ridiculous prank is the funniest thing you'll see today")
    assert funny["humor"] > bland["humor"]


def test_controversy_is_bounded_by_platform_safety():
    loaded = score_dimensions(
        "Controversial unpopular opinion: everyone is wrong, hot take, banned debate, disagree"
    )
    # Bounded even when every controversy trigger word is present.
    assert loaded["controversy"] <= 75


def test_short_punchy_hook_scores_higher_first_3_second_hook():
    punchy = score_dimensions("Wait, what? This changes everything.")
    rambling = score_dimensions(
        "So here is a very long and detailed opening line that goes on and on before making any point at all"
    )
    assert punchy["first_3_second_hook"] > rambling["first_3_second_hook"]


def test_viral_score_report_has_strengths_and_weaknesses():
    text = "The hidden secret nobody tells you about procrastination — a shocking study proves you were wrong"
    dimensions = score_dimensions(text)
    score = viral_score(dimensions)
    report = build_report(dimensions, score, title="The Hidden Secret", hook=text)

    assert report["viral_score"] == score
    assert report["tier"]
    assert len(report["strengths"]) == 3
    assert len(report["weaknesses"]) == 3
    assert set(report["dimension_notes"]) == EXPECTED_DIMENSIONS
    for item in report["strengths"] + report["weaknesses"]:
        assert item["dimension"]
        assert item["note"]
        assert 0 <= item["score"] <= 100
    assert "Hidden Secret" in report["summary"] or "hidden secret" in report["summary"].lower()


def test_psychology_engine_attaches_score_and_report_to_every_candidate():
    context = {
        "candidates": [
            {"title": "The Hidden Secret", "hook": "Nobody tells you this.", "angle": "The hidden truth"},
            {"title": "A Plain Title", "hook": "This is a plain hook.", "angle": "plain"},
        ]
    }
    updates = registry.get_engine("psychology").run(context)
    for candidate in updates["candidates"]:
        assert 0 <= candidate["psychology_score"] <= 100
        assert candidate["viral_score"] == candidate["psychology_score"]
        assert set(candidate["psychology"]) == EXPECTED_DIMENSIONS
        report = candidate["psychology_report"]
        assert report["viral_score"] == candidate["viral_score"]
        assert report["strengths"] and report["weaknesses"]
    assert "psychology_summary" in updates
    assert updates["psychology_summary"]["scored"] == 2


def test_psychology_engine_handles_empty_candidates():
    updates = registry.get_engine("psychology").run({"candidates": []})
    assert updates["candidates"] == []
    assert updates["psychology_summary"]["average_viral_score"] == 0


def test_intelligence_pipeline_attaches_viral_score_to_every_idea():
    context = {"command": COMMAND, "count": 5, "model": "", "threshold": 0}
    run = WorkflowEngine().execute("intelligence", context)
    assert run.succeeded, run.summary()

    for idea in context["ideas"]:
        assert 0 <= idea["viral_score"] <= 100
        assert idea["psychology_report"]["viral_score"] == idea["viral_score"]
        scores = idea["scores"]
        assert "virality" in scores
        assert 0 <= scores["virality"] <= 100
