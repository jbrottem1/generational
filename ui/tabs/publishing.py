"""Publishing tab — platform connection placeholders + autonomous-publish safety."""

from __future__ import annotations

import streamlit as st

from core.constants import AUTONOMOUS_PUBLISHING_ENABLED, PUBLISHING_COMING_SOON, PUBLISHING_PLATFORMS
from services.assets import get_publishing_queue
from ui import components


def render() -> None:
    st.subheader("📤 Publishing")
    st.caption(
        "Connect platforms to publish generated content. "
        "Autonomous public posting stays disabled until quality gates consistently pass."
    )

    autonomous = bool(
        st.session_state.get("autonomous_publishing_enabled", AUTONOMOUS_PUBLISHING_ENABLED)
    )
    if autonomous:
        st.error(
            "Autonomous publishing kill-switch is ON. Live posting still requires "
            "connected providers and passing intelligence + production gates."
        )
    else:
        st.success(
            "Autonomous publishing is DISABLED. Render packages are held for human review — "
            "enqueue ≠ publish."
        )

    queue = get_publishing_queue()
    pending = queue.list_pending()
    held = [item for item in pending if item.get("status") == "held"]
    ready = [item for item in pending if item.get("status") == "queued"]
    cols_q = st.columns(3)
    cols_q[0].metric("In queue", len(pending))
    cols_q[1].metric("Held for review", len(held))
    cols_q[2].metric("Ready (gates passed)", len(ready))

    if held:
        with st.expander(f"Held packages ({len(held)})", expanded=False):
            for item in held[:20]:
                reason = item.get("hold_reason") or "review"
                st.markdown(
                    f"- **{item.get('title', 'Untitled')}** — `{reason}` "
                    f"(score {item.get('publish_score', 0)})"
                )

    st.divider()
    cols = st.columns(len(PUBLISHING_PLATFORMS))
    for col, (icon, platform) in zip(cols, PUBLISHING_PLATFORMS):
        with col:
            components.status_card(icon, platform, "Not Connected")
            st.button("Connect", key=f"connect_{platform}", disabled=True, use_container_width=True)

    st.divider()
    st.markdown("### 🔮 Coming Soon")
    components.coming_soon_grid(PUBLISHING_COMING_SOON)
