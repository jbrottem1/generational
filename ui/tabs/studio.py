"""Creative Studio tab — primary workspace for the Generational platform."""

from __future__ import annotations

import streamlit as st

from core import storage
from core.models import project_from_result, project_widget_key
from services import studio
from services.studio.projects import list_folders, list_tags
from ui import notify
from ui.studio import components


def render() -> None:
    st.subheader("🎬 Creative Studio")
    st.caption("Control the complete content production pipeline — from idea to publish.")

    _handle_pending_actions()

    workspace, create, pipeline, preview, settings, providers, library, dashboard, readiness = st.tabs([
        "🏠 Workspace",
        "✨ Create",
        "⚡ Pipeline",
        "👁️ Preview",
        "⚙️ Settings",
        "🔌 Providers",
        "📚 Library",
        "📊 Dashboard",
        "🛡 Readiness",
    ])

    with workspace:
        _render_workspace()
    with create:
        _render_create()
    with pipeline:
        _render_pipeline()
    with preview:
        _render_preview()
    with settings:
        _render_settings()
    with providers:
        _render_providers()
    with library:
        _render_library()
    with dashboard:
        _render_dashboard()
    with readiness:
        _render_readiness()


def _handle_pending_actions() -> None:
    action = st.session_state.pop("_studio_action", None)
    if not action:
        return
    kind, target = action
    try:
        if kind == "open":
            project = storage.load_project_by_id(target) if target else None
            if project is None and target:
                project = storage.load_project(target)
            if project:
                from ui.project_state import queue_project_open

                queue_project_open(project)
                notify.success(f"Opened '{project['name']}' — switch to the Projects tab for the workspace.")
            else:
                raise ValueError(f"Project '{target}' not found.")
        elif kind == "duplicate":
            source = storage.load_project_by_id(target) or storage.load_project(target)
            if not source:
                raise ValueError(f"Project '{target}' not found.")
            new_name = f"{source['name']} (copy)"
            studio.duplicate_project(source["name"], new_name)
            notify.success(f"Duplicated as '{new_name}'")
        elif kind == "archive":
            source = storage.load_project_by_id(target) or storage.load_project(target)
            if not source:
                raise ValueError(f"Project '{target}' not found.")
            studio.archive_project(source["name"])
            notify.success(f"Archived '{source['name']}'")
    except ValueError as exc:
        notify.error(str(exc))
    st.rerun()


def _render_workspace() -> None:
    st.markdown("### Project Workspace")

    filter_cols = st.columns([2, 1, 1, 1])
    search = filter_cols[0].text_input("Search projects", key="studio_search")
    folders = ["All"] + list_folders()
    folder = filter_cols[1].selectbox("Folder", folders)
    platforms = ["All"] + [p["id"] for p in studio.STUDIO_PLATFORMS]
    platform = filter_cols[2].selectbox(
        "Platform",
        platforms,
        format_func=lambda x: "All" if x == "All" else next(
            p["label"] for p in studio.STUDIO_PLATFORMS if p["id"] == x
        ),
    )
    show_archived = filter_cols[3].checkbox("Archived", key="studio_show_archived")

    all_tags = list_tags()
    selected_tags = st.multiselect("Filter by tags", all_tags, key="studio_tag_filter")

    projects = studio.list_studio_projects(
        search=search,
        folder="" if folder == "All" else folder,
        platform="" if platform == "All" else platform,
        tags=selected_tags or None,
        include_archived=show_archived,
    )

    new_cols = st.columns([3, 1, 1])
    new_name = new_cols[0].text_input("New project name", key="studio_new_project_name")
    new_platform = new_cols[1].selectbox(
        "Platform",
        [p["id"] for p in studio.STUDIO_PLATFORMS],
        format_func=lambda x: next(p["label"] for p in studio.STUDIO_PLATFORMS if p["id"] == x),
        key="studio_new_platform",
    )
    if new_cols[2].button("➕ Create", use_container_width=True):
        _create_new_project(new_name, new_platform)

    st.divider()
    if not projects:
        st.caption("No projects match your filters.")
        return

    for index, project in enumerate(projects):
        components.project_card(
            project,
            index=index,
            on_open_key=project_widget_key(project, "studio_open", index),
            on_dup_key=project_widget_key(project, "studio_dup", index),
            on_archive_key=project_widget_key(project, "studio_arch", index),
        )


