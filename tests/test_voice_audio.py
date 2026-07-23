"""Tests for the Voice & Audio Engine (audio planning brain)."""

import engines  # noqa: F401 - importing registers all engines
from core.workflows import WORKFLOWS, WorkflowEngine
from engines import registry
from services.audio import (
    AUDIO_SCORE_WEIGHTS,
    IDEAL_EVENTS_PER_10S_HIGH,
    IDEAL_EVENTS_PER_10S_LOW,
    NICHE_VOICE_STYLES,
    PURPOSE_DELIVERY,
    REQUIRED_CUE_COMPONENTS,
    build_audio_mood,
    build_audio_package,
    build_music_direction,
    build_narration_plan,
    build_retention_notes,
    build_sfx_plan,
    pick_emphasis,
    plan_pauses,
    plan_scene_sfx,
    select_voice_style,
    target_wpm,
)
from services.visual import build_visual_package, plan_scenes

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


def _scenes(idea=SCRIPTED_IDEA):
    return [scene.to_dict() for scene in plan_scenes(idea, niche="Psychology", subject="procrastination")]


def _run_pipeline():
    context = {"command": COMMAND, "count": 5, "model": ""}
    run = WorkflowEngine().execute("intelligence", context)
    assert run.succeeded, run.summary()
    return context


# --- Voice style --------------------------------------------------------------

def test_every_niche_voice_style_is_complete():
    for niche, style in NICHE_VOICE_STYLES.items():
        for field in ("persona", "tone", "pitch", "character"):
            assert style[field], f"{niche}.{field}"


def test_voice_style_carries_energy_arc_and_platform_tone():
    scenes = _scenes()
    style = select_voice_style(scenes, niche="Psychology", platform_tone="conversational and raw")
    assert style["persona"] == NICHE_VOICE_STYLES["Psychology"]["persona"]
    assert style["energy"] in ("low", "medium", "high")
    assert style["emotional_arc"] == f"{scenes[0]['emotion']} → {scenes[-1]['emotion']}"
    assert any("conversational and raw" in note for note in style["delivery_notes"])


def test_unknown_niche_falls_back_to_default_style():
    style = select_voice_style(_scenes(), niche="Underwater Basket Weaving")
    assert style["persona"]
    assert style["energy"] in ("low", "medium", "high")


# --- Narration plan: pacing, pauses, emphasis ---------------------------------

def test_purpose_wpm_modulation_orders_hook_above_payoff():
    base = 160
    assert target_wpm("hook", base) > target_wpm("story_beat", base) > target_wpm("payoff", base)


def test_plan_pauses_always_includes_purpose_pause_and_reacts_to_questions():
    plain = plan_pauses("A simple statement.", "story_beat")
    assert len(plain) == 1
    assert plain[0]["duration_sec"] > 0 and plain[0]["reason"]
    questioning = plan_pauses("Why does this happen? Nobody knows.", "story_beat")
    assert len(questioning) == 2
    assert any("question" in pause["at"] for pause in questioning)


def test_payoff_gets_the_longest_dramatic_pause():
    durations = {
        purpose: PURPOSE_DELIVERY[purpose]["pause"]["duration_sec"]
        for purpose in PURPOSE_DELIVERY
    }
    assert durations["payoff"] == max(durations.values())


def test_emphasis_prefers_numbers_and_trigger_words():
    picks = pick_emphasis("The secret study followed 2,000 people for 10 years.")
    assert "2,000" in picks
    assert "secret" in picks
    assert len(picks) <= 4


def test_emphasis_falls_back_to_content_words():
    picks = pick_emphasis("Gentle sentences about ordinary furniture placement.")
    assert picks


def test_narration_plan_covers_every_scene_with_delivery_and_wpm():
    scenes = _scenes()
    plan = build_narration_plan(scenes, base_wpm=160, voice_style={"persona": "test narrator"})
    assert len(plan["segments"]) == len(scenes)
    for segment in plan["segments"]:
        assert segment["delivery"]
        assert segment["target_wpm"] > 0
        assert segment["pace"] in ("fast", "steady", "measured")
        assert segment["pauses"]
    assert plan["voice_persona"] == "test narrator"
    assert plan["total_words"] > 0
    assert 0 <= plan["pacing_fitness"] <= 100
    assert plan["pacing_verdict"]


