"""Studio project management — browse, create, duplicate, archive, search."""

from __future__ import annotations

import copy
from datetime import datetime, timezone

from core import storage
from core.models import project_from_result, result_from_project
from services.studio.models import STUDIO_PROJECT_METADATA_FIELDS, build_default_settings, platform_label


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_metadata(project: dict, platform: str = "youtube_shorts") -> dict:
    project.setdefault("folder", "General")
    project.setdefault("tags", [])
    project.setdefault("platform", platform)
    project.setdefault("archived", False)
    project.setdefault("studio_settings", build_default_settings(platform))
    project.setdefault("pipeline_state", {})
    project.setdefault("longform_job_id", "")
    return project


def list_studio_projects(
    *,
    search: str = "",
    folder: str = "",
    tags: "list[str] | None" = None,
    platform: str = "",
    include_archived: bool = False,
) -> list[dict]:
    """Filter and sort projects for the Studio workspace."""
    projects = storage.list_projects()
    results = []
    search_lower = search.strip().lower()
    tag_set = {t.lower() for t in (tags or [])}

    for project in projects:
        if not include_archived and project.get("archived"):
            continue
        if folder and project.get("folder", "General") != folder:
            continue
        if platform and project.get("platform", "") != platform:
            continue
        if tag_set:
            project_tags = {t.lower() for t in project.get("tags", [])}
            if not tag_set.intersection(project_tags):
                continue
        if search_lower:
            haystack = " ".join(
                str(part).lower()
                for part in (
                    project.get("name", ""),
                    project.get("command", ""),
                    project.get("niche", ""),
                    project.get("folder", ""),
                    " ".join(project.get("tags", [])),
                    platform_label(project.get("platform", "")),
                )
            )
            if search_lower not in haystack:
                continue
        results.append(project)
    return results


def list_folders() -> list[str]:
    folders = sorted({p.get("folder", "General") for p in storage.list_projects()})
    return folders or ["General"]


def list_tags() -> list[str]:
    tags: set[str] = set()
    for project in storage.list_projects():
        tags.update(project.get("tags", []))
    return sorted(tags)


def create_studio_project(
    name: str,
    *,
    command: str = "",
    platform: str = "youtube_shorts",
    folder: str = "General",
    tags: "list[str] | None" = None,
    settings: "dict | None" = None,
    result: "dict | None" = None,
) -> dict:
    """Create a new studio project with metadata."""
    name = name.strip()
    if not name:
        raise ValueError("Project name is required.")
    if storage.load_project(name):
        raise ValueError(f"Project '{name}' already exists.")

    if result:
        project = project_from_result(name, result)
    else:
        project = {
            "name": name,
            "command": command,
            "niche": "General Content",
            "video_count": 1,
            "goal": command or f"Create content for {platform_label(platform)}",
            "ideas": [],
            "demo_mode": True,
            "model": "gpt-4o-mini",
        }

    project["folder"] = folder
    project["tags"] = list(tags or [])
    project["platform"] = platform
    project["archived"] = False
    project["studio_settings"] = settings or build_default_settings(platform)
    project["pipeline_state"] = {}
    project["longform_job_id"] = ""
    storage.save_project(project)
    return project


def duplicate_project(source_name: str, new_name: str) -> dict:
    """Clone an existing project under a new name."""
    source = storage.load_project(source_name)
    if not source:
        raise ValueError(f"Project '{source_name}' not found.")
    new_name = new_name.strip()
    if not new_name:
        raise ValueError("New project name is required.")
    if storage.load_project(new_name):
        raise ValueError(f"Project '{new_name}' already exists.")

    clone = copy.deepcopy(source)
    clone["name"] = new_name
    clone["created_at"] = _now()
    clone["updated_at"] = _now()
    storage.save_project(clone)
    return clone


def archive_project(name: str) -> dict:
    project = storage.load_project(name)
    if not project:
        raise ValueError(f"Project '{name}' not found.")
    project["archived"] = True
    storage.save_project(project)
    return project


def unarchive_project(name: str) -> dict:
    project = storage.load_project(name)
    if not project:
        raise ValueError(f"Project '{name}' not found.")
    project["archived"] = False
    storage.save_project(project)
    return project


def update_project_metadata(name: str, **fields) -> dict:
    """Update studio metadata fields on a project."""
    project = storage.load_project(name)
    if not project:
        raise ValueError(f"Project '{name}' not found.")

    allowed = set(STUDIO_PROJECT_METADATA_FIELDS)
    for key, value in fields.items():
        if key in allowed:
            project[key] = value
    storage.save_project(project)
    return project


def open_project_result(name: str) -> "dict | None":
    """Rehydrate a session result from a stored project."""
    project = storage.load_project(name)
    if not project:
        return None
    return result_from_project(project)
