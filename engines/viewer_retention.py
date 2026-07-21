"""Viewer Retention & Cinematic Excellence Engine (V2.0).

Runs after cinematography / visual intelligence. Improves hook, pacing,
camera, narration, sound, captions, visuals, and retention — polishing
until overall production score exceeds 98 before export.
"""

from __future__ import annotations

from core.log import get_logger, log_event
from engines.base import Engine
from services.viewer_retention.excellence import build_excellence_package
from services.viewer_retention.models import EXCELLENCE_PASS_THRESHOLD

logger = get_logger(__name__)


class ViewerRetentionEngine(Engine):
    key = "viewer_retention"
    label = "Viewer Retention & Cinematic Excellence"
    icon = "🎯"
    description = (
        "Optimize every second for curiosity, pacing, cinematography, narration, "
        "sound, captions, and retention — auto-polish until production score ≥ 98."
    )
    version = "2.0.0"

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        candidates = list(context.get("candidates") or [])
        if not candidates:
            # Still allow subject-only contexts
            subject = str(context.get("subject") or context.get("topic") or "").strip()
            if not subject:
                return {}
            candidates = [{"title": subject, "topic": subject}]

        packages: list[dict] = []
        for candidate in candidates:
            report = build_excellence_package(
                candidate,
                topic=str(candidate.get("title") or context.get("subject") or ""),
            )
            data = report.to_dict()
            candidate["viewer_retention_package"] = data
            candidate["viewer_retention_score"] = report.overall_score
            candidate["cinematic_excellence_score"] = report.overall_score
            candidate["viewer_retention_passed"] = report.passed
            candidate["retention_predictions"] = report.predictions
            # Surface selected hook for downstream script/voice if stronger
            if report.selected_hook.get("text"):
                candidate["v2_selected_hook"] = report.selected_hook
                if int(report.selected_hook.get("score") or 0) >= int(
                    (candidate.get("hook_score") or 0)
                ):
                    candidate["hook"] = report.selected_hook["text"]
                    candidate["hook_style"] = report.selected_hook.get("style")
            packages.append(data)

        avg = int(
            sum(p.get("overall_score") or 0 for p in packages) / max(1, len(packages))
        )
        summary = {
            "candidates": len(candidates),
            "average_score": avg,
            "passed": avg >= EXCELLENCE_PASS_THRESHOLD,
            "threshold": EXCELLENCE_PASS_THRESHOLD,
            "polish_rounds": sum(p.get("polish_rounds") or 0 for p in packages),
            "version": "2.0.0",
        }
        log_event(
            logger,
            "viewer_retention.completed",
            candidates=len(candidates),
            average_score=avg,
            passed=summary["passed"],
        )
        return {
            "candidates": candidates,
            "viewer_retention_summary": summary,
            "viewer_retention_packages": packages,
            "cinematic_excellence_score": avg,
        }
