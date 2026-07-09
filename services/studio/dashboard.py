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
