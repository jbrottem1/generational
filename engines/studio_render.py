"""Studio Render & Motion Graphics Engine (V3.0).

Consumes cinematography + viewer retention packages and becomes the final
visual authority before Production QA / export.
"""

from __future__ import annotations

from core.log import get_logger, log_event
from engines.base import Engine
from services.studio_render.director import build_studio_render_package
from services.studio_render.models import RENDER_QUALITY_THRESHOLD

logger = get_logger(__name__)


class StudioRenderEngine(Engine):
    key = "studio_render"
    label = "Studio Render & Motion Graphics"
    icon = "🎞️"
    description = (
        "Transform storyboards into documentary-grade motion graphics: "
        "master timeline, cinematic transitions, color LUTs, kinetic type, "
        "diagrams, B-roll direction, export presets — revise until render quality ≥ 98."
    )
    version = "3.0.0"

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        candidates = list(context.get("candidates") or [])
        if not candidates:
            subject = str(context.get("subject") or context.get("topic") or "").strip()
            if not subject:
                return {}
            candidates = [{"title": subject, "topic": subject}]

        write_library = bool(context.get("studio_render_write_library") or context.get("write_media_library"))
        packages: list[dict] = []
        for idx, candidate in enumerate(candidates):
            if isinstance(candidate, str):
                candidate = {"title": candidate, "topic": candidate, "hook": candidate}
                candidates[idx] = candidate
            if not isinstance(candidate, dict):
                continue
            report = build_studio_render_package(candidate, write_library=write_library)
            data = report.to_dict()
            candidate["studio_render_package"] = data
            candidate["studio_render_score"] = report.overall_score
            candidate["render_quality_score"] = report.overall_score
            candidate["studio_render_passed"] = report.passed
            candidate["master_timeline_v3"] = report.master_timeline
            candidate["export_plan_v3"] = report.export_plan
            if report.project_folder:
                candidate["studio_project_folder"] = report.project_folder
            # Merge timeline into render_package additively when present
            rp_raw = candidate.get("render_package")
            rp = dict(rp_raw) if isinstance(rp_raw, dict) else {}
            rp["studio_render_v3"] = {
                "overall_score": report.overall_score,
                "passed": report.passed,
                "export_plan": report.export_plan,
                "color_grade": report.color_grade,
                "transitions": report.transitions,
            }
            candidate["render_package"] = rp
            packages.append(data)

        avg = int(sum(p.get("overall_score") or 0 for p in packages) / max(1, len(packages)))
        summary = {
            "candidates": len(candidates),
            "average_score": avg,
            "passed": avg >= RENDER_QUALITY_THRESHOLD,
            "threshold": RENDER_QUALITY_THRESHOLD,
            "revision_rounds": sum(p.get("revision_rounds") or 0 for p in packages),
            "version": "3.0.0",
        }
        log_event(
            logger,
            "studio_render.completed",
            candidates=len(candidates),
            average_score=avg,
            passed=summary["passed"],
        )
        return {
            "candidates": candidates,
            "studio_render_summary": summary,
            "studio_render_packages": packages,
            "render_quality_score": avg,
        }
