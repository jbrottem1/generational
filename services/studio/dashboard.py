"""Executive dashboard — projects, providers, queues, costs, analytics."""

from __future__ import annotations

from core import storage
from core.jobs import JobStatus, get_queue
from services.studio.providers import get_provider_dashboard


def get_executive_dashboard() -> dict:
    """Aggregate metrics for the Studio executive dashboard."""
    projects = storage.list_projects()
    active = [p for p in projects if not p.get("archived")]
    archived = [p for p in projects if p.get("archived")]

    queue = get_queue()
    jobs = queue.jobs()
    running_jobs = [j for j in jobs if j.status == JobStatus.RUNNING]
    pending_jobs = [j for j in jobs if j.status == JobStatus.PENDING]

    provider_dashboard = get_provider_dashboard()
    publishing = _publishing_queue_summary()
    analytics = _analytics_summary()
    rendering = _rendering_queue_summary(projects)
    production = _production_dashboard(projects, provider_dashboard, publishing, rendering)
    executive = _executive_studio_dashboard()

    return {
        "projects_total": len(projects),
        "projects_active": len(active),
        "projects_archived": len(archived),
        "projects_running": len(running_jobs) + len(publishing.get("processing", [])),
        "provider_usage": provider_dashboard,
        "content_published": publishing.get("published_count", 0),
        "estimated_costs_usd": provider_dashboard.get("total_cost_usd", 0.0),
        "rendering_queue": rendering,
        "publishing_queue": publishing,
        "analytics_summary": analytics,
        "jobs_running": len(running_jobs),
        "jobs_pending": len(pending_jobs),
        "production_dashboard": production,
        "executive_orchestrator": executive,
        "continuous_learning": _continuous_learning_dashboard(),
        "optimization_lab": _optimization_lab_dashboard(),
        "production_operations": _production_operations_dashboard(),
        "production_acceptance": _production_acceptance_dashboard(),
        "publishing_intelligence": _publishing_intelligence_dashboard(),
        "creative_performance_lab": _creative_performance_lab_dashboard(),
    }


def _creative_performance_lab_dashboard() -> dict:
    try:
        from services.creative_performance_lab.dashboard import build_creative_performance_board

        return build_creative_performance_board()
    except Exception:  # noqa: BLE001
        return {"error": "unavailable", "experiment_count": 0}


def _publishing_intelligence_dashboard() -> dict:
    try:
        from services.publishing_intelligence.dashboard import build_studio_intelligence_dashboard

        return build_studio_intelligence_dashboard()
    except Exception:  # noqa: BLE001
        return {"error": "unavailable", "confidence_score": 0}


def _optimization_lab_dashboard() -> dict:
    try:
        from services.optimization_lab.dashboard import build_optimization_dashboard

        return build_optimization_dashboard()
    except Exception:  # noqa: BLE001
        return {"error": "unavailable", "videos_optimized": 0}


def _production_operations_dashboard() -> dict:
    """Live Production Operations command-center board."""
    try:
        import json

        from services.production_operations import build_live_dashboard, queue_summary
        from services.production_operations.status import dashboard_path

        path = dashboard_path()
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            data["queue"] = queue_summary()
            return data
        return build_live_dashboard(queue_summary=queue_summary())
    except Exception:  # noqa: BLE001
        return {"error": "unavailable", "pipeline_health": "unknown", "overall_progress_pct": 0}


def _production_acceptance_dashboard() -> dict:
    try:
        import json

        from services.production_acceptance.models import DASHBOARD_PATH
        from services.production_acceptance.dashboard import build_acceptance_dashboard

        if DASHBOARD_PATH.exists():
            return json.loads(DASHBOARD_PATH.read_text(encoding="utf-8"))
        return build_acceptance_dashboard()
    except Exception:  # noqa: BLE001
        return {"error": "unavailable", "pass_pct": 0}


def _executive_studio_dashboard() -> dict:
    """Live Executive Orchestrator stage board (Discovery → Publishing)."""
    try:
        from services.executive_orchestrator import get_executive_orchestrator, stage_plan

        dash = get_executive_orchestrator().dashboard()
        dash["stage_plan"] = stage_plan()
        return dash
    except Exception:  # noqa: BLE001
        return {"active_count": 0, "recent_runs": [], "stages": [], "error": "unavailable"}


