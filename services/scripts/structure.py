"""Structured script output — the clean handoff contract for Visual Intelligence.

One winning script variant becomes one JSON-safe `structured_script` dict
with exactly the fields the visual pipeline (and any future consumer) needs:
title, hook, narration, scene breakdown, timestamps, emotional beats, visual
notes, CTA, and platform format. Everything is derived from data the Script
Engine already produces — this module only assembles it into one canonical
shape, so consumers stop reaching into scattered variant/candidate keys.

Scene timing is allocated proportionally to each section's word count
against the variant's estimated runtime, so boundaries are contiguous and
the last scene always ends exactly at the total runtime.
"""

from __future__ import annotations

from services.scripts.models import PlatformSpec, ScriptVariant

# The canonical top-level fields of every structured script.
STRUCTURED_SCRIPT_FIELDS = (
    "title",
    "hook",
    "narration",
    "scene_breakdown",
    "timestamps",
    "emotional_beats",
    "visual_notes",
    "cta",
    "platform_format",
)

# Script sections in narrative order → the seed of the visual storyboard.
SECTION_ORDER = (
    ("hook", "hook"),
    ("pattern_interrupt", "pattern_interrupt"),
    ("curiosity_loop", "curiosity_loop"),
    ("core_story", "core_story"),
    ("call_to_action", "cta"),
)


def _scene_breakdown(variant: ScriptVariant, runtime_sec: int) -> list:
    sections = [
        (section_name, getattr(variant, attr).strip())
        for attr, section_name in SECTION_ORDER
        if getattr(variant, attr, "").strip()
    ]
    total_words = sum(len(text.split()) for _, text in sections) or 1
    arc = variant.emotional_progression or ["curiosity"]
    visuals = variant.visual_prompts or []
    broll = variant.broll_suggestions or []

    scenes = []
    cursor = 0.0
    for number, (section, text) in enumerate(sections, start=1):
        share = len(text.split()) / total_words
        start = round(cursor, 1)
        end = round(cursor + share * runtime_sec, 1)
        if number == len(sections):
            end = float(runtime_sec)  # absorb rounding so the last scene closes the runtime
        visual_note = visuals[(number - 1) % len(visuals)] if visuals else ""
        if broll:
            broll_note = broll[(number - 1) % len(broll)]
            visual_note = f"{visual_note} B-roll: {broll_note}" if visual_note else f"B-roll: {broll_note}"
        scenes.append(
            {
                "scene": number,
                "section": section,
                "narration": text,
                "start_sec": start,
                "end_sec": end,
                "duration_sec": round(end - start, 1),
                "emotion": arc[(number - 1) % len(arc)],
                "visual_note": visual_note,
                "sound_effect": variant.sound_effects[(number - 1) % len(variant.sound_effects)]
                if variant.sound_effects
                else "",
            }
        )
        cursor = end
    return scenes


def build_structured_script(idea: dict, variant: ScriptVariant, spec: PlatformSpec) -> dict:
    """Assemble the canonical structured output for one scripted idea."""
    runtime = int(variant.estimated_runtime_sec or spec.target_runtime_sec)
    scenes = _scene_breakdown(variant, runtime)
    return {
        "title": idea.get("title", ""),
        "hook": variant.hook,
        "narration": variant.full_script,
        "scene_breakdown": scenes,
        "timestamps": {
            "estimated_runtime_sec": runtime,
            "scene_boundaries_sec": [scene["start_sec"] for scene in scenes] + [float(runtime)],
            "retention_checkpoints": list(variant.retention_checkpoints),
        },
        "emotional_beats": list(variant.emotional_progression),
        "visual_notes": {
            "ai_visual_prompts": list(variant.visual_prompts),
            "broll_suggestions": list(variant.broll_suggestions),
            "sound_effects": list(variant.sound_effects),
            "music_style": variant.music_style,
        },
        "cta": variant.call_to_action,
        "platform_format": spec.to_dict(),
    }
