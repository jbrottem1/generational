"""Settings tab — API key, model selection, and app info."""

from __future__ import annotations

import os

import streamlit as st

from core import state, storage
from core.constants import APP_VERSION, MODEL_OPTIONS
from core.production_models import VOICE_MODES, VOICE_PROFILES
from core.diagnostics import run_diagnostics
from services.voice_profiles import get_voice_profile_manager


def render() -> None:
    st.subheader("⚙️ Settings")

    st.markdown("### 🔑 OpenAI API Key")
    if os.getenv("OPENAI_API_KEY"):
        st.success("An `OPENAI_API_KEY` was found in your environment (`.env`). Real AI generation is enabled.")
    else:
        st.warning("No `OPENAI_API_KEY` found in your environment. You're running in Demo Mode.")

    st.text_input(
        "Session API key override (optional)",
        type="password",
        key="openai_api_key_override",
        help="Paste a key to use for this browser session only. It is never written to disk.",
        placeholder="sk-...",
    )
    if st.session_state.openai_api_key_override:
        st.info("Using the session key you entered above for this session only.")

    st.divider()
    st.markdown("### 🤖 Model")
    st.selectbox("OpenAI model", MODEL_OPTIONS, key="selected_model")

    st.divider()
    st.markdown("### 🎙️ Voice")
    st.selectbox(
        "Narration mode",
        options=list(VOICE_MODES),
        format_func=lambda m: {"ai": "AI Voice", "recorded": "User Recorded", "clone": "Voice Clone (coming soon)"}[m],
        key="voice_mode",
        help="How narration is generated during media production. Clone mode is architecture-only for now.",
    )
    st.selectbox("Default voice style", VOICE_PROFILES, key="voice_style")
    profiles = get_voice_profile_manager().list_profiles()
    st.caption(f"{len(profiles)} custom voice profile(s) saved · recordings stored under data/voice_recordings/")

    st.divider()
    st.markdown("### 🔬 Research")
    from core.constants import RESEARCH_DEPTH_OPTIONS, RESEARCH_PROVIDER_LABELS, RESEARCH_PROVIDERS

    st.multiselect(
        "Enabled research providers",
        options=RESEARCH_PROVIDERS,
        format_func=lambda key: RESEARCH_PROVIDER_LABELS.get(key, key),
        key="research_enabled_providers",
        help="Live connectors: Wikipedia, PubMed, arXiv, Crossref. Others are placeholders.",
    )
    st.selectbox("Research depth", RESEARCH_DEPTH_OPTIONS, key="research_depth")
    st.slider(
        "Cache expiration (hours)",
        min_value=1,
        max_value=168,
        step=1,
        key="research_cache_hours",
        help="Reuse cached research for the same topic within this window.",
    )
    st.slider(
        "Maximum sources",
        min_value=5,
        max_value=50,
        step=5,
        key="research_max_sources",
        help="Cap the number of research documents after scoring.",
    )
    st.slider(
        "Source confidence threshold",
        min_value=0.0,
        max_value=0.9,
        step=0.05,
        key="research_min_confidence",
        help="Sources below this score are removed automatically.",
    )
    st.checkbox(
        "Science / medical strict mode",
        key="science_medical_strict",
        help="Raises source bar for Science and Health niches.",
    )
    st.checkbox(
        "Citation required for publish gate",
        key="citation_required",
        help="Scripts must include at least one citation to pass the quality gate.",
    )
    st.slider(
        "Research confidence gate",
        min_value=0.0,
        max_value=0.9,
        step=0.05,
        key="research_confidence_threshold",
        help="Minimum average research confidence to publish.",
    )
    st.slider(
        "Max unsupported claims",
        min_value=0,
        max_value=5,
        step=1,
        key="max_unsupported_claims",
        help="Scripts with more unsupported claims are held back.",
    )
    st.slider(
        "Minimum claim confidence",
        min_value=0.0,
        max_value=0.9,
        step=0.05,
        key="min_claim_confidence",
        help="Citation engine claim confidence required to publish.",
    )

    st.divider()
    st.markdown("### 🎯 Quality Gate"))
    st.slider(
        "Minimum publish score",
        min_value=0,
        max_value=100,
        step=5,
        key="publish_threshold",
        help="Content scoring below this threshold is held back and will never be auto-published.",
    )

    st.divider()
    st.markdown("### ℹ️ App Info")
    st.write(f"**Version:** v{APP_VERSION}")
    st.write(f"**Projects saved:** {storage.project_count()}")

    st.divider()
    st.markdown("### 🩺 System Diagnostics")
    with st.expander("Run health checks across all services"):
        icons = {"ok": "🟢", "warn": "🟡", "error": "🔴"}
        for check in run_diagnostics():
            st.markdown(f"{icons[check['status']]} **{check['name']}** — {check['detail']}")

    st.divider()
    if st.button("🔄 Reset Session Stats"):
        state.reset_session()
        st.success("Session reset.")
        st.rerun()
