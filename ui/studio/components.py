"""Studio UI components — pipeline visualization, previews, and panels."""

from __future__ import annotations

import streamlit as st

STATUS_ICONS = {
    "pending": "○",
    "running": "⏳",
    "completed": "✔",
    "failed": "✗",
    "retry": "↻",
}

STATUS_COLORS = {
    "pending": "#6b7280",
    "running": "#7c5cff",
    "completed": "#22c55e",
    "failed": "#ef4444",
    "retry": "#f59e0b",
}


def pipeline_timeline(stages: list) -> None:
    """Vertical pipeline visualization with status, timing, and retry."""
    if not stages:
        st.caption("No pipeline data yet. Run a production to see stage progress.")
        return

    for stage in stages:
        icon = STATUS_ICONS.get(stage.get("status", "pending"), "○")
        color = STATUS_COLORS.get(stage.get("status", "pending"), "#6b7280")
        elapsed = stage.get("elapsed_sec", 0)
        remaining = stage.get("estimated_remaining_sec", 0)

        timing = ""
        if elapsed:
            timing += f" · {elapsed}s elapsed"
        if remaining and stage.get("status") in ("pending", "running"):
            timing += f" · ~{remaining}s remaining"

        st.markdown(
            f"<div style='display:flex;align-items:center;gap:12px;padding:8px 0;"
            f"border-left:3px solid {color};padding-left:16px;margin-left:8px;'>"
            f"<span style='font-size:1.2rem;'>{stage.get('icon', '')}</span>"
            f"<div><b>{stage.get('label', '')}</b> "
            f"<span style='color:{color};'>{icon} {stage.get('status', 'pending').title()}</span>"
            f"<span style='color:#9aa0ab;font-size:0.85rem;'>{timing}</span></div></div>",
            unsafe_allow_html=True,
        )

        if stage.get("errors"):
            for error in stage["errors"]:
                if error:
                    st.caption(f"⚠️ {error}")
        if stage.get("can_retry"):
            st.caption("↻ Retry available")


def settings_preview_card(preview: dict) -> None:
    """Display production settings before execution."""
    cols = st.columns(4)
    cols[0].metric("Platform", preview.get("platform", "—"))
    cols[1].metric("Duration", preview.get("video_length_label", "—"))
    cols[2].metric("Videos", preview.get("video_count", 1))
    cols[3].metric("Mode", "Long-form" if preview.get("longform") else "Standard")

    with st.expander("Full Production Settings", expanded=False):
        settings_cols = st.columns(3)
        fields = [
            ("Voice", preview.get("voice")),
            ("Narrator", preview.get("narrator")),
            ("Visual Style", preview.get("visual_style")),
            ("Camera Style", preview.get("camera_style")),
            ("Music Style", preview.get("music_style")),
            ("Pacing", preview.get("pacing")),
            ("Audience", preview.get("target_audience")),
            ("Language", preview.get("language")),
            ("Quality", preview.get("quality_level")),
            ("Creative Style", preview.get("creative_style")),
            ("Brand", preview.get("brand") or "—"),
            ("Budget", f"${preview.get('budget_usd', 0):.2f}"),
        ]
        for index, (label, value) in enumerate(fields):
            settings_cols[index % 3].caption(f"**{label}:** {value}")
        providers = preview.get("preferred_providers", [])
        if providers:
            st.caption(f"**Preferred Providers:** {', '.join(providers)}")


def preview_panel(previews: dict) -> None:
    """Tabbed live preview panels for all asset types."""
    tabs = st.tabs([
        "Scripts", "Images", "Animation", "Voice", "Music",
        "Video", "Thumbnails", "Titles", "Descriptions", "Captions", "Subtitles",
    ])

    with tabs[0]:
        _render_scripts(previews.get("scripts", []))
    with tabs[1]:
        _render_images(previews.get("images", []))
    with tabs[2]:
        _render_animation(previews.get("animation", []))
    with tabs[3]:
        _render_voice(previews.get("voice", []))
    with tabs[4]:
        _render_music(previews.get("music", []))
    with tabs[5]:
        _render_videos(previews.get("videos", []))
    with tabs[6]:
        _render_thumbnails(previews.get("thumbnails", []))
    with tabs[7]:
        _render_list("Titles", previews.get("titles", []))
    with tabs[8]:
        _render_list("Descriptions", previews.get("descriptions", []))
    with tabs[9]:
        _render_captions(previews.get("captions", []))
    with tabs[10]:
        _render_subtitles(previews.get("subtitles", []))


def provider_status_grid(dashboard: dict) -> None:
    """Provider health, cost, and availability grid."""
    cols = st.columns(4)
    cols[0].metric("Healthy", dashboard.get("healthy_count", 0))
    cols[1].metric("Degraded", dashboard.get("degraded_count", 0))
    cols[2].metric("Total Calls", dashboard.get("total_calls", 0))
    cols[3].metric("Est. Cost", f"${dashboard.get('total_cost_usd', 0):.4f}")

    for provider in dashboard.get("providers", []):
        health_icon = {"healthy": "🟢", "degraded": "🟡", "unavailable": "🔴"}.get(
            provider.get("health", ""), "⚪"
        )
        with st.container(border=True):
            pcols = st.columns([3, 1, 1, 1])
            pcols[0].markdown(
                f"**{provider.get('label', provider.get('name', ''))}** {health_icon}  \n"
                f"{', '.join(provider.get('capabilities', [])[:3])}"
            )
            pcols[1].metric("Calls", provider.get("calls", 0))
            pcols[2].metric("Cost", f"${provider.get('cost_usd', 0):.4f}")
            pcols[3].caption(f"~{provider.get('estimated_runtime_sec', 0)}s/call")


