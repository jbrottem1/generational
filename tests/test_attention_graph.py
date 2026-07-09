"""Tests for the Attention Graph engine (Phase 2 — Attention Intelligence)."""

import engines  # noqa: F401 - importing registers all engines
from core.workflows import WORKFLOWS, WorkflowEngine
from engines import registry
from engines.attention_graph import (
    ATTENTION_DIMENSIONS,
    ATTENTION_GRAPH_WEIGHTS,
    ATTENTION_LABELS,
    attention_score,
    build_attention_graph,
    build_radar_chart,
    build_recommendations,
    score_attention_dimensions,
)

EXPECTED_DIMENSIONS = {
    "first_3_second_hook",
    "curiosity_gap",
    "dopenness",
    "emotional_intensity",
    "story_tension",
    "surprise",
    "visual_novelty",
    "shareability",
    "rewatch_probability",
    "comment_likelihood",
    "identity_signaling",
    "tribal_engagement",
}

COMMAND = "Create 5 psychology shorts about procrastination"


def test_exactly_12_dimensions():
    assert set(ATTENTION_DIMENSIONS) == EXPECTED_DIMENSIONS
    assert len(ATTENTION_DIMENSIONS) == 12
    assert set(ATTENTION_GRAPH_WEIGHTS) == EXPECTED_DIMENSIONS
    assert set(ATTENTION_LABELS) == EXPECTED_DIMENSIONS


def test_weights_sum_to_one():
    assert round(sum(ATTENTION_GRAPH_WEIGHTS.values()), 6) == 1.0


def test_dimension_scores_bounded_0_to_100():
    scores = score_attention_dimensions("The hidden secret nobody tells you about procrastination")
    assert set(scores) == EXPECTED_DIMENSIONS
    for value in scores.values():
        assert 0 <= value <= 100


def test_scoring_is_deterministic():
    text = "Why does procrastination happen to smart people?"
    assert score_attention_dimensions(text) == score_attention_dimensions(text)


def test_attention_score_bounded_0_to_100():
    for text in (
        "The secret truth nobody tells you — a shocking twist you won't believe",
        "A plain statement about a topic.",
        "",
    ):
        score = attention_score(score_attention_dimensions(text))
        assert 0 <= score <= 100


def test_dopenness_rewards_open_loop_language():
    bland = score_attention_dimensions("A video about procrastination habits and daily routines")
    open_loop = score_attention_dimensions("Wait for it — here's what happens next, guess what occurs")
    assert open_loop["dopenness"] > bland["dopenness"]


def test_story_tension_rewards_turning_point_language():
    flat = score_attention_dimensions("A calm explanation of a normal daily habit")
    tense = score_attention_dimensions("Everything was fine until suddenly it all changed in an instant")
    assert tense["story_tension"] > flat["story_tension"]


def test_visual_novelty_rewards_visual_transformation_language():
    plain = score_attention_dimensions("A description of an abstract concept")
    visual = score_attention_dimensions("Watch this before and after transformation in slow motion close-up")
    assert visual["visual_novelty"] > plain["visual_novelty"]


def test_radar_chart_labels_and_scores_align_in_order():
    dimensions = score_attention_dimensions("The hidden secret about procrastination")
    radar = build_radar_chart(dimensions)
    assert radar["labels"] == [ATTENTION_LABELS[key] for key in ATTENTION_DIMENSIONS]
    assert radar["scores"] == [dimensions[key] for key in ATTENTION_DIMENSIONS]
    assert len(radar["labels"]) == len(radar["scores"]) == 12


def test_recommendations_present_for_every_dimension():
    dimensions = score_attention_dimensions("A plain, unremarkable statement about a topic")
    recommendations = build_recommendations(dimensions)
    assert set(recommendations) == EXPECTED_DIMENSIONS
    for tip in recommendations.values():
        assert isinstance(tip, str) and len(tip) > 10


def test_build_attention_graph_full_payload_shape():
    graph = build_attention_graph(title="The Hidden Secret", hook="Nobody tells you this about procrastination.")
    assert set(graph) == {"scores", "attention_score", "radar_chart", "recommendations"}
    assert set(graph["scores"]) == EXPECTED_DIMENSIONS
    assert 0 <= graph["attention_score"] <= 100
    assert len(graph["radar_chart"]["labels"]) == 12
    assert set(graph["recommendations"]) == EXPECTED_DIMENSIONS


def test_engine_attaches_attention_graph_to_every_candidate():
    context = {
        "candidates": [
            {"title": "The Hidden Secret", "hook": "Nobody tells you this.", "angle": "The hidden truth"},
            {"title": "A Plain Title", "hook": "This is a plain hook.", "angle": "plain"},
        ]
    }
    updates = registry.get_engine("attention_graph").run(context)
    for candidate in updates["candidates"]:
        graph = candidate["attention_graph"]
        assert set(graph["scores"]) == EXPECTED_DIMENSIONS
        assert 0 <= graph["attention_score"] <= 100
        assert len(graph["radar_chart"]["scores"]) == 12
        assert len(graph["recommendations"]) == 12
    assert updates["attention_graph_summary"]["scored"] == 2


def test_engine_handles_empty_candidates():
    updates = registry.get_engine("attention_graph").run({"candidates": []})
    assert updates["candidates"] == []
    assert updates["attention_graph_summary"]["average_attention_score"] == 0


def test_attention_graph_registered_in_intelligence_workflow():
    assert "attention_graph" in WORKFLOWS["intelligence"]
    assert "attention_graph" in WORKFLOWS["full_content"]


def test_intelligence_pipeline_attaches_attention_graph_to_every_idea():
    context = {"command": COMMAND, "count": 5, "model": "", "threshold": 0}
    run = WorkflowEngine().execute("intelligence", context)
    assert run.succeeded, run.summary()

    for idea in context["ideas"]:
        graph = idea["attention_graph"]
        assert set(graph["scores"]) == EXPECTED_DIMENSIONS
        assert 0 <= graph["attention_score"] <= 100
        assert len(graph["radar_chart"]["labels"]) == 12
        assert len(graph["recommendations"]) == 12
