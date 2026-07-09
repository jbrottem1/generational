"""Tests for the Visual Intelligence Engine (visual planning brain)."""

import engines  # noqa: F401 - importing registers all engines
from core.workflows import WORKFLOWS, WorkflowEngine
from engines import registry
from services.visual import (
    HOOK_FRAME_COUNT,
    IMAGE_MODELS,
    PACKAGE_SCORE_WEIGHTS,
    REQUIRED_SCENE_COMPONENTS,
    THUMBNAIL_ARCHETYPES,
    THUMBNAIL_SCORE_KEYS,
    THUMBNAIL_SCORE_WEIGHTS,
    VIDEO_MODELS,
    VISUAL_DIMENSION_KEYS,
    VISUAL_DIMENSION_LABELS,
    VISUAL_SCORE_WEIGHTS,
    build_hook_sequence,
    build_image_prompts,
    build_thumbnail_concepts,
    build_video_prompts,
    build_visual_package,
    expected_ctr_pct,
    plan_scenes,
    scene_visual_score,
    score_scene_visuals,
)

COMMAND = "Create 5 psychology shorts about procrastination"

SCRIPTED_IDEA = {
    "title": "Why Smart People Procrastinate",
    "hook": "Here's the secret reason procrastination hits smart people hardest.",
    "script": (
        "Here's the secret reason procrastination hits smart people hardest. "
        "Turns out, the cause is fear of failure, not laziness. Researchers found "
        "one small change flips the pattern. Try one task for two minutes. "
        "That's the answer that finally makes sense. Follow for more."
    ),
    "cta": "Follow for the next deep dive.",
    "estimated_runtime_sec": 30,
    "emotional_progression": ["curiosity", "tension", "revelation", "understanding", "resolve"],
    "broll_suggestions": ["Close-up of a ticking clock", "Overhead desk time-lapse"],
    "sound_effects": ["whoosh on the opening cut", "sub-bass hit on the reveal"],
    "music_style": "cinematic tension build",
    "script_variants": [
        {
            "hook": "Here's the secret reason procrastination hits smart people hardest.",
            "pattern_interrupt": "Stop scrolling — this is not what you were taught.",
            "curiosity_loop": "In a moment you'll see the one detail almost everyone misses.",
            "core_story": (
                "Most people miss this about procrastination: the surface story is not the real "
                "story. Fear of failure drives the delay, not laziness. Researchers watched the "
                "pattern repeat across thousands of people. One small change flipped it. Start a "
                "task for just two minutes and the loop breaks. That single detail reframes "
                "everything completely."
            ),
            "call_to_action": "Follow for the next deep dive.",
            "emotional_progression": ["curiosity", "tension", "revelation", "understanding", "resolve"],
            "broll_suggestions": ["Close-up of a ticking clock", "Overhead desk time-lapse"],
            "sound_effects": ["whoosh on the opening cut", "sub-bass hit on the reveal"],
            "music_style": "cinematic tension build",
            "estimated_runtime_sec": 30,
        }
    ],
}

BARE_IDEA = {
    "title": "A Plain Concept",
    "hook": "A simple hook line.",
    "script": "A simple hook line. One short body sentence. A closing line.",
}


def _run_pipeline():
    context = {"command": COMMAND, "count": 5, "model": ""}
    run = WorkflowEngine().execute("intelligence", context)
    assert run.succeeded, run.summary()
    return context


# --- Visual psychology --------------------------------------------------------

def test_exactly_12_visual_dimensions():
    assert len(VISUAL_DIMENSION_KEYS) == 12
    assert set(VISUAL_SCORE_WEIGHTS) == set(VISUAL_DIMENSION_KEYS)
    assert set(VISUAL_DIMENSION_LABELS) == set(VISUAL_DIMENSION_KEYS)


def test_expected_visual_dimensions_present():
    expected = {
        "curiosity", "mystery", "wonder", "fear", "beauty", "novelty",
        "scale", "contrast", "motion", "satisfaction", "humor", "identity",
    }
    assert set(VISUAL_DIMENSION_KEYS) == expected


def test_visual_weights_sum_to_one():
    assert round(sum(VISUAL_SCORE_WEIGHTS.values()), 6) == 1.0


