"""Recorded voice provider — attaches user recordings to narration tracks."""

from __future__ import annotations

import os
import uuid

from providers.voice.base import NarrationResult, VoiceMode, VoiceProvider


class RecordedVoiceProvider(VoiceProvider):
    name = "recorded"
    mode = VoiceMode.RECORDED

    def __init__(self, recordings_dir: str) -> None:
        self.recordings_dir = recordings_dir

    def is_available(self) -> bool:
        return os.path.isdir(self.recordings_dir)

    def synthesize(self, text: str, profile: dict, settings: dict) -> NarrationResult:
        path = profile.get("recording_path", "")
        exists = path and os.path.isfile(path)
        return NarrationResult(
            asset_id=f"rec_{uuid.uuid4().hex[:10]}",
            duration_sec=settings.get("duration_sec", 5.0),
            path=path if exists else "",
            mode=VoiceMode.RECORDED,
            placeholder=not exists,
            metadata={"text": text[:80], "attached": exists},
        )