# --- Sound effects --------------------------------------------------------------

def test_scene_sfx_keeps_storyboard_primary_effect_and_adds_layers():
    scenes = _scenes()
    hook = scenes[0]
    cues = plan_scene_sfx(hook)
    assert cues[0]["layer"] == "primary"
    assert cues[0]["effect"] == hook["sound_effect"]
    assert cues[0]["intensity"] == "high"
    assert len(cues) >= 2  # purpose layer on top of the primary


def test_sfx_plan_covers_all_scenes_with_diagnostics():
    scenes = _scenes()
    plan = build_sfx_plan(scenes)
    assert len(plan["scenes"]) == len(scenes)
    assert plan["scene_coverage_pct"] == 100.0
    assert plan["total_cues"] >= len(scenes)
    assert 0 <= plan["coverage_score"] <= 100
    assert plan["mix_note"]


# --- Music direction + mood --------------------------------------------------------------

def test_music_direction_has_tempo_key_sections_and_energy_curve():
    scenes = _scenes()
    direction = build_music_direction(scenes, music_style="cinematic tension build")
    assert direction["style"] == "cinematic tension build"
    low, high = direction["bpm_range"]
    assert 60 <= low < high <= 150
    assert direction["key_mode"] in ("major", "minor")
    assert len(direction["energy_curve"]) == len(scenes)
    assert len(direction["sections"]) == len(scenes)
    for point in direction["energy_curve"]:
        assert 0 <= point["energy"] <= 100
    assert direction["ducking"]


def test_tense_arc_selects_minor_key():
    scenes = _scenes()  # arc includes tension
    assert build_music_direction(scenes)["key_mode"] == "minor"


def test_payoff_scene_carries_peak_music_section():
    scenes = _scenes()
    direction = build_music_direction(scenes)
    payoff = next(scene for scene in scenes if scene["purpose"] == "payoff")
    section = next(s for s in direction["sections"] if s["scene_number"] == payoff["scene_number"])
    assert "swell" in section["section"]


def test_audio_mood_progression_matches_scenes():
    scenes = _scenes()
    mood = build_audio_mood(scenes)
    assert len(mood["progression"]) == len(scenes)
    assert mood["overall"].startswith("opens on")
    for point in mood["progression"]:
        assert point["mood"]
    assert 0 <= mood["variety_score"] <= 100


# --- Retention pacing notes --------------------------------------------------------------

def test_retention_notes_audit_hook_payoff_and_cta():
    scenes = _scenes()
    plan = build_narration_plan(scenes, base_wpm=160, voice_style={})
    sfx = build_sfx_plan(scenes)
    music = build_music_direction(scenes)
    notes = build_retention_notes(scenes, sfx_plan=sfx, music_direction=music, narration_plan=plan)
    text = " ".join(notes["notes"])
    assert "Scene 1" in text
    assert "silence before the payoff" in text
    assert "CTA" in text
    assert notes["audio_events"] > 0
    assert notes["events_per_10s"] > 0
    assert 0 <= notes["fitness"] <= 100
    assert notes["verdict"]


def test_retention_ideal_window_is_sane():
    assert 0 < IDEAL_EVENTS_PER_10S_LOW < IDEAL_EVENTS_PER_10S_HIGH


def test_retention_notes_handle_empty_scenes():
    empty = build_retention_notes([], sfx_plan={}, music_direction={}, narration_plan={})
    assert empty["notes"] == []
    assert empty["fitness"] == 0


# --- Audio Production Package --------------------------------------------------------------

def test_audio_weights_sum_to_one():
    assert round(sum(AUDIO_SCORE_WEIGHTS.values()), 6) == 1.0


def test_build_audio_package_shape():
    package = build_audio_package(SCRIPTED_IDEA, niche="Psychology", subject="procrastination")
    expected_keys = {
        "audio_score", "score_components", "summary", "platform",
        "voice_style", "narration_plan", "pacing", "pause_map", "emphasis_map",
        "sfx_plan", "music_direction", "audio_mood", "scene_cues", "retention_notes",
    }
    assert set(package) == expected_keys
    assert 0 <= package["audio_score"] <= 100
    assert set(package["score_components"]) == set(AUDIO_SCORE_WEIGHTS)
    assert isinstance(package["summary"], str) and len(package["summary"]) > 10
    assert len(package["pause_map"]) == len(package["scene_cues"])
    assert len(package["emphasis_map"]) == len(package["scene_cues"])


