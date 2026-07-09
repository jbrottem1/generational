"""Tests for the Visual Intelligence Engine (the Cinematic AI Director)."""

import engines  # noqa: F401 - importing registers all engines
from core.workflows import WORKFLOWS, WorkflowEngine
from engines import registry
from services.visual import (
    HOOK_FRAME_COUNT,
    IMAGE_MODELS,
    PACKAGE_SCORE_WEIGHTS,
    RENDER_PACKAGE_VERSION,
    REQUIRED_SCENE_COMPONENTS,
    SHOT_TYPES,
    THUMBNAIL_ARCHETYPES,
    THUMBNAIL_SCORE_KEYS,
    THUMBNAIL_SCORE_WEIGHTS,
    VIDEO_MODELS,
    VISUAL_DIMENSION_KEYS,
    VISUAL_DIMENSION_LABELS,
    VISUAL_SCORE_WEIGHTS,
    AssetSourceAdapter,
    attention_level_for,
    build_hook_sequence,
    build_image_prompts,
    build_shot_list,
    build_thumbnail_concepts,
    build_video_prompts,
    build_visual_package,
    expected_ctr_pct,
    get_source,
    get_style,
    plan_scenes,
    predict_scene_retention,
    register_source,
    register_style,
    resolve_style,
    scene_visual_score,
    score_scene_visuals,
    source_keys,
    style_keys,
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
        "curiosity", "pattern_interrupt", "contrast", "novelty",
        "human_faces", "eye_contact", "motion", "scale", "speed",
        "emotional_color", "negative_space", "visual_hierarchy",
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


def test_eye_contact_dimension_rewards_direct_address():
    away = {"narration": "a landscape", "visual_description": "wide valley at dawn"}
    direct = {"narration": "a person", "visual_description": "subject locks eyes into the camera, direct eye contact with the lens"}
    assert score_scene_visuals(direct)["eye_contact"] > score_scene_visuals(away)["eye_contact"]


def test_pattern_interrupt_purposes_score_higher():
    beat = {"narration": "the middle of the story", "purpose": "story_beat"}
    interrupt = {"narration": "the middle of the story", "purpose": "pattern_interrupt"}
    assert score_scene_visuals(interrupt)["pattern_interrupt"] > score_scene_visuals(beat)["pattern_interrupt"]


# --- Predicted retention --------------------------------------------------------

def test_retention_decays_with_scene_position():
    scene = {"narration": "a beat", "length_sec": 5.0, "visual_score": 60}
    early = predict_scene_retention(scene, scene_index=0, total_scenes=8)
    late = predict_scene_retention(scene, scene_index=7, total_scenes=8)
    assert 0 <= late < early <= 100


def test_strong_visuals_slow_retention_decay():
    weak = {"narration": "a beat", "length_sec": 5.0, "visual_score": 30}
    strong = {"narration": "a beat", "length_sec": 5.0, "visual_score": 90}
    index = 3
    assert predict_scene_retention(strong, scene_index=index, total_scenes=8) > predict_scene_retention(
        weak, scene_index=index, total_scenes=8
    )


def test_attention_graph_hook_signal_shifts_first_scene_retention():
    scene = {"narration": "the hook", "length_sec": 3.0, "visual_score": 60, "purpose": "hook"}
    strong_hook = {"scores": {"first_3_second_hook": 90, "rewatch_probability": 50}}
    weak_hook = {"scores": {"first_3_second_hook": 20, "rewatch_probability": 50}}
    assert predict_scene_retention(scene, scene_index=0, total_scenes=6, attention=strong_hook) > (
        predict_scene_retention(scene, scene_index=0, total_scenes=6, attention=weak_hook)
    )


def test_attention_levels_bucket_correctly():
    assert attention_level_for(90) == "high"
    assert attention_level_for(60) == "medium"
    assert attention_level_for(30) == "low"


# --- Style presets --------------------------------------------------------------

def test_all_15_required_styles_registered():
    expected = {
        "documentary", "luxury", "minimal", "dark_history", "cyberpunk",
        "corporate", "nature", "science", "psychology", "finance",
        "horror", "conspiracy", "modern_tech", "motivational", "cinematic",
    }
    assert expected <= set(style_keys())
    for key in expected:
        preset = get_style(key)
        for field in ("label", "palette", "lighting_bias", "art_style", "grade", "overlay_style", "caption_style", "mood"):
            assert preset[field], f"{key}.{field}"


def test_resolve_style_prefers_override_then_niche_then_default():
    key, _ = resolve_style(style_key="horror", niche="Science")
    assert key == "horror"
    key, _ = resolve_style(niche="Science")
    assert key == "science"
    key, _ = resolve_style(niche="Unknown Niche")
    assert key == "cinematic"


def test_future_engines_can_register_new_styles():
    register_style(
        "test_brand",
        {
            "label": "Test Brand",
            "palette": "brand blue and white",
            "lighting_bias": "soft key",
            "art_style": "flat vector",
            "grade": "clean",
            "overlay_style": "brand sans",
            "caption_style": "brand captions",
            "mood": "friendly",
        },
    )
    key, preset = resolve_style(style_key="test_brand")
    assert key == "test_brand" and preset["label"] == "Test Brand"
    scenes = plan_scenes(SCRIPTED_IDEA, niche="Psychology", style_key="test_brand")
    assert scenes[0].visual_style == "test_brand"
    assert "brand blue" in scenes[0].color_palette


# --- Shot list --------------------------------------------------------------

def test_all_14_professional_shot_types_exist():
    expected = {
        "wide", "medium", "close_up", "extreme_close_up", "drone", "pov",
        "tracking", "orbit", "push_in", "pull_out", "static", "macro",
        "slow_motion", "hyperlapse",
    }
    assert set(SHOT_TYPES) == expected
    for shot in SHOT_TYPES.values():
        assert shot["lens"] and shot["depth_of_field"] and shot["camera_motion"]
        assert 0 <= shot["motion_intensity"] <= 100


def test_shot_list_covers_every_scene_with_valid_shots():
    scenes = [scene.to_dict() for scene in plan_scenes(SCRIPTED_IDEA, niche="Psychology")]
    shot_list = build_shot_list(scenes)
    assert len(shot_list) == len(scenes)
    for shot in shot_list:
        assert shot["shot_type"] in SHOT_TYPES
        assert shot["lens"] and shot["depth_of_field"]
        assert shot["duration_sec"] > 0


def test_story_beats_rotate_shot_types():
    scenes = plan_scenes(SCRIPTED_IDEA, niche="Psychology")
    beat_shots = [scene.shot_type for scene in scenes if scene.purpose == "story_beat"]
    if len(beat_shots) >= 2:
        assert len(set(beat_shots)) > 1


# --- Asset source adapters --------------------------------------------------------

def test_all_6_asset_sources_registered():
    expected = {"ai_image", "ai_video", "stock_footage", "user_asset", "brand_asset", "avatar"}
    assert expected <= set(source_keys())


def test_avatar_source_reserved_but_unavailable():
    avatar = get_source("avatar")
    assert avatar is not None
    assert avatar.is_available() is False


def test_asset_requests_route_through_adapters():
    package = build_visual_package(SCRIPTED_IDEA, niche="Psychology")
    requests = package["asset_requests"]
    assert len(requests) == len(package["scenes"])
    for request, scene in zip(requests, package["scenes"]):
        assert request["scene_number"] == scene["scene_number"]
        assert request["source"] in source_keys()
        assert request["source"] != "avatar"  # unavailable sources fall back
        if request["source"] == "ai_image":
            assert request["prompt"]
        if request["source"] == "stock_footage":
            assert request["query"]


def test_future_engines_can_register_new_sources():
    class TestSource(AssetSourceAdapter):
        key = "test_source"
        label = "Test Source"
        asset_kind = "image"

        def build_request(self, scene):
            request = self._base_request(scene)
            request["custom"] = True
            return request

    register_source(TestSource())
    assert "test_source" in source_keys()
    request = get_source("test_source").build_request({"scene_number": 1, "length_sec": 3.0})
    assert request["custom"] is True and request["source"] == "test_source"


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
        assert 0 <= data["predicted_retention"] <= 100
        assert data["attention_level"] in ("high", "medium", "low")
        assert data["shot_type"] in SHOT_TYPES
        assert data["lens_recommendation"]
        assert data["depth_of_field"]
        assert data["asset_type"] in source_keys()
        assert data["ai_image_prompt"] and data["ai_video_prompt"]
        assert data["stock_footage_query"]
        assert data["caption_placement"]
        assert "at_sec" in data["sfx_timing"]


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


def test_hook_and_payoff_flagged_as_thumbnail_candidates():
    scenes = plan_scenes(SCRIPTED_IDEA, niche="Psychology")
    by_purpose = {scene.purpose: scene for scene in scenes}
    assert by_purpose["hook"].thumbnail_candidate is True
    assert by_purpose["payoff"].thumbnail_candidate is True
    assert by_purpose["cta"].thumbnail_candidate is False


def test_plan_scenes_works_without_script_variants():
    scenes = plan_scenes(BARE_IDEA, niche="Science")
    assert scenes
    assert scenes[0].purpose == "hook"


def test_scene_planning_is_deterministic():
    first = [scene.to_dict() for scene in plan_scenes(SCRIPTED_IDEA, niche="Psychology")]
    second = [scene.to_dict() for scene in plan_scenes(SCRIPTED_IDEA, niche="Psychology")]
    assert first == second


def test_plan_scenes_prefers_structured_script():
    structured_idea = dict(SCRIPTED_IDEA)
    structured_idea["structured_script"] = {
        "scene_breakdown": [
            {"scene": 1, "section": "hook", "narration": "The structured hook line.", "duration_sec": 3.0},
            {"scene": 2, "section": "core_story", "narration": "The structured core story sentence. Another one.", "duration_sec": 20.0},
            {"scene": 3, "section": "cta", "narration": "The structured call to action.", "duration_sec": 3.0},
        ]
    }
    scenes = plan_scenes(structured_idea, niche="Psychology")
    assert scenes[0].narration == "The structured hook line."
    assert scenes[0].purpose == "hook"
    assert scenes[-1].purpose == "cta"
    assert any(scene.purpose == "payoff" for scene in scenes)


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


def test_prompt_lens_follows_the_shot_table():
    scenes = [scene.to_dict() for scene in plan_scenes(SCRIPTED_IDEA, niche="Psychology")]
    prompt_sets = build_image_prompts(scenes, niche="Psychology", aspect_ratio="9:16")
    for scene, prompt_set in zip(scenes, prompt_sets):
        assert prompt_set["spec"]["lens"] == scene["lens_recommendation"]


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
        assert 0 < concept.click_probability_pct <= 14.0


def test_thumbnail_concepts_carry_full_click_design_brief():
    for concept in build_thumbnail_concepts(SCRIPTED_IDEA):
        assert concept.title_overlay
        assert concept.emotion
        assert concept.color_strategy
        assert concept.focal_subject
        assert concept.eye_direction
        assert concept.contrast_score == concept.scores["contrast"]
        # Back-compat mirrors stay in sync for the UI and audio engine.
        assert concept.text_overlay == concept.title_overlay
        assert concept.expected_ctr_pct == concept.click_probability_pct


def test_thumbnails_sorted_best_first():
    concepts = build_thumbnail_concepts(SCRIPTED_IDEA)
    overalls = [concept.overall for concept in concepts]
    assert overalls == sorted(overalls, reverse=True)


def test_click_probability_scales_with_overall_score():
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
        "visual_score", "score_components", "summary", "aspect_ratio", "visual_style",
        "style_preset", "color_palette", "storyboard", "scenes", "shot_list",
        "asset_requests", "image_prompts", "video_prompts", "thumbnails",
        "hook_sequence", "caption_plan", "pacing_report", "camera_plan",
        "transitions", "motion_report", "retention_curve", "render_package",
    }
    assert set(package) == expected_keys
    assert 0 <= package["visual_score"] <= 100
    assert len(package["storyboard"]) == len(package["scenes"])
    assert len(package["shot_list"]) == len(package["scenes"])
    assert len(package["caption_plan"]) == len(package["scenes"])
    assert len(package["transitions"]) == len(package["scenes"]) - 1
    assert len(package["thumbnails"]) == 5
    assert isinstance(package["summary"], str) and len(package["summary"]) > 10