def test_scene_visual_scores_bounded_and_deterministic():
    scene = {
        "narration": "A massive hidden reveal in slow motion",
        "visual_description": "Towering silhouette emerging from fog, high contrast",
        "motion_intensity": 70,
        "camera_motion": "crash zoom",
    }
    scores = score_scene_visuals(scene)
    assert set(scores) == set(VISUAL_DIMENSION_KEYS)
    for value in scores.values():
        assert 0 <= value <= 100
    assert scores == score_scene_visuals(dict(scene))
    assert 0 <= scene_visual_score(scores) <= 100


def test_motion_dimension_tracks_motion_intensity():
    calm = {"narration": "a quiet desk", "visual_description": "still frame", "motion_intensity": 10, "camera_motion": "locked-off"}
    kinetic = {"narration": "a quiet desk", "visual_description": "still frame", "motion_intensity": 95, "camera_motion": "whip pan"}
    assert score_scene_visuals(kinetic)["motion"] > score_scene_visuals(calm)["motion"]


def test_mystery_dimension_rewards_concealment_language():
    plain = {"narration": "a bright office", "visual_description": "clean daylight office scene"}
    mysterious = {"narration": "a shadowed figure", "visual_description": "silhouette half-hidden behind fog, obscured in darkness"}
    assert score_scene_visuals(mysterious)["mystery"] > score_scene_visuals(plain)["mystery"]


# --- Scene planner --------------------------------------------------------------

def test_plan_scenes_carries_all_required_components():
    scenes = plan_scenes(SCRIPTED_IDEA, niche="Psychology", subject="procrastination")
    assert len(scenes) >= 4
    for scene in scenes:
        data = scene.to_dict()
        for component in REQUIRED_SCENE_COMPONENTS:
            assert component in data, component
        assert data["length_sec"] > 0
        assert 0 <= data["visual_score"] <= 100


def test_scene_purposes_follow_narrative_order():
    scenes = plan_scenes(SCRIPTED_IDEA, niche="Psychology", subject="procrastination")
    purposes = [scene.purpose for scene in scenes]
    assert purposes[0] == "hook"
    assert purposes[-1] == "cta"
    assert "payoff" in purposes
    assert purposes.index("hook") < purposes.index("payoff") < purposes.index("cta")


def test_scene_lengths_roughly_match_runtime():
    scenes = plan_scenes(SCRIPTED_IDEA, niche="Psychology", subject="procrastination")
    total = sum(scene.length_sec for scene in scenes)
    assert abs(total - SCRIPTED_IDEA["estimated_runtime_sec"]) <= 8


def test_caption_timings_are_contiguous():
    scenes = plan_scenes(SCRIPTED_IDEA, niche="Psychology")
    for previous, current in zip(scenes, scenes[1:]):
        assert current.caption_timing["start_sec"] == previous.caption_timing["end_sec"]


def test_transition_in_matches_previous_transition_out():
    scenes = plan_scenes(SCRIPTED_IDEA, niche="Psychology")
    assert scenes[0].transition_in == "none"
    for previous, current in zip(scenes, scenes[1:]):
        assert current.transition_in == previous.transition_out


def test_plan_scenes_works_without_script_variants():
    scenes = plan_scenes(BARE_IDEA, niche="Science")
    assert scenes
    assert scenes[0].purpose == "hook"


def test_scene_planning_is_deterministic():
    first = [scene.to_dict() for scene in plan_scenes(SCRIPTED_IDEA, niche="Psychology")]
    second = [scene.to_dict() for scene in plan_scenes(SCRIPTED_IDEA, niche="Psychology")]
    assert first == second


# --- AI prompts --------------------------------------------------------------

def test_image_prompts_cover_all_models_and_spec_fields():
    scenes = [scene.to_dict() for scene in plan_scenes(SCRIPTED_IDEA, niche="Psychology")]
    prompt_sets = build_image_prompts(scenes, niche="Psychology", aspect_ratio="9:16")
    assert len(prompt_sets) == len(scenes)
    expected_models = {"midjourney", "flux", "stable_diffusion", "dalle", "openai_images"}
    assert set(IMAGE_MODELS) == expected_models
    for prompt_set in prompt_sets:
        assert set(prompt_set["prompts"]) == expected_models
        spec = prompt_set["spec"]
        for field in ("lighting", "composition", "lens", "mood", "art_style", "color_palette", "quality", "aspect_ratio"):
            assert spec[field], field
        for prompt in prompt_set["prompts"].values():
            assert len(prompt) > 40


