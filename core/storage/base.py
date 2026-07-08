"""Project store interface.

The rest of the app depends only on this interface, so the JSON file store
can be swapped for SQLite/Postgres/cloud storage later without touching UI
or service code.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class ProjectStore(ABC):
    @abstractmethod
    def list_projects(self) -> list:
        """All projects, newest-updated first."""

    @abstractmethod
    def load_project(self, name: str) -> "dict | None":
        """A single project by name, or None if it doesn't exist."""

    @abstractmethod
    def save_project(self, project: dict) -> str:
        """Create or update a project. Returns a storage locator (e.g. file path)."""

    @abstractmethod
    def delete_project(self, name: str) -> bool:
        """Delete by name. Returns True if something was deleted."""

    @abstractmethod
    def project_count(self) -> int:
        """Number of stored projects."""
