"""Phase 6 — Studio Intelligence Executive Dashboard."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.publishing_intelligence.business_intel import estimate_business_metrics
from services.publishing_intelligence.calibration import build_calibration_report
from services.publishing_intelligence.creative_library import _load_library
from services.publishing_intelligence.analytics_layer import list_intelligence_records

ROOT = Path(__file__).resolve().parents[2]
DASH_PATH = ROOT / "data" / "analytics" / "STUDIO_INTELLIGENCE_DASHBOARD.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _today_prefix() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def build_studio_intelligence_dashboard() -> dict[str, Any]:
    """Aggregate studio + learning + publishing health into one board."""
    # Soft imports — avoid circular dependency with get_executive_dashboard
    publishing: dict = {}
    learning: dict = {}
    acceptance: dict = {}
    ops: dict = {}
    jobs_running = 0
    jobs_pending = 0
    try:
        from services.publishing.models import JobStatus
        from services.publishing.queue import PublishingHistory, PublishingQueue

        q = PublishingQueue()
        h = PublishingHistory()
        pending = q.list_jobs(JobStatus.QUEUED)
        scheduled = q.list_jobs(JobStatus.SCHEDULED)
        publishing = {
            "published_count": len(h.all()),
            "pending": pending[:20],
            "scheduled": scheduled[:20],
            "queue_total": q.count(),
        }
    except Exception:  # noqa: BLE001
        publishing = {"published_count": 0, "pending": [], "scheduled": []}

    try:
        from services.learning.dashboard import build_learning_dashboard

        learning = build_learning_dashboard()
    except Exception:  # noqa: BLE001
        learning = {}

    try:
        from services.production_operations import queue_summary
        from services.production_operations.status import dashboard_path

        path = dashboard_path()
        if path.exists():
            ops = json.loads(path.read_text(encoding="utf-8"))
        ops["queue"] = queue_summary()
    except Exception:  # noqa: BLE001
        ops = {}

    try:
        from services.production_acceptance.dashboard import build_acceptance_dashboard
        from services.production_acceptance.models import DASHBOARD_PATH

        if DASHBOARD_PATH.exists():
            acceptance = json.loads(DASHBOARD_PATH.read_text(encoding="utf-8"))
        else:
            acceptance = build_acceptance_dashboard()
    except Exception:  # noqa: BLE001
        acceptance = {}

    try:
        from core.jobs import JobStatus, get_queue

        jobs = get_queue().jobs()
        jobs_running = sum(1 for j in jobs if j.status == JobStatus.RUNNING)
        jobs_pending = sum(1 for j in jobs if j.status == JobStatus.PENDING)
    except Exception:  # noqa: BLE001
        pass

    calibration = build_calibration_report()
    biz = estimate_business_metrics()
    lib = _load_library()
    intel = list_intelligence_records(limit=300)

    # Ops history / production counts
    productions_today = 0
    try:
        hist = ROOT / "data" / "productions" / "_ops" / "PRODUCTION_HISTORY.json"
        if hist.exists():
            rows = json.loads(hist.read_text(encoding="utf-8"))
            if isinstance(rows, list):
                productions_today = sum(
                    1 for r in rows if str(r.get("finished_at") or r.get("generated_at") or "").startswith(_today_prefix())
                )
    except Exception:  # noqa: BLE001
        productions_today = 0

    publishing = publishing
    published = int(publishing.get("published_count") or publishing.get("completed") or 0)
    scheduled = len(publishing.get("scheduled") or publishing.get("pending") or [])

    # Best / worst from intelligence actuals
    ranked = []
    for r in intel:
        views = float((r.get("actual_metrics") or {}).get("views") or 0)
        if views > 0:
            ranked.append((views, r))
    ranked.sort(key=lambda x: -x[0])
    best = ranked[0][1] if ranked else None
    worst = ranked[-1][1] if ranked else None

    # Validation / quality averages
    avg_quality = None
    try:
        suite = ROOT / "data" / "productions" / "_validation" / "content_validation" / "CONTENT_VALIDATION_SUITE.json"
        if suite.exists():
            data = json.loads(suite.read_text(encoding="utf-8"))
            avg_quality = (data.get("average_scores") or {}).get("overall_production_score")
    except Exception:  # noqa: BLE001
        avg_quality = None

    confidence = 55.0
    if avg_quality:
        confidence += min(25.0, float(avg_quality) * 0.2)
    if calibration.get("average_prediction_accuracy_pct"):
        confidence += min(15.0, float(calibration["average_prediction_accuracy_pct"]) * 0.1)
    if published > 0:
        confidence += 5.0
    confidence = round(min(99.0, confidence), 1)

    dashboard = {
        "generated_at": _now(),
        "version": "2.0.0",
        "productions_today": productions_today,
        "videos_published": published,
        "videos_scheduled": scheduled,
        "average_quality_score": avg_quality,
        "average_prediction_accuracy": calibration.get("average_prediction_accuracy_pct"),
        "average_audience_retention": _avg_metric(intel, "audience_retention"),
        "average_ctr": _avg_metric(intel, "ctr"),
        "best_performing_video": _video_card(best) if best else None,
        "worst_performing_video": _video_card(worst) if worst else None,
        "trending_topics": _trending_topics(intel, learning),
        "production_queue": (ops.get("queue") or {}),
        "publishing_queue": publishing,
        "system_health": {
            "pipeline_health": ops.get("pipeline_health") or "unknown",
            "acceptance_pass_pct": acceptance.get("pass_pct"),
            "jobs_running": jobs_running,
            "jobs_pending": jobs_pending,
            "providers": "ok",
        },
        "learning_progress": {
            "productions_recorded": learning.get("productions_recorded") or learning.get("productions") or 0,
            "creative_library_winners": len(lib.get("winning_combinations") or []),
            "videos_calibrated": calibration.get("videos_calibrated") or 0,
            "intelligence_records": len(intel),
        },
        "confidence_score": confidence,
        "business_intelligence": biz,
        "calibration_summary": {
            "accuracy_pct": calibration.get("average_prediction_accuracy_pct"),
            "divergences": calibration.get("divergence_highlights") or [],
        },
    }
    DASH_PATH.parent.mkdir(parents=True, exist_ok=True)
    DASH_PATH.write_text(json.dumps(dashboard, indent=2), encoding="utf-8")
    return dashboard


def _avg_metric(records: list[dict], key: str) -> float | None:
    vals = []
    for r in records:
        v = (r.get("actual_metrics") or {}).get(key)
        if v is not None:
            try:
                vals.append(float(v))
            except (TypeError, ValueError):
                continue
    return round(sum(vals) / len(vals), 3) if vals else None


def _video_card(record: dict) -> dict:
    return {
        "video_id": record.get("video_id"),
        "topic": record.get("topic"),
        "platform": record.get("platform"),
        "views": (record.get("actual_metrics") or {}).get("views"),
        "ctr": (record.get("actual_metrics") or {}).get("ctr"),
        "hook_used": record.get("hook_used"),
    }


def _trending_topics(intel: list[dict], learning: dict) -> list[str]:
    topics = []
    for r in intel[-30:]:
        t = r.get("topic")
        if t and t not in topics:
            topics.append(str(t))
    for t in learning.get("top_topics") or learning.get("trending_topics") or []:
        if t not in topics:
            topics.append(str(t))
    return topics[:10]
