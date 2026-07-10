"""JSON-file-backed project store (one file per project under data/projects/)."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone

from core.log import get_logger
from core.models import ensure_project_id
from core.storage.base import ProjectStore

logger = get_logger(__name__)

_DEFAULT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "projects"
)


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "project"


class JsonProjectStore(ProjectStore):
    def __init__(self, directory: str = _DEFAULT_DIR) -> None:
        self.directory = directory

    def _ensure_dir(self) -> None:
        os.makedirs(self.directory, exist_ok=True)

    def _path_for(self, name: str) -> str:
        return os.path.join(self.directory, f"{_slugify(name)}.json")

    def list_projects(self) -> list:
        self._ensure_dir()
        projects = []
        for filename in sorted(os.listdir(self.directory)):
            if not filename.endswith(".json"):
                continue
            path = os.path.join(self.directory, filename)
            try:
                with open(path, "r", encoding="utf-8") as file:
                    project = json.load(file)
                stem = filename[:-5]
                ensure_project_id(project, file_stem=stem)
                project["_storage_stem"] = stem
                projects.append(project)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Skipping unreadable project file %s: %s", filename, exc)
                continue
        projects.sort(key=lambda project: project.get("updated_at", ""), reverse=True)
        return projects

    def load_project(self, name: str) -> "dict | None":
        path = self._path_for(name)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as file:
                project = json.load(file)
            ensure_project_id(project, file_stem=_slugify(name))
            return project
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Failed to load project '%s': %s", name, exc)
            return None

    def save_project(self, project: dict) -> str:
        self._ensure_dir()
        now = datetime.now(timezone.utc).isoformat()
        project["updated_at"] = now
        project.setdefault("created_at", now)
        ensure_project_id(project, file_stem=_slugify(project["name"]))
        path = self._path_for(project["name"])
        with open(path, "w", encoding="utf-8") as file:
            json.dump(project, file, indent=2)
        logger.info("Saved project '%s' to %s", project["name"], path)
        return path

    def delete_project(self, name: str) -> bool:
        path = self._path_for(name)
        if os.path.exists(path):
            os.remove(path)
            logger.info("Deleted project '%s'", name)
            return True
        return False

    def load_project_by_id(self, project_id: str) -> "dict | None":
        for project in self.list_projects():
            if project.get("project_id") == project_id:
                return project
        return None

    def delete_project_by_id(self, project_id: str) -> bool:
        self._ensure_dir()
        for filename in sorted(os.listdir(self.directory)):
            if not filename.endswith(".json"):
                continue
            path = os.path.join(self.directory, filename)
            try:
                with open(path, "r", encoding="utf-8") as file:
                    project = json.load(file)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Skipping unreadable project file %s: %s", filename, exc)
                continue
            stem = filename[:-5]
            ensure_project_id(project, file_stem=stem)
            if project.get("project_id") == project_id:
                os.remove(path)
                logger.info("Deleted project '%s' (id=%s)", project.get("name", ""), project_id)
                return True
        return False

    def project_count(self) -> int:
        self._ensure_dir()
        return len([f for f in os.listdir(self.directory) if f.endswith(".json")])
