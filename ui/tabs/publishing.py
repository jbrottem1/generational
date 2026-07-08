"""Publishing tab — platform connection placeholders + roadmap for Auto Posting."""

from __future__ import annotations

import streamlit as st

from core.constants import PUBLISHING_COMING_SOON, PUBLISHING_PLATFORMS
from ui import components


def render() -> None:
    st.subheader("📤 Publishing")
    st.caption("Connect platforms to auto-publish your generated content. Coming soon.")

    cols = st.columns(len(PUBLISHING_PLATFORMS))
    for col, (icon, platform) in zip(cols, PUBLISHING_PLATFORMS):
        with col:
            components.status_card(icon, platform, "Not Connected")
            st.button("Connect", key=f"connect_{platform}", disabled=True, use_container_width=True)

    st.divider()
    st.markdown("### 🔮 Coming Soon")
    components.coming_soon_grid(PUBLISHING_COMING_SOON)
