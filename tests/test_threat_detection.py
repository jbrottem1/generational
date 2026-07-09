"""Tests for the Psychology Threat Detection engine (Phase 3 — Threat Intelligence)."""

import engines  # noqa: F401 - importing registers all engines
from core.workflows import WORKFLOWS, WorkflowEngine
from engines import registry
from engines.threat_detection import (
    THREAT_FIXES,
    THREAT_KEYS,
    THREAT_LABELS,
    THREAT_WEIGHTS,
    build_flagged_threats,
    build_threat_report,
    overall_threat_score,
    score_threats,
)

COMMAND = "Create 5 psychology shorts about procrastination"

CLEAN_IDEA = {
    "title": "Why Smart People Procrastinate",
    "hook": "Here's why procrastination happens to smart people the most.",
    "script": (
        "Here's why procrastination happens to smart people the most. Turns out, "
        "the reason is fear of failure, not laziness. Here's how to test it: try "
        "one task for two minutes. That's the answer researchers found."
    ),
    "cta": "Try it today and tell us what happens.",
    "thumbnail_concept": "Close-up of a smart person staring at a clock, procrastination theme.",
    "psychology": {
        "curiosity_gap": 70, "satisfaction": 68, "dopamine_curve": 72,
        "first_3_second_hook": 80, "surprise": 65, "novelty": 60,
        "retention_potential": 75, "controversy": 30, "fear": 30,
    },
    "retention_checkpoints": [{"at_pct": 25}, {"at_pct": 50}, {"at_pct": 75}],
    "estimated_runtime_sec": 25,
}

RISKY_IDEA = {
    "title": "You Must Act Now Or Regret This Forever",
    "hook": "In this video we talk about a shocking secret nobody tells you.",
    "script": (
        "In this video we talk about a shocking secret nobody tells you. "
        "Everyone is doing it, you'll regret it, act now before it's too late. "
        "This is guaranteed to kill your productivity — it's basically a weapon "
        "against your life. You must trust me, no one else will tell you this."
    ),
    "cta": "Act now or you'll regret it forever.",
    "thumbnail_concept": "A red warning triangle on a plain background.",
    "psychology": {
        "curiosity_gap": 85, "satisfaction": 20, "dopamine_curve": 15,
        "first_3_second_hook": 20, "surprise": 20, "novelty": 15,
        "retention_potential": 20, "controversy": 90, "fear": 90,
    },
    "retention_checkpoints": [],
    "estimated_runtime_sec": 45,
}


def _run_pipeline(threshold=0):
    context = {"command": COMMAND, "count": 5, "model": "", "threshold": threshold}
    run = WorkflowEngine().execute("intelligence", context)
    assert run.succeeded, run.summary()
    return context


def test_exactly_10_threat_keys():
    assert len(THREAT_KEYS) == 10
    assert set(THREAT_WEIGHTS) == set(THREAT_KEYS)
    assert set(THREAT_LABELS) == set(THREAT_KEYS)
    assert set(THREAT_FIXES) == set(THREAT_KEYS)


def test_expected_threat_categories_present():
    expected = {
        "clickbait_without_payoff", "low_dopamine_pacing", "weak_hooks",
        "viewer_fatigue", "thumbnail_mismatch", "predictable_scripting",
        "retention_cliff_risk", "platform_policy_risk", "manipulative_language",
        "repetitive_content",
    }
    assert set(THREAT_KEYS) == expected


def test_weights_sum_to_one():
    assert round(sum(THREAT_WEIGHTS.values()), 6) == 1.0


def test_threat_scores_bounded_0_to_100():
    for idea in (CLEAN_IDEA, RISKY_IDEA):
        threats = score_threats(idea, [idea])
        assert set(threats) == set(THREAT_KEYS)
        for value in threats.values():
            assert 0 <= value <= 100


def test_scoring_is_deterministic():
    assert score_threats(CLEAN_IDEA, [CLEAN_IDEA]) == score_threats(CLEAN_IDEA, [CLEAN_IDEA])


def test_risky_idea_scores_worse_overall_than_clean_idea():
    clean_score = overall_threat_score(score_threats(CLEAN_IDEA, [CLEAN_IDEA]))
    risky_score = overall_threat_score(score_threats(RISKY_IDEA, [RISKY_IDEA]))
    assert risky_score > clean_score


def test_weak_hooks_inverts_hook_strength():
    strong_hook = {**CLEAN_IDEA, "psychology": {**CLEAN_IDEA["psychology"], "first_3_second_hook": 90}}
    weak_hook = {**CLEAN_IDEA, "psychology": {**CLEAN_IDEA["psychology"], "first_3_second_hook": 10}}
    assert score_threats(weak_hook, [weak_hook])["weak_hooks"] > score_threats(strong_hook, [strong_hook])["weak_hooks"]


