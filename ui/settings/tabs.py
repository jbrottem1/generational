"""Individual Settings tabs for Provider Integration Management."""

from __future__ import annotations

import json
import os
from pathlib import Path

import streamlit as st

from core import state, storage
from core.constants import (
    APP_VERSION,
    MODEL_OPTIONS,
    RESEARCH_DEPTH_OPTIONS,
    RESEARCH_PROVIDER_LABELS,
    RESEARCH_PROVIDERS,
)
from core.diagnostics import run_diagnostics
from core.production_models import VOICE_MODES, VOICE_PROFILES
from services.voice_profiles import get_voice_profile_manager


def render_general() -> None:
    st.markdown("### General")
    st.selectbox("Default OpenAI-compatible model", MODEL_OPTIONS, key="selected_model")

    st.markdown("#### Voice")
    st.selectbox(
        "Narration mode",
        options=list(VOICE_MODES),
        format_func=lambda m: {
            "ai": "AI Voice",
            "recorded": "User Recorded",
            "clone": "Voice Clone (coming soon)",
        }[m],
        key="voice_mode",
    )
    st.selectbox("Default voice style", VOICE_PROFILES, key="voice_style")
    profiles = get_voice_profile_manager().list_profiles()
    st.caption(f"{len(profiles)} custom voice profile(s) · data/voice_recordings/")

    st.markdown("#### Research")
    st.multiselect(
        "Enabled research providers",
        options=RESEARCH_PROVIDERS,
        format_func=lambda key: RESEARCH_PROVIDER_LABELS.get(key, key),
        key="research_enabled_providers",
    )
    st.selectbox("Research depth", RESEARCH_DEPTH_OPTIONS, key="research_depth")
    st.slider("Cache expiration (hours)", 1, 168, key="research_cache_hours")
    st.slider("Maximum sources", 5, 50, 5, key="research_max_sources")
    st.slider("Source confidence threshold", 0.0, 0.9, 0.05, key="research_min_confidence")
    st.checkbox("Science / medical strict mode", key="science_medical_strict")
    st.checkbox("Citation required for publish gate", key="citation_required")
    st.slider("Research confidence gate", 0.0, 0.9, 0.05, key="research_confidence_threshold")
    st.slider("Max unsupported claims", 0, 5, 1, key="max_unsupported_claims")
    st.slider("Minimum claim confidence", 0.0, 0.9, 0.05, key="min_claim_confidence")

    st.markdown("#### Quality Gate")
    st.slider("Minimum publish score", 0, 100, 5, key="publish_threshold")

    st.markdown("#### App")
    st.write(f"**Version:** v{APP_VERSION}")
    st.write(f"**Projects saved:** {storage.project_count()}")
    if st.button("🔄 Reset Session Stats", key="reset_session_stats"):
        state.reset_session()
        st.success("Session reset.")
        st.rerun()


