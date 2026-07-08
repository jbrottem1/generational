"""AI Command Center sidebar — always-visible status and session stats."""

import streamlit as st

from core import ai, storage
from core.constants import APP_VERSION


def render() -> None:
    """Renders sidebar content into whatever container is currently active.

    Call this wrapped in `with st.sidebar:` (or a container placed inside the
    sidebar) AFTER tab logic has run in the same script pass, so session
    stats reflect the latest updates instead of stale pre-run values.
    """
    st.markdown("## 🧠 AI Command Center")

    demo_mode = ai.is_demo_mode()
    status_label = "🟡 Demo Mode" if demo_mode else "🟢 Connected"

    st.markdown(f"**API Status**  \n{status_label}")
    st.markdown(f"**Model**  \n`{st.session_state.selected_model}`")
    st.markdown(f"**Version**  \nv{APP_VERSION}")

    st.divider()
    st.markdown("### 📈 Session Stats")

    col1, col2 = st.columns(2)
    col1.metric("Ideas Generated", st.session_state.ideas_generated_total)
    col2.metric("Projects Saved", storage.project_count())

    token_display = st.session_state.token_usage_total if not demo_mode else "—"
    st.metric("Token Usage", token_display)
    st.caption("Token usage is tracked live from the OpenAI API once connected.")

    if demo_mode:
        st.divider()
        st.info("Add an OpenAI API key in **Settings** (or a `.env` file) to enable real AI generation.")
