"""Storage facade.

Callers use these module-level functions (or `get_store()` directly); the
active backend is chosen here. Currently a local JSON store — swap in a
database-backed `ProjectStore` implementation later by changing one line.
"""

from __future__ import annotations

from core.storage.base import ProjectStore
from core.storage.json_store import JsonProjectStore

__all__ = [
    "ProjectStore",
    "get_store",
    "list_projects",
    "load_project",
    "load_project_by_id",
    "save_project",
    "delete_project",
    "delete_project_by_id",
    "project_count",
]

_store: ProjectStore = JsonProjectStore()


def get_store() -> ProjectStore:
    return _store


def list_projects() -> list:
    return _store.list_projects()


def load_project(name: str) -> "dict | None":
    return _store.load_project(name)


def load_project_by_id(project_id: str) -> "dict | None":
    loader = getattr(_store, "load_project_by_id", None)
    if loader is None:
        return None
    return loader(project_id)


def save_project(project: dict) -> str:
    return _store.save_project(project)


def delete_project(name: str) -> bool:
    return _store.delete_project(name)


def delete_project_by_id(project_id: str) -> bool:
    deleter = getattr(_store, "delete_project_by_id", None)
    if deleter is None:
        return False
    return deleter(project_id)


def project_count() -> int:
    return _store.project_count()
