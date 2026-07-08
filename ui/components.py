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
    scores = idea.get("scores")
    header = f"{index}. {title}"
    if scores:
        gate = "🟢" if idea.get("publishable") else "🔒"
        header = f"{gate} {header} · {scores['publish']}"

    with st.expander(header):
        if scores:
            score_cols = st.columns(6)
            score_cols[0].metric("Publish", scores["publish"])
            score_cols[1].metric("Opportunity", scores["opportunity"])
            score_cols[2].metric("Psychology", scores["psychology"])
            score_cols[3].metric("SEO", scores["seo"])
            score_cols[4].metric("Retention", f"{scores['retention']}%")
            score_cols[5].metric("CTR", f"{scores['ctr']}%")
            if not idea.get("publishable"):
                st.warning("🔒 Below the publish threshold — held back from publishing.")

        st.markdown(f"**🎣 Hook:** {idea.get('hook', '—')}")
        st.markdown("**📝 Script (15-30s):**")
        st.write(idea.get("script", "—"))
        st.markdown(f"**📣 CTA:** {idea.get('cta', '—')}")
        st.markdown(f"**#️⃣ Hashtags:** {hashtags_text(idea.get('hashtags'))}")
        if idea.get("keywords"):
            st.markdown(f"**🔑 Keywords:** {', '.join(idea['keywords'])}")
        if idea.get("description"):
            st.markdown(f"**📄 Description:** {idea['description']}")
        st.markdown(f"**🖼️ Thumbnail Concept:** {idea.get('thumbnail_concept', '—')}")

        critique = idea.get("critique")
        if critique is not None:
            if idea.get("revised"):
                fixes = "; ".join(idea.get("revisions", [])) or "minor polish"
                st.caption(f"🔧 Auto-revised after critic review ({fixes}) · Critic score: {critique['score']}")
            else:
                st.caption(f"🧐 Passed critic review clean · Critic score: {critique['score']}")

        production = idea.get("production")
        if production:
            st.markdown("**🎬 Production Package**")
            pcols = st.columns(4)
            pcols[0].metric("Scenes", production.get("scenes", 0))
            pcols[1].metric("Duration", f"{production.get('duration_sec', 0)}s")
            pcols[2].metric("Assets", production.get("assets", 0))
            pcols[3].metric("Queue", production.get("queue_status", "—"))

        refs = idea.get("references")
        citations = idea.get("citations")
        if citations or refs:
            with st.expander("📎 Citations & Fact-Check"):
                if citations:
                    st.metric("Claim Confidence", f"{citations.get('claim_confidence', 0)}%")
                    for note in citations.get("fact_check_notes", []):
                        st.caption(f"· {note}")
                    unsupported = citations.get("unsupported_claims", [])
                    if unsupported:
                        st.warning("Unsupported claims:")
                        for claim in unsupported:
                            st.markdown(f"- {claim}")
                    for cite in citations.get("citation_list", []):
                        st.markdown(f"- **{cite.get('title', 'Source')}** ({cite.get('source_name', '')}) — {cite.get('url', '')}")
                elif refs:
                    for src in refs.get("sources", []):
                        st.markdown(f"- **{src.get('title', 'Source')}** ({src.get('provider', '')}) — {src.get('url', '')}")


def production_dashboard(stages: list) -> None:
    """Compact production progress panel — intelligence + media stages."""
    if not stages:
        return

    state_icons = {
        "completed": "✔",
        "running": "⏳",
        "waiting": "○",
        "retrying": "↻",
        "failed": "✗",
    }
    cols = st.columns(min(len(stages), 6))
    for index, stage in enumerate(stages):
        icon = state_icons.get(stage.get("state", "waiting"), "○")
        cols[index % len(cols)].caption(f"{icon} **{stage.get('label', stage.get('key', ''))}**")


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
