"""Tests for project-root .env loading and startup credential reporting."""

from __future__ import annotations

from pathlib import Path

import pytest


def test_ensure_env_file_creates_from_example(tmp_path, monkeypatch):
    from core import env as env_mod

    example = tmp_path / ".env.example"
    example.write_text("OPENAI_API_KEY=\nANTHROPIC_API_KEY=\n", encoding="utf-8")
    target = tmp_path / ".env"

    monkeypatch.setattr(env_mod, "_PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(env_mod, "_ENV_PATH", target)
    monkeypatch.setattr(env_mod, "_ENV_EXAMPLE_PATH", example)

    result = env_mod.ensure_env_file()
    assert result["created"] is True
    assert target.exists()
    assert "OPENAI_API_KEY=" in target.read_text(encoding="utf-8")

    again = env_mod.ensure_env_file()
    assert again["created"] is False


def test_load_application_env_reads_openai_key(tmp_path, monkeypatch):
    from core import env as env_mod

    env_file = tmp_path / ".env"
    env_file.write_text("OPENAI_API_KEY=sk-test-from-dotenv-12345\n", encoding="utf-8")

    monkeypatch.setattr(env_mod, "_PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(env_mod, "_ENV_PATH", env_file)
    monkeypatch.setattr(env_mod, "_ENV_EXAMPLE_PATH", tmp_path / ".env.example")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    env_mod._DOTENV_LOADED = False

    boot = env_mod.load_application_env(create_if_missing=False)
    assert boot["loaded"] is True
    assert boot["exists"] is True

    report = env_mod.startup_credential_report(("OPENAI_API_KEY",))
    assert report["openai_loaded"] is True
    assert report["demo_mode"] is False
    assert any("✓ OPENAI_API_KEY" in line for line in report["lines"])


def test_startup_report_missing_openai(tmp_path, monkeypatch):
    from core import env as env_mod

    env_file = tmp_path / ".env"
    env_file.write_text("ANTHROPIC_API_KEY=\n", encoding="utf-8")

    monkeypatch.setattr(env_mod, "_PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(env_mod, "_ENV_PATH", env_file)
    monkeypatch.setattr(env_mod, "_ENV_EXAMPLE_PATH", tmp_path / ".env.example")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    env_mod._DOTENV_LOADED = False
    env_mod.load_application_env(create_if_missing=False)

    report = env_mod.startup_credential_report(("OPENAI_API_KEY",))
    assert report["openai_loaded"] is False
    assert report["demo_mode"] is True
    assert any("✗ OPENAI_API_KEY" in line for line in report["lines"])


def test_write_env_value_upserts(tmp_path, monkeypatch):
    from core import env as env_mod

    env_file = tmp_path / ".env"
    env_file.write_text("OPENAI_API_KEY=old\nXAI_API_KEY=\n", encoding="utf-8")
    monkeypatch.setattr(env_mod, "_ENV_PATH", env_file)
    monkeypatch.setattr(env_mod, "_ENV_EXAMPLE_PATH", tmp_path / ".env.example")
    monkeypatch.setattr(env_mod, "_PROJECT_ROOT", tmp_path)

    result = env_mod.write_env_value("OPENAI_API_KEY", "sk-new-key")
    assert result["ok"] is True
    text = env_file.read_text(encoding="utf-8")
    assert "OPENAI_API_KEY=sk-new-key" in text
    assert "old" not in text


def test_openai_provider_uses_credential_stack(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-live-test-key")
    from core.ai.openai_provider import get_api_key

    assert get_api_key() == "sk-live-test-key"