def test_clickbait_without_payoff_flags_high_pull_with_no_resolution():
    teased_no_payoff = {
        "hook": "The secret nobody tells you",
        "script": "The secret nobody tells you about this topic and how it affects your life every single day.",
        "psychology": {"curiosity_gap": 90, "satisfaction": 20},
    }
    resolved = {
        "hook": "The secret nobody tells you",
        "script": "The secret nobody tells you is this: here's why it happens and here's how to fix it, the answer is simple.",
        "psychology": {"curiosity_gap": 90, "satisfaction": 20},
    }
    threats_teased = score_threats(teased_no_payoff, [teased_no_payoff])
    threats_resolved = score_threats(resolved, [resolved])
    assert threats_teased["clickbait_without_payoff"] > threats_resolved["clickbait_without_payoff"]


def test_platform_policy_risk_flags_risky_language():
    safe = {"title": "A calm topic", "hook": "A gentle explanation", "script": "Nothing risky here at all.", "psychology": {}}
    risky = {"title": "A weapon", "hook": "This is deadly and illegal", "script": "It involves a weapon and violence.", "psychology": {}}
    assert score_threats(risky, [risky])["platform_policy_risk"] > score_threats(safe, [safe])["platform_policy_risk"]


def test_manipulative_language_flags_pressure_phrases():
    honest = {"hook": "Here is a helpful tip", "script": "This tip may help you.", "cta": "Consider trying it."}
    manipulative = {
        "hook": "You must act now",
        "script": "Everyone is doing it, don't miss out, act now before it's too late.",
        "cta": "Act now or you'll regret it.",
    }
    assert score_threats(manipulative, [manipulative])["manipulative_language"] > score_threats(honest, [honest])["manipulative_language"]


def test_thumbnail_mismatch_flags_unrelated_thumbnail():
    matched = {"title": "Procrastination Secrets", "hook": "Why you procrastinate", "thumbnail_concept": "A person procrastinating, secrets text overlay"}
    mismatched = {"title": "Procrastination Secrets", "hook": "Why you procrastinate", "thumbnail_concept": "A random unrelated beach sunset photo"}
    assert score_threats(mismatched, [mismatched])["thumbnail_mismatch"] > score_threats(matched, [matched])["thumbnail_mismatch"]


def test_thumbnail_mismatch_neutral_when_missing():
    no_thumbnail = {"title": "A Title", "hook": "A hook"}
    assert score_threats(no_thumbnail, [no_thumbnail])["thumbnail_mismatch"] == 50


def test_predictable_scripting_flags_generic_openers():
    generic = {"hook": "intro", "script": "In this video we're going to talk about a topic. So basically, as we all know, things happen.", "psychology": {"surprise": 40, "novelty": 40}}
    fresh = {"hook": "intro", "script": "Everything changed the moment researchers found the opposite was true.", "psychology": {"surprise": 80, "novelty": 80}}
    assert score_threats(generic, [generic])["predictable_scripting"] > score_threats(fresh, [fresh])["predictable_scripting"]


def test_retention_cliff_risk_flags_missing_checkpoints_on_long_runtime():
    no_checkpoints = {"psychology": {"retention_potential": 50}, "retention_checkpoints": [], "estimated_runtime_sec": 30}
    full_checkpoints = {"psychology": {"retention_potential": 50}, "retention_checkpoints": [1, 2, 3], "estimated_runtime_sec": 30}
    assert score_threats(no_checkpoints, [no_checkpoints])["retention_cliff_risk"] > score_threats(full_checkpoints, [full_checkpoints])["retention_cliff_risk"]


def test_viewer_fatigue_flags_word_repetition():
    repetitive = {"script": "problem problem problem problem is that people people people struggle daily."}
    varied = {"script": "The core issue is that people often struggle to build consistent daily habits."}
    assert score_threats(repetitive, [repetitive])["viewer_fatigue"] > score_threats(varied, [varied])["viewer_fatigue"]


def test_low_dopamine_pacing_rewards_checkpoints():
    flat = {"psychology": {"dopamine_curve": 30}, "retention_checkpoints": []}
    paced = {"psychology": {"dopamine_curve": 30}, "retention_checkpoints": [1, 2, 3]}
    assert score_threats(flat, [flat])["low_dopamine_pacing"] > score_threats(paced, [paced])["low_dopamine_pacing"]