def _create_new_project(name: str, platform: str) -> None:
    if not name.strip():
        st.warning("Enter a project name.")
        return
    try:
        settings = studio.build_default_settings(platform)
        studio.create_studio_project(name, platform=platform, settings=settings)
        st.session_state.current_project_name = name.strip()
        st.session_state.studio_settings = settings
        notify.success(f"Created '{name}'")
        st.rerun()
    except ValueError as exc:
        notify.error(str(exc))


def _render_create() -> None:
    st.markdown("### Creative Prompt Panel")

    command = st.text_area(
        "Production command",
        key="studio_command",
        placeholder='e.g. "Create a 12 minute documentary" or "Create ten TikTok videos"',
        height=100,
    )

    st.caption("Example prompts:")
    prompt_cols = st.columns(2)
    for index, prompt in enumerate(studio.STUDIO_EXAMPLE_PROMPTS):
        if prompt_cols[index % 2].button(prompt, key=f"studio_prompt_{index}", use_container_width=True):
            st.session_state.studio_command = prompt
            st.rerun()

    platform = st.selectbox(
        "Production type",
        [p["id"] for p in studio.STUDIO_PLATFORMS],
        format_func=lambda x: next(f"{p['icon']} {p['label']}" for p in studio.STUDIO_PLATFORMS if p["id"] == x),
        key="studio_create_platform",
    )

    if platform != st.session_state.studio_settings.get("platform"):
        st.session_state.studio_settings = studio.build_default_settings(platform)

    preview = studio.build_settings_preview(command or "Preview command", st.session_state.studio_settings)
    components.settings_preview_card(preview)

    run_cols = st.columns(2)
    run_standard = run_cols[0].button("🚀 Run Production", type="primary", use_container_width=True)
    run_longform = run_cols[1].button("⏱️ Submit Long-form Job", use_container_width=True)

    if run_standard or run_longform:
        _execute_production(command, longform=run_longform)


def _ensure_autosave_project(command: str) -> str:
    """Create a named project when production succeeds without one selected."""
    from datetime import datetime, timezone

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    snippet = " ".join((command or "production").strip().split())[:40] or "production"
    name = f"RC1 {snippet} ({stamp})"
    try:
        studio.create_studio_project(name, folder="Studio Autosave", tags=["autosave", "rc1"])
    except ValueError:
        # Name collision — fold into the existing project.
        pass
    return name


