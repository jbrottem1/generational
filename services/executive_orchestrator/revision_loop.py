"""PQA-driven auto-revision loop for the Executive Orchestrator."""

from __future__ import annotations

from typing import Any, Callable

from core.log import get_logger, log_event
from core.workflows import WorkflowEngine

logger = get_logger(__name__)


def collect_revision_engines(context: dict) -> list[str]:
    by_engine = context.get("pqa_revision_by_engine") or {}
    if isinstance(by_engine, dict) and by_engine:
        return sorted(by_engine.keys())
    engines: set[str] = set()
    for item in (
        context.get("selected_ideas")
        or context.get("ideas")
        or context.get("candidates")
        or []
    ):
        if not isinstance(item, dict):
            continue
        for req in item.get("pqa_revision_requests") or []:
            if isinstance(req, dict):
                for eng in req.get("target_engines") or []:
                    engines.add(str(eng))
    return sorted(engines)


def any_needs_revision(context: dict) -> bool:
    for item in (
        context.get("selected_ideas")
        or context.get("ideas")
        or context.get("candidates")
        or []
    ):
        if isinstance(item, dict) and item.get("pqa_decision") == "REQUEST_REVISION":
            return True
    if context.get("pqa_summary", {}).get("request_revision", 0) > 0:
        return True
    return False


def any_blocked(context: dict) -> bool:
    for item in (
        context.get("selected_ideas")
        or context.get("ideas")
        or context.get("candidates")
        or []
    ):
        if isinstance(item, dict) and item.get("pqa_decision") == "BLOCK_EXPORT":
            return True
    return bool(context.get("pqa_summary", {}).get("blocked", 0))


def pqa_approved(context: dict) -> bool:
    items = (
        context.get("selected_ideas")
        or context.get("ideas")
        or context.get("candidates")
        or []
    )
    if not items:
        return bool(context.get("pqa_passed"))
    return all(
        isinstance(i, dict) and i.get("pqa_decision") == "APPROVE" for i in items
    )


def run_revision_loop(
    context: dict,
    *,
    workflows: WorkflowEngine | None = None,
    max_rounds: int = 2,
    on_round: Callable[[int, list[str]], None] | None = None,
) -> dict[str, Any]:
    """Re-run owning engines then Production QA until APPROVE or max rounds.

    Returns summary: rounds, engines_touched, final_decision, approved.
    """
    workflows = workflows or WorkflowEngine()
    engines_touched: list[str] = []
    rounds = 0

    for round_i in range(1, max(1, max_rounds) + 1):
        if pqa_approved(context) or not any_needs_revision(context):
            break
        if any_blocked(context):
            break

        targets = [e for e in collect_revision_engines(context) if e != "production_qa"]
        if not targets:
            break

        rounds = round_i
        if on_round:
            on_round(round_i, targets)

        log_event(logger, "executive.revision_round", round=round_i, engines=targets)
        run = workflows.execute(targets, context)
        for step in run.summary().get("steps") or []:
            eng = step.get("engine")
            if eng and eng not in engines_touched:
                engines_touched.append(eng)

        # Always re-QA after revisions
        workflows.execute(["production_qa"], context)
        if "production_qa" not in engines_touched:
            engines_touched.append("production_qa")

    decision = "UNKNOWN"
    score = None
    items = (
        context.get("selected_ideas")
        or context.get("ideas")
        or context.get("candidates")
        or []
    )
    if items and isinstance(items[0], dict):
        decision = str(items[0].get("pqa_decision") or "UNKNOWN")
        score = items[0].get("pqa_score")
    elif context.get("pqa_reports"):
        decision = str((context["pqa_reports"][0] or {}).get("decision") or "UNKNOWN")
        score = (context["pqa_reports"][0] or {}).get("overall_score")

    return {
        "rounds": rounds,
        "engines_touched": engines_touched,
        "final_decision": decision,
        "qa_score": score,
        "approved": pqa_approved(context),
        "blocked": any_blocked(context),
    }