def output_library_view(library: dict) -> None:
    """Output library with asset counts and browse."""
    categories = [
        ("videos", "Videos", "🎬"),
        ("audio", "Audio", "🎵"),
        ("images", "Images", "🖼️"),
        ("assets", "Assets", "📦"),
        ("scripts", "Scripts", "📝"),
        ("projects", "Projects", "📁"),
        ("characters", "Characters", "👤"),
        ("worlds", "Worlds", "🌍"),
        ("brand_packs", "Brand Packs", "🏷️"),
    ]
    cols = st.columns(len(categories))
    for index, (key, label, icon) in enumerate(categories):
        cols[index].metric(f"{icon} {label}", len(library.get(key, [])))

    selected = st.selectbox(
        "Browse category",
        [c[0] for c in categories],
        format_func=lambda k: next(f"{i} {l}" for key, l, i in categories if key == k),
    )
    items = library.get(selected, [])
    if not items:
        st.caption("No items in this category yet.")
        return
    for item in items[:25]:
        st.caption(f"· {item}")


def executive_dashboard_view(dashboard: dict) -> None:
    """Executive dashboard metrics."""
    cols = st.columns(4)
    cols[0].metric("Active Projects", dashboard.get("projects_active", 0))
    cols[1].metric("Running", dashboard.get("projects_running", 0))
    cols[2].metric("Published", dashboard.get("content_published", 0))
    cols[3].metric("Est. Costs", f"${dashboard.get('estimated_costs_usd', 0):.4f}")

    cols2 = st.columns(3)
    cols2[0].metric("Render Queue", dashboard.get("rendering_queue", {}).get("count", 0))
    cols2[1].metric("Publish Queue", dashboard.get("publishing_queue", {}).get("queued_count", 0))
    cols2[2].metric("Analytics Records", dashboard.get("analytics_summary", {}).get("record_count", 0))

    analytics = dashboard.get("analytics_summary", {})
    if analytics.get("record_count", 0):
        acols = st.columns(2)
        acols[0].metric("Total Views", analytics.get("total_views", 0))
        acols[1].metric("Avg Engagement", f"{analytics.get('avg_engagement', 0)}%")


def project_card(project: dict, *, on_open_key: str, on_dup_key: str, on_archive_key: str) -> None:
    """Render one project card in the workspace browser."""
    with st.container(border=True):
        cols = st.columns([4, 1, 1, 1])
        platform = project.get("platform", "").replace("_", " ").title()
        tags = ", ".join(project.get("tags", [])) or "—"
        updated = (project.get("updated_at") or "")[:19].replace("T", " ")
        cols[0].markdown(
            f"**{project['name']}**  \n"
            f"📂 {project.get('folder', 'General')} · 📱 {platform} · "
            f"🏷️ {tags} · {len(project.get('ideas', []))} ideas · updated {updated or '—'}"
        )
        if cols[1].button("Open", key=on_open_key, use_container_width=True):
            st.session_state._studio_action = ("open", project["name"])
        if cols[2].button("Duplicate", key=on_dup_key, use_container_width=True):
            st.session_state._studio_action = ("duplicate", project["name"])
        if cols[3].button("Archive", key=on_archive_key, use_container_width=True):
            st.session_state._studio_action = ("archive", project["name"])


def _render_scripts(scripts: list) -> None:
    if not scripts:
        st.caption("No scripts yet.")
        return
    for script in scripts:
        with st.expander(script.get("title", "Script")):
            if script.get("hook"):
                st.markdown(f"**Hook:** {script['hook']}")
            st.write(script.get("script", ""))


def _render_images(images: list) -> None:
    if not images:
        st.caption("No images yet.")
        return
    for img in images:
        st.caption(f"· [{img.get('type', 'image')}] {img.get('label', '')} — {img.get('description', '')}")


def _render_animation(items: list) -> None:
    if not items:
        st.caption("No animation data yet.")
        return
    for item in items:
        st.caption(f"· Scene {item.get('scene', '')}: {item.get('motion', '')} ({item.get('camera', '')})")


def _render_voice(items: list) -> None:
    if not items:
        st.caption("No voice assets yet.")
        return
    for item in items:
        st.caption(f"· {item.get('profile', 'voice')} — {item.get('duration_sec', 0)}s ({item.get('status', '')})")


def _render_music(items: list) -> None:
    if not items:
        st.caption("No music assets yet.")
        return
    for item in items:
        st.caption(f"· {item.get('mood', 'music')} — {item.get('duration_sec', 0)}s")


def _render_videos(items: list) -> None:
    if not items:
        st.caption("No videos yet.")
        return
    for item in items:
        st.caption(f"· {item.get('format', 'mp4')} — {item.get('duration_sec', 0)}s ({item.get('status', '')})")


def _render_thumbnails(items: list) -> None:
    if not items:
        st.caption("No thumbnails yet.")
        return
    for item in items:
        score = f" ({item['score']}/100)" if item.get("score") else ""
        st.caption(f"· **{item.get('title', '')}**{score}: {item.get('concept', '')}")


def _render_list(label: str, items: list) -> None:
    if not items:
        st.caption(f"No {label.lower()} yet.")
        return
    for item in items:
        st.caption(f"· {item}")


def _render_captions(items: list) -> None:
    if not items:
        st.caption("No captions yet.")
        return
    for item in items:
        if isinstance(item, dict):
            st.caption(f"· {item.get('title', '')}: {item.get('hashtags', item)}")
        else:
            st.caption(f"· {item}")


def _render_subtitles(items: list) -> None:
    if not items:
        st.caption("No subtitles yet.")
        return
    for item in items:
        st.caption(f"· {item}")
