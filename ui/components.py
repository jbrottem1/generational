"""Reusable UI components shared by tabs and the sidebar."""

from __future__ import annotations

import streamlit as st


def hashtags_text(hashtags) -> str:
    if isinstance(hashtags, list):
        return " ".join(hashtags)
    return str(hashtags or "—")


def attention_radar_chart(attention: dict) -> None:
    """Render the 12-dimension Attention Graph as a radar/spider chart.

    Falls back to a plain score list if plotly isn't installed, so the
    Ideas tab never breaks over an optional charting dependency.
    """
    radar = attention.get("radar_chart", {})
    labels = radar.get("labels", [])
    scores = radar.get("scores", [])
    if not labels or not scores:
        return

    try:
        import plotly.graph_objects as go
    except ImportError:
        for label, score in zip(labels, scores):
            st.caption(f"· {label}: {score}")
        return

    fig = go.Figure(
        data=go.Scatterpolar(
            r=scores + scores[:1],
            theta=labels + labels[:1],
            fill="toself",
            name="Attention Graph",
        )
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False,
        margin=dict(l=30, r=30, t=20, b=20),
        height=360,
    )
    st.plotly_chart(fig, use_container_width=True)


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
            score_cols[2].metric("Viral Score", scores["psychology"])
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

        report = idea.get("psychology_report")
        if report:
            with st.expander(f"🧠 Psychology & Virality Report · {report.get('viral_score', 0)}/100 ({report.get('tier', '—')})"):
                st.write(report.get("summary", ""))
                strength_col, weak_col = st.columns(2)
                with strength_col:
                    st.markdown("**💪 Top Strengths**")
                    for item in report.get("strengths", []):
                        st.caption(f"· {item['dimension']} ({item['score']}) — {item['note']}")
                with weak_col:
                    st.markdown("**⚠️ Weakest Levers**")
                    for item in report.get("weaknesses", []):
                        st.caption(f"· {item['dimension']} ({item['score']}) — {item['note']}")

        attention = idea.get("attention_graph")
        if attention:
            with st.expander(f"🕸️ Attention Graph · {attention.get('attention_score', 0)}/100"):
                attention_radar_chart(attention)
                st.markdown("**🎯 Recommendations to raise each score**")
                scores = attention.get("scores", {})
                recommendations = attention.get("recommendations", {})
                labels = dict(zip(scores.keys(), attention.get("radar_chart", {}).get("labels", [])))
                for key in sorted(scores, key=lambda k: scores[k]):
                    label = labels.get(key, key.replace("_", " ").title())
                    st.caption(f"· **{label}** ({scores[key]}) — {recommendations.get(key, '')}")

        threat_report = idea.get("threat_report")
        if threat_report:
            level = threat_report.get("threat_level", "Low")
            level_icon = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}.get(level, "🟢")
            with st.expander(
                f"🚨 Threat Report · {level_icon} {level} "
                f"({threat_report.get('threat_score', 0)}/100 · {threat_report.get('confidence', 0)}% confidence)"
            ):
                st.write(threat_report.get("summary", ""))
                flagged = threat_report.get("flagged_threats", [])
                if flagged:
                    st.markdown("**⚠️ Flagged Threats & Fixes**")
                    for item in flagged:
                        st.caption(f"· **{item['label']}** ({item['score']}) — {item['fix']}")
                else:
                    st.caption("No threats crossed the flagging threshold.")

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


def trend_dashboard(dashboard: dict, opportunities: list) -> None:
    """Compact Trend Discovery panel — top opportunities and aggregate signals."""
    if not opportunities:
        return

    cols = st.columns(4)
    cols[0].metric("Top Opportunity Score", f"{dashboard.get('top_score', 0)}/100")
    cols[1].metric("Avg Growth", f"{dashboard.get('average_growth_pct', 0)}%")
    cols[2].metric("Velocity", f"{dashboard.get('average_velocity', 0):.2f}")
    cols[3].metric("Platforms", len(dashboard.get("platforms", [])))

    meta = []
    if dashboard.get("countries"):
        meta.append("🌍 " + ", ".join(dashboard["countries"]))
    if dashboard.get("platforms"):
        meta.append("📱 " + ", ".join(dashboard["platforms"]))
    if dashboard.get("languages"):
        meta.append("🗣 " + ", ".join(dashboard["languages"]))
    if dashboard.get("discovered_at"):
        meta.append(f"🕒 discovered {dashboard['discovered_at'][:16].replace('T', ' ')} UTC")
    if meta:
        st.caption(" · ".join(meta))

    with st.expander(f"📡 Top {len(opportunities)} Opportunities"):
        for rank, opp in enumerate(opportunities, start=1):
            trend = opp.get("trend", {})
            st.markdown(
                f"**{rank}. {trend.get('topic', '—')}** — score {opp.get('opportunity_score', 0)}/100 · "
                f"{trend.get('platform', '?')} · {trend.get('country', '?')} · "
                f"growth {trend.get('growth_pct', 0)}% · via {trend.get('source', '?')}"
            )


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
