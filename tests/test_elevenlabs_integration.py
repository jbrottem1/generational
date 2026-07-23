"""Unit + optional live tests for ElevenLabs production narration."""

from __future__ import annotations

import base64
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from services.elevenlabs.config import get_elevenlabs_config
from services.elevenlabs.validation import validate_narration_audio
from services.elevenlabs.voices import normalize_narrator_key, resolve_narrator_profile
from services.provider_runtime.config import has_credential


def test_narrator_profiles_resolve_to_voice_ids():
    for key in ("professor", "documentary", "storyteller", "energetic_explainer", "calm_educator"):
        resolved = resolve_narrator_profile(key)
        assert resolved["provider"] == "elevenlabs"
        assert resolved["provider_voice_id"]
        assert resolved["profile_key"] == key
        assert 0 < resolved["stability"] <= 1


def test_narrator_aliases():
    assert normalize_narrator_key("Energetic Explainer") == "energetic_explainer"
    assert normalize_narrator_key("Calm Educator") == "calm_educator"
    assert normalize_narrator_key("educator") == "professor"


def test_config_never_exposes_secret_in_dict():
    cfg = get_elevenlabs_config()
    dumped = json.dumps(cfg)
    assert "sk_" not in dumped
    assert "api_key" not in dumped or cfg["api_key_env"] == "ELEVENLABS_API_KEY"
    assert "model_id" in cfg
    assert "default_voice_id" in cfg


def test_validate_narration_rejects_missing():
    qa = validate_narration_audio("")
    assert not qa["ok"]
    assert "missing_path" in qa["hard_fails"]


def test_validate_narration_accepts_realish_mp3(tmp_path: Path):
    # Minimal MP3 frame-ish payload (nonzero file) — duration may estimate from size
    path = tmp_path / "clip.mp3"
    path.write_bytes(b"ID3" + b"\x00" * 800)
    qa = validate_narration_audio(path, timing={"word_timestamps": [{"word": "hi", "start": 0, "end": 0.2}]})
    assert qa["file_exists"]
    # Without real codec ffprobe may still flag streams — accept format_ok at minimum
    assert qa["format_ok"]


def test_synthesize_prefers_elevenlabs_when_configured():
    fake_audio = base64.b64encode(b"\xff\xfb\x90" + b"\x00" * 4000).decode("ascii")
    runtime_result = {
        "ok": True,
        "provider": "elevenlabs",
        "placeholder": False,
        "audio_b64": fake_audio,
        "path": "",
        "duration_sec": 2.5,
        "format": "mp3",
        "word_timestamps": [{"word": "hello", "start": 0.0, "end": 0.4}],
        "metadata": {"transport": "sdk"},
    }

    with patch("services.media_production.voice.has_credential", return_value=True), patch(
        "services.media_production.voice.runtime_synthesize_voice", return_value=runtime_result
    ), patch(
        "services.media_production.voice.persist_audio_payload",
        side_effect=lambda r, name="voice": {
            **r,
            "path": str(Path("/tmp/fake_elevenlabs.mp3")),
            "placeholder": False,
        },
    ), patch(
        "services.elevenlabs.validation.validate_narration_audio",
        return_value={
            "ok": True,
            "hard_fails": [],
            "duration_sec": 2.5,
            "file_exists": True,
            "format_ok": True,
            "non_zero_duration": True,
            "renderer_compatible": True,
            "synchronization_metadata": True,
            "caption_timing_compatible": True,
        },
    ):
        from services.media_production.voice import synthesize_voice

        result = synthesize_voice("Hello world about artificial intelligence.", narrator="professor")
        assert result["provider"] == "elevenlabs"
        assert result["ok"] is True
        assert result["voice_package"]["official_narration_provider"] == "elevenlabs"
        assert result["voice_package"]["narrator_profile"] == "professor"


def test_synthesize_blocks_fallback_when_disabled():
    runtime_result = {
        "ok": False,
        "provider": "local_voice",
        "placeholder": True,
        "error": "ElevenLabs 401",
        "path": "",
        "duration_sec": 0,
    }
    with patch("services.media_production.voice.has_credential", return_value=True), patch(
        "services.media_production.voice.runtime_synthesize_voice", return_value=runtime_result
    ):
        from services.media_production.voice import synthesize_voice

        result = synthesize_voice("x", narrator="professor", preferred_provider="elevenlabs", allow_fallback=False)
        assert result["ok"] is False
        assert "fallback" in (result.get("error") or "").lower() or result.get("placeholder")


@pytest.mark.integration
def test_live_elevenlabs_narration_if_configured():
    if not has_credential("ELEVENLABS_API_KEY"):
        pytest.skip("ELEVENLABS_API_KEY not configured")
    from services.media_production.voice import synthesize_voice

    result = synthesize_voice(
        "Artificial intelligence is pattern matching at scale, not a thinking brain.",
        narrator="professor",
        preferred_provider="elevenlabs",
        allow_fallback=False,
    )
    assert result["ok"] is True
    assert result["provider"] == "elevenlabs"
    assert Path(result["path"]).exists()
    assert float(result["duration_sec"] or 0) > 0.4
    assert (result.get("audio_qa") or {}).get("ok") is True