def test_midjourney_prompt_carries_aspect_ratio_flag():
    scenes = [scene.to_dict() for scene in plan_scenes(SCRIPTED_IDEA, niche="Psychology")]
    prompt_sets = build_image_prompts(scenes, niche="Psychology", aspect_ratio="9:16")
    assert "--ar 9:16" in prompt_sets[0]["prompts"]["midjourney"]


def test_video_prompts_cover_all_models_and_motion_fields():
    scenes = [scene.to_dict() for scene in plan_scenes(SCRIPTED_IDEA, niche="Psychology")]
    prompt_sets = build_video_prompts(scenes, niche="Psychology", aspect_ratio="9:16")
    expected_models = {"runway", "veo", "pika", "luma", "kling", "sora"}
    assert set(VIDEO_MODELS) == expected_models
    for prompt_set in prompt_sets:
        assert set(prompt_set["prompts"]) == expected_models
        spec = prompt_set["spec"]
        for field in ("camera_movement", "character_action", "physics", "mood", "duration_sec"):
            assert spec[field] or spec[field] == 0, field
        for prompt in prompt_set["prompts"].values():
            assert "Camera:" in prompt and "Physics:" in prompt


# --- Thumbnails --------------------------------------------------------------

def test_exactly_5_thumbnail_concepts_scored_on_7_dimensions():
    assert len(THUMBNAIL_ARCHETYPES) == 5
    assert round(sum(THUMBNAIL_SCORE_WEIGHTS.values()), 6) == 1.0
    concepts = build_thumbnail_concepts(SCRIPTED_IDEA)
    assert len(concepts) == 5
    for concept in concepts:
        assert set(concept.scores) == set(THUMBNAIL_SCORE_KEYS)
        for value in concept.scores.values():
            assert 0 <= value <= 100
        assert 0 <= concept.overall <= 100
        assert 0 < concept.expected_ctr_pct <= 14.0


def test_thumbnails_sorted_best_first():
    concepts = build_thumbnail_concepts(SCRIPTED_IDEA)
    overalls = [concept.overall for concept in concepts]
    assert overalls == sorted(overalls, reverse=True)


def test_expected_ctr_scales_with_overall_score():
    assert expected_ctr_pct(90) > expected_ctr_pct(50) > expected_ctr_pct(10)


def test_curiosity_language_raises_curiosity_thumbnail_scores():
    plain = {"title": "A calm overview", "hook": "A gentle summary of the topic."}
    curious = {"title": "The hidden secret nobody found", "hook": "Why the truth was never revealed."}
    plain_best = build_thumbnail_concepts(plain)[0]
    curious_best = build_thumbnail_concepts(curious)[0]
    plain_by_id = {c.concept_id: c for c in build_thumbnail_concepts(plain)}
    curious_by_id = {c.concept_id: c for c in build_thumbnail_concepts(curious)}
    for concept_id in plain_by_id:
        assert curious_by_id[concept_id].scores["curiosity"] >= plain_by_id[concept_id].scores["curiosity"] - 6
    assert curious_best.overall >= plain_best.overall


# --- Hook visualizer --------------------------------------------------------------

def test_hook_sequence_has_5_frames_inside_3_seconds():
    sequence = build_hook_sequence(SCRIPTED_IDEA, subject="procrastination")
    assert sequence["frame_count"] == HOOK_FRAME_COUNT == 5
    frames = sequence["frames"]
    assert len(frames) == 5
    assert [frame["frame"] for frame in frames] == [1, 2, 3, 4, 5]
    for frame in frames:
        assert 0 <= frame["time_sec"] < 3.0
        assert frame["visual"]
        assert frame["camera"]
        assert frame["technique"]


