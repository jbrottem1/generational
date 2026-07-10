"""AudioMixer — the multitrack mix plan for one video.

Consumes the Voice & Audio Engine's Audio Production Package (voice style,
scene cues, SFX plan, music direction) plus the render timeline, and emits
the mix instructions a renderer executes: four tracks (narration, music,
SFX, transitions), music ducking under narration, silence drops on payoff
beats, per-track volume levels, and a platform-safe loudness placeholder.
No audio is generated or mixed here — these are instructions.
"""

from __future__ import annotations

from engines.render.transitions import TRANSITION_SOUNDS

# Track levels (dBFS) for a narration-led vertical short.
TRACK_LEVELS_DB = {
    "narration": -3.0,
    "music": -18.0,
    "sfx": -10.0,
    "transitions": -12.0,
}

# Streaming platforms normalize around -14 LUFS integrated; true peak must
# stay under -1 dBTP to survive transcoding. Placeholder until a real
# loudness pass exists.
LOUDNESS_TARGET = {
    "standard": "platform_safe_placeholder",
    "integrated_lufs": -14.0,
    "true_peak_db": -1.0,
    "notes": "Verify with a real loudness pass when actual audio is rendered.",
}

# Ducking: music drops under the voice whenever narration is present.
DUCKING = {
    "enabled": True,
    "trigger": "narration",
    "duck_to_db": -26.0,
    "attack_ms": 150,
    "release_ms": 400,
}

# Scene purposes that earn a full-mix silence drop just before they land.
_SILENCE_DROP_PURPOSES = ("payoff", "pattern_interrupt")
SILENCE_DROP_SEC = 0.4


class AudioMixer:
    """Builds the audio mix plan (instructions, not audio)."""

    def build(
        self,
        scenes: list,
        audio_package: "dict | None" = None,
        timeline: "dict | None" = None,
        transitions: "list | None" = None,
    ) -> dict:
        audio_package = audio_package or {}
        timeline = timeline or {}
        cues_by_scene = {
            cue.get("scene_number", 0): cue
            for cue in audio_package.get("scene_cues", [])
        }
        windows = {
            segment["scene_id"]: (segment["start_time"], segment["end_time"])
            for segment in timeline.get("segments", [])
        }
        total_duration = timeline.get("total_duration_sec") or round(
            sum(float(scene.get("length_sec", 0.0)) for scene in scenes), 2
        )

        narration_segments = []
        sfx_cues = []
        silence_drops = []
        cursor = 0.0
        for scene in scenes:
            scene_id = scene.get("scene_number", 0)
            start, end = windows.get(
                scene_id, (cursor, cursor + float(scene.get("length_sec", 0.0)))
            )
            cursor = end
            cue = cues_by_scene.get(scene_id, {})
            narration_segments.append(
                {
                    "scene_id": scene_id,
                    "start_sec": round(start, 2),
                    "end_sec": round(end, 2),
                    "text": scene.get("narration", ""),
                    "delivery": cue.get("delivery", ""),
                    "target_wpm": cue.get("target_wpm", 0),
                    "pauses": cue.get("pauses", []),
                    "emphasis": cue.get("emphasis", []),
                    "path": cue.get("path")
                    or audio_package.get("path")
                    or (audio_package.get("timing") and audio_package.get("path"))
                    or "",
                }
            )

            sfx_timing = scene.get("sfx_timing") or {}
            if scene.get("sound_effect") or sfx_timing:
                sfx_cues.append(
                    {
                        "scene_id": scene_id,
                        "cue": sfx_timing.get("cue", scene.get("sound_effect", "")),
                        "at_sec": round(float(sfx_timing.get("at_sec", start)), 2),
                    }
                )

            # Silence just before high-impact beats makes the hit land harder.
            if scene.get("purpose", "") in _SILENCE_DROP_PURPOSES and start > 0:
                silence_drops.append(
                    {
                        "scene_id": scene_id,
                        "at_sec": round(max(start - SILENCE_DROP_SEC, 0.0), 2),
                        "duration_sec": SILENCE_DROP_SEC,
                        "reason": f"drop the full mix before the {scene.get('purpose')} beat",
                    }
                )

        transition_cues = []
        for transition in transitions or []:
            sound = transition.get("sound_cue") or TRANSITION_SOUNDS.get(transition.get("type", ""), "")
            if not sound:
                continue  # silent transitions (cuts) need no cue
            boundary = windows.get(transition.get("from_scene", 0), (0.0, 0.0))[1]
            transition_cues.append(
                {
                    "at_sec": round(boundary, 2),
                    "sound": sound,
                    "transition_type": transition.get("type", "cut"),
                }
            )

        music_direction = audio_package.get("music_direction", {})
        return {
            "duration_sec": total_duration,
            "tracks": {
                "narration": {
                    "level_db": TRACK_LEVELS_DB["narration"],
                    "voice_style": audio_package.get("voice_style", {}),
                    "segments": narration_segments,
                },
                "music": {
                    "level_db": TRACK_LEVELS_DB["music"],
                    "style": music_direction.get("style", ""),
                    "bpm_range": music_direction.get("bpm_range", []),
                    "energy_curve": music_direction.get("energy_curve", []),
                    "ducking": dict(DUCKING),
                },
                "sfx": {
                    "level_db": TRACK_LEVELS_DB["sfx"],
                    "cues": sfx_cues,
                },
                "transitions": {
                    "level_db": TRACK_LEVELS_DB["transitions"],
                    "cues": transition_cues,
                },
            },
            "silence_drops": silence_drops,
            "loudness_target": dict(LOUDNESS_TARGET),
        }
