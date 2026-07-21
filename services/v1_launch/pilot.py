"""Phase 2 — Pilot productions via existing run_studio_ops (publishing off)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from core.log import get_logger, log_event
from services.v1_launch.library import ROOT, completed_launch_ids, ensure_library, store_pilot
from services.v1_launch.pilot_catalog import filter_pilot
from services.validation_program.scoring import score_validation_run

logger = get_logger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_pilot_batch(
    *,
    limit: int | None = None,
    offset: int = 0,
    categories: list[str] | None = None,
    skip_completed: bool = True,
) -> dict[str, Any]:
    """
    Produce pilot videos for the V1 Launch Program.

    Uses frozen pipeline only. Publishing disabled.
    Success / deliverable_ok follow ops truth (MP4 required unless soft export).
    """
    from services.production_operations import run_studio_ops

    ensure_library()
    catalog = filter_pilot(limit=limit, offset=offset, categories=categories)
    done = completed_launch_ids() if skip_completed else set()
    results: list[dict[str, Any]] = []
    log_event(logger, "v1_launch.pilot_started", planned=len(catalog), already_done=len(done))

    for brief in catalog:
        lid = brief["launch_id"]
        if lid in done:
            log_event(logger, "v1_launch.skip_completed", launch_id=lid)
            continue

        log_event(logger, "v1_launch.production_started", launch_id=lid, topic=brief["topic"])
        ops = run_studio_ops(
            topic=brief["topic"],
            platform=brief.get("platform") or "youtube_shorts",
            length_sec=int(brief.get("length_sec") or 45),
            style=brief.get("style") or "educational",
            narrator=brief.get("narrator") or "professor",
            voice=brief.get("voice") or "default",
            quality_target=98,
            constraints={
                "audience": brief.get("audience") or "",
                "publishing_enabled": False,
                "v1_launch_pilot": True,
                "category": brief["launch_category"],
            },
            context={
                "candidate_count": 1,
                "video_count": 1,
                "v1_launch_pilot": True,
                "domain": brief["launch_category"],
                "category": brief["launch_category"],
                "audience": brief.get("audience") or "",
                "publishing_enabled": False,
            },
        )
        if isinstance(ops.get("brief"), dict):
            ops["brief"]["domain"] = brief["launch_category"]

        card = score_validation_run(ops, category=brief["launch_category"])
        status = ops.get("status") or {}
        card["video_exists"] = bool(status.get("video_exists") or (ops.get("export_validation") or {}).get("video_exists"))
        card["deliverable_ok"] = bool(status.get("deliverable_ok") if status.get("deliverable_ok") is not None else card["video_exists"])
        # Prefer ops truth for success under launch program
        if status.get("success") is not None:
            card["success"] = bool(status.get("success"))
        if isinstance(status.get("stages"), list):
            card.setdefault("timing", {})["stage_ms"] = {
                str(s.get("key")): int(s.get("duration_ms") or 0)
                for s in status["stages"]
                if isinstance(s, dict) and s.get("key")
            }

        stored = store_pilot(
            card,
            launch_id=lid,
            creative_review=str(card.get("creative_recommendation") or ""),
            qa_notes=f"pipeline_health={card.get('pipeline_health')} validation_score={card.get('validation_score')}",
        )
        results.append(
            {
                "launch_id": lid,
                "topic": brief["topic"],
                "category": brief["launch_category"],
                "production_id": card.get("production_id"),
                "success": card.get("success"),
                "video_exists": card.get("video_exists"),
                "deliverable_ok": card.get("deliverable_ok"),
                "overall": card.get("overall_program_score"),
                "elapsed_ms": (card.get("timing") or {}).get("elapsed_ms"),
                "stored": stored,
            }
        )
        log_event(
            logger,
            "v1_launch.production_finished",
            launch_id=lid,
            success=card.get("success"),
            video_exists=card.get("video_exists"),
            overall=card.get("overall_program_score"),
        )

    summary = {
        "generated_at": _now(),
        "program": "V1 Launch Pilot — Phase 2",
        "planned_this_batch": len(catalog),
        "executed_this_batch": len(results),
        "library_total": len(completed_launch_ids()),
        "target": 25,
        "results": results,
        "library_root": str(ROOT),
        "publishing_enabled": False,
    }
    (ROOT / "PILOT_BATCH_SUMMARY.json").write_text(json.dumps(summary, indent=2, default=str) + "\n", encoding="utf-8")
    return summary
