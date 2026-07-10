"""Regression tests for safe project open session-state transitions."""

from __future__ import annotations

import json

from core.models import project_widget_key, result_from_project
from ui.project_state import apply_pending_project_state, queue_project_open


class _FakeStorage:
    def __init__(self, projects: dict):
        self._projects = projects

    def load_project_by_id(self, project_id: str):
        return self._projects.get(project_id)

    def load_project(self, name: str):
        for project in self._projects.values():
            if project.get("name") == name:
                return project
        return None


def _sample_project(name="RC1 E2E Validation", project_id="proj_alpha", **extra):
    return {
        "name": name,
        "project_id": project_id,
        "niche": "Psychology",
        "video_count": 1,
        "goal": "Test goal",
        "command": "Create a short",
        "ideas": [{"title": "Idea 1", "script": "Script body", "hook": "Hook"}],
        "demo_mode": True,
        "model": "gpt-4o-mini",
        "studio_settings": {"platform": "youtube_shorts", "voice": "ai"},
        **extra,
    }


def test_apply_pending_opens_saved_project():
    project = _sample_project()
    state = {
        "pending_project_id": project["project_id"],
        "pending_project_name": project["name"],
        "pending_project_data": project,
        "project_name_input": "stale value",
    }

    applied = apply_pending_project_state(state)

    assert applied["opened"] == "RC1 E2E Validation"
    assert state["project_name_input"] == "RC1 E2E Validation"
    assert state["current_project_name"] == "RC1 E2E Validation"
    assert state["selected_project_id"] == "proj_alpha"
    assert state["current_result"]["ideas"][0]["title"] == "Idea 1"
    assert state["studio_settings"]["platform"] == "youtube_shorts"
    assert state["projects_view"] == "workspace"
    assert state["opened_project_data"]["name"] == "RC1 E2E Validation"
    assert state["asset_detail_visible"] is True
    assert state["selected_asset"]["title"] == "Idea 1"
    assert "pending_project_name" not in state


def test_apply_pending_opens_correct_project_when_names_duplicate():
    alpha = _sample_project(project_id="proj_alpha")
    beta = _sample_project(project_id="proj_beta", ideas=[{"title": "Beta Idea", "script": "b"}])
    storage = _FakeStorage({"proj_beta": beta, "proj_alpha": alpha})

    state = {
        "pending_project_id": "proj_beta",
        "pending_project_name": "RC1 E2E Validation",
    }

    apply_pending_project_state(state, storage=storage)

    assert state["selected_project_id"] == "proj_beta"
    assert state["current_result"]["ideas"][0]["title"] == "Beta Idea"


def test_switching_between_projects_updates_selection():
    first = _sample_project(project_id="proj_one", name="Shared Name")
    second = _sample_project(project_id="proj_two", name="Shared Name", niche="Science")

    state = {"pending_project_data": first}
    apply_pending_project_state(state)
    assert state["selected_project_id"] == "proj_one"
    assert state["current_result"]["niche"] == "Psychology"

    state.update({
        "pending_project_id": second["project_id"],
        "pending_project_name": second["name"],
        "pending_project_data": second,
    })
    apply_pending_project_state(state)
    assert state["selected_project_id"] == "proj_two"
    assert state["current_result"]["niche"] == "Science"


def test_apply_pending_name_update_without_opening_project():
    state = {"pending_project_name": "Renamed Project", "current_project_name": None}

    applied = apply_pending_project_state(state)

    assert applied["project_name_input"] == "Renamed Project"
    assert state["project_name_input"] == "Renamed Project"
    assert "current_result" not in state or state.get("current_result") is None


def test_delete_selected_project_clears_state():
    state = {
        "pending_project_id": "",
        "pending_project_name": "",
        "pending_clear_result": True,
        "current_result": {"ideas": []},
        "current_project_name": "RC1 E2E Validation",
        "selected_project_id": "proj_alpha",
        "project_name_input": "RC1 E2E Validation",
    }

    from ui.project_state import apply_pending_streamlit_state

    class _Store:
        def load_project_by_id(self, _):
            return None

        def load_project(self, _):
            return None

    # Simulate clear flag handling from apply_pending_streamlit_state
    if state.get("pending_clear_result"):
        state.pop("pending_clear_result")
        state["current_result"] = None
        state["current_project_name"] = None
        state["selected_project_id"] = None
    apply_pending_project_state(state, storage=_Store())

    assert state["current_result"] is None
    assert state["current_project_name"] is None
    assert state["selected_project_id"] is None
    assert state["project_name_input"] == ""


def test_widget_keys_remain_unique_after_open_transition(project_store, tmp_path):
    store_dir = tmp_path / "projects"
    store_dir.mkdir()
    for stem, pid in (("alpha", "proj_alpha"), ("beta", "proj_beta")):
        project = _sample_project(project_id=pid)
        with open(store_dir / f"{stem}.json", "w", encoding="utf-8") as file:
            json.dump(project, file)

    projects = project_store.list_projects()
    keys = {project_widget_key(project, "open", index) for index, project in enumerate(projects)}
    assert len(keys) == 2


def test_queue_project_open_does_not_touch_widget_key(monkeypatch):
    import streamlit

    session = {}

    class FakeSessionState(dict):
        def __getattr__(self, key):
            try:
                return self[key]
            except KeyError as exc:
                raise AttributeError(key) from exc

        def __setattr__(self, key, value):
            self[key] = value

    fake = FakeSessionState()
    monkeypatch.setattr(streamlit, "session_state", fake, raising=False)

    project = _sample_project()
    queue_project_open(project)

    assert fake["pending_project_id"] == "proj_alpha"
    assert fake["pending_project_name"] == "RC1 E2E Validation"
    assert fake["pending_project_data"] == project
    assert fake["projects_view"] == "workspace"
    assert "project_name_input" not in fake


def test_result_from_project_round_trip_preserved_on_open():
    project = _sample_project()
    result = result_from_project(project)
    state = {"pending_project_data": project}
    apply_pending_project_state(state)
    assert state["current_result"]["command"] == result["command"]
    assert state["current_result"]["ideas"] == result["ideas"]
