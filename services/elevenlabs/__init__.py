"""ElevenLabs production narration — thin services layer over ProviderRuntime.

Engines do not import this package (architecture rule). All production TTS
still flows through ``services.media_production.voice.synthesize_voice``.
"""

from __future__ import annotations

from services.elevenlabs.auth import verify_elevenlabs_authentication
from services.elevenlabs.config import (
    DEFAULT_MODEL_ID,
    NARRATOR_PROFILE_ENV_KEYS,
    get_elevenlabs_config,
)
from services.elevenlabs.validation import validate_narration_audio
from services.elevenlabs.voices import (
    NARRATOR_PROFILES,
    list_elevenlabs_voices,
    resolve_narrator_profile,
)

__all__ = [
    "DEFAULT_MODEL_ID",
    "NARRATOR_PROFILES",
    "NARRATOR_PROFILE_ENV_KEYS",
    "get_elevenlabs_config",
    "list_elevenlabs_voices",
    "resolve_narrator_profile",
    "validate_narration_audio",
    "verify_elevenlabs_authentication",
]
