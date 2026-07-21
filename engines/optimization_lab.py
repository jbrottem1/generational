"""Autonomous Optimization & Experimentation Engine (V4.0).

Graduates the Agent 13 `optimization_lab` stub into a live self-improving
studio: multi-variant generation → comparison → self-critic → revision loop
→ performance prediction → knowledge + experiment history.
"""

from __future__ import annotations

from core.log import get_logger, log_event
from engines.base import Engine
from services.optimization_lab.models import DEFAULT_VARIANT_COUNT, OPTIMIZATION_PASS_THRESHOLD

logger = get_logger(__name__)


class OptimizationLabEngine(Engine):
    key = "optimization_lab"
    label = "Optimization Lab"
    icon = "🧪"
    description = (
        "Generate competing production variants, score and rank them, self-critique, "
        "auto-revise until excellence, predict performance, and learn for the next run."
    )
    version = "4.0.0"

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        from services.optimization_lab.dashboard import build_optimization_dashboard
        from services.optimization_lab.director import build_optimization_package

        candidates = list(
            context.get("candidates")
            or context.get("selected_ideas")
            or context.get("ideas")
            or []
        )
        if not candidates:
            subject = str(context.get("subject") or context.get("topic") or "").strip()
            if not subject:
                return {}
            candidates = [{"title": subject, "topic": subject}]

        variant_count = int(context.get("optimization_variant_count") or DEFAULT_VARIANT_COUNT)
        max_rounds = int(context.get("optimization_max_revisions") or 4)
        require_review = bool(context.get("require_human_review") or False)
        record_history = context.get("optimization_record_history", True)

        packages: list[dict] = []
        reports: list[dict] = []
        recommendations: list[str] = []
        updated: list[dict] = []

        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            package, new_cand = build_optimization_package(
                candidate,
                variant_count=variant_count,
                max_revision_rounds=max_rounds,
                record_history=bool(record_history),
                require_human_review=require_review,
            )
            data = package.to_dict()
            packages.append(data)
            updated.append(new_cand)
            reports.append(
                {
                    "topic": new_cand.get("title") or new_cand.get("topic"),
                    "winner": data.get("winner", {}).get("label"),
                    "score": data.get("overall_score"),
                    "passed": data.get("passed"),
                    "experiment_id": data.get("experiment_id"),
                }
            )
            for lesson in data.get("lessons_learned") or []:
                recommendations.append(str(lesson))
            for issue in (data.get("critique") or {}).get("issues") or []:
                if issue.get("suggestion"):
                    recommendations.append(str(issue["suggestion"]))

        avg = int(
            sum(p.get("overall_score") or 0 for p in packages) / max(1, len(packages))
        )
        summary = {
            "candidates": len(packages),
            "average_score": avg,
            "passed": avg >= OPTIMIZATION_PASS_THRESHOLD,
            "threshold": OPTIMIZATION_PASS_THRESHOLD,
            "variant_count": variant_count,
            "version": "4.0.0",
        }
        log_event(
            logger,
            "optimization_lab.completed",
            candidates=len(packages),
            average_score=avg,
            passed=summary["passed"],
        )

        # Keep selected_ideas / ideas in sync when those keys were the source
        result = {
            "candidates": updated,
            "optimization_package": packages[0] if packages else {},
            "optimization_packages": packages,
            "optimization_summary": summary,
            "optimization_report": {
                "runs": reports,
                "average_score": avg,
                "passed": summary["passed"],
            },
            "optimization_recommendations": list(dict.fromkeys(recommendations))[:20],
            "optimization_dashboard": build_optimization_dashboard(),
        }
        if context.get("selected_ideas") is not None:
            result["selected_ideas"] = updated
        if context.get("ideas") is not None and not context.get("candidates"):
            result["ideas"] = updated
        return result
