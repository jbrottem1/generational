"""Voice & Audio service — the sound brain of the pipeline.

Public API for turning any scripted idea (ideally one that already carries
a Visual Production Package) into a complete Audio Production Package:
voice style, narration plan with per-scene pacing / pauses / emphasis, SFX
recommendations, background music direction, audio mood, a scene-by-scene
audio cue sheet, and retention pacing notes. The `voice_audio` pipeline
engine is a thin wrapper around this module; it is equally usable
standalone (e.g. re-planning the audio of an approved idea for a different
platform):

    from services.audio import build_audio_package

    package = build_audio_package(idea, niche="Science",
                                  subject="black holes", platform="tiktok")
    cue_sheet = package["scene_cues"]

No audio files are generated — every downstream audio renderer (TTS, music
provider, sound designer) consumes this package as its brief.
"""

from __future__ import annotations

from services.audio.models import REQUIRED_CUE_COMPONENTS, AudioSceneCue
from services.audio.music import (
    DEFAULT_AUDIO_MOOD,
    DEFAULT_MUSIC_STYLE,
    EMOTION_AUDIO_MOODS,
    PURPOSE_MUSIC_SECTIONS,
    build_audio_mood,
    build_music_direction,
)
from services.audio.narration import (
    PURPOSE_DELIVERY,
    build_narration_plan,
    pace_label,
    pick_emphasis,
    plan_pauses,
    target_wpm,
)
from services.audio.package import (
    AUDIO_SCORE_WEIGHTS,
    build_audio_package,
    build_scene_cues,
    overall_audio_score,
)
from services.audio.retention import (
    IDEAL_EVENTS_PER_10S_HIGH,
    IDEAL_EVENTS_PER_10S_LOW,
    build_retention_notes,
)
from services.audio.sfx import PURPOSE_SFX_LAYERS, build_sfx_plan, plan_scene_sfx
from services.audio.voice import (
    DEFAULT_VOICE_STYLE,
    NICHE_VOICE_STYLES,
    select_voice_style,
)

__all__ = [
    "AUDIO_SCORE_WEIGHTS",
    "AudioSceneCue",
    "DEFAULT_AUDIO_MOOD",
    "DEFAULT_MUSIC_STYLE",
    "DEFAULT_VOICE_STYLE",
    "EMOTION_AUDIO_MOODS",
    "IDEAL_EVENTS_PER_10S_HIGH",
    "IDEAL_EVENTS_PER_10S_LOW",
    "NICHE_VOICE_STYLES",
    "PURPOSE_DELIVERY",
    "PURPOSE_MUSIC_SECTIONS",
    "PURPOSE_SFX_LAYERS",
    "REQUIRED_CUE_COMPONENTS",
    "build_audio_mood",
    "build_audio_package",
    "build_music_direction",
    "build_narration_plan",
    "build_retention_notes",
    "build_scene_cues",
    "build_sfx_plan",
    "overall_audio_score",
    "pace_label",
    "pick_emphasis",
    "plan_pauses",
    "plan_scene_sfx",
    "select_voice_style",
    "target_wpm",
]