def test_hook_sequence_explains_scroll_stop():
    sequence = build_hook_sequence(SCRIPTED_IDEA, subject="procrastination")
    rationale = sequence["scroll_stop_rationale"]
    assert len(rationale) > 100
    assert "procrastination" in rationale


# --- Visual Production Package --------------------------------------------------------------

def test_package_weights_sum_to_one():
    assert round(sum(PACKAGE_SCORE_WEIGHTS.values()), 6) == 1.0


def test_build_visual_package_shape():
    package = build_visual_package(SCRIPTED_IDEA, niche="Psychology", subject="procrastination")
    expected_keys = {
        "visual_score", "score_components", "summary", "aspect_ratio", "color_palette",
        "storyboard", "scenes", "image_prompts", "video_prompts", "thumbnails",
        "hook_sequence", "caption_plan", "pacing_report", "camera_plan",
        "transitions", "motion_report",
    }
    assert set(package) == expected_keys
    assert 0 <= package["visual_score"] <= 100
    assert len(package["storyboard"]) == len(package["scenes"])
    assert len(package["caption_plan"]) == len(package["scenes"])
    assert len(package["transitions"]) == len(package["scenes"]) - 1
    assert len(package["thumbnails"]) == 5
    assert isinstance(package["summary"], str) and len(package["summary"]) > 10


def test_package_reports_have_diagnostics():
    package = build_visual_package(SCRIPTED_IDEA, niche="Psychology")
    pacing = package["pacing_report"]
    assert pacing["scene_count"] == len(package["scenes"])
    assert pacing["cuts_per_10s"] > 0
    assert pacing["verdict"]
    camera = package["camera_plan"]
    assert len(camera["shots"]) == len(package["scenes"])
    assert 0 <= camera["variety_score"] <= 100
    motion = package["motion_report"]
    assert motion["level"] in ("low", "medium", "high")
    assert motion["peak_intensity"] >= motion["average_intensity"]


def test_package_is_deterministic():
    first = build_visual_package(SCRIPTED_IDEA, niche="Psychology")
    second = build_visual_package(SCRIPTED_IDEA, niche="Psychology")
    assert first == second


def test_richer_scripted_idea_outscores_bare_idea():
    rich = build_visual_package(SCRIPTED_IDEA, niche="Psychology")
    bare = build_visual_package(BARE_IDEA, niche="Psychology")
    assert rich["visual_score"] >= bare["visual_score"]


# --- Engine + pipeline --------------------------------------------------------------

def test_engine_attaches_package_to_every_candidate():
    context = {
        "candidates": [dict(SCRIPTED_IDEA), dict(BARE_IDEA)],
        "niche": "Psychology",
        "subject": "procrastination",
        "target_platform": "tiktok",
    }
    updates = registry.get_engine("visual_intelligence").run(context)
    for candidate in updates["candidates"]:
        package = candidate["visual_package"]
        assert 0 <= candidate["visual_score"] <= 100
        assert package["aspect_ratio"] == "9:16"
        assert len(candidate["thumbnail_concepts"]) == 5
    summary = updates["visual_intelligence_summary"]
    assert summary["planned"] == 2
    assert summary["platform"] == "tiktok"
    assert summary["total_scenes"] > 0


def test_engine_handles_empty_candidates():
    assert registry.get_engine("visual_intelligence").run({"candidates": []}) == {}
    assert registry.get_engine("visual_intelligence").run({}) == {}


def test_visual_intelligence_runs_after_script_generation_and_before_attention_graph():
    for workflow_key in ("intelligence", "full_content"):
        steps = WORKFLOWS[workflow_key]
        assert "visual_intelligence" in steps
        assert steps.index("script_generation") < steps.index("visual_intelligence") < steps.index("attention_graph")


def test_intelligence_pipeline_attaches_visual_package_to_every_idea():
    context = _run_pipeline()
    assert "visual_intelligence_summary" in context
    for idea in context["ideas"]:
        package = idea["visual_package"]
        assert 0 <= package["visual_score"] <= 100
        assert package["scenes"]
        assert package["scenes"][0]["purpose"] == "hook"
        assert len(package["thumbnails"]) == 5
        assert len(package["hook_sequence"]["frames"]) == 5
        assert 0 <= idea["visual_score"] <= 100
