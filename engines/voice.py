"""Voice engine (planned) — AI voiceover generation from scripts."""

from __future__ import annotations

from engines.base import PlannedEngine


class VoiceEngine(PlannedEngine):
    key = "voice"
    label = "Voice"
    icon = "🎙️"
    description = "Generate AI voiceovers from scripts."
