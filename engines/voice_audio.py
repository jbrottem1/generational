"""Voice & Audio Engine — the sound brain of the pipeline.

Runs immediately after Visual Intelligence and before every rendering stage
(voice synthesis, image, video): every scripted candidate that carries a
Visual Production Package receives a complete **Audio Production Package**,
so the eventual renderers execute one canonical sound plan instead of
improvising audio per stage.

Each package contains:

- A **voice style** — niche-matched narrator persona (tone, pitch,
  character, energy) with delivery notes tied to the emotional arc
- A **narration plan** — per-scene delivery direction, target words-per-
  minute (platform base modulated per scene purpose), scripted pauses, and
  emphasis words, plus a global pacing verdict and fitness score
- **Sound effect recommendations** per scene — the storyboard's primary
  effect plus purpose-specific support layers with timing and intensity
- **Background music direction** — style, BPM range, key/mode, per-scene
  energy curve, named sections mapped to scene purposes, ducking guidance
- The **audio mood** — overall mood plus scene-by-scene mood progression
- A **scene-by-scene audio cue sheet** merging narration delivery, SFX,
  music, and mood per scene
- **Retention pacing notes** — an audit of audio events against the
  short-form ideal (a sonic change every 3-6 seconds), with concrete,
  scene-anchored fixes
- One weighted **Overall Audio Score (0-100)**

Planning is delegated to the modular `services/audio` package, which is
equally usable standalone to re-plan audio for any approved idea. All
planning is deterministic — Demo Mode carries the full engine, and no audio
files are generated: this is the brief the future voice/music renderers
will execute.
"""

from __future__ import annotations

from core.log import get_logger, log_event
from engines.base import Engine
from services.audio import build_audio_package
from services.scripts import DEFAULT_PLATFORM

logger = get_logger(__name__)


class VoiceAudioEngine(Engine):
    key = "voice_audio"
    label = "Voice & Audio"
    icon = "🎙️"
    description = (
        "Transform every scripted candidate's visual package into a complete "
        "Audio Production Package — voice style, narration plan (pacing, pauses, "
        "emphasis), SFX recommendations, music direction, audio mood, scene-by-scene "
        "audio cues, retention pacing notes, and an Overall Audio Score (0-100)."
    )

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        candidates = context.get("candidates", [])
        if not candidates:
            return {}

        platform = context.get("target_platform", DEFAULT_PLATFORM)
        niche = context.get("niche", "")
        subject = context.get("subject", "")

        for candidate in candidates:
            package = build_audio_package(
                candidate,
                niche=niche,
                subject=subject,
                platform=platform,
            )
            candidate["audio_package"] = package
            candidate["audio_score"] = package["audio_score"]

        scores = [candidate["audio_score"] for candidate in candidates]
        avg_score = round(sum(scores) / len(scores), 1)
        total_cues = sum(len(c["audio_package"]["scene_cues"]) for c in candidates)

        log_event(
            logger,
            "voice_audio.planned",
            candidates=len(candidates),
            scene_cues=total_cues,
            avg_audio_score=avg_score,
        )
        return {
            "candidates": candidates,
            "voice_audio_summary": {
                "planned": len(candidates),
                "total_scene_cues": total_cues,
                "average_audio_score": avg_score,
                "platform": platform,
            },
        }