def _execute_production(command: str, *, longform: bool = False) -> None:
    if not command.strip():
        st.warning("Enter a production command.")
        return

    settings = dict(st.session_state.studio_settings)
    research_settings = {
        "enabled_providers": st.session_state.research_enabled_providers,
        "cache_ttl_hours": st.session_state.research_cache_hours,
        "max_sources": st.session_state.research_max_sources,
        "min_confidence": st.session_state.research_min_confidence,
        "research_depth": st.session_state.research_depth,
        "science_medical_strict": st.session_state.science_medical_strict,
        "citation_required": st.session_state.citation_required,
        "research_confidence_threshold": st.session_state.research_confidence_threshold,
        "max_unsupported_claims": st.session_state.max_unsupported_claims,
        "min_claim_confidence": st.session_state.min_claim_confidence,
    }

    if longform or studio.is_longform_command(command):
        with st.spinner("Submitting long-form production job..."):
            job = studio.submit_longform_job(
                command,
                settings,
                model=st.session_state.selected_model,
                project_name=st.session_state.current_project_name or "",
            )
        project_name = st.session_state.current_project_name or _ensure_autosave_project(command)
        project = storage.load_project(project_name) or {"name": project_name}
        project["command"] = command
        project["studio_settings"] = settings
        project["longform_job_id"] = job.get("job_id", "")
        if job.get("run_id"):
            project["workflow_run_id"] = job["run_id"]
        storage.save_project(project)
        st.session_state.current_project_name = project_name
        notify.success(
            f"Long-form job submitted: {job.get('job_id')} · saved on project '{project_name}'. "
            "Open Projects to track workflow_run_id / resume from Workflow Executor."
        )
        return

    with st.spinner("Running production via Workflow Executor → Orchestrator..."):
        result = studio.run_studio_production(
            command,
            settings,
            model=st.session_state.selected_model,
            threshold=st.session_state.publish_threshold,
            research_settings=research_settings,
            project_name=st.session_state.current_project_name,
        )

    error = result.pop("error", None)
    tokens = result.pop("tokens_used", 0)
    st.session_state.current_result = result
    st.session_state.studio_pipeline = studio.build_pipeline_view(
        stage_reports=result.get("stage_reports"),
        production_dashboard=result.get("production_dashboard"),
        pipeline_steps=result.get("pipeline_steps"),
    )

    from core import state
    state.record_ideas_generated(len(result.get("ideas", [])))
    state.add_token_usage(tokens)

    project_name = st.session_state.current_project_name or _ensure_autosave_project(command)
    project = storage.load_project(project_name) or {"name": project_name}
    project.update(project_from_result(project_name, result))
    project["studio_settings"] = settings
    project["pipeline_state"] = {"stages": st.session_state.studio_pipeline}
    if result.get("workflow_run_id"):
        project["workflow_run_id"] = result["workflow_run_id"]
    storage.save_project(project)
    st.session_state.current_project_name = project_name

    if error:
        st.warning(f"Pipeline completed with warnings: {error}")
    notify.success(f"Production complete — {len(result.get('ideas', []))} scripts generated")


def _render_pipeline() -> None:
    st.markdown("### Pipeline Visualization")
    result = st.session_state.current_result
    stages = st.session_state.studio_pipeline
    if not stages and result:
        stages = studio.build_pipeline_view(
            stage_reports=result.get("stage_reports"),
            production_dashboard=result.get("production_dashboard"),
            pipeline_steps=result.get("pipeline_steps"),
        )
    components.pipeline_timeline(stages or [
        {**s, "status": "pending", "elapsed_sec": 0, "estimated_remaining_sec": 0, "errors": [], "warnings": [], "can_retry": False}
        for s in studio.STUDIO_PIPELINE_STAGES
    ])


def _render_preview() -> None:
    st.markdown("### Live Preview")
    previews = studio.extract_previews(st.session_state.current_result)
    components.preview_panel(previews)


