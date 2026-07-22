"""Tests for the v7.4 Motivational Media Studio extensions."""

from __future__ import annotations

import engines  # noqa: F401
from core.constants import AUTONOMOUS_PUBLISHING_ENABLED, NICHE_KEYWORDS
from core.workflows import WorkflowEngine
from engines import registry
from engines.production_quality import score_production_package
from services.channels import default_motivational_channel
from services.editorial import (
    CONTENT_PILLARS,
    MOTIVATIONAL_PROGRESSION,
    REQUIRED_STORY_BEATS,
    beats_complete,
    is_motivational_niche,
    score_story_structure,
    score_viewer_progression,
)
from services.editorial.integrity import quote_integrity_flags
from services.scripts import generate_variants, rank_variants


def test_motivation_niche_and_pillars_catalog():
    assert "Motivation" in NICHE_KEYWORDS
    assert is_motivational_niche("Motivation")
    assert len(CONTENT_PILLARS) >= 20
    assert "discipline" in CONTENT_PILLARS


def test_struggle_to_action_variants_have_complete_beats():
    idea = {
        "title": "Discipline Is Built in Private",
        "hook": "You already know what to do about discipline — so why are you still stuck?",
        "angle": "private responsibility",
        "content_pillars": ["discipline"],
        "psychology_score": 70,
    }
    research = {
        "important_facts": [
            "Behavioral research shows small repeated actions compound into identity change.",
            "Delayed gratification predicts long-term goal follow-through across studies.",
        ],
        "statistics": [],
    }
    variants = generate_variants(
        idea,
        platform="youtube_shorts",
        subject="discipline",
        niche="Motivation",
        research=research,
        variant_count=3,
    )
    assert variants[0].style == "struggle_to_action"
    ranked = rank_variants(variants)
    best = ranked[0]
    assert beats_complete(best.story_beats)
    for beat in REQUIRED_STORY_BEATS:
        assert best.story_beats[beat].strip()
    assert best.emotional_progression == list(MOTIVATIONAL_PROGRESSION)
    assert "story_structure" in best.score_breakdown
    assert "action_drive" in best.score_breakdown
    structure = score_story_structure(best.story_beats, best.full_script)
    assert structure["score"] >= 70
    progression = score_viewer_progression(best.emotional_progression, best.full_script)
    assert progression["score"] >= 65


def test_quote_integrity_flags_unverified_attribution():
    script = 'As Einstein once said, "Imagination is more important than knowledge for your grind."'
    flags = quote_integrity_flags(script, research={})
    assert flags


def test_quality_gate_enforces_story_structure_for_motivation():
    idea = {
        "title": "Get Up",
        "hook": "Why do you keep waiting to start?",
        "script": "You feel stuck. Start today with one small action.",
        "story_beats": {},
        "emotional_progression": ["curiosity"],
        "psychology": {
            "retention_potential": 80,
            "dopamine_curve": 70,
            "replay_value": 60,
            "curiosity_gap": 80,
            "first_3_second_hook": 75,
            "surprise": 50,
            "share_likelihood": 60,
            "comment_likelihood": 55,
            "audience_identity": 50,
            "community_appeal": 40,
            "controversy": 20,
        },
        "psychology_score": 75,
        "seo_score": 70,
        "critique": {"score": 80, "issues": []},
        "citations": {
            "unsupported_claims": [],
            "quote_integrity_flags": [],
            "claim_confidence": 80,
            "citation_count": 1,
        },
        "script_variants": [],
    }
    context = {
        "niche": "Motivation",
        "selected_ideas": [idea],
        "threshold": 0,
        "research": {"opportunity_score": 70, "research_confidence": 0.8},
        "research_settings": {
            "research_confidence_threshold": 0.0,
            "citation_required": False,
            "max_unsupported_claims": 5,
            "min_claim_confidence": 0.0,
        },
    }
    registry.get_engine("quality").run(context)
    assert not idea["publishable"]
    assert "story_structure" in idea["gate_failures"]


def test_autonomous_publishing_disabled_by_default():
    assert AUTONOMOUS_PUBLISHING_ENABLED is False
    ctx = {
        "niche": "Motivation",
        "approved_content": [
            {
                "title": "Responsibility Short",
                "hook": "The moment you stop blaming is the moment you grow.",
                "script": (
                    "You've been waiting for permission. The struggle is real. "
                    "History shows people change through repeated action. "
                    "The lesson is responsibility. Today, take one step. Begin."
                ),
                "story_beats": {
                    "hook": "The moment you stop blaming is the moment you grow.",
                    "struggle": "You've been waiting for permission.",
                    "real_life_example": "Documented patterns show change through repeated action.",
                    "lesson": "Responsibility is chosen in private.",
                    "application": "Today, take one step before the day ends.",
                    "memorable_ending": "Get off the couch. Begin.",
                },
                "publishable": True,
                "scores": {"publish": 85},
            }
        ],
        "autonomous_publishing_enabled": False,
    }
    run = WorkflowEngine().execute("media_production", ctx)
    assert run.succeeded
    pkg = ctx["production_packages"][0]
    assert pkg["queue_status"] == "held"
    assert pkg["hold_reason"] == "autonomous_publishing_disabled"
    assert ctx.get("autonomous_publishing_enabled") is False


def test_production_quality_scores_package():
    pkg = {
        "scenes": [
            {
                "narration": "Start today.",
                "visual_description": "Mountain path at dawn",
                "camera_movement": "slow push-in",
                "on_screen_text": "Start today",
            }
        ],
        "narration": {"full_text": "Start today with one honest action."},
        "visual_prompts": [{"prompt_text": "mountain path"}],
        "subtitles": {"srt_content": "1\n00:00:00,000 --> 00:00:02,000\nStart"},
        "story_beats": {
            "hook": "h",
            "struggle": "s",
            "real_life_example": "e",
            "lesson": "l",
            "application": "a",
            "memorable_ending": "m",
        },
    }
    result = score_production_package(pkg, niche="Motivation")
    assert result["scores"]["production"] >= 70
    assert result["passed"]


def test_default_motivational_channel_seed():
    channel = default_motivational_channel()
    assert channel["niche"] == "Motivation"
    assert channel["autonomous_publishing_enabled"] is False
    assert "discipline" in channel["content_pillars"]
    assert "youtube_shorts" in channel["platforms"]


def test_motivational_intelligence_pipeline_end_to_end():
    context = {
        "command": "Create 3 motivational shorts about discipline",
        "count": 10,
        "model": "gpt-4o-mini",
        "threshold": 0,
        "require_story_structure": True,
        "require_psychology_progression": True,
        "require_quote_integrity": True,
        "research_settings": {
            "research_confidence_threshold": 0.0,
            "citation_required": False,
            "max_unsupported_claims": 10,
            "min_claim_confidence": 0.0,
        },
    }
    run = WorkflowEngine().execute("intelligence", context)
    assert run.succeeded, run.summary()
    assert context.get("niche") == "Motivation" or "motivat" in context.get("command", "").lower()
    for idea in context.get("selected_ideas", [])[:3]:
        assert idea.get("script")
        # Script generation attaches beats for motivational niche.
        if context.get("niche") == "Motivation":
            assert idea.get("story_beats")
            assert idea.get("emotional_progression")
