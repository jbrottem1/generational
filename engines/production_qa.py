"""Production Quality Assurance Engine — final authority before export/publish.

Inspects every completed production across research, evidence, visuals,
typography, annotations, cinematography, audio, narration, sync, education,
psychology, SEO, and platform compliance.

Decisions: APPROVE | REQUEST_REVISION | BLOCK_EXPORT
Nothing reaches Publishing without PQA APPROVE.
"""

from __future__ import annotations

from core.log import get_logger, log_event
from engines.base import Engine
from services.production_qa.inspector import inspect_production
from services.production_qa.publish_gate import ensure_pqa_gate_registered
from services.production_qa.revision import group_revisions_by_engine
from services.production_qa.store import store_report

logger = get_logger(__name__)


def _pick_items(context: dict) -> tuple[list, str]:
    for key in ("selected_ideas", "ideas", "candidates", "productions"):
        items = context.get(key)
        if isinstance(items, list) and items:
            return items, key
    return [], "selected_ideas"


def _is_finished_production(item: dict, context: dict) -> bool:
    """True when PQA should hard-block publishing (assembled production).

    Planning packages (evidence/visual/cinematography) still receive a PQA
    report for learning, but QualityEngine's publishable flag remains
    authoritative until a render/export package exists.
    """
    if context.get("enforce_pqa") or item.get("enforce_pqa"):
        return True
    return bool(
        item.get("render_package")
        or context.get("executive_export")
        or context.get("production_packages")
        or item.get("export_path")
        or (item.get("verification") or {}).get("ok")
    )


class ProductionQAEngine(Engine):
    key = "production_qa"
    label = "Production QA"
    icon = "🏛️"
    description = (
        "Documentary-level Production Quality Assurance — the final editor-in-chief. "
        "Approves, requests revision, or blocks export before Publishing."
    )
    version = "1.0.0"

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        ensure_pqa_gate_registered()

        items, source_key = _pick_items(context)
        if not items:
            return {}

        reports: list[dict] = []
        approved = 0
        revision = 0
        blocked = 0
        all_revision_by_engine: dict[str, list] = {}

        for item in items:
            report = inspect_production(item, context)
            data = report.to_dict()
            item["pqa_report"] = data
            item["pqa_passed"] = report.decision == "APPROVE"
            item["pqa_decision"] = report.decision
            item["pqa_score"] = report.overall_score
            item["pqa_revision_requests"] = [r.to_dict() for r in report.revision_requests]

            enforce = _is_finished_production(item, context)
            item["pqa_enforced"] = enforce
            if enforce and report.decision != "APPROVE":
                item["publishable"] = False
                failures = list(item.get("gate_failures") or [])
                if "production_qa" not in failures:
                    failures.append("production_qa")
                item["gate_failures"] = failures
            elif report.decision == "APPROVE" and item.get("publishable") is None:
                item["publishable"] = True

            if report.decision == "APPROVE":
                approved += 1
            elif report.decision == "REQUEST_REVISION":
                revision += 1
            else:
                blocked += 1

            by_engine = group_revisions_by_engine(report.revision_requests)
            for engine_key, payloads in by_engine.items():
                all_revision_by_engine.setdefault(engine_key, []).extend(payloads)

            try:
                store_report(data, idea_id=report.idea_id or str(item.get("title") or "item"))
            except Exception as exc:
                log_event(logger, "production_qa.store_failed", error=str(exc))

            reports.append(data)

        summary = {
            "items": len(items),
            "approved": approved,
            "request_revision": revision,
            "blocked": blocked,
            "average_score": int(
                sum(r.get("overall_score") or 0 for r in reports) / max(1, len(reports))
            ),
            "pass_rate": round(approved / max(1, len(items)), 3),
            "revision_targets": sorted(all_revision_by_engine.keys()),
            "source_key": source_key,
        }
        log_event(
            logger,
            "production_qa.completed",
            items=len(items),
            approved=approved,
            revision=revision,
            blocked=blocked,
            average=summary["average_score"],
        )
        return {
            source_key: items,
            "pqa_reports": reports,
            "pqa_summary": summary,
            "pqa_revision_by_engine": all_revision_by_engine,
            "pqa_passed": approved > 0 and blocked == 0 and revision == 0,
        }
