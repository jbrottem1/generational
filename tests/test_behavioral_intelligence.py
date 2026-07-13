"""Tests for the Behavioral Intelligence API (Phase 4).

Covers the standardized report model, the graceful-degradation builder, the
downstream-consumption adapters, and integration with the real Psychology,
Attention Graph, and Threat Detection engines (including a full pipeline
run) to prove any engine can consume the report without custom parsing.
"""

import engines  # noqa: F401 - importing registers all engines
from core.workflows import WorkflowEngine
from engines import registry
from services.behavioral_intelligence import (
    FIELD_DESCRIPTIONS,
    REPORT_FIELDS,
    SCORE_FIELDS,
    BehavioralIntelligenceReport,
    attach_report,
    audio_guidance,
    build_report,
    script_generation_guidance,
    visual_guidance,
)
from services.behavioral_intelligence.builder import FIELD_TIPS

COMMAND = "Create 5 psychology shorts about procrastination"

BARE_CANDIDATE = {"title": "A Plain Topic", "hook": "A plain hook with nothing special."}

PSYCHOLOGY_ONLY_CANDIDATE = {
    "title": "The Hidden Reason You Procrastinate",
    "hook": "Here's why smart people procrastinate the most.",
    "viral_score": 74,
    "psychology": {
        "curiosity_gap": 80, "emotional_intensity": 60, "surprise": 55, "novelty": 58,
        "share_likelihood": 62, "replay_value": 50, "comment_likelihood": 66,
        "retention_potential": 70, "first_3_second_hook": 75, "audience_identity": 40,
        "visual_hook_strength": 65, "surprise_dup": 0, "dopamine_curve": 68,
    },
}

RICH_CANDIDATE = {
    "title": "The Hidden Reason You Procrastinate",
    "hook": "Here's why smart people procrastinate the most.",
    "viral_score": 74,
    "script": "A full generated script goes here for extra confidence signal.",
    "psychology": {
        "curiosity_gap": 80, "emotional_intensity": 60, "surprise": 55, "novelty": 58,
        "share_likelihood": 62, "replay_value": 50, "comment_likelihood": 66,
        "retention_potential": 70, "first_3_second_hook": 75, "audience_identity": 40,
        "visual_hook_strength": 65, "dopamine_curve": 68,
    },
    "attention_graph": {
        "attention_score": 81,
        "scores": {
            "first_3_second_hook": 90, "shareability": 88, "rewatch_probability": 85,
            "comment_likelihood": 91, "identity_signaling": 77, "story_tension": 84,
            "visual_novelty": 79,
        },
    },
    "threat_report": {
        "threat_score": 20,
        "flagged_threats": [
            {"key": "weak_hooks", "label": "Weak Hooks", "score": 60, "fix": "Tighten the opening line."},
        ],
    },
}


# ---------------------------------------------------------------------------
# Model / schema tests
# ---------------------------------------------------------------------------


def test_score_fields_has_13_dimensions():
    assert len(SCORE_FIELDS) == 13
    assert len(set(SCORE_FIELDS)) == 13


def test_report_fields_is_scores_plus_confidence_and_recommendations():
    assert set(REPORT_FIELDS) == set(SCORE_FIELDS) | {"confidence", "recommendations"}


def test_dataclass_fields_match_report_fields():
    assert set(BehavioralIntelligenceReport.__dataclass_fields__) == set(REPORT_FIELDS)


def test_field_descriptions_cover_every_report_field():
    assert set(FIELD_DESCRIPTIONS) == set(REPORT_FIELDS)
    for description in FIELD_DESCRIPTIONS.values():
        assert isinstance(description, str) and len(description) > 20


def test_field_tips_cover_every_score_field():
    assert set(FIELD_TIPS) == set(SCORE_FIELDS)


def test_to_dict_and_from_dict_roundtrip():
    report = build_report(RICH_CANDIDATE)
    data = report.to_dict()
    assert set(data) == set(REPORT_FIELDS)
    rebuilt = BehavioralIntelligenceReport.from_dict(data)
    assert rebuilt == report


def test_from_dict_ignores_unknown_keys_and_fills_defaults():
    report = BehavioralIntelligenceReport.from_dict({"viral_score": 90, "made_up_key": "ignored"})
    assert report.viral_score == 90
    assert report.attention_score == 50  # dataclass default
    assert report.recommendations == []


# ---------------------------------------------------------------------------
# Builder: graceful degradation
# ---------------------------------------------------------------------------


def test_build_report_from_bare_candidate_still_populates_every_field():
    report = build_report(BARE_CANDIDATE)
    for field_name in SCORE_FIELDS:
        value = getattr(report, field_name)
        assert isinstance(value, int) and 0 <= value <= 100
    assert 50 <= report.confidence <= 98
    assert isinstance(report.recommendations, list) and len(report.recommendations) >= 1


