"""Safe Streamlit session-state transitions for project open/select.

Widget-bound keys (e.g. project_name_input) must not be mutated after their
widgets are instantiated in the same script run. Queue pending values and apply
them at the start of the next run before any widget renders.
"""

from __future__ import annotations

from core.models import result_from_project


def apply_pending_project_state(state: dict, *, storage=None) -> dict:
    """Apply queued project-open/clear transitions to a state dict.

    Returns keys that were applied (for tests). Mutates ``state`` in place.
    """
    applied: dict = {}
    if not (
        state.get("pending_project_id")
        or state.get("pending_project_name") is not None
        or state.get("pending_project_data")
    ):
        return applied

    project = state.pop("pending_project_data", None)
    project_id = state.pop("pending_project_id", "") or ""
    pending_name = state.pop("pending_project_name", None)

    if project is None and storage is not None:
        if project_id:
            project = storage.load_project_by_id(project_id)
        if project is None and pending_name:
            project = storage.load_project(pending_name)

    if project is not None:
        state["current_result"] = result_from_project(project)
        state["current_project_name"] = project["name"]
        state["project_name_input"] = project["name"]
        state["selected_project_id"] = project.get("project_id", project_id)
        if project.get("studio_settings"):
            state["studio_settings"] = project["studio_settings"]
        applied["opened"] = project["name"]
        applied["project_id"] = state["selected_project_id"]
    elif pending_name is not None:
        state["project_name_input"] = pending_name
        applied["project_name_input"] = pending_name

    notice = state.pop("pending_open_notification", None)
    if notice:
        applied["notification"] = notice

    return applied


def queue_project_open(project: dict) -> None:
    """Queue opening a project for the next Streamlit rerun."""
    import streamlit as st

    st.session_state.pending_project_id = project.get("project_id", "")
    st.session_state.pending_project_name = project["name"]
    st.session_state.pending_project_data = project
    st.session_state.pending_open_notification = project["name"]


def queue_project_name_update(name: str) -> None:
    """Queue updating the project name input without touching the widget key."""
    import streamlit as st

    st.session_state.pending_project_name = name


def queue_project_clear(*, clear_result: bool = True) -> None:
    """Queue clearing the active project selection on the next rerun."""
    import streamlit as st

    st.session_state.pending_project_id = ""
    st.session_state.pending_project_name = ""
    st.session_state.pending_project_data = None
    if clear_result:
        st.session_state.pending_clear_result = True


def apply_pending_streamlit_state(storage=None) -> dict:
    """Apply pending project transitions using Streamlit session state."""
    import streamlit as st

    if st.session_state.get("pending_clear_result"):
        st.session_state.pop("pending_clear_result")
        st.session_state.current_result = None
        st.session_state.current_project_name = None
        st.session_state.selected_project_id = None

    applied = apply_pending_project_state(st.session_state, storage=storage)
    if applied.get("opened"):
        st.session_state._projects_open_notice = applied["opened"]
    return applied
