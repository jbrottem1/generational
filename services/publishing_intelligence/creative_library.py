"""Phase 4 — Creative Knowledge Library: winning pattern storage + recommendations."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.analytics.store import get_analytics_store
from services.learning.patterns import mine_patterns
from services.publishing_intelligence.analytics_layer import list_intelligence_records

ROOT = Path(__file__).resolve().parents[2]
LIBRARY_PATH = ROOT / "data" / "analytics" / "creative_knowledge_library.json"

CREATIVE_DIMENSIONS = (
    "hook",
    "opening",
    "narration",
    "visual_pacing",
    "camera_motion",
    "animation",
    "caption_style",
    "thumbnail_style",
    "topic",
    "publishing_time",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_library() -> dict:
    if LIBRARY_PATH.exists():
        try:
            data = json.loads(LIBRARY_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
    return {
        "version": "2.0.0",
        "updated_at": None,
        "winning_combinations": [],
        "by_dimension": {d: [] for d in CREATIVE_DIMENSIONS},
    }


def _save_library(lib: dict) -> None:
    LIBRARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    lib["updated_at"] = _now()
    LIBRARY_PATH.write_text(json.dumps(lib, indent=2), encoding="utf-8")


def update_creative_library(*, min_performance: float = 60.0) -> dict[str, Any]:
    """Mine analytics + intelligence records into the Creative Knowledge Library."""
    lib = _load_library()
    records = list(get_analytics_store().list_records())
    intel = list_intelligence_records(limit=500)

    # Convert intelligence rows with actuals into pattern-friendly records
    for row in intel:
        metrics = {k: v for k, v in (row.get("actual_metrics") or {}).items() if v is not None}
        if not metrics:
            continue
        records.append(
            {
                "topic": row.get("topic"),
                "hook": row.get("hook_used"),
                "platform": row.get("platform"),
                "niche": row.get("category"),
                "video_length_sec": row.get("length_sec"),
                "posting_time": row.get("publish_date"),
                "thumbnail_version": row.get("thumbnail_style"),
                "voice_version": row.get("narration_style"),
                "visual_style": row.get("visual_style"),
                "music_style": row.get("music_style"),
                "metrics": metrics,
                "metrics_status": "collected",
            }
        )

    insights = mine_patterns(records) if records else []
    # Map mined insights into creative dimensions
    dim_map = {
        "hook": "hook",
        "psychology_strategy": "opening",
        "voice_version": "narration",
        "video_length": "visual_pacing",
        "thumbnail_version": "thumbnail_style",
        "topic": "topic",
        "posting_hour": "publishing_time",
        "platform": "publishing_time",
        "title": "opening",
    }
    by_dim: dict[str, list] = {d: [] for d in CREATIVE_DIMENSIONS}
    winners = []
    for insight in insights:
        if not isinstance(insight, dict):
            continue
        score = float(insight.get("performance_score") or insight.get("score") or 0)
        if score < min_performance:
            continue
        dim = str(insight.get("dimension") or "")
        creative_dim = dim_map.get(dim, "topic")
        entry = {
            "dimension": creative_dim,
            "source_dimension": dim,
            "value": insight.get("value") or insight.get("pattern") or insight.get("label"),
            "performance_score": score,
            "confidence": insight.get("confidence"),
            "sample_size": insight.get("sample_size") or insight.get("n"),
            "recommendation": insight.get("recommendation") or insight.get("insight"),
        }
        by_dim.setdefault(creative_dim, []).append(entry)
        winners.append(entry)

    # Enrich from intelligence style attrs of top performers
    scored_intel = []
    for row in intel:
        views = float((row.get("actual_metrics") or {}).get("views") or 0)
        ctr = float((row.get("actual_metrics") or {}).get("ctr") or 0)
        if views <= 0 and ctr <= 0:
            continue
        scored_intel.append((views + ctr * 1000, row))
    scored_intel.sort(key=lambda x: -x[0])
    for _, row in scored_intel[:20]:
        for creative_dim, key in (
            ("hook", "hook_used"),
            ("visual_pacing", "visual_style"),
            ("narration", "narration_style"),
            ("animation", "visual_style"),
            ("thumbnail_style", "thumbnail_style"),
            ("topic", "topic"),
            ("publishing_time", "publish_date"),
            ("camera_motion", "visual_style"),
            ("caption_style", "visual_style"),
            ("opening", "hook_used"),
        ):
            val = row.get(key)
            if not val:
                continue
            entry = {
                "dimension": creative_dim,
                "value": val,
                "performance_score": float((row.get("actual_metrics") or {}).get("views") or 0),
                "source": "intelligence_top_performer",
                "platform": row.get("platform"),
            }
            by_dim[creative_dim].append(entry)
            winners.append(entry)

    for d in by_dim:
        by_dim[d] = sorted(by_dim[d], key=lambda e: -float(e.get("performance_score") or 0))[:25]

    lib["by_dimension"] = by_dim
    lib["winning_combinations"] = sorted(winners, key=lambda e: -float(e.get("performance_score") or 0))[:100]
    lib["insight_count"] = len(insights)
    _save_library(lib)
    return lib


def recommend_creative_patterns(
    *,
    topic: str = "",
    platform: str = "youtube_shorts",
    limit: int = 5,
) -> dict[str, Any]:
    """Recommend winning patterns for the next production."""
    lib = _load_library()
    if not lib.get("updated_at"):
        lib = update_creative_library()

    recommendations = []
    for dim in CREATIVE_DIMENSIONS:
        entries = (lib.get("by_dimension") or {}).get(dim) or []
        if not entries:
            continue
        top = entries[0]
        recommendations.append(
            {
                "dimension": dim,
                "pattern": top.get("value"),
                "performance_score": top.get("performance_score"),
                "confidence": top.get("confidence"),
                "why": top.get("recommendation") or f"Historically strong {dim} pattern",
                "apply_to": platform,
                "topic_hint": topic,
            }
        )
        if len(recommendations) >= limit:
            break

    return {
        "generated_at": _now(),
        "topic": topic,
        "platform": platform,
        "recommendations": recommendations,
        "library_updated_at": lib.get("updated_at"),
        "winners_available": len(lib.get("winning_combinations") or []),
    }
