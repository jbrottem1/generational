"""Local JSON-based project persistence.

Each project is stored as its own JSON file under data/projects/. This keeps
Phase 3 simple and dependency-free — swapping this out for a real database
later only requires changing this module.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone

PROJECTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "projects")


def _ensure_dir() -> None:
    os.makedirs(PROJECTS_DIR, exist_ok=True)


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "project"


def _path_for(name: str) -> str:
    return os.path.join(PROJECTS_DIR, f"{_slugify(name)}.json")


def list_projects() -> list[dict]:
    _ensure_dir()
    projects = []
    for filename in sorted(os.listdir(PROJECTS_DIR)):
        if not filename.endswith(".json"):
            continue
        path = os.path.join(PROJECTS_DIR, filename)
        try:
            with open(path, "r", encoding="utf-8") as file:
                projects.append(json.load(file))
        except (json.JSONDecodeError, OSError):
            continue
    projects.sort(key=lambda project: project.get("updated_at", ""), reverse=True)
    return projects


def load_project(name: str) -> dict | None:
    path = _path_for(name)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_project(project: dict) -> str:
    _ensure_dir()
    now = datetime.now(timezone.utc).isoformat()
    project["updated_at"] = now
    project.setdefault("created_at", now)
    path = _path_for(project["name"])
    with open(path, "w", encoding="utf-8") as file:
        json.dump(project, file, indent=2)
    return path


def delete_project(name: str) -> bool:
    path = _path_for(name)
    if os.path.exists(path):
        os.remove(path)
        return True
    return False


def project_count() -> int:
    _ensure_dir()
    return len([f for f in os.listdir(PROJECTS_DIR) if f.endswith(".json")])