def render_providers() -> None:
    from services.provider_integration import (
        MODEL_ROLES,
        catalog_by_category,
        disable_provider,
        enable_provider,
        get_model_defaults,
        set_model_defaults,
        run_provider_connection_test,
    )

    st.markdown("### Providers")
    dash_cols = st.columns(4)
    grouped = catalog_by_category()
    total = sum(len(v) for v in grouped.values())
    dash_cols[0].metric("Registered", total)
    enabled = sum(1 for items in grouped.values() for p in items if p.get("enabled"))
    dash_cols[1].metric("Enabled", enabled)
    cred = sum(1 for items in grouped.values() for p in items if p.get("credential_present"))
    dash_cols[2].metric("Credentialed", cred)
    live = sum(1 for items in grouped.values() for p in items if p.get("status") == "live")
    dash_cols[3].metric("Live", live)

    st.markdown("#### Model defaults & fallbacks")
    defaults = get_model_defaults()
    updates = {}
    cols = st.columns(3)
    for i, role in enumerate(MODEL_ROLES):
        updates[role] = cols[i % 3].text_input(
            role.replace("_", " ").title(),
            value=defaults.get(role, ""),
            key=f"model_default_{role}",
            help="Provider or model id preferred for this role",
        )
    if st.button("Save model defaults", key="save_model_defaults"):
        set_model_defaults(updates)
        st.success("Model defaults saved to provider runtime config.")

    for category, items in grouped.items():
        if not items:
            continue
        with st.expander(f"{category.title()} ({len(items)})", expanded=category in ("text", "publishing")):
            for provider in items:
                name = provider.get("name", "")
                c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
                status = provider.get("status", "")
                cred_flag = "🔑" if provider.get("credential_present") else "—"
                enabled_flag = "on" if provider.get("enabled") else "off"
                c1.markdown(
                    f"**{provider.get('label', name)}** `{name}` · {status} · "
                    f"{cred_flag} · enabled={enabled_flag}"
                )
                c1.caption(", ".join(provider.get("capabilities") or []) or "no capabilities listed")
                if c2.button("Enable", key=f"en_{name}", disabled=bool(provider.get("enabled"))):
                    enable_provider(name)
                    st.rerun()
                if c3.button("Disable", key=f"dis_{name}", disabled=not provider.get("enabled")):
                    disable_provider(name)
                    st.rerun()
                if c4.button("Test", key=f"test_{name}"):
                    report = run_provider_connection_test(name)
                    if report.get("ok"):
                        st.success(
                            f"{name}: auth={report.get('authentication')} · "
                            f"latency={report.get('latency_ms')}ms · "
                            f"health={report.get('health_score')}"
                        )
                    else:
                        st.warning(
                            f"{name}: {report.get('auth_reason') or report.get('error') or 'failed'}"
                        )


def render_publishing() -> None:
    from services.provider_integration import catalog_by_category, list_oauth_connections

    st.markdown("### Publishing providers")
    pubs = catalog_by_category().get("publishing") or []
    for p in pubs:
        st.caption(
            f"· **{p.get('label', p.get('name'))}** — "
            f"{'credentialed' if p.get('credential_present') else 'needs OAuth/API key'} · "
            f"{'enabled' if p.get('enabled') else 'disabled'}"
        )
    st.markdown("#### Connection status")
    for row in list_oauth_connections():
        st.write(
            f"`{row['platform']}` — **{row['status']}** · "
            f"access={'yes' if row['access_token_present'] else 'no'} · "
            f"refresh={'yes' if row['refresh_token_present'] else 'no'}"
        )
    st.info("Use the OAuth tab to connect platforms. Secrets are never shown after save.")


def render_analytics_settings() -> None:
    from services.provider_integration import catalog_by_category

    st.markdown("### Analytics providers")
    items = catalog_by_category().get("analytics") or []
    if not items:
        st.caption("No analytics providers registered yet.")
    for p in items:
        st.caption(
            f"· **{p.get('label', p.get('name'))}** — status={p.get('status')} · "
            f"credential={'yes' if p.get('credential_present') else 'no'}"
        )
    st.markdown("#### Defaults")
    from services.provider_integration import get_model_defaults, set_model_defaults

    defaults = get_model_defaults()
    value = st.text_input("Preferred analytics provider", value=defaults.get("analytics", ""), key="pref_analytics")
    if st.button("Save analytics preference", key="save_analytics_pref"):
        set_model_defaults({"analytics": value})
        st.success("Saved.")


