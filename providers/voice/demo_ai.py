"""Demo AI voice provider — placeholder narration metadata, no API required."""

from __future__ import annotations

import uuid

from providers.voice.base import NarrationResult, VoiceMode, VoiceProvider


class DemoAIVoiceProvider(VoiceProvider):
    name = "demo_ai"
    mode = VoiceMode.AI

    def is_available(self) -> bool:
        return True

    def synthesize(self, text: str, profile: dict, settings: dict) -> NarrationResult:
        wpm = 150 * settings.get("speaking_speed", 1.0)
        words = max(len(text.split()), 1)
        duration = round(words / wpm * 60, 2)
        return NarrationResult(
            asset_id=f"nar_{uuid.uuid4().hex[:10]}",
            duration_sec=duration,
            path="",
            mode=VoiceMode.AI,
            placeholder=True,
            metadata={"profile": profile.get("name", ""), "style": profile.get("style", "documentary")},
        )
