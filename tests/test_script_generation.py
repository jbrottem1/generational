"""Tests for the v7.2 Script Generation Engine.

Covers the modular services/scripts package (platform specs, variant
generation, deterministic scoring) and the pipeline engine integration
(position after Psychology, ranking weight, fallback behavior).
All tests run in Demo Mode — no API key required.
"""

import engines  # noqa: F401 - importing registers all engines
from core.workflows import WORKFLOWS, WorkflowEngine
from engines import registry
from engines.ranking import RANKING_WEIGHTS_WITH_SCRIPT
from services.scripts import (
    PLATFORM_SPECS,
    SCRIPT_PLATFORMS,
    VARIANT_SCORE_WEIGHTS,
    generate_script_package,
    generate_variants,
    rank_variants,
)
from services.scripts.models import REQUIRED_VARIANT_COMPONENTS

IDEA = {
    "title": "The Hidden Truth About Black Holes",
    "hook": "Nobody tells you this about black holes, and it changes everything.",
    "angle": "The hidden truth",
    "psychology_score": 72,
}

RESEARCH = {
    "important_facts": [
        "A 2023 study found black holes can spin at near light speed.",
        "Research shows the event horizon is not a physical surface.",
    ],
    "statistics": ["90% of galaxies host a supermassive black hole."],
}


def _variants(platform="youtube_shorts", count=3):
    return generate_variants(
        IDEA, platform=platform, subject="black holes", niche="Science",
        research=RESEARCH, variant_count=count,
    )


# ---------------------------------------------------------------- platforms

def test_all_six_platforms_supported():
    expected = {
        "youtube_shorts", "tiktok", "instagram_reels",
        "facebook_reels", "x_video", "youtube_long",
    }
    assert expected == set(SCRIPT_PLATFORMS)
    for spec in PLATFORM_SPECS.values():
        assert spec.min_runtime_sec < spec.max_runtime_sec
        assert spec.words_per_minute > 0
        assert spec.min_runtime_sec <= spec.target_runtime_sec <= spec.max_runtime_sec


# ---------------------------------------------------------------- generation

def test_variants_contain_all_required_components():
    for variant in _variants():
        data = variant.to_dict()
        for component in REQUIRED_VARIANT_COMPONENTS:
            assert data.get(component), f"missing {component} in {variant.style}"
        assert data["full_script"].startswith(data["hook"])
        assert data["estimated_runtime_sec"] > 0


def test_variants_are_stylistically_distinct():
    variants = _variants()
    assert len(variants) == 3
    assert len({v.style for v in variants}) == 3
    assert len({v.full_script for v in variants}) == 3
    assert len({v.hook for v in variants}) == 3


def test_generation_is_deterministic():
    first = [v.to_dict() for v in _variants()]
    second = [v.to_dict() for v in _variants()]
    assert first == second


def test_short_form_runtime_lands_inside_platform_window():
    for platform in ("youtube_shorts", "tiktok", "instagram_reels", "facebook_reels"):
        spec = PLATFORM_SPECS[platform]
        for variant in _variants(platform=platform):
            assert spec.min_runtime_sec <= variant.estimated_runtime_sec <= spec.max_runtime_sec, (
                platform, variant.style, variant.estimated_runtime_sec,
            )


def test_retention_checkpoints_are_ordered_and_timed():
    for variant in _variants():
        times = [cp["time_sec"] for cp in variant.retention_checkpoints]
        assert times == sorted(times)
        assert all(cp["technique"] and cp["line"] for cp in variant.retention_checkpoints)


# ---------------------------------------------------------------- scoring

def test_variant_scoring_weights_sum_to_one():
    assert abs(sum(VARIANT_SCORE_WEIGHTS.values()) - 1.0) < 1e-9


def test_rank_variants_scores_and_sorts_best_first():
    ranked = rank_variants(_variants())
    scores = [v.score for v in ranked]
    assert scores == sorted(scores, reverse=True)
    for variant in ranked:
        assert 0 <= variant.score <= 100
        assert set(variant.score_breakdown) == set(VARIANT_SCORE_WEIGHTS)


def test_generate_script_package_for_every_platform():
    for platform in SCRIPT_PLATFORMS:
        package = generate_script_package(
            IDEA, platform=platform, subject="black holes", niche="Science", research=RESEARCH,
        )
        assert package["platform"] == platform
        assert package["variant_count"] >= 3
        assert package["best_variant"]["full_script"]
        assert package["best_score"] == package["variants"][0]["score"]


# ---------------------------------------------------------------- engine

def _engine_context():
    return {
        "candidates": [dict(IDEA), {
            "title": "Black Holes vs What You Learned",
            "hook": "Everything you learned about black holes is a myth.",
            "angle": "The myth",
            "psychology_score": 61,
        }],
        "subject": "black holes",
        "niche": "Science",
        "research": dict(RESEARCH),
        "video_count": 2,
        "model": "",
    }


