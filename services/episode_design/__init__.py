"""Retention & Episode Design — Director of educational episode rhythm (Agent 25).

NOTE: Mission brief named this Agent 24; registry assigns Agent 25 because
Agent 24 is already Executive Intelligence (key: autonomous_executive).

Reviews completed scripts before production. Improves hooks, curiosity,
information flow, emotional pacing, reveals, endings, and series continuity.
Never animates or renders — coordinates via Orchestrator contracts only.
"""

from __future__ import annotations

from services.episode_design.blueprint import build_lesson_blueprint
from services.episode_design.models import (
    BLUEPRINT_BEATS,
    EPISODE_DESIGN_ENGINE_VERSION,
    EPISODE_DESIGN_PACKAGE_FIELDS,
    EPISODE_DESIGN_PACKAGE_VERSION,
    EPISODE_DESIGN_SUMMARY_FIELDS,
    PLAYBOOK_FIELDS,
    RETENTION_SCORE_FIELDS,
    SERIES_DESIGN_FIELDS,
    STRATEGIC_DESIGN_QUESTIONS,
    EpisodeDesignStatus,
)
from services.episode_design.package import (
    build_episode_design_package,
    collect_episode_design_items,
    run_episode_design_engine,
)
from services.episode_design.playbook import EpisodePlaybook, get_playbook
from services.episode_design.retention import build_retention_review
from services.episode_design.series import build_series_design

__all__ = [
    "BLUEPRINT_BEATS",
    "EPISODE_DESIGN_ENGINE_VERSION",
    "EPISODE_DESIGN_PACKAGE_FIELDS",
    "EPISODE_DESIGN_PACKAGE_VERSION",
    "EPISODE_DESIGN_SUMMARY_FIELDS",
    "PLAYBOOK_FIELDS",
    "RETENTION_SCORE_FIELDS",
    "SERIES_DESIGN_FIELDS",
    "STRATEGIC_DESIGN_QUESTIONS",
    "EpisodeDesignStatus",
    "EpisodePlaybook",
    "build_episode_design_package",
    "build_lesson_blueprint",
    "build_retention_review",
    "build_series_design",
    "collect_episode_design_items",
    "get_playbook",
    "run_episode_design_engine",
]
