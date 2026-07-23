"""Tests — permanent Founder Voice (VOICE_ASSET_0001)."""

from __future__ import annotations

from pathlib import Path

from services.elevenlabs.voices import resolve_narrator_profile
from services.studio_assets.founder_voice import (
    ASSET_ID,
    FOUNDATION_VOICE_ID,
    ensure_founder_voice_asset,
    get_founder_voice_id,
)
from services.voice_studio.config_store import get_studio_default_voice_id, load_profile_voice_config

ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "data" / "studio_assets" / "VOICE-0001-FOUNDER-VOICE"


def test_ensure_writes_voice_asset_files():
    ensure_founder_voice_asset(sync_env=False)
    assert (ASSET / "VOICE_PROFILE.json").is_file()
    assert (ASSET / "VOICE_ASSET.json").is_file()
    assert (ASSET / "VOICE_DEFAULT_CONFIG.json").is_file()
    assert get_founder_voice_id() == FOUNDATION_VOICE_ID


def test_unspecified_narrator_resolves_to_founder():
    ensure_founder_voice_asset(sync_env=False)
    r = resolve_narrator_profile("")
    assert r["voice_id"] == FOUNDATION_VOICE_ID
    assert r.get("permanent_default") is True
    assert r.get("studio_asset_id") == ASSET_ID


def test_explicit_voice_override_wins():
    ensure_founder_voice_asset(sync_env=False)
    r = resolve_narrator_profile("professor", explicit_voice_id="EXAVITQu4vr4xnSDxMaL")
    assert r["voice_id"] == "EXAVITQu4vr4xnSDxMaL"
    assert r.get("permanent_default") is False


def test_voice_studio_default_points_to_founder():
    ensure_founder_voice_asset(sync_env=False)
    cfg = load_profile_voice_config()
    assert cfg.get("default_voice_id") == FOUNDATION_VOICE_ID
    assert cfg.get("default_voice_asset_id") == ASSET_ID
    assert get_studio_default_voice_id() == FOUNDATION_VOICE_ID
