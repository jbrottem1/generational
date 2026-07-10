"""Projects tab — Create, Save, Open, Delete, and Project Workspace."""

from __future__ import annotations

import streamlit as st

from core import storage
from core.log import get_logger
from core.models import project_from_result, project_widget_key
from ui import notify
from ui.project_state import queue_project_clear, queue_project_open
from ui.project_workspace import render_workspace

logger = get_logger(__name__)


def render() -> None:
    if st.session_state.get("projects_view") == "workspace":
        render_workspace()
        return

    notice = st.session_state.pop("_projects_open_notice", None)
    if notice:
        notify.success(f"Opened '{notice}'")

    if st.session_state.pop("_projects_studio_hint", None):
        st.info("Project remains loaded in session. Switch to the **Studio** tab to continue.")

    st.subheader("📁 Projects")

    # If a project is loaded but user is on the list, offer a shortcut back in.
    if st.session_state.get("current_project_name") and st.session_state.get("opened_project_data"):
        cols = st.columns([3, 1])
        cols[0].caption(f"Currently loaded: **{st.session_state.current_project_name}**")
        if cols[1].button("Open workspace", key="reopen_workspace_shortcut", use_container_width=True):
            st.session_state.projects_view = "workspace"
            st.rerun()

    _render_create_save_panel()
    st.divider()
    _render_project_list()


def _render_create_save_panel() -> None:
    name = st.text_input("Project name", key="project_name_input")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Create Project", use_container_width=True):
            _create_project(name)
    with col2:
        if st.button("💾 Save Project", use_container_width=True):
            _save_project(name)


def _create_project(name: str) -> None:
    result = st.session_state.current_result
    if not name.strip():
        st.warning("Please enter a project name.")
        return
    if not result:
        st.warning("Generate some ideas in the Ideas tab first.")
        return
    if storage.load_project(name):
        st.warning("A project with that name already exists. Choose a different name or use Save Project.")
        return

    try:
        storage.save_project(project_from_result(name, result))
    except OSError as exc:
        logger.error("Failed to create project '%s': %s", name, exc)
        notify.error(f"Could not create project: {exc}")
        return
    st.session_state.current_project_name = name.strip()
    notify.success(f"Project '{name}' created!")
    st.rerun()


def _save_project(name: str) -> None:
    result = st.session_state.current_result
    if not name.strip():
        st.warning("Please enter a project name.")
        return

    existing = storage.load_project(name)
    if not existing and not result:
        st.warning("Nothing to save yet. Generate ideas or create a project first.")
        return

    project = existing or {"name": name.strip()}
    if result:
        project.update(project_from_result(name, result))
    project["name"] = name.strip()

    try:
        storage.save_project(project)
    except OSError as exc:
        logger.error("Failed to save project '%s': %s", name, exc)
        notify.error(f"Could not save project: {exc}")
        return
    st.session_state.current_project_name = name.strip()
    notify.success(f"Project '{name}' saved!")
    st.rerun()


def _render_project_list() -> None:
    projects = storage.list_projects()
    if not projects:
        st.caption("No saved projects yet. Generate ideas, then create a project above.")
        return

    st.markdown("### 🗂️ Saved Projects")
    for index, project in enumerate(projects):
        with st.container(border=True):
            cols = st.columns([3, 1, 1])
            updated = (project.get("updated_at") or "")[:19].replace("T", " ")
            idea_count = len(project.get("ideas") or project.get("generated_ideas") or [])
            cols[0].markdown(
                f"**{project['name']}**  \n"
                f"{project.get('niche', '—')} · {idea_count} ideas · updated {updated or '—'}"
            )
            if cols[1].button(
                "📂 Open",
                key=project_widget_key(project, "open", index),
                use_container_width=True,
            ):
                _open_project(project)
            if cols[2].button(
                "🗑️ Delete",
                key=project_widget_key(project, "delete", index),
                use_container_width=True,
            ):
                _delete_project(project)


def _open_project(project: dict) -> None:
    queue_project_open(project)
    st.session_state.projects_view = "workspace"
    st.rerun()


def _delete_project(project: dict) -> None:
    project_id = project.get("project_id", "")
    deleted = storage.delete_project_by_id(project_id) if project_id else storage.delete_project(project["name"])
    if not deleted:
        notify.error(f"Could not delete '{project['name']}'")
        return
    selected_id = st.session_state.get("selected_project_id")
    if selected_id == project_id or st.session_state.current_project_name == project["name"]:
        queue_project_clear(clear_result=True)
    notify.success(f"Deleted '{project['name']}'")
    st.rerun()
