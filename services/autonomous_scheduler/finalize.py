"""Post-production organization + publish-queue preparation (no new engines)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from core.log import get_logger, log_event

logger = get_logger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def organize_completed_project(job: dict[str, Any], ops_result: dict[str, Any]) -> dict[str, Any]:
    """Register into GenOS media library + optional Channel OS video folder."""
    out: dict[str, Any] = {"library": None, "channel_package": None}
    report = ops_result.get("report") if isinstance(ops_result.get("report"), dict) else {}
    pid = str(
        ops_result.get("production_id")
        or job.get("production_id")
        or report.get("production_id")
        or ""
    )
    topic = str(job.get("topic") or report.get("topic") or "Untitled")
    try:
        from services.generational_os.media_library import register_library_entry

        entry = {
            "project_id": pid or job.get("job_id"),
            "title": report.get("title") or topic,
            "topic": topic,
            "category": job.get("category") or "",
            "platform": job.get("platform") or "youtube_shorts",
            "created_at": _now(),
            "quality_score": job.get("quality_score") or report.get("overall_quality_score"),
            "production_id": pid,
            "job_id": job.get("job_id"),
            "target_channel": job.get("target_channel") or "",
            "keywords": list(report.get("keywords") or [])[:12],
        }
        register_library_entry(entry)
        out["library"] = entry
    except Exception as exc:  # noqa: BLE001
        out["library_error"] = str(exc)[:200]

    channel = str(job.get("target_channel") or "").strip()
    if channel:
        try:
            from services.channel_os.library import package_channel_production
            from services.channel_os.store import get_profile, list_profiles

            profile = get_profile(channel)
            if not profile:
                for p in list_profiles(status=None) or []:
                    if not isinstance(p, dict):
                        continue
                    if channel.lower() in (
                        str(p.get("channel_id") or "").lower(),
                        str(p.get("brand_name") or "").lower(),
                        str(p.get("name") or "").lower(),
                    ):
                        profile = p
                        break
            if profile:
                out["channel_package"] = package_channel_production(
                    ops_result,
                    profile=profile,
                    category=str(job.get("category") or ""),
                )
        except Exception as exc:  # noqa: BLE001
            out["channel_error"] = str(exc)[:200]

    log_event(
        logger,
        "autonomous_scheduler.organized",
        production_id=pid,
        topic=topic,
        library=bool(out.get("library")),
        channel=bool(out.get("channel_package")),
    )
    return out


def prepare_publishing_queue(
    job: dict[str, Any],
    ops_result: dict[str, Any],
    *,
    publishing_enabled: bool = False,
) -> dict[str, Any]:
    """Prepare (not execute) publishing jobs when enabled; otherwise dry metadata only."""
    if not publishing_enabled and not job.get("publishing_enabled"):
        return {
            "prepared": False,
            "publishing_enabled": False,
            "note": "Publishing queue preparation skipped — publishing disabled",
        }

    report = ops_result.get("report") if isinstance(ops_result.get("report"), dict) else {}
    context = ops_result.get("context") if isinstance(ops_result.get("context"), dict) else {}
    candidates = context.get("candidates") or ops_result.get("candidates") or []
    item = candidates[0] if candidates and isinstance(candidates[0], dict) else {
        "title": report.get("topic") or job.get("topic"),
        "topic": job.get("topic"),
        "platforms": [job.get("platform") or "youtube_shorts"],
        "project_id": ops_result.get("production_id") or job.get("production_id"),
        "render_package": (candidates[0].get("render_package") if candidates else {}) or {},
    }
    if candidates and isinstance(candidates[0], dict):
        item = dict(candidates[0])
        item.setdefault("platforms", [job.get("platform") or "youtube_shorts"])
        item.setdefault("project_id", ops_result.get("production_id") or job.get("production_id"))

    try:
        from services.publishing.manager import PublishingManager

        mgr = PublishingManager()
        jobs, warnings = mgr.prepare_jobs(
            item,
            optimization={
                "platforms": item.get("platforms") or [job.get("platform") or "youtube_shorts"],
                "project_id": item.get("project_id"),
                "title": item.get("title") or job.get("topic"),
            },
            mode="scheduled",
            brand_id=str(job.get("target_channel") or ""),
            channel_id=str(job.get("target_channel") or ""),
            visibility="public",
        )
        return {
            "prepared": True,
            "publishing_enabled": True,
            "jobs": len(jobs),
            "job_ids": [j.get("job_id") for j in jobs if isinstance(j, dict)][:10],
            "warnings": warnings[:8],
            "executed": False,
            "note": "Jobs prepared/scheduled only — Autonomous Scheduler does not auto-publish",
        }
    except Exception as exc:  # noqa: BLE001
        return {"prepared": False, "publishing_enabled": True, "error": str(exc)[:240]}
