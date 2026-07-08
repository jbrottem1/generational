"""Engine plugin interface.

An Engine is one capability in the content pipeline (research, SEO, script,
voice, ...). Engines register themselves in `engines.registry`; the workflow
engine, job queue, and UI discover them from there — nothing outside the
engine's own module needs to change when one is added or replaced.

Contract:
- `run(context)` receives the shared workflow context dict and returns a
  dict of updates to merge back into it.
- Engines that are not yet implemented report `is_ready() == False` and are
  skipped by the workflow engine.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class Engine(ABC):
    key: str = "base"
    label: str = "Base"
    icon: str = "⚙️"
    description: str = ""
    version: str = "0.1.0"

    def is_ready(self) -> bool:
        """Whether this engine is implemented and can do real work."""
        return False

    @abstractmethod
    def run(self, context: dict) -> dict:
        """Process the workflow context and return updates to merge into it."""


class PlannedEngine(Engine):
    """Base for engines that are registered but not yet implemented.

    Registering planned engines now means workflows, diagnostics, and the UI
    already know about every pipeline stage — implementing one later is just
    overriding `run` and `is_ready` without touching any orchestration code.
    """

    def run(self, context: dict) -> dict:
        return {f"{self.key}_status": "not_implemented"}