def _render_settings() -> None:
    st.markdown("### Project Settings")
    settings = st.session_state.studio_settings

    cols = st.columns(3)
    settings["video_length_sec"] = cols[0].number_input(
        "Video length (sec)", min_value=15, max_value=14400, value=settings.get("video_length_sec", 60)
    )
    settings["platform"] = cols[1].selectbox(
        "Platform",
        [p["id"] for p in studio.STUDIO_PLATFORMS],
        index=[p["id"] for p in studio.STUDIO_PLATFORMS].index(settings.get("platform", "youtube_shorts")),
        format_func=lambda x: next(p["label"] for p in studio.STUDIO_PLATFORMS if p["id"] == x),
    )
    settings["quality_level"] = cols[2].selectbox(
        "Quality Level", ["draft", "standard", "high", "cinema"],
        index=["draft", "standard", "high", "cinema"].index(settings.get("quality_level", "standard")),
    )

    cols2 = st.columns(3)
    settings["voice"] = cols2[0].selectbox("Voice", ["ai", "clone", "human"], index=["ai", "clone", "human"].index(settings.get("voice", "ai")))
    settings["narrator"] = cols2[1].selectbox(
        "Narrator", ["documentary", "energetic", "calm", "professional"],
        index=["documentary", "energetic", "calm", "professional"].index(settings.get("narrator", "documentary")),
    )
    settings["language"] = cols2[2].text_input("Language", value=settings.get("language", "en"))

    cols3 = st.columns(3)
    settings["visual_style"] = cols3[0].selectbox(
        "Visual Style", ["cinematic", "minimal", "animated", "documentary", "corporate"],
        index=["cinematic", "minimal", "animated", "documentary", "corporate"].index(settings.get("visual_style", "cinematic")),
    )
    settings["camera_style"] = cols3[1].selectbox(
        "Camera Style", ["dynamic", "static", "handheld", "aerial", "studio"],
        index=["dynamic", "static", "handheld", "aerial", "studio"].index(settings.get("camera_style", "dynamic")),
    )
    settings["music_style"] = cols3[2].selectbox(
        "Music Style", ["uplifting", "dramatic", "ambient", "corporate", "none"],
        index=["uplifting", "dramatic", "ambient", "corporate", "none"].index(settings.get("music_style", "uplifting")),
    )

    cols4 = st.columns(3)
    settings["pacing"] = cols4[0].selectbox(
        "Pacing", ["slow", "moderate", "dynamic", "fast"],
        index=["slow", "moderate", "dynamic", "fast"].index(settings.get("pacing", "dynamic")),
    )
    settings["target_audience"] = cols4[1].text_input("Target Audience", value=settings.get("target_audience", "general"))
    settings["budget_usd"] = cols4[2].number_input("Budget (USD)", min_value=0.0, value=float(settings.get("budget_usd", 0)))

    cols5 = st.columns(3)
    settings["brand"] = cols5[0].text_input("Brand", value=settings.get("brand", ""))
    settings["character_set"] = cols5[1].text_input("Character Set", value=settings.get("character_set", ""))
    settings["creative_style"] = cols5[2].selectbox(
        "Creative Style", ["narrative_arc", "listicle", "tutorial", "interview", "montage"],
        index=["narrative_arc", "listicle", "tutorial", "interview", "montage"].index(
            settings.get("creative_style", "narrative_arc")
        ),
    )

    settings["preferred_providers"] = st.multiselect(
        "Preferred Providers",
        [p["name"] for p in studio.get_provider_dashboard().get("providers", [])],
        default=settings.get("preferred_providers", []),
    )

    st.session_state.studio_settings = settings

    if st.button("💾 Save Settings to Project", use_container_width=True):
        name = st.session_state.current_project_name
        if not name:
            st.warning("Open or create a project first.")
            return
        studio.update_project_metadata(name, studio_settings=settings)
        notify.success(f"Settings saved to '{name}'")


def _render_providers() -> None:
    st.markdown("### Provider Status")
    dashboard = studio.get_provider_dashboard()
    components.provider_status_grid(dashboard)


def _render_library() -> None:
    st.markdown("### Output Library")
    library = studio.collect_output_library()
    components.output_library_view(library)


def _render_dashboard() -> None:
    st.markdown("### Executive Dashboard")
    dashboard = studio.get_executive_dashboard()
    components.executive_dashboard_view(dashboard)


def _render_readiness() -> None:
    st.markdown("### Production Readiness")
    report = studio.get_production_readiness()
    components.production_readiness_view(report)

    master = report.get("master_pipeline") or {}
    if master:
        st.markdown("#### Master Pipeline (Agent 1)")
        st.metric("E2E readiness score", master.get("score", "—"))
        st.caption(f"Band: `{master.get('band')}`")
        reg = master.get("registry") or {}
        c1, c2, c3 = st.columns(3)
        c1.metric("Engines ready", f"{reg.get('engines_ready', 0)}/{reg.get('engine_count', 0)}")
        c2.metric("Agents ready", reg.get("agents_ready", 0))
        c3.metric("Providers configured", master.get("providers_configured", 0))
        if master.get("blockers"):
            st.warning("Blockers for finished MP4 / live publish:")
            for item in master["blockers"]:
                st.markdown(f"- {item}")
        st.caption(f"First production: {master.get('estimated_time_to_first_production')}")
        st.caption(f"First publish: {master.get('estimated_time_to_first_publish')}")
        if master.get("next_priorities"):
            with st.expander("Recommended next priorities"):
                for item in master["next_priorities"]:
                    st.markdown(f"1. {item}")