def test_scene_cues_carry_all_required_components():
    package = build_audio_package(SCRIPTED_IDEA, niche="Psychology", subject="procrastination")
    assert len(package["scene_cues"]) >= 4
    for cue in package["scene_cues"]:
        for component in REQUIRED_CUE_COMPONENTS:
            assert component in cue, component
        assert cue["retention_note"]
        assert cue["music"]["section"]


def test_scene_cues_align_with_visual_package_scenes():
    visual = build_visual_package(SCRIPTED_IDEA, niche="Psychology", subject="procrastination")
    idea = dict(SCRIPTED_IDEA, visual_package=visual)
    package = build_audio_package(idea, niche="Psychology", subject="procrastination")
    assert len(package["scene_cues"]) == len(visual["scenes"])
    for cue, scene in zip(package["scene_cues"], visual["scenes"]):
        assert cue["scene_number"] == scene["scene_number"]
        assert cue["start_sec"] == scene["caption_timing"]["start_sec"]
        assert cue["end_sec"] == scene["caption_timing"]["end_sec"]


def test_package_works_without_visual_package():
    package = build_audio_package(BARE_IDEA, niche="Science")
    assert package["scene_cues"]
    assert package["scene_cues"][0]["purpose"] == "hook"


def test_package_respects_platform_base_wpm():
    tiktok = build_audio_package(SCRIPTED_IDEA, niche="Psychology", platform="tiktok")
    facebook = build_audio_package(SCRIPTED_IDEA, niche="Psychology", platform="facebook_reels")
    assert tiktok["platform"] == "tiktok"
    assert tiktok["pacing"]["base_wpm"] > facebook["pacing"]["base_wpm"]


def test_package_is_deterministic():
    first = build_audio_package(SCRIPTED_IDEA, niche="Psychology")
    second = build_audio_package(SCRIPTED_IDEA, niche="Psychology")
    assert first == second


def test_no_final_audio_is_generated():
    package = build_audio_package(SCRIPTED_IDEA, niche="Psychology")
    flat = str(package)
    for extension in (".mp3", ".wav", ".m4a", ".ogg"):
        assert extension not in flat


# --- Engine + pipeline --------------------------------------------------------------

def test_engine_attaches_package_to_every_candidate():
    context = {
        "candidates": [dict(SCRIPTED_IDEA), dict(BARE_IDEA)],
        "niche": "Psychology",
        "subject": "procrastination",
        "target_platform": "tiktok",
    }
    updates = registry.get_engine("voice_audio").run(context)
    for candidate in updates["candidates"]:
        package = candidate["audio_package"]
        assert 0 <= candidate["audio_score"] <= 100
        assert package["platform"] == "tiktok"
        assert package["scene_cues"]
    summary = updates["voice_audio_summary"]
    assert summary["planned"] == 2
    assert summary["platform"] == "tiktok"
    assert summary["total_scene_cues"] > 0


def test_engine_handles_empty_candidates():
    assert registry.get_engine("voice_audio").run({"candidates": []}) == {}
    assert registry.get_engine("voice_audio").run({}) == {}


def test_voice_audio_runs_after_visual_intelligence_and_before_video():
    for workflow_key in ("intelligence", "full_content"):
        steps = WORKFLOWS[workflow_key]
        assert "voice_audio" in steps
        assert steps.index("visual_intelligence") < steps.index("voice_audio")
    full = WORKFLOWS["full_content"]
    assert full.index("voice_audio") < full.index("video")


def test_intelligence_pipeline_attaches_audio_package_to_every_idea():
    context = _run_pipeline()
    assert "voice_audio_summary" in context
    for idea in context["ideas"]:
        package = idea["audio_package"]
        assert 0 <= package["audio_score"] <= 100
        assert package["scene_cues"]
        assert package["scene_cues"][0]["purpose"] == "hook"
        assert package["voice_style"]["persona"]
        assert package["retention_notes"]["notes"]
        assert 0 <= idea["audio_score"] <= 100
