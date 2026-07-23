"""Tests for Project Workspace open/navigation and schema normalization."""

from __future__ import annotations

from core.models import normalize_idea_asset, normalize_project_for_workspace, result_from_project
from ui.project_state import apply_pending_project_state, queue_project_open


def test_normalize_idea_recovers_nested_script_and_keywords():
    idea = {
        "title": "Nested",
        "structured_script": {"full_script": "Hello world script"},
        "suggested_seo_keywords": ["a", "b"],
        "thumbnail_concepts": [{"concept": "glowing ocean"}],
        "broll_suggestions": ["underwater light"],
    }
    asset = normalize_idea_asset(idea, index=0)
    assert asset["script"] == "Hello world script"
    assert asset["keywords"] == ["a", "b"]
    assert asset["thumbnail_concept"] == "glowing ocean"
    assert asset["visual_prompts"] == ["underwater light"]
    assert asset["workspace_status"] == "draft"


def test_normalize_project_for_workspace_counts_ideas():
    project = normalize_project_for_workspace(
        {
            "name": "Legacy",
            "generated_ideas": [{"title": "One"}, {"title": "Two"}],
            "demo_mode": False,
            "provider_usage": {"openai": {"calls": 5}},
        }
    )
    assert len(project["ideas"]) == 2
    assert project["video_count"] == 2
    assert project["provider"] == "openai"
    assert project["token_usage"] == 5


def test_open_sets_workspace_view_and_preserves_all_ideas():
    ideas = [{"title": f"Idea {i}", "script": f"Script {i}", "hook": f"Hook {i}"} for i in range(20)]
    project = {
        "name": "RC1 create one 20 second clip over biolumine (20260710-025738)",
        "project_id": "run_5ad55df3",
        "command": "create one 20 second clip over bioluminescence ",
        "ideas": ideas,
        "model": "gpt-4o-mini",
        "demo_mode": False,
        "created_at": "2026-07-10T02:57:38+00:00",
    }
    state = {
        "pending_project_id": project["project_id"],
        "pending_project_name": project["name"],
        "pending_project_data": project,
        "projects_view": "list",
        "project_asset_index": 99,
    }
    applied = apply_pending_project_state(state)
    assert applied["opened"] == project["name"]
    assert state["projects_view"] == "workspace"
    assert state["opened_project_data"] is not None
    assert len(state["current_result"]["ideas"]) == 20
    assert state["project_asset_index"] == 0
    assert state["current_result"]["ideas"][0]["title"] == "Idea 0"
    assert state["current_result"]["ideas"][19]["title"] == "Idea 19"


def test_back_to_list_does_not_require_pending_clear():
    state = {
        "projects_view": "workspace",
        "opened_project_data": {"name": "X", "ideas": []},
        "current_project_name": "X",
    }
    # Simulate Back to Projects
    state["projects_view"] = "list"
    state["project_asset_index"] = 0
    assert state["projects_view"] == "list"
    assert state["current_project_name"] == "X"


def test_result_from_project_includes_workspace_fields():
    project = {
        "name": "P",
        "command": "do thing",
        "ideas": [{"title": "T", "hook": "H", "script": "S", "thumbnail_concept": "Thumb"}],
        "model": "gpt-4o-mini",
        "demo_mode": False,
        "provider_usage": {"openai": {"calls": 3}},
        "created_at": "2026-01-01T00:00:00+00:00",
    }
    result = result_from_project(project)
    assert result["provider"] == "openai"
    assert result["token_usage"] == 3
    assert result["ideas"][0]["thumbnail_concept"] == "Thumb"
    assert len(result["ideas"]) == 1


def test_queue_project_open_sets_workspace_immediately(monkeypatch):
    import streamlit

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
    queue_project_open({"name": "N", "project_id": "pid", "ideas": []}, asset_index=2)
    assert fake["projects_view"] == "workspace"
    assert fake["pending_project_asset_index"] == 2


def test_open_asset_updates_session_state_for_all_indices(monkeypatch):
    import streamlit
    from ui.project_workspace import _open_asset

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

    ideas = [
        {"title": f"Idea {i}", "script": f"Script body {i}", "hook": f"Hook {i}", "thumbnail_concept": f"Thumb {i}"}
        for i in range(20)
    ]
    for i in range(20):
        _open_asset(i, ideas, source="test")
        assert fake["project_asset_index"] == i
        assert fake["asset_detail_visible"] is True
        assert fake["active_asset_id"]
        assert fake["selected_asset"]["title"] == f"Idea {i}"
        assert fake["selected_asset"]["script"] == f"Script body {i}"
        assert fake["_asset_open_notice"]["index"] == i


def test_open_sets_detail_visible_and_selected_asset():
    ideas = [{"title": f"Idea {i}", "script": f"S{i}"} for i in range(20)]
    project = {
        "name": "RC1",
        "project_id": "run_test",
        "ideas": ideas,
        "model": "gpt-4o-mini",
        "demo_mode": False,
    }
    state = {
        "pending_project_data": project,
        "pending_project_id": "run_test",
        "pending_project_name": "RC1",
        "projects_view": "list",
    }
    apply_pending_project_state(state)
    assert state["asset_detail_visible"] is True
    assert state["asset_workspace_open"] is True
    assert state["_scroll_asset_workspace"] is True
    assert state["selected_asset"]["title"] == "Idea 0"
    assert state["active_asset_id"]


def test_scene_plan_and_no_fake_mp4():
    from ui.project_workspace import _has_rendered_video, _scene_plan

    asset = {
        "title": "Secrets of Bioluminescence Revealed",
        "script": "Full voiceover script here",
        "script_sections": [
            {
                "label": "Primary Hook",
                "narration": "Hook line",
                "visual_intent": "Hero shot",
                "estimated_duration_sec": 5,
            }
        ],
        "render_package": {"aspect_ratio": "9:16", "duration_sec": 20},
    }
    scenes = _scene_plan(asset)
    assert len(scenes) == 1
    assert scenes[0]["narration"] == "Hook line"
    assert _has_rendered_video(asset, {}) is False


def test_open_secrets_asset_sets_workspace_flags(monkeypatch):
    import streamlit
    from ui.project_workspace import _open_asset

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
    ideas = [
        {
            "title": "Secrets of Bioluminescence Revealed",
            "script": "What if everything you believe...",
            "hook": "Ever been curious...",
            "thumbnail_concept": "A glowing jellyfish...",
        }
    ]
    _open_asset(0, ideas, source="test")
    assert fake["asset_workspace_open"] is True
    assert fake["_scroll_asset_workspace"] is True
    assert fake["selected_asset"]["title"] == "Secrets of Bioluminescence Revealed"
    assert "What if everything" in fake["selected_asset"]["script"]
    assert fake["show_build_video_checklist"] is False
