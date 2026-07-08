"""Centralized Streamlit session state initialization and helpers."""

import streamlit as st

from core.constants import DEFAULT_MODEL, DEFAULT_PUBLISH_THRESHOLD, DEFAULT_RESEARCH_SETTINGS

DEFAULTS = {
    "command_text": "",
    "current_result": None,
    "current_project_name": None,
    "project_name_input": "",
    "ideas_generated_total": 0,
    "token_usage_total": 0,
    "openai_api_key_override": "",
    "selected_model": DEFAULT_MODEL,
    "publish_threshold": DEFAULT_PUBLISH_THRESHOLD,
    "voice_mode": "ai",
    "voice_style": "documentary",
    "research_enabled_providers": list(DEFAULT_RESEARCH_SETTINGS["enabled_providers"]),
    "research_cache_hours": DEFAULT_RESEARCH_SETTINGS["cache_ttl_hours"],
    "research_max_sources": DEFAULT_RESEARCH_SETTINGS["max_sources"],
    "research_min_confidence": DEFAULT_RESEARCH_SETTINGS["min_confidence"],
}


def init_session_state() -> None:
    for key, value in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def record_ideas_generated(count: int) -> None:
    st.session_state.ideas_generated_total += count


def add_token_usage(tokens: int) -> None:
    st.session_state.token_usage_total += tokens


def reset_session() -> None:
    st.session_state.current_result = None
    st.session_state.current_project_name = None
    st.session_state.ideas_generated_total = 0
    st.session_state.token_usage_total = 0