def render_api_keys() -> None:
    from services.provider_integration import (
        delete_api_key,
        import_api_keys,
        list_api_keys,
        set_api_key,
        validate_api_key,
    )

    st.markdown("### API Keys")
    st.caption(
        "Keys are stored via SecretManager (encrypted when `PROVIDER_SECRETS_PASSPHRASE` is set) "
        "or environment variables. Values are never shown after save."
    )

    if not os.getenv("PROVIDER_SECRETS_PASSPHRASE"):
        st.warning(
            "Set `PROVIDER_SECRETS_PASSPHRASE` in `.env` to encrypt keys at rest. "
            "Without it, keys remain session overrides / env only."
        )

    rows = list_api_keys()
    if rows:
        for row in rows:
            cols = st.columns([2, 2, 2, 1])
            cols[0].write(row.get("provider") or "—")
            cols[1].code(row.get("env_var") or "")
            cols[2].write(row.get("masked") or ("missing" if not row.get("present") else "••••"))
            if cols[3].button("Delete", key=f"del_key_{row.get('env_var')}"):
                delete_api_key(row.get("env_var") or "")
                st.rerun()
    else:
        st.info("No credentials detected yet.")

    st.markdown("#### Add / update key")
    env_var = st.text_input("Environment variable name", placeholder="OPENAI_API_KEY", key="new_key_env")
    value = st.text_input("Secret value", type="password", key="new_key_value", placeholder="••••••••")
    c1, c2 = st.columns(2)
    if c1.button("Save key", type="primary", key="save_api_key"):
        result = set_api_key(env_var, value)
        if result.get("ok"):
            st.success(f"Saved {result['env_var']} as {result['masked']}")
        else:
            st.error(result.get("error") or "failed")
    provider = st.text_input("Validate provider id", placeholder="openai", key="validate_provider_id")
    if c2.button("Validate", key="validate_api_key_btn"):
        report = validate_api_key(provider)
        st.json({k: v for k, v in report.items() if k != "secret"})

    st.markdown("#### Import JSON map")
    blob = st.text_area("JSON object of env_var → secret", height=120, key="import_keys_json")
    if st.button("Import keys", key="import_keys_btn"):
        try:
            payload = json.loads(blob or "{}")
            if not isinstance(payload, dict):
                raise ValueError("expected object")
            result = import_api_keys({str(k): str(v) for k, v in payload.items()})
            st.success(f"Imported {result.get('imported', 0)} keys")
        except Exception as exc:  # noqa: BLE001
            st.error(str(exc))


def render_oauth() -> None:
    from services.provider_integration import (
        OAUTH_PLATFORMS,
        disconnect_oauth,
        list_oauth_connections,
        save_oauth_tokens,
        run_oauth_connection_test,
    )

    st.markdown("### OAuth")
    st.caption("Connect publishing platforms. Client secrets and tokens are masked after save.")

    for row in list_oauth_connections():
        st.write(
            f"**{row['platform']}** — {row['status']} · "
            f"tested={row.get('last_tested_at') or 'never'} · "
            f"ok={row.get('last_test_ok')}"
        )

    platform = st.selectbox("Platform", list(OAUTH_PLATFORMS), key="oauth_platform")
    client_id = st.text_input("Client ID", key="oauth_client_id")
    client_secret = st.text_input("Client Secret", type="password", key="oauth_client_secret")
    access_token = st.text_input("Access Token", type="password", key="oauth_access")
    refresh_token = st.text_input("Refresh Token", type="password", key="oauth_refresh")
    expires_at = st.text_input("Expiration (ISO-8601 optional)", key="oauth_expires")

    c1, c2, c3, c4 = st.columns(4)
    if c1.button("Connect / Save", type="primary", key="oauth_save"):
        result = save_oauth_tokens(
            platform,
            client_id=client_id,
            client_secret=client_secret,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
        )
        st.success(f"Saved fields: {', '.join(result.get('saved_fields') or []) or 'none'}")
    if c2.button("Test connection", key="oauth_test"):
        st.json(run_oauth_connection_test(platform))
    if c3.button("Reconnect", key="oauth_reconnect"):
        st.info("Update tokens above and click Connect / Save to reconnect.")
    if c4.button("Disconnect", key="oauth_disconnect"):
        disconnect_oauth(platform)
        st.warning(f"Disconnected {platform}")
        st.rerun()


def render_storage() -> None:
    st.markdown("### Storage")
    root = Path(__file__).resolve().parents[2]
    paths = {
        "Projects": root / "data" / "projects",
        "Provider config": root / "data" / "provider_runtime" / "config.json",
        "Encrypted secrets": root / "data" / "provider_runtime" / "secrets.enc.json",
        "Workflow runs": root / "data" / "workflow_runs",
        "Publishing queue": root / "data" / "publishing_queue",
        "Analytics": root / "data" / "analytics",
        "Asset generation": root / "data" / "asset_generation",
    }
    for label, path in paths.items():
        exists = path.exists()
        st.write(f"{'✅' if exists else '○'} **{label}** — `{path}`")
    st.caption(
        "Override secrets path with `PROVIDER_SECRETS_PATH`. "
        "Override config with `PROVIDER_CONFIG_PATH`. Environment variables always win for credentials."
    )


