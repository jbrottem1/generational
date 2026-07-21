"""Data contracts for the Continuous Learning Engine (Agent 9).

Field tuples are the testable contract. All shapes are JSON-safe dicts;
additive-only from 1.0 on.
"""

from __future__ import annotations

from services.analytics.models import LEARNING_ENGINE_VERSION  # noqa: F401 - shared version

LEARNING_REPORT_VERSION = "1.0"

# Attribution dimensions the pattern miner analyzes. Each maps a record
# field (or derived bucket) to the upstream engines that own the decision.
PATTERN_DIMENSIONS = (
    "hook",
    "psychology_strategy",
    "thumbnail_version",
    "voice_version",
    "posting_hour",
    "platform",
    "topic",
    "niche",
    "length_bucket",
    "title",
    "keyword",
    "camera_movement",
    "evidence_modality",
)

# One mined pattern — "content with this attribute performs like this".
INSIGHT_FIELDS = (
    "insight_id",
    "dimension",          # PATTERN_DIMENSIONS value
    "value",              # the attribute value (hook text, hour, platform, ...)
    "samples",            # how many records support it
    "average_score",      # mean composite performance score
    "baseline_score",     # mean score across ALL records (context)
    "lift",               # average_score - baseline_score
    "confidence",         # 0-100 (sample size x consistency)
    "example_titles",     # up to 3 titles carrying the attribute
    "generated_at",
)

# One actionable recommendation flowing back to an upstream engine.
RECOMMENDATION_FIELDS = (
    "recommendation_id",
    "target_engine",      # TARGET_ENGINES value
    "dimension",
    "action",             # human/machine-readable instruction
    "value",              # the winning attribute value to prefer
    "confidence",         # 0-100
    "evidence",           # {samples, average_score, baseline_score, lift}
    "generated_at",
)

# Engines that consume learning recommendations (feedback-loop targets).
TARGET_ENGINES = (
    "psychology",
    "script_generation",
    "visual_intelligence",
    "voice_audio",
    "seo_optimization",
    "seo",
    "publishing",
    "trend_discovery",
    "discovery",
    "evidence_intelligence",
    "cinematography",
    "viewer_retention",
    "studio_render",
    "optimization_lab",
    "audience_intelligence",
)

# dimension → engines whose next-generation output should absorb it.
DIMENSION_TARGETS = {
    "hook": ("script_generation", "psychology", "viewer_retention"),
    "psychology_strategy": ("psychology", "audience_intelligence", "viewer_retention"),
    "thumbnail_version": ("visual_intelligence", "seo_optimization", "seo"),
    "voice_version": ("voice_audio",),
    "posting_hour": ("publishing", "seo_optimization", "seo"),
    "platform": ("publishing", "seo_optimization", "seo"),
    "topic": ("trend_discovery", "discovery", "script_generation"),
    "niche": ("trend_discovery", "discovery"),
    "length_bucket": ("script_generation", "voice_audio", "cinematography", "viewer_retention"),
    "title": ("seo_optimization", "seo"),
    "keyword": ("seo_optimization", "seo"),
    "camera_movement": ("cinematography", "viewer_retention", "visual_intelligence"),
    "evidence_modality": ("evidence_intelligence", "visual_intelligence"),
}

# The ContentPackage `learning_metadata` slot (Agent 9's write zone).
LEARNING_METADATA_FIELDS = (
    "engine_version",
    "status",             # learned | insufficient_data
    "signals",            # insights relevant to this item's attributes
    "recommendations",    # recommendations applied/available for this item
    "knowledge_size",     # records the learning ran against
    "confidence",         # 0-100 overall learning confidence
    "generated_at",
)

# The learning report returned on the `learning_report` context key.
LEARNING_REPORT_FIELDS = (
    "report_version",
    "engine_version",
    "status",             # learned | insufficient_data
    "records_analyzed",
    "insights",
    "recommendations",
    "memory_entries_added",
    "confidence",
    "generated_at",
)

# Performance report periods.
REPORT_PERIODS = ("daily", "weekly", "monthly")

PERFORMANCE_REPORT_FIELDS = (
    "report_version",
    "period",             # REPORT_PERIODS value
    "window",             # {start, end} ISO-8601
    "totals",             # records/views/watch time/engagement rollup
    "top_content",
    "worst_content",
    "engine_recommendations",
    "trending_opportunities",
    "optimization_priorities",
    "confidence",
    "generated_at",
)

# Minimum records a dimension value needs before it can drive a
# recommendation (below this it is signal, not strategy).
MIN_SAMPLES_FOR_RECOMMENDATION = 2

# Records with a composite score at/above this are "successful",
# at/below the failure line are "failed" — the memory thresholds.
SUCCESS_SCORE_THRESHOLD = 60
FAILURE_SCORE_THRESHOLD = 30
