"""Publishing tab — platform connection placeholders + roadmap for Auto Posting."""

import streamlit as st

from core.constants import PUBLISHING_COMING_SOON, PUBLISHING_PLATFORMS


def render() -> None:
    st.subheader("📤 Publishing")
    st.caption("Connect platforms to auto-publish your generated content. Coming soon.")

    cols = st.columns(len(PUBLISHING_PLATFORMS))
    for col, (icon, platform) in zip(cols, PUBLISHING_PLATFORMS):
        with col:
            st.markdown(
                f"<div class='status-card'>{icon}<br><b>{platform}</b><br>"
                f"<span class='badge-muted'>Not Connected</span></div>",
                unsafe_allow_html=True,
            )
            st.button("Connect", key=f"connect_{platform}", disabled=True, use_container_width=True)

    st.divider()
    st.markdown("### 🔮 Coming Soon")
    coming_cols = st.columns(len(PUBLISHING_COMING_SOON))
    for col, (icon, feature) in zip(coming_cols, PUBLISHING_COMING_SOON):
        col.info(f"{icon}  **{feature}**")
