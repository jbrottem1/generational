"""Tests for the Script Generation Engine (structured cinematic storytelling).

Covers the modular services/scripts package — section architecture, Hook
Engine, retention model, scene breakdown, structured output, multi-language
readiness, platform specs, deterministic scoring — and the pipeline engine
integration (position after Psychology, psychology-aware generation,
ranking weight, fallback behavior, Visual Intelligence contract).
All tests run in Demo Mode — no API key required.
"""

import engines  # noqa: F401 - importing registers all engines
from core.workflows import WORKFLOWS, WorkflowEngine
from engines import registry
from engines.ranking import RANKING_WEIGHTS_WITH_SCRIPT
from services.scripts import (
    HOOK_STYLES,
    PLATFORM_SPECS,
    REQUIRED_SCRIPT_SECTIONS,
    REQUIRED_SECTION_FIELDS,
    SCRIPT_PLATFORMS,
    STRUCTURED_SCRIPT_FIELDS,
    VARIANT_SCORE_WEIGHTS,
    Locale,
    generate_hook_candidates,
    generate_script_package,
    generate_variants,
    rank_hooks,
    rank_variants,
)
from services.scripts.models import REQUIRED_VARIANT_COMPONENTS

IDEA = {
    "title": "The Hidden Truth About Black Holes",
    "hook": "Nobody tells you this about black holes, and it changes everything.",
    "angle": "The hidden truth",
    "psychology_score": 72,
    "psychology": {
        "curiosity_gap": 80,
        "emotional_intensity": 65,
        "novelty": 70,
        "first_3_second_hook": 75,
        "retention_potential": 68,
        "comment_likelihood": 60,
        "share_likelihood": 62,
    },
}

RESEARCH = {
    "important_facts": [
        "A 2023 study found black holes can spin at near light speed.",
        "Research shows the event horizon is not a physical surface.",
    ],
    "statistics": ["90% of galaxies host a supermassive black hole."],
}