def render_costs() -> None:
    from services.provider_integration import get_cost_dashboard

    st.markdown("### Costs")
    dash = get_cost_dashboard()
    cols = st.columns(4)
    cols[0].metric("Estimated spend", f"${dash.get('total_cost_usd', 0):.4f}")
    cols[1].metric("Calls", dash.get("total_calls", 0))
    cols[2].metric("Tokens", dash.get("tokens", 0))
    cols[3].metric("Images", dash.get("images", 0))
    cols2 = st.columns(4)
    cols2[0].metric("Video minutes", dash.get("video_minutes", 0))
    cols2[1].metric("Voice minutes", dash.get("voice_minutes", 0))
    cols2[2].metric("Music", dash.get("music", 0))
    cols2[3].metric("Publishing calls", dash.get("publishing_calls", 0))
    st.caption(dash.get("note", ""))
    rows = dash.get("per_provider") or []
    if rows:
        st.markdown("#### Per provider")
        for row in rows[:40]:
            st.caption(
                f"· **{row['provider']}** — calls={row['calls']} · "
                f"cost=${row['cost_usd']:.4f} · tokens={row.get('tokens', 0)}"
            )
    else:
        st.info("No usage recorded in this session yet.")


def render_logs() -> None:
    from services.provider_runtime.security import get_audit_log

    st.markdown("### Audit logs")
    st.caption("Credential and provider management events (secrets never logged).")
    events = list(reversed(get_audit_log().events()[-100:]))
    if not events:
        st.info("No audit events yet.")
        return
    for event in events:
        st.caption(
            f"`{event.get('timestamp', '')}` · **{event.get('action', '')}** · "
            + ", ".join(f"{k}={v}" for k, v in event.items() if k not in ("timestamp", "action", "secret"))
        )


def render_health() -> None:
    from services.provider_integration import get_health_dashboard
    from services.provider_runtime import get_provider_runtime

    st.markdown("### Provider health")
    dash = get_health_dashboard()
    cols = st.columns(3)
    cols[0].metric("Healthy", dash.get("healthy_count", 0))
    cols[1].metric("Degraded", dash.get("degraded_count", 0))
    cols[2].metric("Unavailable", dash.get("unavailable_count", 0))
    for row in dash.get("providers") or []:
        st.caption(
            f"· **{row.get('label') or row.get('name')}** — {row.get('status')} · "
            f"failures={row.get('failures')} · circuit_open={row.get('circuit_open')} · "
            f"calls={row.get('calls')} · cost=${row.get('cost_usd', 0)}"
        )

    runtime = get_provider_runtime()
    name = st.text_input("Provider to recover / blacklist", key="health_provider_name")
    c1, c2 = st.columns(2)
    if c1.button("Recover provider", key="recover_provider") and name:
        if hasattr(runtime, "recover_provider"):
            runtime.recover_provider(name)
            st.success(f"Recover requested for {name}")
    if c2.button("Blacklist provider", key="blacklist_provider") and name:
        if hasattr(runtime, "blacklist_provider"):
            runtime.blacklist_provider(name)
            st.warning(f"Blacklisted {name}")


def render_diagnostics() -> None:
    from services.provider_integration import get_integration_dashboard
    from services.provider_runtime import get_provider_runtime
    from services.provider_runtime.security import credential_inventory

    st.markdown("### Diagnostics")
    icons = {"ok": "🟢", "warn": "🟡", "error": "🔴"}
    for check in run_diagnostics():
        st.markdown(f"{icons[check['status']]} **{check['name']}** — {check['detail']}")

    st.markdown("#### ProviderRuntime")
    runtime = get_provider_runtime()
    integ = get_integration_dashboard()
    st.write(
        {
            "catalog": integ.get("provider_count"),
            "credentialed": integ.get("credentialed_count"),
            "enabled": integ.get("enabled_count"),
            "cache": runtime.cache_stats() if hasattr(runtime, "cache_stats") else {},
            "secrets": runtime.secrets_status() if hasattr(runtime, "secrets_status") else {},
        }
    )
    st.markdown("#### Credential inventory (masked)")
    st.json(credential_inventory())
