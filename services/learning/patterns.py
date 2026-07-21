"""Pattern miner — turns historical analytics records into insights.

Deterministic, pure statistics over ANALYTICS_RECORD dicts: group records
by attribution dimension (hook, psychology strategy, posting hour, topic,
platform, video length, title, keyword, thumbnail/voice fingerprints),
score each group with the shared composite performance score, and emit
INSIGHT_FIELDS dicts with confidence derived from sample size and
consistency. No I/O, no engine imports.
"""

from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone

from services.analytics.models import MetricsStatus, performance_score
from services.learning.models import PATTERN_DIMENSIONS


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# --------------------------------------------------------- dimension keys


def _length_bucket(seconds: float) -> str:
    if seconds <= 0:
        return ""
    if seconds < 30:
        return "under_30s"
    if seconds < 60:
        return "30_60s"
    if seconds < 180:
        return "1_3min"
    return "over_3min"


def _posting_hour(record: dict) -> str:
    stamp = record.get("posting_time") or record.get("published_at") or ""
    if len(stamp) >= 13 and stamp[10] == "T":
        return f"{stamp[11:13]}:00"
    return ""


def dimension_values(record: dict, dimension: str) -> list:
    """The attribute value(s) a record contributes to one dimension."""
    if dimension == "posting_hour":
        value = _posting_hour(record)
        return [value] if value else []
    if dimension == "length_bucket":
        value = _length_bucket(float(record.get("video_length_sec", 0) or 0))
        return [value] if value else []
    if dimension == "psychology_strategy":
        return [str(v) for v in record.get("psychology_strategy", []) or []]
    if dimension == "keyword":
        return [str(k).lower() for k in record.get("keywords", []) or []][:8]
    if dimension == "camera_movement":
        value = record.get("camera_movement") or record.get("animation_style") or ""
        return [str(value)] if value else []
    if dimension == "evidence_modality":
        value = record.get("evidence_modality") or record.get("visual_modality") or ""
        return [str(value)] if value else []
    value = record.get(dimension, "")
    return [str(value)] if value else []


# ---------------------------------------------------------------- mining


def _confidence(scores: list) -> int:
    """0-100: sample-size factor x consistency factor.

    More observations and tighter score spread both raise confidence;
    a single data point caps out low so one lucky video never rewrites
    the strategy.
    """
    samples = len(scores)
    sample_factor = samples / (samples + 4.0)          # 1→0.2, 4→0.5, 12→0.75
    mean = sum(scores) / samples
    if samples > 1 and mean > 0:
        variance = sum((s - mean) ** 2 for s in scores) / (samples - 1)
        spread = math.sqrt(variance) / mean
        consistency = max(0.25, 1.0 - min(1.0, spread))
    else:
        consistency = 0.5
    return int(round(100 * sample_factor * consistency))


def scored_records(records: list) -> list:
    """Records with collected metrics, each annotated with its composite
    `_score` (annotation is local — records are copied, never mutated)."""
    scored = []
    for record in records:
        if record.get("metrics_status") != MetricsStatus.COLLECTED:
            continue
        entry = dict(record)
        entry["_score"] = performance_score(record.get("metrics", {}))
        scored.append(entry)
    return scored


def mine_patterns(records: list, dimensions: "tuple | list" = PATTERN_DIMENSIONS) -> list:
    """All INSIGHT_FIELDS dicts minable from the given records."""
    scored = scored_records(records)
    if not scored:
        return []
    baseline = sum(r["_score"] for r in scored) / len(scored)

    insights = []
    for dimension in dimensions:
        groups: "dict[str, list]" = {}
        titles: "dict[str, list]" = {}
        for record in scored:
            for value in dimension_values(record, dimension):
                groups.setdefault(value, []).append(record["_score"])
                title = record.get("title", "")
                if title and title not in titles.setdefault(value, []):
                    titles[value].append(title)

        for value, scores in groups.items():
            average = sum(scores) / len(scores)
            insights.append({
                "insight_id": f"in_{uuid.uuid4().hex[:12]}",
                "dimension": dimension,
                "value": value,
                "samples": len(scores),
                "average_score": int(round(average)),
                "baseline_score": int(round(baseline)),
                "lift": int(round(average - baseline)),
                "confidence": _confidence(scores),
                "example_titles": titles.get(value, [])[:3],
                "generated_at": _now_iso(),
            })

    insights.sort(key=lambda i: (i["lift"], i["confidence"], i["samples"]), reverse=True)
    return insights


def best_performers(records: list, dimension: str, limit: int = 5) -> list:
    """The highest-lift insight per value for one dimension (e.g. the
    highest-retention hooks, best posting times, strongest keywords)."""
    insights = [i for i in mine_patterns(records, dimensions=(dimension,)) if i["lift"] >= 0]
    return insights[:limit]


def worst_performers(records: list, dimension: str, limit: int = 5) -> list:
    """The lowest-lift insights for one dimension — what to stop doing."""
    insights = mine_patterns(records, dimensions=(dimension,))
    insights.sort(key=lambda i: (i["lift"], -i["confidence"]))
    return insights[:limit]


def platform_breakdown(records: list) -> dict:
    """platform → {samples, average_score, lift} for platform-specific
    optimization."""
    return {
        insight["value"]: {
            "samples": insight["samples"],
            "average_score": insight["average_score"],
            "lift": insight["lift"],
            "confidence": insight["confidence"],
        }
        for insight in mine_patterns(records, dimensions=("platform",))
    }
