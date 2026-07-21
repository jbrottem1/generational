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

    executive_orchestrator_board(dashboard.get("executive_orchestrator") or {})
    continuous_learning_dashboard_view(dashboard.get("continuous_learning") or {})
    optimization_lab_board(dashboard.get("optimization_lab") or {})
    creative_performance_lab_board(dashboard.get("creative_performance_lab") or {})
    publishing_intelligence_board(dashboard.get("publishing_intelligence") or {})


def optimization_lab_board(board: dict) -> None:
    """Autonomous Optimization & Experimentation V4 board."""
    if not board or board.get("error") == "unavailable":
        return
    st.markdown("#### Optimization Lab")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Videos optimized", board.get("videos_optimized", 0))
    c2.metric("Avg QA score", board.get("average_qa_score", 0))
    c3.metric("Avg predicted CTR", f"{board.get('average_predicted_ctr', 0)}%")
    c4.metric("Avg retention proxy", f"{board.get('average_retention_proxy', 0)}%")

    st.caption(
        f"System health · {board.get('system_health', 'unknown')} · "
        f"Experiments recorded={(board.get('learning_progress') or {}).get('experiments_recorded', 0)}"
    )

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Top performing topics**")
        for row in (board.get("top_performing_topics") or [])[:5]:
            st.caption(f"· {row.get('topic')} — avg {row.get('avg_score')} (n={row.get('n')})")
        st.markdown("**Best hooks**")
        for hook in (board.get("best_hooks") or [])[:5]:
            st.caption(f"· {hook}")
    with col_b:
        st.markdown("**Best narration styles**")
        for style in (board.get("best_narration_styles") or [])[:5]:
            st.caption(f"· {style}")
        st.markdown("**Recent experiments**")
        for exp in (board.get("recent_experiments") or [])[:5]:
            w = exp.get("winning_version") or {}
            st.caption(
                f"· {exp.get('topic', '')[:40]} → v{w.get('label')} ({exp.get('production_score')})"
            )


def creative_performance_lab_board(board: dict) -> None:
    """Creative Performance Lab — evidence loop board."""
    if not board or board.get("error") == "unavailable":
        return
    st.markdown("#### Creative Performance Lab")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Experiments", board.get("experiment_count", 0))
    c2.metric("Awaiting review", len(board.get("awaiting_human_review") or []))
    c3.metric("Awaiting analytics", len(board.get("awaiting_analytics") or []))
    c4.metric("Validated learnings", board.get("validated_learnings_count", 0))
    st.caption(board.get("prediction_note") or "")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Recent experiments**")
        for exp in (board.get("recent_experiments") or [])[:6]:
            st.caption(f"· {exp.get('experiment_id')} — {str(exp.get('topic') or '')[:36]} [{exp.get('status')}]")
    with col_b:
        st.markdown("**Recent learnings**")
        for L in (board.get("recent_learnings") or [])[:6]:
            st.caption(f"· {L.get('creative_variable')}: {str(L.get('winning_pattern') or '')[:48]}")


def publishing_intelligence_board(board: dict) -> None:
    """Publishing Intelligence summary (already fetched by dashboard)."""
    if not board or board.get("error") == "unavailable":
        return
    st.markdown("#### Publishing Intelligence")
    c1, c2 = st.columns(2)
    c1.metric("Confidence", board.get("confidence_score", 0))
    cal = board.get("calibration")
    c2.metric("Calibration", str(cal.get("status") if isinstance(cal, dict) else (cal or "n/a"))[:24])


def continuous_learning_dashboard_view(board: dict) -> None:
    """Continuous Learning Dashboard — topics, CTR, retention, improvements."""
    if not board or board.get("error") == "unavailable":
        return
    st.markdown("#### Continuous Learning")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Productions recorded", board.get("productions_recorded", 0))
    c2.metric("Analytics records", board.get("analytics_records", 0))
    c3.metric("Insights", board.get("insights_count", 0))
    c4.metric("Recommendations", board.get("recommendations_count", 0))

    graph = board.get("knowledge_graph") or {}
    st.caption(
        f"Knowledge graph · {graph.get('node_count', 0)} nodes · {graph.get('edge_count', 0)} edges · "
        f"Experiments running={(board.get('experiments') or {}).get('running', 0)}"
    )

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Top topics**")
        for row in (board.get("top_performing_topics") or [])[:5]:
            st.caption(f"· {row.get('value')} (lift {row.get('lift')})")
        st.markdown("**Best hooks**")
        for row in (board.get("best_hooks") or [])[:5]:
            st.caption(f"· {str(row.get('value') or '')[:80]}")
    with col_b:
        st.markdown("**Highest CTR**")
        for row in (board.get("highest_ctr") or [])[:5]:
            st.caption(f"· {row.get('title') or row.get('topic')} — CTR {row.get('ctr')}")
        st.markdown("**Suggested improvements**")
        for tip in (board.get("suggested_improvements") or [])[:6]:
            st.caption(f"· {tip}")

    if board.get("viral_opportunity_queue"):
        with st.expander("Viral opportunity queue"):
            for row in board["viral_opportunity_queue"][:10]:
                st.markdown(f"- `{row.get('dimension')}` **{row.get('topic')}** · lift {row.get('lift')}")


