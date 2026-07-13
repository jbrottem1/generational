"""Internal Critic engine — stage 6: adversarial review of every script.

Flags weak hooks, repetition, low retention risk, boring phrasing,
unsupported claims, and poor pacing. Deterministic, so critiques are
reproducible; the revision engine consumes these findings.
"""

from __future__ import annotations

from core.log import get_logger, log_event

# The critique implementation lives in the shared analysis library
# (`engines/analysis.py`) per Architecture Directive #1 — the Revision
# engine and the citation service consume it without importing this engine.
# Re-exported here because this module remains its public critic-facing home.
from engines.analysis import ISSUE_PENALTY, analyze_script, critic_score  # noqa: F401
from engines.base import Engine

logger = get_logger(__name__)


class CriticEngine(Engine):
    key = "critic"
    label = "Critic"
    icon = "🧐"
    description = "Adversarial review: hooks, repetition, retention, phrasing, claims, pacing."

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        selected = context.get("selected_ideas", [])
        flagged = 0
        for idea in selected:
            issues = analyze_script(idea.get("hook", ""), idea.get("script", ""))
            idea["critique"] = {"issues": issues, "score": critic_score(issues)}
            flagged += bool(issues)

        log_event(logger, "critic.reviewed", scripts=len(selected), flagged=flagged)
        return {"selected_ideas": selected}