def _variants(platform="youtube_shorts", count=3, **kwargs):
    return generate_variants(
        IDEA, platform=platform, subject="black holes", niche="Science",
        research=RESEARCH, variant_count=count, **kwargs,
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


# ---------------------------------------------------------------- sections

def test_every_variant_carries_all_required_sections():
    for variant in _variants():
        keys = [section["key"] for section in variant.sections]
        for required in REQUIRED_SCRIPT_SECTIONS:
            assert required in keys, f"missing section {required} in {variant.style}"
        # canonical narrative order
        assert keys[0] == "primary_hook"
        assert keys[-1] == "call_to_action"


def test_every_section_is_fully_annotated():
    for variant in _variants():
        for section in variant.sections:
            for field in REQUIRED_SECTION_FIELDS:
                assert section.get(field) not in ("", None), (variant.style, section["key"], field)
            assert section["estimated_duration_sec"] > 0
            assert 0 <= section["emotional_intensity"] <= 100
            assert 0 <= section["attention_score"] <= 100
            assert section["narration"].strip()


def test_emotional_peak_is_the_hottest_section():
    for variant in _variants():
        peak = variant.get_section("emotional_peak")["emotional_intensity"]
        assert peak == max(s["emotional_intensity"] for s in variant.sections)


def test_flat_fields_stay_in_sync_with_sections():
    """The legacy view (hook, curiosity_loop, core_story...) derives from sections."""
    for variant in _variants():
        assert variant.hook == variant.get_section("primary_hook")["narration"]
        assert variant.curiosity_loop == variant.get_section("curiosity_hook")["narration"]
        assert variant.call_to_action == variant.get_section("call_to_action")["narration"]
        assert variant.get_section("context")["narration"] in variant.core_story
        assert variant.get_section("resolution")["narration"] in variant.core_story
        assert variant.full_script.startswith(variant.hook)
        assert variant.full_script.endswith(variant.call_to_action)


def test_variants_contain_all_required_components():
    for variant in _variants():
        data = variant.to_dict()
        for component in REQUIRED_VARIANT_COMPONENTS:
            assert data.get(component), f"missing {component} in {variant.style}"
        assert data["full_script"].startswith(data["hook"])
        assert data["estimated_runtime_sec"] > 0


# ---------------------------------------------------------------- hook engine

def test_hook_engine_supports_ten_styles():
    # Catalog grew beyond the original ten; require the core educational styles remain.
    required = {
        "curiosity", "shock", "question", "fomo", "statistics",
        "contrarian", "story", "mystery", "authority", "urgency",
    }
    assert required.issubset(set(HOOK_STYLES))
    assert len(HOOK_STYLES) >= 10


def test_hook_candidates_are_generated_and_ranked():
    candidates = generate_hook_candidates(IDEA, "black holes", RESEARCH)
    assert len(candidates) >= len(HOOK_STYLES)  # ten styles + the original hook
    assert all(c["text"].strip() for c in candidates)
    ranked = rank_hooks(candidates, IDEA["psychology"])
    scores = [c["score"] for c in ranked]
    assert scores == sorted(scores, reverse=True)
    assert all(0 <= s <= 100 for s in scores)


def test_hook_ranking_responds_to_psychology():
    candidates = generate_hook_candidates(IDEA, "black holes", RESEARCH)
    contrarian_friendly = {"controversy": 95, "surprise": 90}
    story_friendly = {"emotional_intensity": 95, "satisfaction": 90}
    score_a = {c["style"]: c["score"] for c in rank_hooks(candidates, contrarian_friendly)}
    score_b = {c["style"]: c["score"] for c in rank_hooks(candidates, story_friendly)}
    assert score_a["contrarian"] > score_b["contrarian"]
    assert score_b["story"] > score_a["story"]


def test_variants_carry_primary_and_alternate_hooks():
    for variant in _variants():
        assert variant.hook_style
        assert variant.alternate_hooks
        alternate_texts = {h["text"] for h in variant.alternate_hooks}
        assert variant.hook not in alternate_texts
        for alt in variant.alternate_hooks:
            assert alt["text"].strip() and alt["style"] and 0 <= alt["score"] <= 100


# ---------------------------------------------------------------- generation

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


# ---------------------------------------------------------------- retention model

def test_retention_model_estimates_all_six_signals():
    for variant in _variants():
        model = variant.retention_model
        for key in ("drop_off_risk", "engagement_score", "retention_score", "curiosity_strength"):
            assert 0 <= model[key] <= 100, key
        assert 0.0 <= model["rewatch_probability"] <= 1.0
        pacing = model["emotional_pacing"]
        assert pacing["label"]
        assert pacing["range"] >= 0
        assert len(pacing["curve"]) == len(variant.sections)


def test_strong_opening_lowers_drop_off_risk():
    strong = _variants()[0]
    # A weak-psychology idea should carry a higher predicted drop-off risk.
    weak_idea = dict(IDEA, psychology={"first_3_second_hook": 10, "emotional_intensity": 20})
    weak = generate_variants(
        weak_idea, platform="youtube_shorts", subject="black holes",
        niche="Science", research=RESEARCH, variant_count=1,
    )[0]
    assert strong.retention_model["drop_off_risk"] < weak.retention_model["drop_off_risk"]


# ---------------------------------------------------------------- multi-language

def test_locale_travels_with_every_variant_and_structured_script():
    default = _variants()[0]
    assert default.locale == {"language": "en", "region": "US", "dialect": "general"}

    localized = _variants(locale={"language": "es", "region": "MX", "dialect": "norteño"})[0]
    assert localized.locale == {"language": "es", "region": "MX", "dialect": "norteño"}

    package = generate_script_package(
        IDEA, platform="tiktok", subject="black holes", niche="Science",
        research=RESEARCH, locale=Locale(language="pt", region="BR"),
    )
    assert package["structured_script"]["locale"] == {
        "language": "pt", "region": "BR", "dialect": "general",
    }


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
        assert candidate["script_sections"] and candidate["alternate_hooks"]
        assert candidate["hook_style"]
        assert candidate["script_retention"]["retention_score"] > 0
        # Best variant won on score — no other variant beats the attached one.
        top = max(v["score"] for v in candidate["script_variants"])
        assert candidate["script_score"] == top
    summary = updates["script_generation_summary"]
    assert summary["scripted"] == 2
    assert summary["platform"] == "youtube_shorts"


def test_engine_runs_after_psychology_before_script():
    for workflow in ("intelligence", "full_content"):
        steps = WORKFLOWS[workflow]
        # Frozen V5 order: Psychology → Audience Intelligence → AI Director → Script
        assert steps.index("audience_intelligence") == steps.index("psychology") + 1
        assert steps.index("ai_director") == steps.index("audience_intelligence") + 1
        assert steps.index("script_generation") == steps.index("ai_director") + 1


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


# ---------------------------------------------------------------- structured output

def test_structured_script_contains_all_required_fields():
    expected = {
        "title", "hook", "alternate_hooks", "sections", "narration",
        "scene_breakdown", "estimated_runtime_sec", "timestamps",
        "emotional_beats", "emotion_timeline", "attention_timeline",
        "visual_prompts", "visual_notes", "voice_instructions",
        "caption_plan", "retention", "cta", "platform_format", "locale",
    }
    assert set(STRUCTURED_SCRIPT_FIELDS) == expected

    context = _engine_context()
    registry.get_engine("script_generation").run(context)
    for candidate in context["candidates"]:
        structured = candidate["structured_script"]
        assert set(structured) == expected
        for field in expected:
            assert structured[field], field
        assert structured["title"] == candidate["title"]
        assert structured["hook"] == candidate["script_variants"][0]["hook"]
        assert structured["narration"] == candidate["script"]
        assert structured["cta"] == candidate["cta"]
        assert structured["platform_format"]["key"] == "youtube_shorts"
        assert structured["platform_format"]["aspect_ratio"]
        assert structured["alternate_hooks"] == candidate["alternate_hooks"]
        assert structured["retention"] == candidate["script_retention"]


def test_scene_breakdown_is_director_ready():
    """Every scene carries the full production direction the mission requires."""
    scene_fields = (
        "scene", "start_sec", "end_sec", "narration", "visual_description",
        "camera_style", "motion", "caption_text", "sound_cue", "transition",
    )
    context = _engine_context()
    registry.get_engine("script_generation").run(context)
    for candidate in context["candidates"]:
        structured = candidate["structured_script"]
        scenes = structured["scene_breakdown"]
        runtime = structured["estimated_runtime_sec"]
        assert len(scenes) >= len(structured["sections"]) - 1  # every non-empty section
        assert scenes[0]["section"] == "primary_hook"
        assert scenes[-1]["section"] == "call_to_action"
        assert scenes[0]["start_sec"] == 0.0
        assert scenes[-1]["end_sec"] == runtime
        for prev, cur in zip(scenes, scenes[1:]):
            assert cur["start_sec"] == prev["end_sec"]
            assert cur["scene"] == prev["scene"] + 1
        for scene in scenes:
            for field in scene_fields:
                assert scene.get(field) not in ("", None), (scene["section"], field)
            assert scene["duration_sec"] > 0
            assert scene["emotion"] in structured["emotional_beats"]
        boundaries = structured["timestamps"]["scene_boundaries_sec"]
        assert boundaries == [s["start_sec"] for s in scenes] + [float(runtime)]
        assert all("time_sec" in cp for cp in structured["timestamps"]["retention_checkpoints"])


def test_emotion_and_attention_timelines_track_the_scenes():
    context = _engine_context()
    registry.get_engine("script_generation").run(context)
    for candidate in context["candidates"]:
        structured = candidate["structured_script"]
        scenes = structured["scene_breakdown"]
        emotion = structured["emotion_timeline"]
        attention = structured["attention_timeline"]
        assert len(emotion) == len(scenes) == len(attention)
        for scene, e_point, a_point in zip(scenes, emotion, attention):
            assert e_point["time_sec"] == scene["start_sec"] == a_point["time_sec"]
            assert e_point["emotion"] and 0 <= e_point["intensity"] <= 100
            assert 0 <= a_point["attention_score"] <= 100
        # timelines are chronological
        times = [p["time_sec"] for p in emotion]
        assert times == sorted(times)


def test_voice_instructions_and_caption_plan_cover_every_section():
    context = _engine_context()
    registry.get_engine("script_generation").run(context)
    for candidate in context["candidates"]:
        structured = candidate["structured_script"]
        voice = structured["voice_instructions"]
        assert voice["pace_wpm"] > 0
        assert voice["tone"] and voice["overall_energy"] in ("calm", "medium", "high")
        directed = {entry["section"] for entry in voice["per_section"]}
        assert directed == {s["key"] for s in structured["sections"]}
        assert all(entry["direction"] for entry in voice["per_section"])

        captions = structured["caption_plan"]
        assert len(captions) == len(structured["scene_breakdown"])
        for caption in captions:
            assert caption["text"].strip() and caption["emphasis"]
            assert caption["end_sec"] > caption["start_sec"]


def test_standalone_package_includes_structured_script():
    for platform in SCRIPT_PLATFORMS:
        package = generate_script_package(
            IDEA, platform=platform, subject="black holes", niche="Science", research=RESEARCH,
        )
        structured = package["structured_script"]
        assert set(structured) == set(STRUCTURED_SCRIPT_FIELDS)
        assert structured["platform_format"]["key"] == platform
        assert structured["narration"] == package["best_variant"]["full_script"]


# ---------------------------------------------------------------- integrations

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
        # structured output stays consistent with the visual plan's inputs
        structured = candidate["structured_script"]
        assert structured["hook"] == scenes[0]["narration"]
        assert structured["emotional_beats"] == variants[0]["emotional_progression"]
        assert structured["timestamps"]["estimated_runtime_sec"] == candidate["estimated_runtime_sec"]


def test_psychology_dimensions_shape_the_generated_script():
    """The same idea with different psychology produces different scripts."""
    hot = dict(IDEA, psychology={"curiosity_gap": 95, "controversy": 95, "surprise": 90,
                                 "emotional_intensity": 95, "first_3_second_hook": 90})
    cold = dict(IDEA, psychology={"curiosity_gap": 10, "controversy": 5, "surprise": 10,
                                  "emotional_intensity": 10, "first_3_second_hook": 15})
    hot_variant = generate_variants(
        hot, platform="youtube_shorts", subject="black holes",
        niche="Science", research=RESEARCH, variant_count=1,
    )[0]
    cold_variant = generate_variants(
        cold, platform="youtube_shorts", subject="black holes",
        niche="Science", research=RESEARCH, variant_count=1,
    )[0]
    # Intensity curves shift with the idea's emotional profile.
    hot_peak = hot_variant.get_section("emotional_peak")["emotional_intensity"]
    cold_peak = cold_variant.get_section("emotional_peak")["emotional_intensity"]
    assert hot_peak > cold_peak
    # Attention curves and the retention model shift with the hook profile.
    hot_open = hot_variant.get_section("primary_hook")["attention_score"]
    cold_open = cold_variant.get_section("primary_hook")["attention_score"]
    assert hot_open > cold_open
    assert hot_variant.retention_model["drop_off_risk"] < cold_variant.retention_model["drop_off_risk"]


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
        assert idea["structured_script"]["scene_breakdown"]
        assert idea["structured_script"]["retention"]
