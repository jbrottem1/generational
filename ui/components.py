"""Reusable UI components shared by tabs and the sidebar."""

from __future__ import annotations

import streamlit as st


def hashtags_text(hashtags) -> str:
    if isinstance(hashtags, list):
        return " ".join(hashtags)
    return str(hashtags or "—")


def idea_card(index: int, idea: dict) -> None:
    """Expandable card showing the full content package for one idea."""
    title = idea.get("title", f"Idea #{index}")
    with st.expander(f"{index}. {title}"):
        st.markdown(f"**🎣 Hook:** {idea.get('hook', '—')}")
        st.markdown("**📝 Script (15-30s):**")
        st.write(idea.get("script", "—"))
        st.markdown(f"**📣 CTA:** {idea.get('cta', '—')}")
        st.markdown(f"**#️⃣ Hashtags:** {hashtags_text(idea.get('hashtags'))}")
        st.markdown(f"**🖼️ Thumbnail Concept:** {idea.get('thumbnail_concept', '—')}")


def pipeline_flow(stages) -> None:
    """Horizontal stage flow (icon boxes joined by arrows)."""
    cols = st.columns(len(stages) * 2 - 1)
    for index, stage in enumerate(stages):
        cols[index * 2].markdown(
            f"<div class='pipeline-step'>{stage.icon}<br>{stage.label}</div>", unsafe_allow_html=True
        )
        if index < len(stages) - 1:
            cols[index * 2 + 1].markdown("<div class='pipeline-arrow'>→</div>", unsafe_allow_html=True)


def coming_soon_grid(features, columns: int = 3) -> None:
    """Grid of (icon, label) feature teasers."""
    cols = st.columns(min(columns, len(features)))
    for index, (icon, feature) in enumerate(features):
        cols[index % len(cols)].info(f"{icon}  **{feature}**")


def status_card(icon: str, label: str, badge: str) -> None:
    """Card with an icon, bold label, and a muted status badge."""
    st.markdown(
        f"<div class='status-card'>{icon}<br><b>{label}</b><br>"
        f"<span class='badge-muted'>{badge}</span></div>",
        unsafe_allow_html=True,
    )
