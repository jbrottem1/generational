"""Audio Production Package — the complete sound plan for one idea.

Assembles everything the future audio renderer (and the video renderer
after it) will consume: voice style, narration plan with per-scene pacing /
pauses / emphasis, SFX recommendations, background music direction, audio
mood progression, a scene-by-scene audio cue sheet, retention pacing notes,
and one weighted Overall Audio Score (0-100) with a plain-English summary.

No audio is generated here — this is the planning layer that makes
generation possible, exactly as the Visual Production Package is for images
and video.
"""

from __future__ import annotations

from engines.heuristics import clamp
from services.audio.models import AudioSceneCue
from services.audio.music import build_audio_mood, build_music_direction
from services.audio.narration import build_narration_plan
from services.audio.retention import build_retention_notes
from services.audio.sfx import build_sfx_plan
from services.audio.voice import select_voice_style
from services.scripts import DEFAULT_PLATFORM, get_platform_spec
from services.visual import plan_scenes

# How much each component contributes to the package's Overall Audio Score.
# Narration carries the most weight because the voice is the retention spine
# of faceless content; retention pacing and sound design follow. Sum == 1.0.
AUDIO_SCORE_WEIGHTS = {
    "narration_fitness": 0.30,
    "retention_audio": 0.20,
    "sfx_coverage": 0.20,
    "music_dynamics": 0.20,
    "mood_variety": 0.10,
}

# The scene-level retention reminder each purpose carries onto its cue.
PURPOSE_RETENTION_NOTES = {
    "hook": "sound must hit inside the first 0.5s — the ear commits before the eye",
    "pattern_interrupt": "hard audio contrast here resets wandering attention",
    "curiosity_loop": "keep the bed sparse so the tease feels unresolved",
    "story_beat": "one audible change in this scene keeps the timeline alive",
    "payoff": "silence before the reveal is the loudest moment in the video",
    "cta": "thin the mix so the ask feels personal and the loop closes calmly",
}


def overall_audio_score(components: dict) -> int:
    """Single weighted 0-100 score from the package components."""
    return clamp(
        sum(components[key] * weight for key, weight in AUDIO_SCORE_WEIGHTS.items()),
        low=0,
        high=100,
    )


def _scenes_for(idea: dict, *, niche: str, subject: str) -> list:
    """Prefer the Visual Intelligence storyboard; plan one standalone otherwise."""
    package = idea.get("visual_package") or {}
    scenes = package.get("scenes") or []
    if scenes:
        return scenes
    return [scene.to_dict() for scene in plan_scenes(idea, niche=niche, subject=subject)]


def build_scene_cues(
    scenes: list,
    *,
    narration_plan: dict,
    sfx_plan: dict,
    music_direction: dict,
    audio_mood: dict,
) -> list:
    """Scene-by-scene audio cue sheet — one merged cue per scene (JSON-safe)."""
    segments = {segment["scene_number"]: segment for segment in narration_plan.get("segments", [])}
    sfx_by_scene = {entry["scene_number"]: entry["cues"] for entry in sfx_plan.get("scenes", [])}
    sections = {section["scene_number"]: section["section"] for section in music_direction.get("sections", [])}
    energies = {point["scene_number"]: point["energy"] for point in music_direction.get("energy_curve", [])}
    moods = {point["scene_number"]: point["mood"] for point in audio_mood.get("progression", [])}

    cues = []
    for scene in scenes:
        number = scene.get("scene_number", 0)
        purpose = scene.get("purpose", "story_beat")
        segment = segments.get(number, {})
        timing = scene.get("caption_timing", {})
        cue = AudioSceneCue(
            scene_number=number,
            purpose=purpose,
            emotion=scene.get("emotion", ""),
            start_sec=timing.get("start_sec", 0.0),
            end_sec=timing.get("end_sec", 0.0),
            narration=scene.get("narration", ""),
            delivery=segment.get("delivery", ""),
            target_wpm=segment.get("target_wpm", 0),
            pace=segment.get("pace", ""),
            pauses=segment.get("pauses", []),
            emphasis=segment.get("emphasis", []),
            sfx=sfx_by_scene.get(number, []),
            music={
                "section": sections.get(number, ""),
                "energy": energies.get(number, 0),
                "ducking": music_direction.get("ducking", ""),
            },
            mood=moods.get(number, ""),
            retention_note=PURPOSE_RETENTION_NOTES.get(purpose, ""),
        )
        cues.append(cue.to_dict())
    return cues


def build_audio_package(
    idea: dict,
    *,
    niche: str = "",
    subject: str = "",
    platform: str = DEFAULT_PLATFORM,
) -> dict:
    """Full Audio Production Package for one scripted idea (JSON-safe dict)."""
    spec = get_platform_spec(platform)
    scenes = _scenes_for(idea, niche=niche, subject=subject)

    voice_style = select_voice_style(scenes, niche=niche, platform_tone=spec.tone)
    narration_plan = build_narration_plan(scenes, base_wpm=spec.words_per_minute, voice_style=voice_style)
    sfx_plan = build_sfx_plan(scenes)
    music_direction = build_music_direction(scenes, music_style=idea.get("music_style", ""))
    audio_mood = build_audio_mood(scenes)
    retention_notes = build_retention_notes(
        scenes,
        sfx_plan=sfx_plan,
        music_direction=music_direction,
        narration_plan=narration_plan,
    )
    scene_cues = build_scene_cues(
        scenes,
        narration_plan=narration_plan,
        sfx_plan=sfx_plan,
        music_direction=music_direction,
        audio_mood=audio_mood,
    )

    components = {
        "narration_fitness": narration_plan["pacing_fitness"],
        "retention_audio": retention_notes["fitness"],
        "sfx_coverage": sfx_plan["coverage_score"],
        "music_dynamics": clamp(45 + music_direction["dynamic_range"] * 1.2, low=10, high=95),
        "mood_variety": audio_mood["variety_score"],
    }
    score = overall_audio_score(components)

    label = idea.get("title") or idea.get("hook") or "This idea"
    bpm_low, bpm_high = music_direction["bpm_range"]
    summary = (
        f"\"{label}\" — Audio Score {score}/100 across {len(scenes)} scenes. "
        f"Voice: {voice_style['persona']} ({voice_style['energy']} energy). "
        f"Music: {music_direction['style']}, {bpm_low}-{bpm_high} BPM {music_direction['key_mode']}. "
        f"Retention: {retention_notes['verdict']}."
    )

    return {
        "audio_score": score,
        "score_components": components,
        "summary": summary,
        "platform": spec.key,
        "voice_style": voice_style,
        "narration_plan": narration_plan,
        "pacing": {
            "base_wpm": narration_plan["base_wpm"],
            "scene_wpm": [
                {"scene_number": segment["scene_number"], "target_wpm": segment["target_wpm"], "pace": segment["pace"]}
                for segment in narration_plan["segments"]
            ],
            "average_wpm_deviation": narration_plan["average_wpm_deviation"],
            "verdict": narration_plan["pacing_verdict"],
            "fitness": narration_plan["pacing_fitness"],
        },
        "pause_map": [
            {"scene_number": segment["scene_number"], "pauses": segment["pauses"]}
            for segment in narration_plan["segments"]
        ],
        "emphasis_map": [
            {"scene_number": segment["scene_number"], "emphasis": segment["emphasis"]}
            for segment in narration_plan["segments"]
        ],
        "sfx_plan": sfx_plan,
        "music_direction": music_direction,
        "audio_mood": audio_mood,
        "scene_cues": scene_cues,
        "retention_notes": retention_notes,
    }