def _continuous_learning_dashboard() -> dict:
    try:
        from services.learning.dashboard import build_learning_dashboard

        return build_learning_dashboard()
    except Exception:  # noqa: BLE001
        return {"error": "unavailable", "productions_recorded": 0}


def _production_dashboard(projects: list, provider_dashboard: dict, publishing: dict, rendering: dict) -> dict:
    """Studio Production Dashboard — progress, providers, costs, outputs."""
    try:
        from services.media_production import ffmpeg_available, media_production_readiness
        from services.media_production.voice import VoiceProviderStatus

        media = media_production_readiness()
        voice = VoiceProviderStatus.snapshot()
    except Exception:  # noqa: BLE001
        media = {}
        voice = []

    latest_outputs = []
    for project in projects[:20]:
        for idea in (project.get("ideas") or [])[:5]:
            render = (idea or {}).get("render_package") or {}
            path = render.get("mp4_path") or render.get("file_uri") or render.get("mock_output_path") or ""
            if path:
                latest_outputs.append(
                    {
                        "project": project.get("name") or project.get("title") or "",
                        "title": idea.get("title") or "",
                        "path": path,
                        "mock": bool(render.get("mock", True)),
                        "status": render.get("render_status") or "",
                    }
                )

    return {
        "pipeline_progress": {
            "jobs_running": rendering.get("count", 0),
            "publish_queued": publishing.get("queued_count", 0),
            "publish_failed": publishing.get("failed_count", 0),
        },
        "provider_status": {
            "voice": voice,
            "ffmpeg_available": bool(media.get("ffmpeg_available")),
            "readiness_score": media.get("score"),
            "band": media.get("band"),
        },
        "api_usage": {
            "total_cost_usd": provider_dashboard.get("total_cost_usd", 0.0),
            "providers": provider_dashboard.get("providers") or [],
        },
        "estimated_cost_usd": provider_dashboard.get("total_cost_usd", 0.0),
        "asset_counts": {
            "projects": len(projects),
            "outputs": len(latest_outputs),
        },
        "final_outputs": latest_outputs[:15],
        "publishing_status": {
            "published": publishing.get("published_count", 0),
            "queued": publishing.get("queued_count", 0),
            "failed": publishing.get("failed_count", 0),
        },
        "blockers": media.get("blockers") or [],
        "checklist": media.get("first_autonomous_checklist") or [],
    }


def _publishing_queue_summary() -> dict:
    try:
        from services.publishing.queue import PublishingQueue
        pq = PublishingQueue()
        jobs = pq.list_jobs()
    except (ImportError, OSError, AttributeError):
        jobs = []

    queued = [j for j in jobs if j.get("status") in ("queued", "scheduled", "pending")]
    processing = [j for j in jobs if j.get("status") in ("processing", "running", "publishing")]
    published = [j for j in jobs if j.get("status") in ("published", "succeeded", "completed")]
    failed = [j for j in jobs if j.get("status") in ("failed", "error")]

    return {
        "queued_count": len(queued),
        "processing_count": len(processing),
        "published_count": len(published),
        "failed_count": len(failed),
        "queued": queued[:10],
        "processing": processing[:10],
    }


def _rendering_queue_summary(projects: list) -> dict:
    queued = []
    for project in projects:
        for pkg in project.get("production_packages", []):
            render = pkg.get("render_package", {})
            if render and render.get("status") in ("queued", "rendering", "pending"):
                queued.append({
                    "project": project.get("name", ""),
                    "status": render.get("status", "queued"),
                    "duration_sec": render.get("duration_sec", 0),
                })
        dashboard = project.get("production_dashboard", [])
        for stage in dashboard:
            if stage.get("key") in ("render", "rendering") and stage.get("state") in ("waiting", "running"):
                queued.append({
                    "project": project.get("name", ""),
                    "status": stage.get("state", "waiting"),
                    "label": stage.get("label", "Rendering"),
                })
    return {"count": len(queued), "items": queued[:15]}


def _analytics_summary() -> dict:
    try:
        from services.analytics.store import AnalyticsStore
        store = AnalyticsStore()
        records = store._read()  # noqa: SLF001 — read-only introspection
    except (ImportError, OSError, AttributeError):
        records = []

    total_views = sum(r.get("views", 0) for r in records)
    total_engagement = sum(r.get("engagement_rate", 0) for r in records)
    return {
        "record_count": len(records),
        "total_views": total_views,
        "avg_engagement": round(total_engagement / len(records), 2) if records else 0.0,
    }
