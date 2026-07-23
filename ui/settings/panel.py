"""Settings panel shell — General through Diagnostics."""

from __future__ import annotations

import streamlit as st

from ui.settings import tabs as settings_tabs


def render_settings_panel() -> None:
    st.subheader("⚙️ Settings")
    st.caption("Provider Integration Management — configure, validate, and monitor every external system.")

    (
        general,
        providers,
        publishing,
        analytics,
        api_keys,
        oauth,
        storage,
        costs,
        logs,
        health,
        diagnostics,
    ) = st.tabs(
        [
            "General",
            "Providers",
            "Publishing",
            "Analytics",
            "API Keys",
            "OAuth",
            "Storage",
            "Costs",
            "Logs",
            "Health",
            "Diagnostics",
        ]
    )

    with general:
        settings_tabs.render_general()
    with providers:
        settings_tabs.render_providers()
    with publishing:
        settings_tabs.render_publishing()
    with analytics:
        settings_tabs.render_analytics_settings()
    with api_keys:
        settings_tabs.render_api_keys()
    with oauth:
        settings_tabs.render_oauth()
    with storage:
        settings_tabs.render_storage()
    with costs:
        settings_tabs.render_costs()
    with logs:
        settings_tabs.render_logs()
    with health:
        settings_tabs.render_health()
    with diagnostics:
        settings_tabs.render_diagnostics()
