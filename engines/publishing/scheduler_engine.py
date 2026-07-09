"""SchedulerEngine — Agent 7's publish-time planner (key: scheduler).

Graduates the contract stub from engines/future_stubs.py (same key, same
input contract, additive output contract). Produces the `publish_schedule`
context key: one timezone-aware schedule entry per publish-eligible item ×
platform, driven by the Optimization Engine's ranked publish windows and
each country's audience timezone. The PublishingEngine consumes the same
scheduling service when it queues jobs, so the two never disagree.
"""

from __future__ import annotations

from core.log import get_logger, log_event
from engines.contracts import ContractEngine
from services.publishing.models import PUBLISHING_ENGINE_VERSION
from services.publishing.scheduler import PublishingScheduler

logger = get_logger(__name__)


def collect_publish_items(context: dict) -> "tuple[list, str]":
    """Publish-eligible items, preferring canonical ContentPackage dicts.

    Mirrors the Optimization Engine's collection order so the item list —
    and therefore the pairing with `publishing_packages` — stays aligned.
    """
    packages = context.get("unified_packages") or []
    eligible = [pkg for pkg in packages if pkg.get("publish_ready", True)]
    if eligible:
        return eligible, "unified_packages"
    for key, flag in (("ideas", "publishable"), ("selected_ideas", "publishable")):
        items = [item for item in context.get(key, []) if item.get(flag, True)]
        if items:
            return items, key
    production = context.get("production_packages") or []
    if production:
        return list(production), "production_packages"
    return [], ""


def pair_with_optimization(items: list, context: dict) -> "list[tuple[dict, dict]]":
    """(item, optimization PublishingPackage) pairs; {} when none exists.

    Agent 8 emits `publishing_packages` in the same collection order, so
    index pairing is the primary strategy, with project_id as an override
    where both sides carry one.
    """
    optimizations = context.get("publishing_packages") or []
    by_project = {
        opt.get("project_id"): opt
        for opt in optimizations
        if opt.get("project_id")
    }
    pairs = []
    for index, item in enumerate(items):
        opt = by_project.get(item.get("project_id") or "")
        if opt is None:
            opt = optimizations[index] if index < len(optimizations) else {}
        pairs.append((item, opt))
    return pairs


def _platforms_of(item: dict, optimization: dict) -> list:
    return list(
        optimization.get("platforms")
        or item.get("target_platforms")
        or item.get("platforms")
        or []
    )


class SchedulerEngine(ContractEngine):
    """Agent 7 — optimal-window publish scheduling for the publishing queue."""

    key = "scheduler"
    label = "Scheduler"
    icon = "🗓️"
    description = "Schedule queued content into optimal posting windows per platform."
    version = PUBLISHING_ENGINE_VERSION
    input_contract = ["production_packages"]
    output_contract = ["publish_schedule"]
    dependencies = ["publishing_queue"]
    capabilities = ["scheduling", "publishing", "timezone-aware", "multi-country"]

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        items, source_key = collect_publish_items(context)
        mode = context.get("publish_mode", "scheduled")
        scheduler = PublishingScheduler()

        schedule = []
        for item, optimization in pair_with_optimization(items, context):
            package = {
                "project_id": optimization.get("project_id") or item.get("project_id", ""),
                "country": optimization.get("country") or item.get("target_country", "US"),
                "language": optimization.get("language") or item.get("target_language", "en"),
                "publish_windows": optimization.get("publish_windows") or [],
            }
            for platform in _platforms_of(item, optimization):
                schedule.append(scheduler.schedule(package, platform, mode=mode))

        log_event(
            logger, "scheduler.completed",
            items=len(items), entries=len(schedule),
            source=source_key or "none", mode=mode,
        )
        return {"publish_schedule": schedule}