def test_package_style_flows_into_every_scene():
    package = build_visual_package(SCRIPTED_IDEA, niche="Psychology", style_key="cyberpunk")
    assert package["visual_style"] == "cyberpunk"
    for scene in package["scenes"]:
        assert scene["visual_style"] == "cyberpunk"
        assert "neon" in scene["color_palette"]


def test_package_retention_curve_covers_every_scene():
    package = build_visual_package(SCRIPTED_IDEA, niche="Psychology")
    curve = package["retention_curve"]
    assert len(curve["points"]) == len(package["scenes"])
    assert 0 <= curve["average_retention"] <= 100
    assert 0 <= curve["final_retention"] <= 100
    assert curve["weakest_scene_number"] in {scene["scene_number"] for scene in package["scenes"]}


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


# --- Render Package --------------------------------------------------------------

def test_render_package_is_machine_consumable():
    package = build_visual_package(SCRIPTED_IDEA, niche="Psychology")
    render = package["render_package"]
    assert render["render_package_version"] == RENDER_PACKAGE_VERSION
    assert render["clip_count"] == len(package["scenes"])
    assert render["total_duration_sec"] > 0
    assert render["aspect_ratio"] == package["aspect_ratio"]
    assert render["style"] == package["visual_style"]
    assert render["thumbnail_brief"] == package["thumbnails"][0]
    for clip, scene in zip(render["clips"], package["scenes"]):
        assert clip["clip_number"] == scene["scene_number"]
        assert clip["end_sec"] > clip["start_sec"]
        assert clip["asset_request"]["source"] in source_keys()
        assert clip["caption"]["text"] == scene["narration"]
        assert clip["transition_out"] == scene["transition_out"]


