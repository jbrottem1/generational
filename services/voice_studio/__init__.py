"""Voice Studio — configurable narrator profiles and ElevenLabs voice comparison.

Does not modify the production pipeline or renderer. Uses existing
``services.media_production.voice.synthesize_voice`` and ElevenLabs integration.
"""

from __future__ import annotations

from services.voice_studio.comparison import run_voice_comparison
from services.voice_studio.config_store import (
    get_configured_voice_id,
    load_profile_voice_config,
    set_default_voice_id,
    set_profile_voice_id,
)
from services.voice_studio.content_routing import select_narrator_profile
from services.voice_studio.profiles import NARRATOR_PROFILE_CATALOG, list_profile_catalog
from services.voice_studio.recommend import recommend_voices_for_profiles
from services.voice_studio.sampler import COMPARISON_TEXT, generate_samples_for_voices, generate_voice_sample
from services.voice_studio.scoring import score_voice_dimensions

__all__ = [
    "COMPARISON_TEXT",
    "NARRATOR_PROFILE_CATALOG",
    "generate_samples_for_voices",
    "generate_voice_sample",
    "get_configured_voice_id",
    "list_profile_catalog",
    "load_profile_voice_config",
    "recommend_voices_for_profiles",
    "run_voice_comparison",
    "score_voice_dimensions",
    "select_narrator_profile",
    "set_default_voice_id",
    "set_profile_voice_id",
]