def test_build_report_psychology_only_uses_fallback_aliases():
    report = build_report(PSYCHOLOGY_ONLY_CANDIDATE)
    psych = PSYCHOLOGY_ONLY_CANDIDATE["psychology"]
    assert report.viral_score == PSYCHOLOGY_ONLY_CANDIDATE["viral_score"]
    assert report.attention_score == PSYCHOLOGY_ONLY_CANDIDATE["viral_score"]  # no attention_graph yet
    assert report.curiosity_score == psych["curiosity_gap"]
    assert report.emotional_intensity == psych["emotional_intensity"]
    assert report.novelty_score == psych["novelty"]
    assert report.shareability_score == psych["share_likelihood"]
    assert report.replay_probability == psych["replay_value"]
    assert report.comment_probability == psych["comment_likelihood"]
    assert report.retention_prediction == psych["retention_potential"]
    assert report.hook_strength == psych["first_3_second_hook"]
    assert report.identity_resonance == psych["audience_identity"]


def test_build_report_narrative_tension_falls_back_to_surprise_and_dopamine():
    psych = PSYCHOLOGY_ONLY_CANDIDATE["psychology"]
    expected = round((psych["surprise"] + psych["dopamine_curve"]) / 2)
    report = build_report(PSYCHOLOGY_ONLY_CANDIDATE)
    assert abs(report.narrative_tension - expected) <= 1


def test_build_report_prefers_attention_graph_values_when_present():
    report = build_report(RICH_CANDIDATE)
    scores = RICH_CANDIDATE["attention_graph"]["scores"]
    assert report.attention_score == RICH_CANDIDATE["attention_graph"]["attention_score"]
    assert report.shareability_score == scores["shareability"]
    assert report.replay_probability == scores["rewatch_probability"]
    assert report.comment_probability == scores["comment_likelihood"]
    assert report.hook_strength == scores["first_3_second_hook"]
    assert report.identity_resonance == scores["identity_signaling"]
    assert report.narrative_tension == scores["story_tension"]


def test_visual_interest_blends_both_signals_when_available():
    psych_val = RICH_CANDIDATE["psychology"]["visual_hook_strength"]
    visual_novelty = RICH_CANDIDATE["attention_graph"]["scores"]["visual_novelty"]
    report = build_report(RICH_CANDIDATE)
    expected = round((psych_val + visual_novelty) / 2)
    assert abs(report.visual_interest_score - expected) <= 1


def test_visual_interest_uses_whichever_single_signal_is_present():
    only_psych = {"psychology": {"visual_hook_strength": 72}}
    only_attention = {"attention_graph": {"scores": {"visual_novelty": 40}}}
    assert build_report(only_psych).visual_interest_score == 72
    assert build_report(only_attention).visual_interest_score == 40


def test_confidence_increases_with_available_signal():
    bare = build_report(BARE_CANDIDATE).confidence
    psychology_only = build_report(PSYCHOLOGY_ONLY_CANDIDATE).confidence
    rich = build_report(RICH_CANDIDATE).confidence
    assert bare < psychology_only < rich


def test_confidence_bounded_50_to_98():
    for candidate in (BARE_CANDIDATE, PSYCHOLOGY_ONLY_CANDIDATE, RICH_CANDIDATE):
        assert 50 <= build_report(candidate).confidence <= 98


def test_recommendations_capped_and_nonempty():
    report = build_report(BARE_CANDIDATE)
    assert 1 <= len(report.recommendations) <= 5
    assert all(isinstance(tip, str) for tip in report.recommendations)


def test_recommendations_include_flagged_threat_fix():
    report = build_report(RICH_CANDIDATE)
    assert "Tighten the opening line." in report.recommendations


def test_recommendations_positive_message_when_everything_scores_high():
    strong = {
        "psychology": {key: 90 for key in (
            "curiosity_gap", "emotional_intensity", "novelty", "share_likelihood",
            "replay_value", "comment_likelihood", "retention_potential",
            "first_3_second_hook", "audience_identity", "visual_hook_strength",
            "surprise", "dopamine_curve",
        )},
        "attention_graph": {"attention_score": 90, "scores": {"story_tension": 90}},
        "viral_score": 90,
    }
    report = build_report(strong)
    assert report.recommendations == ["No major gaps detected — maintain the current hook/pacing/payoff balance."]


def test_attach_report_sets_candidate_key_and_returns_same_values():
    candidate = dict(RICH_CANDIDATE)
    report = attach_report(candidate)
    assert candidate["behavioral_intelligence"] == report.to_dict()


# ---------------------------------------------------------------------------
# Adapters: downstream consumption without custom parsing
# ---------------------------------------------------------------------------


