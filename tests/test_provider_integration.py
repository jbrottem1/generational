"""Tests for Provider Integration Management control plane."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from services.provider_integration import (
    MODEL_ROLES,
    OAUTH_PLATFORMS,
    PROVIDER_CATEGORIES,
    catalog_by_category,
    delete_api_key,
    disable_provider,
    enable_provider,
    get_cost_dashboard,
    get_health_dashboard,
    get_integration_dashboard,
    get_model_defaults,
    import_api_keys,
    list_api_keys,
    list_oauth_connections,
    list_registered_providers,
    register_catalog_entry,
    rotate_api_key,
    save_oauth_tokens,
    set_api_key,
    set_model_defaults,
    run_oauth_connection_test,
    run_provider_connection_test,
    validate_api_key,
)
from services.provider_runtime.config import get_credential, save_runtime_config
from services.provider_runtime.secrets import SecretManager, mask_secret


@pytest.fixture()
def isolated_provider_config(tmp_path, monkeypatch):
    cfg = tmp_path / "config.json"
    secrets = tmp_path / "secrets.enc.json"
    env_file = tmp_path / ".env"
    env_file.write_text("OPENAI_API_KEY=\n", encoding="utf-8")
    monkeypatch.setenv("PROVIDER_CONFIG_PATH", str(cfg))
    monkeypatch.setenv("PROVIDER_SECRETS_PATH", str(secrets))
    monkeypatch.setenv("PROVIDER_SECRETS_PASSPHRASE", "rc-test-passphrase")
    # Keep credential tests from writing into the real project .env
    from core import env as env_mod

    monkeypatch.setattr(env_mod, "_PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(env_mod, "_ENV_PATH", env_file)
    monkeypatch.setattr(env_mod, "_ENV_EXAMPLE_PATH", tmp_path / ".env.example")
    save_runtime_config({"disabled_providers": [], "model_defaults": {}, "oauth": {}})
    return tmp_path


def test_catalog_covers_categories_and_planned_providers(isolated_provider_config):
    providers = list_registered_providers()
    assert providers
    names = {p["name"] for p in providers}
    assert "openai" in names
    assert "youtube" in names
    assert "suno" in names  # planned
    assert "openrouter" in names
    grouped = catalog_by_category()
    for cat in ("text", "image", "video", "voice", "publishing"):
        assert cat in PROVIDER_CATEGORIES
        assert isinstance(grouped.get(cat), list)


def test_register_catalog_entry_plugin_surface(isolated_provider_config):
    entry = register_catalog_entry(
        {
            "name": "future_llm_xyz",
            "label": "Future LLM",
            "category": "text",
            "api_key_env": "FUTURE_LLM_API_KEY",
            "capabilities": ["llm"],
        }
    )
    assert entry["name"] == "future_llm_xyz"
    names = {p["name"] for p in list_registered_providers()}
    assert "future_llm_xyz" in names


def test_api_key_set_rotate_delete_masked(isolated_provider_config, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result = set_api_key("OPENAI_API_KEY", "sk-test-secret-value-123456")
    assert result["ok"] is True
    assert "sk-t" in result["masked"] or "…" in result["masked"]
    assert "secret-value" not in result["masked"]
    assert get_credential("OPENAI_API_KEY").startswith("sk-test")

    rows = list_api_keys()
    openai_rows = [r for r in rows if r.get("env_var") == "OPENAI_API_KEY"]
    assert openai_rows
    assert openai_rows[0]["present"] is True
    assert "sk-test-secret-value-123456" not in json.dumps(openai_rows)

    rotated = rotate_api_key("OPENAI_API_KEY", "sk-rotated-99999999")
    assert rotated["ok"] is True
    assert get_credential("OPENAI_API_KEY") == "sk-rotated-99999999"

    deleted = delete_api_key("OPENAI_API_KEY")
    assert deleted["ok"] is True


def test_import_api_keys(isolated_provider_config):
    result = import_api_keys({"ANTHROPIC_API_KEY": "sk-ant-test-abcdef"})
    assert result["imported"] == 1
    assert get_credential("ANTHROPIC_API_KEY").startswith("sk-ant")


def test_mask_secret_never_returns_full_value():
    assert mask_secret("") == ""
    assert mask_secret("short") == "••••••••"
    masked = mask_secret("sk-abcdefghijklmnopqrstuvwxyz")
    assert "abcdefghijklmnop" not in masked
    assert masked.startswith("sk-a") or "…" in masked


def test_enable_disable_provider(isolated_provider_config):
    providers = {p["name"]: p for p in list_registered_providers()}
    target = "openai" if "openai" in providers else next(iter(providers))
    disable_provider(target)
    providers = {p["name"]: p for p in list_registered_providers()}
    assert providers[target]["enabled"] is False
    enable_provider(target)
    providers = {p["name"]: p for p in list_registered_providers()}
    assert providers[target]["enabled"] is True


def test_model_defaults_round_trip(isolated_provider_config):
    defaults = set_model_defaults({"default_text": "openai", "image": "flux"})
    assert defaults["default_text"] == "openai"
    loaded = get_model_defaults()
    assert loaded["default_text"] == "openai"
    assert loaded["image"] == "flux"
    for role in MODEL_ROLES:
        assert role in loaded


def test_oauth_save_and_list(isolated_provider_config):
    assert set(OAUTH_PLATFORMS) >= {"youtube", "tiktok", "instagram"}
    result = save_oauth_tokens(
        "youtube",
        client_id="cid",
        client_secret="csecret",
        access_token="ya29.access",
        refresh_token="1//refresh",
        expires_at="2099-01-01T00:00:00+00:00",
    )
    assert result["ok"] is True
    rows = {r["platform"]: r for r in list_oauth_connections()}
    assert rows["youtube"]["access_token_present"] is True
    assert rows["youtube"]["status"] == "connected"
    # Never expose raw token in list payload
    assert "ya29.access" not in json.dumps(rows["youtube"])
    test = run_oauth_connection_test("youtube")
    assert test["ok"] is True


def test_connection_test_and_dashboards(isolated_provider_config):
    report = run_provider_connection_test("demo")
    assert "provider" in report
    assert "latency_ms" in report
    assert "health_score" in report
    assert get_integration_dashboard()["provider_count"] > 0
    assert "total_cost_usd" in get_cost_dashboard()
    assert "healthy_count" in get_health_dashboard()


def test_validate_api_key_unknown_provider():
    result = validate_api_key("not_a_real_provider_xyz")
    assert result["valid"] is False


def test_settings_panel_importable():
    from ui.settings import render_settings_panel
    from ui.tabs import settings as settings_tab

    assert callable(render_settings_panel)
    assert callable(settings_tab.render)


def test_secret_manager_persist_round_trip(isolated_provider_config, monkeypatch):
    mgr = SecretManager()
    mgr.rotate("TEST_PROVIDER_KEY", "value-should-persist-001")
    import os
    path = Path(os.environ["PROVIDER_SECRETS_PATH"])
    assert path.exists()
    mgr2 = SecretManager()
    assert mgr2.get("TEST_PROVIDER_KEY") == "value-should-persist-001"