def test_engine_attaches_scored_scripts_to_every_candidate():
    context = _engine_context()
    updates = registry.get_engine("script_generation").run(context)
    for candidate in updates["candidates"]:
        assert candidate["script"]
        assert candidate["cta"]
        assert len(candidate["script_variants"]) >= 3
        assert 0 <= candidate["script_score"] <= 100
        assert candidate["script_style"]
        assert candidate["estimated_runtime_sec"] > 0
        assert candidate["broll_suggestions"] and candidate["visual_prompts"]
        assert candidate["sound_effects"] and candidate["music_style"]
        # Best variant won on score — no other variant beats the attached one.
        top = max(v["score"] for v in candidate["script_variants"])
        assert candidate["script_score"] == top
    summary = updates["script_generation_summary"]
    assert summary["scripted"] == 2
    assert summary["platform"] == "youtube_shorts"


def test_engine_runs_immediately_after_psychology_in_pipeline():
    for workflow in ("intelligence", "full_content"):
        steps = WORKFLOWS[workflow]
        assert steps.index("script_generation") == steps.index("psychology") + 1


def test_ranking_blends_script_quality_into_rank_score():
    context = _engine_context()
    registry.get_engine("script_generation").run(context)
    context["research"]["opportunity_score"] = 60
    updates = registry.get_engine("ranking").run(context)
    for candidate in updates["ranked_candidates"]:
        expected = round(
            RANKING_WEIGHTS_WITH_SCRIPT["psychology"] * candidate["psychology_score"]
            + RANKING_WEIGHTS_WITH_SCRIPT["opportunity"] * 60
            + RANKING_WEIGHTS_WITH_SCRIPT["script"] * candidate["script_score"],
            1,
        )
        assert candidate["rank_score"] == expected


def test_script_fallback_engine_preserves_generated_variants():
    context = _engine_context()
    registry.get_engine("script_generation").run(context)
    idea = context["candidates"][0]
    original_script = idea["script"]
    registry.get_engine("script").run({"selected_ideas": [idea]})
    assert idea["script"] == original_script  # fallback never overwrites


def test_script_output_satisfies_visual_intelligence_contract():
    """Guard the Script Generation → Visual Intelligence (Agent 4) seam.

    Visual Intelligence reads script_variants[0] as the winning variant and
    consumes these fields to build scenes, narration, emotional beats,
    timestamps, and visual notes. If either side changes shape, this fails.
    """
    from services.visual import build_visual_package

    context = _engine_context()
    registry.get_engine("script_generation").run(context)

    consumed_fields = (
        "hook", "pattern_interrupt", "curiosity_loop", "core_story",
        "call_to_action", "emotional_progression", "broll_suggestions",
        "sound_effects", "music_style", "estimated_runtime_sec",
    )
    for candidate in context["candidates"]:
        variants = candidate["script_variants"]
        # Best-first ordering — visual planning trusts variants[0].
        scores = [v["score"] for v in variants]
        assert scores == sorted(scores, reverse=True)
        for field in consumed_fields:
            assert variants[0].get(field), field

        package = build_visual_package(
            candidate, niche=context["niche"], subject=context["subject"],
        )
        scenes = package["scenes"]
        # hook
        assert scenes[0]["purpose"] == "hook"
        assert scenes[0]["narration"] == variants[0]["hook"]
        # scenes + narration
        assert len(scenes) >= 4
        assert all(s["narration"].strip() for s in scenes)
        # emotional beats
        assert all(s["emotion"] for s in scenes)
        assert set(s["emotion"] for s in scenes) <= set(variants[0]["emotional_progression"])
        # timestamps — contiguous captions matching the script's runtime
        for prev, cur in zip(scenes, scenes[1:]):
            assert cur["caption_timing"]["start_sec"] == prev["caption_timing"]["end_sec"]
        total = sum(s["length_sec"] for s in scenes)
        assert abs(total - candidate["estimated_runtime_sec"]) <= 8
        assert all("time_sec" in cp for cp in candidate["retention_checkpoints"])
        # visual notes
        assert all(s["visual_description"] for s in scenes)
        assert package["image_prompts"] and package["video_prompts"]


def test_full_pipeline_still_succeeds_end_to_end():
    context = {
        "command": "Create 3 science shorts about black holes",
        "count": 10, "model": "gpt-4o-mini", "threshold": 70,
    }
    run = WorkflowEngine().execute("intelligence", context)
    assert run.succeeded, run.summary()
    step_status = {s.engine_key: s.status for s in run.steps}
    assert step_status["script_generation"] == "succeeded"
    for idea in context["selected_ideas"]:
        assert idea["script_variants"]
        assert idea["script"]
