"""Script engine (planned) — long-form script refinement beyond ideation drafts."""

from __future__ import annotations

from engines.base import PlannedEngine


class ScriptEngine(PlannedEngine):
    key = "script"
    label = "Script"
    icon = "📝"
    description = "Refine and expand voiceover scripts."
