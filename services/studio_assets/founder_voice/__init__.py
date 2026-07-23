"""VOICE_ASSET_0001 — Founder Voice — permanent default ElevenLabs narrator."""

from __future__ import annotations

from services.studio_assets.founder_voice.asset import (
    ASSET_ID,
    ASSET_SLUG,
    ASSET_VERSION,
    DISPLAY_NAME,
    FOUNDATION_VOICE_ID,
    ensure_founder_voice_asset,
    get_founder_default_config,
    get_founder_voice_id,
    get_founder_voice_profile,
    resolve_default_narrator,
)
from services.studio_assets.founder_voice.qa import run_founder_voice_qa

__all__ = [
    "ASSET_ID",
    "ASSET_SLUG",
    "ASSET_VERSION",
    "DISPLAY_NAME",
    "FOUNDATION_VOICE_ID",
    "ensure_founder_voice_asset",
    "get_founder_default_config",
    "get_founder_voice_id",
    "get_founder_voice_profile",
    "resolve_default_narrator",
    "run_founder_voice_qa",
]
