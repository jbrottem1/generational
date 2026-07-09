"""Structured script output — the clean handoff contract for downstream engines.

One winning script variant becomes one JSON-safe `structured_script` dict —
the complete production brief: title, ranked hook + alternates, annotated
sections, a director-ready scene breakdown (camera, motion, captions, sound
cues, transitions), full narration, emotion and attention timelines, voice
instructions, a caption plan, the retention model, CTA, platform format,
and locale. Everything is derived from data the Script Engine already
produces — this module only assembles it into one canonical shape, so
consumers stop reaching into scattered variant/candidate keys.

Scene timing comes from each section's estimated duration, normalized so
boundaries are contiguous and the last scene ends exactly at the total
runtime.
"""

from __future__ import annotations

from services.scripts.models import PlatformSpec, ScriptVariant
from services.scripts.sections import SECTION_SPECS

# The canonical top-level fields of every structured script.
STRUCTURED_SCRIPT_FIELDS = (
    "title",
    "hook",
    "alternate_hooks",
    "sections",
    "narration",
    "scene_breakdown",
    "estimated_runtime_sec",
    "timestamps",
    "emotional_beats",
    "emotion_timeline",
    "attention_timeline",
    "visual_prompts",
    "visual_notes",
    "voice_instructions",
    "caption_plan",
    "retention",
    "cta",
    "platform_format",
    "locale",
)


def _caption_text(narration: str, max_words: int = 8) -> str:
    """The on-screen caption: the narration's first punchy phrase."""
    first_sentence = narration.split(".")[0].split("—")[0].strip()
    words = first_sentence.split()
    text = " ".join(words[:max_words])
    return f"{text}…" if len(words) > max_words else text


def _voice_direction(section: dict) -> str:
    spec = SECTION_SPECS.get(section["key"], {})
    return spec.get("voice_direction", "natural conversational delivery")


def _scene_breakdown(variant: ScriptVariant, runtime_sec: int) -> list:
    """One director-ready scene per section, timed contiguously to runtime."""
    sections = [s for s in variant.sections if s.get("narration", "").strip()]
    total_duration = sum(s["estimated_duration_sec"] for s in sections) or 1.0
    sfx = variant.sound_effects or []

    scenes = []
    cursor = 0.0
    for number, section in enumerate(sections, start=1):
        spec = SECTION_SPECS.get(section["key"], {})
        share = section["estimated_duration_sec"] / total_duration
        start = round(cursor, 1)
        end = round(cursor + share * runtime_sec, 1)
        if number == len(sections):
            end = float(runtime_sec)  # absorb rounding so the last scene closes the runtime
        scenes.append(
            {
                "scene": number,
                "section": section["key"],
                "start_sec": start,
                "end_sec": end,
                "duration_sec": round(end - start, 1),
                "narration": section["narration"],
                "visual_description": section["visual_intent"],
                "broll_type": section["broll_type"],
                "camera_style": spec.get("camera_style", "medium shot"),
                "motion": spec.get("motion", "static"),
                "caption_text": _caption_text(section["narration"]),
                "caption_emphasis": section["caption_emphasis"],
                "sound_cue": sfx[(number - 1) % len(sfx)] if sfx else "",
                "transition": spec.get("transition", "hard cut"),
                "emotion": section.get("emotion", ""),
                "emotional_intensity": section["emotional_intensity"],
                "attention_score": section["attention_score"],
            }
        )
        cursor = end
    return scenes


def _timelines(scenes: list) -> "tuple[list, list]":
    """Emotion and attention timelines sampled at every scene boundary."""
    emotion_timeline = [
        {
            "time_sec": scene["start_sec"],
            "section": scene["section"],
            "emotion": scene["emotion"],
            "intensity": scene["emotional_intensity"],
        }
        for scene in scenes
    ]
    attention_timeline = [
        {
            "time_sec": scene["start_sec"],
            "section": scene["section"],
            "attention_score": scene["attention_score"],
        }
        for scene in scenes
    ]
    return emotion_timeline, attention_timeline


def _voice_instructions(variant: ScriptVariant, spec: PlatformSpec) -> dict:
    intensities = [s["emotional_intensity"] for s in variant.sections] or [50]
    average = sum(intensities) / len(intensities)
    energy = "high" if average >= 75 else "medium" if average >= 55 else "calm"
    return {
        "pace_wpm": spec.words_per_minute,
        "tone": spec.tone,
        "overall_energy": energy,
        "per_section": [
            {
                "section": section["key"],
                "direction": _voice_direction(section),
                "intensity": section["emotional_intensity"],
            }
            for section in variant.sections
        ],
    }


def _caption_plan(scenes: list) -> list:
    return [
        {
            "scene": scene["scene"],
            "start_sec": scene["start_sec"],
            "end_sec": scene["end_sec"],
            "text": scene["caption_text"],
            "emphasis": scene["caption_emphasis"],
        }
        for scene in scenes
    ]


def build_structured_script(idea: dict, variant: ScriptVariant, spec: PlatformSpec) -> dict:
    """Assemble the canonical structured output for one scripted idea."""
    runtime = int(variant.estimated_runtime_sec or spec.target_runtime_sec)
    scenes = _scene_breakdown(variant, runtime)
    emotion_timeline, attention_timeline = _timelines(scenes)
    return {
        "title": idea.get("title", ""),
        "hook": variant.hook,
        "alternate_hooks": list(variant.alternate_hooks),
        "sections": [dict(section) for section in variant.sections],
        "narration": variant.full_script,
        "scene_breakdown": scenes,
        "estimated_runtime_sec": runtime,
        "timestamps": {
            "estimated_runtime_sec": runtime,
            "scene_boundaries_sec": [scene["start_sec"] for scene in scenes] + [float(runtime)],
            "retention_checkpoints": list(variant.retention_checkpoints),
        },
        "emotional_beats": list(variant.emotional_progression),
        "emotion_timeline": emotion_timeline,
        "attention_timeline": attention_timeline,
        "visual_prompts": list(variant.visual_prompts),
        "visual_notes": {
            "ai_visual_prompts": list(variant.visual_prompts),
            "broll_suggestions": list(variant.broll_suggestions),
            "sound_effects": list(variant.sound_effects),
            "music_style": variant.music_style,
        },
        "voice_instructions": _voice_instructions(variant, spec),
        "caption_plan": _caption_plan(scenes),
        "retention": dict(variant.retention_model),
        "cta": variant.call_to_action,
        "platform_format": spec.to_dict(),
        "locale": dict(variant.locale),
    }
