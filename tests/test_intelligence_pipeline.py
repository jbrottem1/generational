"""Tests for the v2.0 intelligence pipeline — per-stage and end-to-end.

All tests run in Demo Mode (deterministic heuristics, no API key needed).
"""

import engines  # noqa: F401 - importing registers all engines
from core.workflows import WorkflowEngine
from engines import registry
from engines.critic import analyze_script, critic_score
from engines.psychology import DIMENSION_WEIGHTS, score_text

COMMAND = "Create 5 science shorts about black holes"


def _run_pipeline(threshold=70):
    context = {"command": COMMAND, "count": 10, "model": "gpt-4o-mini", "threshold": threshold}
    run = WorkflowEngine().execute("intelligence", context)
    assert run.succeeded, run.summary()
    return context


def test_research_builds_full_brief():
    context = {"command": COMMAND, "model": ""}
    updates = registry.get_engine("research").run(context)
    research = updates["research"]
    assert updates["niche"] == "Science"
    for field in ("topic_context", "audience", "search_intent", "trend_strength", "summary", "opportunity_score"):
        assert research.get(field) not in (None, "")
    assert 0 <= research["trend_strength"] <= 100
    assert research.get("source_count", 0) >= 0
    assert "important_facts" in research
    assert updates.get("research_references")


def test_ideation_produces_20_candidates():
    context = _run_pipeline()
    assert len(context["candidates"]) == 20
    for candidate in context["candidates"]:
        assert candidate["title"] and candidate["hook"] and candidate["angle"]


def test_psychology_scores_all_six_dimensions():
    scores = score_text("The secret truth about black holes — a study proves you were wrong")
    assert set(scores) == set(DIMENSION_WEIGHTS)
    for value in scores.values():
        assert 0 <= value <= 100


def test_psychology_is_deterministic():
    text = "Why does procrastination happen to smart people?"
    assert score_text(text) == score_text(text)


def test_ranking_sorts_and_selects_requested_count():
    context = _run_pipeline()
    ranked = context["ranked_candidates"]
    rank_scores = [c["rank_score"] for c in ranked]
    assert rank_scores == sorted(rank_scores, reverse=True)
    # command asks for 5 videos → only the top 5 get scripts
    assert len(context["selected_ideas"]) == 5


def test_scripts_generated_only_for_selected():
    context = _run_pipeline()
    assert all(idea.get("script") for idea in context["selected_ideas"])
    unselected = [c for c in context["ranked_candidates"] if c not in context["selected_ideas"]]
    assert all("script" not in c for c in unselected)


def test_scripts_have_citations():
    context = _run_pipeline()
    for idea in context["selected_ideas"]:
        assert idea.get("citations")
        assert "citation_list" in idea["citations"]
        assert idea.get("references")


def test_critic_flags_known_weaknesses():
    issues = analyze_script(
        hook="This is a plain opening line",  # no curiosity gap
        script=(
            "In this video we discuss things. Everyone always fails at this. "
            "It affects people, people, people, people, people every day."
        ),
    )
    joined = " ".join(issues)
    assert "Weak hook" in joined
    assert "Boring phrasing" in joined
    assert "Unsupported claim" in joined
    assert "Repetition" in joined
    assert "Low retention" in joined
    assert critic_score(issues) < critic_score([])


def test_revision_improves_critic_score():
    idea = {
        "hook": "This is a plain opening line",
        "script": (
            "This is a plain opening line. In this video we discuss things. "
            "Everyone always fails at this and there is nothing that can be done about it in any case whatsoever "
            "because the problem is just too large and too complicated for anyone to solve alone."
        ),
    }
    before = analyze_script(idea["hook"], idea["script"])
    idea["critique"] = {"issues": before, "score": critic_score(before)}
    before_score = idea["critique"]["score"]

    registry.get_engine("revision").run({"selected_ideas": [idea]})
    assert idea["revised"] is True
    assert idea["critique"]["score"] > before_score


def test_seo_packages_every_selected_idea():
    context = _run_pipeline()
    for idea in context["selected_ideas"]:
        assert len(idea["title"]) <= 60
        assert 3 <= len(idea["hashtags"]) <= 6
        assert len(idea["keywords"]) >= 5
        assert idea["description"]
        assert idea["thumbnail_concept"]
        assert 0 <= idea["seo_score"] <= 100


def test_quality_scores_and_threshold_gate():
    context = _run_pipeline(threshold=70)
    assert context["ideas"] == context["selected_ideas"]
    for idea in context["ideas"]:
        scores = idea["scores"]
        assert set(scores) >= {"opportunity", "seo", "psychology", "retention", "ctr", "publish"}
        assert "claim_confidence" in scores
        assert idea["publishable"] == (scores["publish"] >= 70 and not idea.get("gate_failures"))

    summary = context["quality_summary"]
    assert summary["publishable"] + summary["held"] == len(context["ideas"])


def test_threshold_100_holds_everything():
    context = _run_pipeline(threshold=100)
    assert context["quality_summary"]["publishable"] == 0
    assert all(not idea["publishable"] for idea in context["ideas"])


def test_threshold_0_publishes_everything():
    context = _run_pipeline(threshold=0)
    assert context["quality_summary"]["held"] == 0
