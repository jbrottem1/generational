"""Projects tab — Create, Save, Open, and Delete projects (stored as local JSON)."""

import streamlit as st

from core import storage
from ui import notify


def render() -> None:
    st.subheader("📁 Projects")

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


def _project_payload(name: str, result: dict) -> dict:
    return {
        "name": name.strip(),
        "command": result["command"],
        "niche": result["niche"],
        "video_count": result["video_count"],
        "goal": result["goal"],
        "ideas": result["ideas"],
        "demo_mode": result["demo_mode"],
        "model": result["model"],
    }


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

    storage.save_project(_project_payload(name, result))
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
        project.update(_project_payload(name, result))
    project["name"] = name.strip()

    storage.save_project(project)
    st.session_state.current_project_name = name.strip()
    notify.success(f"Project '{name}' saved!")
    st.rerun()


def _render_project_list() -> None:
    projects = storage.list_projects()
    if not projects:
        st.caption("No saved projects yet. Generate ideas, then create a project above.")
        return

    st.markdown("### 🗂️ Saved Projects")
    for project in projects:
        with st.container(border=True):
            cols = st.columns([3, 1, 1])
            updated = (project.get("updated_at") or "")[:19].replace("T", " ")
            cols[0].markdown(
                f"**{project['name']}**  \n"
                f"{project.get('niche', '—')} · {len(project.get('ideas', []))} ideas · updated {updated or '—'}"
            )
            if cols[1].button("📂 Open", key=f"open_{project['name']}", use_container_width=True):
                _open_project(project)
            if cols[2].button("🗑️ Delete", key=f"delete_{project['name']}", use_container_width=True):
                _delete_project(project["name"])


def _open_project(project: dict) -> None:
    st.session_state.current_result = {
        "command": project.get("command", ""),
        "niche": project.get("niche", "General Content"),
        "video_count": project.get("video_count", len(project.get("ideas", []))),
        "goal": project.get("goal", ""),
        "ideas": project.get("ideas", []),
        "demo_mode": project.get("demo_mode", True),
        "model": project.get("model", "—"),
    }
    st.session_state.current_project_name = project["name"]
    st.session_state.project_name_input = project["name"]
    notify.success(f"Opened '{project['name']}'")
    st.rerun()


def _delete_project(name: str) -> None:
    storage.delete_project(name)
    if st.session_state.current_project_name == name:
        st.session_state.current_project_name = None
    notify.success(f"Deleted '{name}'")
    st.rerun()
