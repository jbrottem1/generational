"""Subtitle engine — sentence and word-level timing with platform formatting."""

from __future__ import annotations

import re

from core.log import get_logger, log_event
from core.production_models import SubtitleCue, SubtitleTrack
from engines.base import Engine

logger = get_logger(__name__)


def _words_with_timing(text: str, start: float, end: float) -> list:
    words = text.split()
    if not words:
        return []
    span = (end - start) / len(words)
    return [{"word": w, "start": round(start + i * span, 2), "end": round(start + (i + 1) * span, 2)} for i, w in enumerate(words)]


def _to_srt(cues: list) -> str:
    lines = []
    for index, cue in enumerate(cues, start=1):
        start = _sec_to_srt(cue["start_sec"])
        end = _sec_to_srt(cue["end_sec"])
        lines.append(f"{index}\n{start} --> {end}\n{cue['text']}\n")
    return "\n".join(lines)


def _sec_to_srt(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int((sec % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


class SubtitleEngine(Engine):
    key = "subtitle"
    label = "Subtitles"
    icon = "💬"
    description = "Generate subtitle timing with sentence and word-level cues."

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        packages = context.get("production_packages") or []
        platform = context.get("target_platform", "youtube_shorts")

        for pkg in packages:
            cues = []
            for scene in pkg.get("scenes", []):
                text = scene.get("narration", "")
                start = scene.get("timing_start", 0.0)
                end = scene.get("timing_end", start + scene.get("duration_sec", 5))
                cue = SubtitleCue(
                    start_sec=start,
                    end_sec=end,
                    text=text,
                    words=_words_with_timing(text, start, end),
                )
                cues.append(cue.to_dict())

            track = SubtitleTrack(
                format="srt" if platform != "tiktok" else "ass",
                platform=platform,
                cues=cues,
                srt_content=_to_srt(cues),
                word_level=True,
            )
            pkg["subtitles"] = track.to_dict()

        log_event(logger, "subtitle.completed", packages=len(packages))
        return {"production_packages": packages}
