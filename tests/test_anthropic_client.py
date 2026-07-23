"""Tests for Anthropic client helpers — never call the live API."""

from __future__ import annotations

from services.anthropic_client import mask_anthropic_key, connection_test, request_text


def test_mask_anthropic_key_format():
    assert mask_anthropic_key("") == ""
    assert mask_anthropic_key("short") == "****"
    masked = mask_anthropic_key("sk-ant-api03-abcdefghijklmnopqrstuvwxyz0123456789")
    assert masked.startswith("sk-ant")
    assert masked.endswith("6789") or "..." in masked
    assert "abcdefghijklmnopqrstuvwxyz" not in masked


def test_connection_test_missing_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(
        "services.anthropic_client.get_anthropic_api_key",
        lambda: "",
    )
    report = connection_test()
    assert report["key_found"] is False
    assert "Missing" in report["key_status"]
    assert report["ok"] is False
    assert report["error_type"] == "missing_key"
    assert "sk-ant" not in str(report)


def test_request_text_does_not_embed_secret_in_error(monkeypatch):
    secret = "sk-ant-api03-SUPERSECRETVALUE000000000000000000"
    monkeypatch.setattr("services.anthropic_client.get_anthropic_api_key", lambda: secret)
    monkeypatch.setattr("services.anthropic_client.get_client", lambda **kwargs: None)

    def boom(*args, **kwargs):
        raise RuntimeError(f"failed with {secret}")

    monkeypatch.setattr("urllib.request.urlopen", boom)
    result = request_text("hi")
    assert result.ok is False
    assert secret not in result.error_message
    assert "sk-ant" in result.error_message or "..." in result.error_message