def test_render_clips_form_contiguous_timeline():
    render = build_visual_package(SCRIPTED_IDEA, niche="Psychology")["render_package"]
    clips = render["clips"]
    assert clips[0]["start_sec"] == 0.0
    for previous, current in zip(clips, clips[1:]):
        assert current["start_sec"] == previous["end_sec"]


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
    assert 0 <= summary["average_predicted_retention"] <= 100
    assert summary["style"] in style_keys()


def test_engine_honors_context_style_override():
    context = {
        "candidates": [dict(SCRIPTED_IDEA)],
        "niche": "Psychology",
        "visual_style": "horror",
    }
    updates = registry.get_engine("visual_intelligence").run(context)
    assert updates["candidates"][0]["visual_package"]["visual_style"] == "horror"


def test_engine_handles_empty_candidates():
    assert registry.get_engine("visual_intelligence").run({"candidates": []}) == {}
    assert registry.get_engine("visual_intelligence").run({}) == {}


def test_visual_intelligence_runs_after_attention_graph_and_before_voice_audio():
    for workflow_key in ("intelligence", "full_content"):
        steps = WORKFLOWS[workflow_key]
        assert "visual_intelligence" in steps
        assert (
            steps.index("script_generation")
            < steps.index("attention_graph")
            < steps.index("visual_intelligence")
            < steps.index("voice_audio")
        )


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


def test_pipeline_director_consumes_all_four_upstream_inputs():
    """Integration: trend niche, psychology, structured script, and attention
    graph signals all shape the Visual Production Package."""
    context = _run_pipeline()
    for idea in context["ideas"]:
        assert idea.get("structured_script"), "Script Engine handoff missing"
        assert idea.get("attention_graph"), "Attention Graph must run before the Director"
        package = idea["visual_package"]
        # Structured script consumed: first scene narration matches the hook section.
        first_section = idea["structured_script"]["scene_breakdown"][0]
        assert package["scenes"][0]["narration"] == first_section["narration"]
        # Attention consumed: every scene carries a retention prediction + level.
        for scene in package["scenes"]:
            assert 0 <= scene["predicted_retention"] <= 100
            assert scene["attention_level"] in ("high", "medium", "low")
        # Render handoff present and aligned.
        assert package["render_package"]["clip_count"] == len(package["scenes"])
