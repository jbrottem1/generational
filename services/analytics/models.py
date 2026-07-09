"""Data contracts for the Analytics & Continuous Learning Engine (Agent 9).

Field tuples are the testable contract (same convention as the Render,
Optimization, and Publishing engines). Everything the engine emits is a
plain JSON-safe dict so the workflow context, ContentPackage slots, the
analytics store, and the UI can carry it without conversion.

Contract rules (DATA_CONTRACTS.md): additive-only from 1.0 on — append
fields freely, never remove, rename, or repurpose existing ones.
"""

from __future__ import annotations

ANALYTICS_ENGINE_VERSION = "1.0.0"
LEARNING_ENGINE_VERSION = "1.0.0"

# Version of the structured analytics record persisted per published piece
# of content (one record per item x platform publish job).
ANALYTICS_RECORD_VERSION = "1.0"


class MetricsStatus:
    """Lifecycle of one analytics record's platform metrics."""

    COLLECTED = "collected"       # metrics fetched from the platform provider
    PENDING = "pending"           # content scheduled but not yet published
    UNAVAILABLE = "unavailable"   # no provider for the platform

    ALL = (COLLECTED, PENDING, UNAVAILABLE)


# The platform performance metrics tracked for every published piece of
# content. RPM/CPM are explicit placeholders until monetization APIs land.
ANALYTICS_METRIC_FIELDS = (
    "views",
    "watch_time_sec",
    "average_view_duration_sec",
    "audience_retention",        # 0-100 percent of video watched on average
    "ctr",                       # 0-100 impression click-through rate
    "likes",
    "comments",
    "shares",
    "saves",
    "subscriber_growth",
    "followers_gained",
    "rpm",                       # placeholder — revenue per mille
    "cpm",                       # placeholder — cost per mille
)

# One structured analytics record — the atom of the learning system.
# Attribution fields tie the outcome back to every upstream decision that
# produced it, so the Learning Engine can credit or blame each one.
ANALYTICS_RECORD_FIELDS = (
    "record_id",
    "record_version",
    "analytics_ref",             # correlation id from the PublishingJob
    "project_id",
    "brand_id",
    "channel_id",
    "platform",
    "post_id",
    "post_url",
    # -- attribution: what produced this content -------------------------
    "topic",
    "niche",
    "title",
    "hook",
    "keywords",
    "psychology_strategy",       # dominant psychological triggers used
    "psychology_score",
    "virality_score",
    "attention_score",
    "quality_score",
    "script_version",            # stable fingerprint of the script used
    "thumbnail_version",         # stable fingerprint of the thumbnail plan
    "voice_version",             # stable fingerprint of the voice/narration
    "render_version",            # render package contract version
    "video_length_sec",
    "posting_time",              # ISO-8601 — when it was posted/scheduled
    "published_at",
    # -- experimentation --------------------------------------------------
    "experiment_id",             # "" when not part of an experiment
    "variant_id",
    # -- outcome -----------------------------------------------------------
    "metrics",                   # ANALYTICS_METRIC_FIELDS dict
    "metrics_status",            # MetricsStatus value
    "metrics_source",            # provider name ("mock" until real APIs land)
    "collected_at",
)

# The ContentPackage `analytics_package` slot (Agent 9's write zone).
ANALYTICS_PACKAGE_FIELDS = (
    "engine_version",
    "status",                    # collected | pending | skipped
    "records",                   # per-platform analytics records
    "metrics",                   # aggregate metrics across platforms
    "performance_score",         # 0-100 composite performance
    "collected_at",
)

# The aggregate summary returned to the orchestrator on the
# `analytics_summary` context key.
ANALYTICS_SUMMARY_FIELDS = (
    "engine_version",
    "status",                    # collected | no_items
    "items",
    "records",
    "collected",
    "pending",
    "platforms",
    "average_performance_score",
    "store_size",                # cumulative records in the analytics store
    "generated_at",
)


def empty_metrics() -> dict:
    """A zeroed metrics dict covering every tracked platform metric."""
    return {metric: 0 for metric in ANALYTICS_METRIC_FIELDS}


# Composite score weights — how much each outcome dimension matters when
# ranking content performance. Candidates for learning-loop retuning.
PERFORMANCE_SCORE_WEIGHTS = {
    "audience_retention": 0.30,
    "ctr": 0.20,
    "engagement_rate": 0.25,
    "reach": 0.25,
}

# Views at (or above) which the reach component saturates at 100.
_REACH_SATURATION_VIEWS = 100_000


def engagement_rate(metrics: dict) -> float:
    """Engagements per 100 views (likes + comments + shares + saves)."""
    views = float(metrics.get("views", 0) or 0)
    if views <= 0:
        return 0.0
    engaged = sum(float(metrics.get(key, 0) or 0) for key in ("likes", "comments", "shares", "saves"))
    return round(engaged * 100.0 / views, 2)


def performance_score(metrics: dict) -> int:
    """0-100 composite performance score for one metrics dict.

    Deterministic pure function so records, packages, insights, and
    experiments all rank content the same way.
    """
    retention = min(100.0, float(metrics.get("audience_retention", 0) or 0))
    ctr = min(100.0, float(metrics.get("ctr", 0) or 0) * 100.0 / 15.0)  # 15% CTR = perfect
    engagement = min(100.0, engagement_rate(metrics) * 100.0 / 10.0)     # 10 per 100 views = perfect
    views = float(metrics.get("views", 0) or 0)
    reach = min(100.0, views * 100.0 / _REACH_SATURATION_VIEWS)

    weights = PERFORMANCE_SCORE_WEIGHTS
    score = (
        retention * weights["audience_retention"]
        + ctr * weights["ctr"]
        + engagement * weights["engagement_rate"]
        + reach * weights["reach"]
    )
    return int(round(min(100.0, max(0.0, score))))
