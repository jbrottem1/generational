"""Analytics tab — session-level placeholder stats until Publishing is live."""

from __future__ import annotations

import streamlit as st

from core import storage
from core.constants import ANALYTICS_COMING_SOON
from ui import components


def render() -> None:
    st.subheader("📊 Analytics")
    st.caption(
        "Real performance analytics will appear here once Auto Posting is connected. "
        "Showing session placeholders for now."
    )

    ideas_total = st.session_state.ideas_generated_total
    projects_total = storage.project_count()
    scripts_total = ideas_total

    cols = st.columns(3)
    cols[0].metric("Ideas Generated", ideas_total)
    cols[1].metric("Scripts Written", scripts_total)
    cols[2].metric("Projects Saved", projects_total)

    st.markdown("#### Estimated Output Trend (placeholder)")
    trend = [max(ideas_total - 3 * i, 0) for i in range(4)][::-1]
    st.bar_chart({"Ideas": trend})

    st.divider()
    st.markdown("### 🔮 Coming Soon")
    components.coming_soon_grid(ANALYTICS_COMING_SOON)
