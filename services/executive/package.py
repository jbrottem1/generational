"""ExecutivePackage assembly and stage entrypoint."""

from __future__ import annotations

from datetime import datetime, timezone

from core.log import get_logger, log_event
from services.executive.dashboard import ExecutiveDashboard
from services.executive.health import CompanyHealthMonitor
from services.executive.loop import ExecutiveLoop
from services.executive.models import (
    EXECUTIVE_ENGINE_VERSION,
    EXECUTIVE_PACKAGE_VERSION,
    EXECUTIVE_SUMMARY_FIELDS,
)
from services.executive.planner import ExecutivePlanner
from services.executive.reports import ExecutiveReporter
from services.executive.roadmap import ExecutiveRoadmap

logger = get_logger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def collect_executive_items(context: dict) -> "tuple[list, str]":
    """Items whose executive_package slot this run should fill."""
    packages = context.get("unified_packages") or []
    if packages:
        return list(packages), "unified_packages"
    for key in ("ideas", "selected_ideas", "candidates"):
        items = context.get(key) or []
        if items:
            return list(items), key
    return [], ""


def build_executive_package(item: dict, plan: dict, health: dict, resources: dict, roadmap: dict) -> dict:
    """One ExecutivePackage for a content item or portfolio unit."""
    decision_id = ""
    decisions = plan.get("decisions") or []
    if decisions:
        decision_id = decisions[0].get("decision_id", "")

    return {
        "executive_package_version": EXECUTIVE_PACKAGE_VERSION,
        "engine_version": EXECUTIVE_ENGINE_VERSION,
        "project_id": str(item.get("project_id", "")),
        "decisions": decisions[:5],
        "goals": plan.get("goals") or [],
        "strategy_snapshot": plan.get("strategy") or {},
        "risk_summary": plan.get("risk") or {},
        "resource_allocation": resources,
        "roadmap_slice": ExecutiveRoadmap().slice_for_item(roadmap, decision_id),
        "health_snapshot": health,
        "validation": {
            "status": "active" if decisions else "no_decisions",
            "confidence": _average_confidence(decisions),
        },
        "generated_at": _now_iso(),
    }


def _average_confidence(decisions: list) -> int:
    if not decisions:
        return 0
    return int(round(sum(int(d.get("confidence", 0)) for d in decisions) / len(decisions)))


def _build_summary(packages: list, plan: dict, health: dict, engines_discovered: int, items: int) -> dict:
    decisions = plan.get("decisions") or []
    priorities = [int(d.get("priority", 0)) for d in decisions]
    confidences = [int(d.get("confidence", 0)) for d in decisions]
    goals = plan.get("goals") or []

    status = "active"
    if not decisions and items == 0:
        status = "no_context"
    elif not decisions:
        status = "planned"

    return {
        "engine_version": EXECUTIVE_ENGINE_VERSION,
        "status": status,
        "items": items,
        "packages": len(packages),
        "decisions": len(decisions),
        "goals_active": len([g for g in goals if g.get("status") != "achieved"]),
        "health_level": health.get("level", "stable"),
        "average_priority": int(round(sum(priorities) / len(priorities))) if priorities else 0,
        "average_confidence": int(round(sum(confidences) / len(confidences))) if confidences else 0,
        "engines_discovered": engines_discovered,
        "generated_at": _now_iso(),
    }


def run_executive_engine(context: dict, orchestrator=None) -> dict:
    """Full executive intelligence run — never crashes the pipeline."""
    try:
        planner = ExecutivePlanner()
        plan = planner.plan(context)
        health_monitor = CompanyHealthMonitor()
        health = health_monitor.assess(context, plan.get("decisions") or [], plan.get("risk") or {})
        resources = plan.get("resource_plan") or {}
        roadmap = plan.get("roadmap") or {}

        dashboard = ExecutiveDashboard().build(plan, health, resources)
        reports = ExecutiveReporter().build_all(plan, health, context)
        loop = ExecutiveLoop().run(context, orchestrator=orchestrator)

        items, source_key = collect_executive_items(context)
        packages = []
        for item in items:
            package = build_executive_package(item, plan, health, resources, roadmap)
            item["executive_package"] = package
            packages.append(package)

        if not items and plan.get("decisions"):
            packages.append(build_executive_package({}, plan, health, resources, roadmap))

        summary = _build_summary(
            packages, plan, health,
            engines_discovered=resources.get("engines_discovered", 0),
            items=len(items),
        )

        log_event(
            logger, "executive.completed",
            items=len(items), decisions=len(plan.get("decisions") or []),
            health=health.get("level"),
        )

        updates = {
            "executive_summary": summary,
            "executive_plan": {
                "engine_version": EXECUTIVE_ENGINE_VERSION,
                "vision": plan.get("vision"),
                "priorities": plan.get("priorities"),
                "decisions": plan.get("decisions"),
                "roadmap": roadmap,
                "resource_plan": resources,
                "generated_at": _now_iso(),
            },
            "executive_dashboard": dashboard,
            "executive_reports": reports,
            "executive_loop": loop,
            "executive_packages": packages,
        }
        if source_key:
            updates[source_key] = context.get(source_key, [])
        return updates

    except Exception as exc:  # noqa: BLE001 - executive never crashes pipeline
        log_event(logger, "executive.failed", level=30, error=str(exc)[:200])
        summary = {field: "" for field in EXECUTIVE_SUMMARY_FIELDS}
        summary.update({
            "engine_version": EXECUTIVE_ENGINE_VERSION,
            "status": "degraded",
            "items": 0,
            "packages": 0,
            "decisions": 0,
            "goals_active": 0,
            "health_level": "warning",
            "average_priority": 0,
            "average_confidence": 0,
            "engines_discovered": 0,
            "generated_at": _now_iso(),
            "reason": str(exc)[:200],
        })
        return {
            "executive_summary": summary,
            "executive_plan": {},
            "executive_dashboard": {},
            "executive_reports": {},
            "executive_loop": {},
            "executive_packages": [],
        }
