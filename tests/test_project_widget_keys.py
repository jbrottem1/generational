"""Regression tests for unique Streamlit project widget keys."""

from __future__ import annotations

import json

from core.models import ensure_project_id, project_widget_key


def _write_project(directory, stem: str, name: str, **extra) -> None:
    project = {"name": name, "niche": "Test", "ideas": [], **extra}
    path = directory / f"{stem}.json"
    with open(path, "w", encoding="utf-8") as file:
        json.dump(project, file)


def test_project_widget_keys_unique_for_duplicate_names(project_store, tmp_path):
    """Two projects with the same display name must not share widget keys."""
    store_dir = tmp_path / "projects"
    store_dir.mkdir()
    _write_project(store_dir, "rc1-e2e-validation", "RC1 E2E Validation")
    _write_project(store_dir, "rc1-e2e-validation-copy", "RC1 E2E Validation")

    projects = project_store.list_projects()
    assert len(projects) == 2
    assert projects[0]["name"] == projects[1]["name"]

    keys = {project_widget_key(project, "open", index) for index, project in enumerate(projects)}
    assert len(keys) == 2


def test_ensure_project_id_assigns_stable_ids(project_store):
    project = {"name": "RC1 E2E Validation", "niche": "Test", "ideas": []}
    pid = ensure_project_id(project, file_stem="rc1-e2e-validation")
    assert pid == "legacy_rc1-e2e-validation"
    assert project["project_id"] == pid

    project_store.save_project(project)
    loaded = project_store.load_project_by_id(pid)
    assert loaded is not None
    assert loaded["name"] == "RC1 E2E Validation"


def test_delete_project_by_id_with_duplicate_names(project_store, tmp_path):
    store_dir = tmp_path / "projects"
    store_dir.mkdir()
    _write_project(store_dir, "alpha", "RC1 E2E Validation", project_id="proj_alpha")
    _write_project(store_dir, "beta", "RC1 E2E Validation", project_id="proj_beta")

    assert project_store.delete_project_by_id("proj_beta") is True
    remaining = project_store.list_projects()
    assert len(remaining) == 1
    assert remaining[0]["project_id"] == "proj_alpha"


def test_save_project_assigns_project_id(project_store):
    project_store.save_project({"name": "New Project", "niche": "Tech", "ideas": []})
    loaded = project_store.load_project("New Project")
    assert loaded["project_id"]


def test_project_from_result_includes_project_id():
    from core.models import project_from_result

    project = project_from_result(
        "Demo",
        {
            "command": "test",
            "niche": "Tech",
            "video_count": 1,
            "goal": "goal",
            "ideas": [],
            "demo_mode": True,
            "model": "gpt-4o-mini",
        },
    )
    assert project["project_id"]
