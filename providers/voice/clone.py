"""Voice clone provider — architecture stub for future implementation.

Register a real clone backend here when ready; engines and the narration
stage require zero changes.
"""

from __future__ import annotations

from providers.voice.base import NarrationResult, VoiceMode, VoiceProvider


class CloneVoiceProvider(VoiceProvider):
    name = "clone_stub"
    mode = VoiceMode.CLONE

    def is_available(self) -> bool:
        return False

    def synthesize(self, text: str, profile: dict, settings: dict) -> NarrationResult:
        raise NotImplementedError("Voice cloning is not yet implemented — architecture placeholder only.")