def test_repetitive_content_flags_near_duplicate_batch():
    a = {"title": "The Hidden Truth About Procrastination", "hook": "Nobody tells you this about procrastination habits"}
    near_duplicate = {"title": "The Hidden Truth About Procrastination Habits", "hook": "Nobody tells you this about procrastination habits"}
    unrelated = {"title": "A Totally Different Topic", "hook": "This covers something else entirely"}

    batch_with_duplicate = [a, near_duplicate]
    batch_with_unrelated = [a, unrelated]
    assert score_threats(a, batch_with_duplicate)["repetitive_content"] > score_threats(a, batch_with_unrelated)["repetitive_content"]


def test_overall_threat_score_bounded_0_to_100():
    for idea in (CLEAN_IDEA, RISKY_IDEA, {}):
        score = overall_threat_score(score_threats(idea, [idea]))
        assert 0 <= score <= 100


def test_build_threat_report_shape():
    report = build_threat_report(CLEAN_IDEA, [CLEAN_IDEA])
    assert set(report) == {
        "threats", "threat_score", "threat_level", "confidence",
        "flagged_threats", "recommendations", "summary",
    }
    assert set(report["threats"]) == set(THREAT_KEYS)
    assert report["threat_level"] in ("Low", "Medium", "High")
    assert 0 <= report["threat_score"] <= 100
    assert 50 <= report["confidence"] <= 97
    assert set(report["recommendations"]) == set(THREAT_KEYS)
    assert isinstance(report["summary"], str) and len(report["summary"]) > 10


def test_clean_idea_reports_low_and_risky_idea_reports_higher_level():
    clean_report = build_threat_report(CLEAN_IDEA, [CLEAN_IDEA])
    risky_report = build_threat_report(RISKY_IDEA, [RISKY_IDEA])
    levels = {"Low": 0, "Medium": 1, "High": 2}
    assert levels[risky_report["threat_level"]] > levels[clean_report["threat_level"]]


def test_flagged_threats_sorted_descending_and_have_fixes():
    report = build_threat_report(RISKY_IDEA, [RISKY_IDEA])
    scores = [item["score"] for item in report["flagged_threats"]]
    assert scores == sorted(scores, reverse=True)
    for item in report["flagged_threats"]:
        assert item["score"] >= 55
        assert item["fix"] == THREAT_FIXES[item["key"]]
        assert item["label"] == THREAT_LABELS[item["key"]]


def test_build_flagged_threats_respects_threshold():
    threats = {key: 10 for key in THREAT_KEYS}
    assert build_flagged_threats(threats) == []
    threats["weak_hooks"] = 80
    flagged = build_flagged_threats(threats)
    assert len(flagged) == 1
    assert flagged[0]["key"] == "weak_hooks"


def test_confidence_increases_with_available_signal():
    thin = {"hook": "A hook"}
    rich = {
        "hook": "A hook", "script": "A full script here.", "psychology": {"a": 1},
        "retention_checkpoints": [1], "thumbnail_concept": "concept", "cta": "cta",
    }
    assert build_threat_report(rich, [rich])["confidence"] > build_threat_report(thin, [thin])["confidence"]


def test_engine_attaches_threat_report_to_every_selected_idea():
    context = {"selected_ideas": [dict(CLEAN_IDEA), dict(RISKY_IDEA)]}
    updates = registry.get_engine("threat_detection").run(context)
    for idea in updates["selected_ideas"]:
        report = idea["threat_report"]
        assert set(report["threats"]) == set(THREAT_KEYS)
        assert report["threat_level"] in ("Low", "Medium", "High")
    summary = updates["threat_detection_summary"]
    assert summary["scored"] == 2
    assert set(summary["level_counts"]) == {"Low", "Medium", "High"}


def test_engine_handles_empty_selected_ideas():
    assert registry.get_engine("threat_detection").run({"selected_ideas": []}) == {}
    assert registry.get_engine("threat_detection").run({}) == {}


def test_threat_detection_registered_after_seo_and_before_quality():
    for workflow_key in ("intelligence", "full_content"):
        steps = WORKFLOWS[workflow_key]
        assert "threat_detection" in steps
        assert steps.index("seo") < steps.index("threat_detection") < steps.index("quality")


def test_intelligence_pipeline_attaches_threat_report_to_every_idea():
    context = _run_pipeline()
    assert "threat_detection_summary" in context
    for idea in context["ideas"]:
        report = idea["threat_report"]
        assert set(report["threats"]) == set(THREAT_KEYS)
        assert 0 <= report["threat_score"] <= 100
        assert report["threat_level"] in ("Low", "Medium", "High")
        assert 50 <= report["confidence"] <= 97
        assert idea["thumbnail_concept"]  # confirms threat_detection runs after SEO