def executive_orchestrator_board(board: dict) -> None:
    """Live Production Dashboard: Discovery → … → Publishing."""
    if not board:
        return
    st.markdown("#### Live Production (Executive Orchestrator)")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Active runs", board.get("active_count", 0))
    m2.metric("Pending", board.get("pending_count", 0))
    m3.metric("Completed", board.get("completed_count", 0))
    m4.metric("Failed", board.get("failed_count", 0))

    stages = board.get("stages") or []
    if stages:
        cols = st.columns(min(4, len(stages)))
        for i, stage in enumerate(stages):
            col = cols[i % len(cols)]
            label = stage.get("label") or stage.get("key")
            running = int(stage.get("running") or 0)
            completed = int(stage.get("completed") or 0)
            failed = int(stage.get("failed") or 0)
            pending = int(stage.get("pending") or 0)
            status = "Running" if running else ("Failed" if failed else ("Completed" if completed and not pending else "Pending"))
            col.metric(label, status, delta=f"η {stage.get('eta_sec', '—')}s")

    for run in (board.get("active_runs") or board.get("recent_runs") or [])[:5]:
        topic = run.get("topic") or run.get("command") or run.get("id")
        with st.expander(f"{run.get('status', '?').upper()} · {topic}"):
            st.caption(
                f"Runtime {run.get('runtime_sec')}s · QA {run.get('qa_score')} ({run.get('qa_decision')}) · "
                f"ETA remaining {run.get('estimated_remaining_sec')}s"
            )
            for key, stage in (run.get("stages") or {}).items():
                st.markdown(
                    f"- **{stage.get('label') or key}**: `{stage.get('status')}`"
                    + (f" — {stage.get('message')}" if stage.get("message") else "")
                    + (f" · err: {stage.get('error')}" if stage.get("error") else "")
                )


def production_readiness_view(report: dict) -> None:
    """Production Readiness Dashboard — overall + area scores + blockers."""
    overall = int(report.get("overall") or 0)
    st.metric("Overall readiness", f"{overall} / 100")
    st.caption(f"v{report.get('version', '')} · {report.get('generated_at', '')}")

    scorecard = report.get("scorecard") or {}
    labels = [
        ("architecture", "Architecture"),
        ("execution", "Engines"),
        ("provider_runtime", "Provider health"),
        ("api", "API"),
        ("publishing", "Publishing"),
        ("longform", "Long-form"),
        ("learning", "Learning"),
        ("analytics", "Analytics"),
        ("security", "Security"),
        ("workflow_executor", "Workflow"),
    ]
    cols = st.columns(5)
    for i, (key, label) in enumerate(labels):
        cols[i % 5].metric(label, scorecard.get(key, "—"))

    engines = report.get("engines") or {}
    st.markdown(
        f"**Engines** — {engines.get('ready', 0)}/{engines.get('total', 0)} ready"
        + (f" · stubs: {', '.join(engines.get('stubs') or [])}" if engines.get("stubs") else "")
    )

    publishing = report.get("publishing") or {}
    analytics = report.get("analytics") or {}
    learning = report.get("learning") or {}
    api = report.get("api") or {}
    st.markdown(
        f"**Publishing** dry-run={publishing.get('dry_run_supported')} · "
        f"YouTube keyed={publishing.get('youtube_credentials')}  \n"
        f"**Analytics** YouTube registered={analytics.get('youtube_provider_registered')} · "
        f"live={analytics.get('youtube_live')}  \n"
        f"**Learning** armed={learning.get('continuous_learning_armed')}  \n"
        f"**API** internal HTTP={api.get('internal_http')}"
    )

    blockers = report.get("blockers") or []
    if blockers:
        st.warning("Remaining blockers:\n\n" + "\n".join(f"- {b}" for b in blockers))
    else:
        st.success("No structural readiness blockers.")


def project_card(
    project: dict,
    *,
    index: int,
    on_open_key: str,
    on_dup_key: str,
    on_archive_key: str,
) -> None:
    """Render one project card in the workspace browser."""
    project_id = project.get("project_id", "")
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
            st.session_state._studio_action = ("open", project_id)
        if cols[2].button("Duplicate", key=on_dup_key, use_container_width=True):
            st.session_state._studio_action = ("duplicate", project_id)
        if cols[3].button("Archive", key=on_archive_key, use_container_width=True):
            st.session_state._studio_action = ("archive", project_id)


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