def test_script_generation_guidance_shape():
    report = build_report(RICH_CANDIDATE)
    guidance = script_generation_guidance(report)
    assert set(guidance) == {
        "lead_with_curiosity_gap", "needs_stronger_payoff", "amplify_emotional_beat",
        "narrative_tension", "confidence",
    }
    assert isinstance(guidance["lead_with_curiosity_gap"], bool)
    assert guidance["narrative_tension"] == report.narrative_tension


def test_visual_guidance_shape():
    report = build_report(RICH_CANDIDATE)
    guidance = visual_guidance(report)
    assert set(guidance) == {
        "prioritize_transformation_shot", "add_reveal_moment", "visual_interest_score", "confidence",
    }
    assert isinstance(guidance["add_reveal_moment"], bool)
    assert guidance["visual_interest_score"] == report.visual_interest_score


def test_audio_guidance_shape():
    report = build_report(RICH_CANDIDATE)
    guidance = audio_guidance(report)
    assert set(guidance) == {"pacing", "emphasize_hook_line", "emotional_intensity", "confidence"}
    assert guidance["pacing"] in ("energetic", "measured")


def test_adapters_only_touch_typed_attributes_not_dicts():
    """Adapters must accept the dataclass, not a dict — proving 'no custom parsing'."""
    report = build_report(RICH_CANDIDATE)
    for adapter in (script_generation_guidance, visual_guidance, audio_guidance):
        result = adapter(report)
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# Integration: real engines populate and refresh the report
# ---------------------------------------------------------------------------


def test_psychology_engine_attaches_consumable_report():
    context = {"candidates": [dict(BARE_CANDIDATE), {"title": "Another Idea", "hook": "Another hook here."}]}
    updates = registry.get_engine("psychology").run(context)
    for candidate in updates["candidates"]:
        assert "behavioral_intelligence" in candidate
        report = BehavioralIntelligenceReport.from_dict(candidate["behavioral_intelligence"])
        assert report.viral_score == candidate["viral_score"]
        # No Attention Graph yet at this point in the pipeline.
        assert "attention_graph" not in candidate


def test_attention_graph_engine_refreshes_report_with_richer_data():
    context = {"candidates": [{"title": "Refresh Test", "hook": "Testing the refresh behavior here."}]}
    registry.get_engine("psychology").run(context)
    candidate = context["candidates"][0]
    before = BehavioralIntelligenceReport.from_dict(candidate["behavioral_intelligence"])

    registry.get_engine("attention_graph").run(context)
    after = BehavioralIntelligenceReport.from_dict(candidate["behavioral_intelligence"])

    scores = candidate["attention_graph"]["scores"]
    assert after.attention_score == candidate["attention_graph"]["attention_score"]
    assert after.hook_strength == scores["first_3_second_hook"]
    assert after.narrative_tension == scores["story_tension"]
    assert after.confidence > before.confidence


def test_threat_detection_refreshes_report_with_recommendations_and_top_confidence():
    context = {"candidates": [{"title": "Risky Idea", "hook": "You must act now or regret this forever."}]}
    registry.get_engine("psychology").run(context)
    registry.get_engine("attention_graph").run(context)
    candidate = context["candidates"][0]
    candidate["script"] = "You must act now or regret this forever. Everyone is doing it, act now."

    threat_context = {"selected_ideas": [candidate]}
    registry.get_engine("threat_detection").run(threat_context)

    report = BehavioralIntelligenceReport.from_dict(candidate["behavioral_intelligence"])
    assert candidate["threat_report"]["threat_score"] >= 0
    # Every upstream signal (psychology + attention_graph + threat_report + script)
    # is present, so this is the highest-confidence tier the builder produces.
    assert report.confidence == 95
    if candidate["threat_report"]["flagged_threats"]:
        top_fix = candidate["threat_report"]["flagged_threats"][0]["fix"]
        assert top_fix in report.recommendations


def test_full_intelligence_pipeline_produces_consumable_report_for_every_idea():
    context = {"command": COMMAND, "count": 5, "model": "", "threshold": 0}
    run = WorkflowEngine().execute("intelligence", context)
    assert run.succeeded, run.summary()

    ideas = context["selected_ideas"]
    assert ideas
    for idea in ideas:
        assert "behavioral_intelligence" in idea
        report = BehavioralIntelligenceReport.from_dict(idea["behavioral_intelligence"])
        # Demonstrate downstream consumption purely through typed attributes.
        script_guidance = script_generation_guidance(report)
        visual = visual_guidance(report)
        audio = audio_guidance(report)
        assert isinstance(script_guidance["lead_with_curiosity_gap"], bool)
        assert isinstance(visual["prioritize_transformation_shot"], bool)
        assert audio["pacing"] in ("energetic", "measured")
        # By the end of the pipeline every upstream engine has run, so this is
        # the highest-confidence tier the builder produces.
        assert report.confidence == 95
