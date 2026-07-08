"""Settings tab — API key, model selection, and app info."""

import os

import streamlit as st

from core import state, storage
from core.constants import APP_VERSION, MODEL_OPTIONS


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
    st.markdown("### ℹ️ App Info")
    st.write(f"**Version:** v{APP_VERSION}")
    st.write(f"**Projects saved:** {storage.project_count()}")

    st.divider()
    if st.button("🔄 Reset Session Stats"):
        state.reset_session()
        st.success("Session reset.")
        st.rerun()
