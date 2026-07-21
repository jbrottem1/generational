"""Phase 2 — Analytics collection schema + enrichment for intelligence records."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from services.analytics.store import get_analytics_store
# Mission-level analytics fields (extends existing ANALYTICS_RECORD via additive enrichment)
INTELLIGENCE_ATTRIBUTION_FIELDS = (
    "video_id",
    "topic",
    "category",
    "platform",
    "publish_date",
    "length_sec",
    "hook_used",
    "visual_style",
    "narration_style",
    "music_style",
    "thumbnail_style",
    "internal_quality_scores",
    "predicted_metrics",
    "actual_metrics",
)

ACTUAL_METRIC_FIELDS = (
    "views",
    "impressions",
    "ctr",
    "audience_retention",
    "average_view_duration",
    "likes",
    "comments",
    "shares",
    "subscribers",
    "watch_time",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_intelligence_analytics_record(
    *,
    candidate: dict,
    platform: str,
    publish_package: dict | None = None,
    predicted: dict | None = None,
    actual: dict | None = None,
    quality_scores: dict | None = None,
) -> dict[str, Any]:
    """Attribution-rich analytics atom for Continuous Learning V2."""
    bp = candidate.get("production_blueprint") or {}
    publish_package = publish_package or {}
    predicted = predicted or {}
    actual = actual or {}
    quality_scores = quality_scores or {}

    video_id = str(
        candidate.get("production_id")
        or candidate.get("video_id")
        or candidate.get("project_id")
        or uuid.uuid4().hex[:12]
    )
    length = float(
        candidate.get("duration_sec")
        or bp.get("video_length_sec")
        or (candidate.get("render_package") or {}).get("duration_sec")
        or 60
    )
    hook = str(
        candidate.get("hook")
        or (candidate.get("hook_strategy") or {}).get("strategy")
        or (candidate.get("structured_script") or {}).get("primary_hook")
        or ""
    )
    record = {
        "record_id": f"intel_{uuid.uuid4().hex[:10]}",
        "record_version": "2.0",
        "generated_at": _now(),
        "video_id": video_id,
        "topic": candidate.get("topic") or candidate.get("title"),
        "category": candidate.get("niche") or candidate.get("category") or bp.get("visual_style") or "Education",
        "platform": platform,
        "publish_date": publish_package.get("suggested_publish_time") or _now(),
        "length_sec": length,
        "hook_used": hook,
        "visual_style": bp.get("visual_style") or candidate.get("visual_style") or "",
        "narration_style": bp.get("narration_style") or candidate.get("narration_style") or "",
        "music_style": bp.get("music_style") or candidate.get("music_mood") or "",
        "thumbnail_style": (bp.get("thumbnail_strategy") or {}).get("layout")
        or candidate.get("thumbnail_layout")
        or "",
        "internal_quality_scores": {
            "hook": quality_scores.get("hook_strength") or candidate.get("hook_score"),
            "overall": quality_scores.get("overall_production_score") or candidate.get("quality_score"),
            "visual": quality_scores.get("visual_quality") or candidate.get("studio_render_score"),
            "retention": quality_scores.get("retention_prediction"),
            "shareability": quality_scores.get("shareability"),
            "seo": quality_scores.get("seo_quality"),
        },
        "predicted_metrics": {
            "hook_score": predicted.get("hook_score") or candidate.get("hook_score"),
            "ctr": predicted.get("ctr") or predicted.get("expected_ctr"),
            "completion": predicted.get("completion") or predicted.get("expected_completion_rate"),
            "retention": predicted.get("retention") or predicted.get("audience_retention"),
            "shareability": predicted.get("shareability"),
            "views": predicted.get("views") or predicted.get("expected_views"),
        },
        "actual_metrics": {
            "views": actual.get("views"),
            "impressions": actual.get("impressions"),
            "ctr": actual.get("ctr"),
            "audience_retention": actual.get("audience_retention"),
            "average_view_duration": actual.get("average_view_duration") or actual.get("average_view_duration_sec"),
            "likes": actual.get("likes"),
            "comments": actual.get("comments"),
            "shares": actual.get("shares"),
            "subscribers": actual.get("subscribers") or actual.get("subscriber_growth"),
            "watch_time": actual.get("watch_time") or actual.get("watch_time_sec"),
        },
    }
    return record


def persist_intelligence_record(record: dict, *, also_legacy_store: bool = True) -> dict:
    """Persist intelligence record; optionally mirror into AnalyticsStore."""
    from pathlib import Path
    import json

    root = Path(__file__).resolve().parents[2] / "data" / "analytics"
    root.mkdir(parents=True, exist_ok=True)
    path = root / "intelligence_records.json"
    rows: list = []
    if path.exists():
        try:
            rows = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            rows = []
    if not isinstance(rows, list):
        rows = []
    rows.append(record)
    path.write_text(json.dumps(rows[-5000:], indent=2), encoding="utf-8")

    if also_legacy_store:
        try:
            store = get_analytics_store()
            metrics = {k: v for k, v in (record.get("actual_metrics") or {}).items() if v is not None}
            legacy = {
                "record_id": record.get("record_id"),
                "record_version": "2.0",
                "platform": record.get("platform"),
                "topic": record.get("topic"),
                "title": record.get("topic"),
                "hook": record.get("hook_used"),
                "niche": record.get("category"),
                "video_length_sec": record.get("length_sec"),
                "published_at": record.get("publish_date"),
                "posting_time": record.get("publish_date"),
                "metrics": metrics,
                "metrics_status": "collected" if metrics else "pending",
                "intelligence_ref": record.get("record_id"),
                "predicted_metrics": record.get("predicted_metrics"),
                "internal_quality_scores": record.get("internal_quality_scores"),
            }
            if hasattr(store, "add_record"):
                store.add_record(legacy)
            elif hasattr(store, "append"):
                store.append(legacy)
        except Exception:  # noqa: BLE001 — never block publish path
            pass
    return {"ok": True, "path": str(path), "record_id": record.get("record_id")}


def list_intelligence_records(limit: int = 200) -> list[dict]:
    from pathlib import Path
    import json

    path = Path(__file__).resolve().parents[2] / "data" / "analytics" / "intelligence_records.json"
    if not path.exists():
        return []
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(rows, list):
        return []
    return rows[-limit:]
