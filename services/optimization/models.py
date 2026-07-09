"""Data contracts for the Optimization Laboratory (Agent 13).

Field tuples are the testable contract (same convention as the Render,
Publishing, and Analytics engines). Everything the laboratory emits is a
plain JSON-safe dict so the workflow context, ContentPackage slots, the
experiment store, and the UI can carry it without conversion.

Contract rules (DATA_CONTRACTS.md): additive-only from 1.0 on — append
fields freely, never remove, rename, or repurpose existing ones.
"""

from __future__ import annotations

OPTIMIZATION_ENGINE_VERSION = "1.0.0"
OPTIMIZATION_REPORT_VERSION = "1.0"
VARIANT_VERSION = "1.0"

# Every experiment type the laboratory supports today. Future types are
# added through OptimizationConfig.extra_experiment_types — validation uses
# all_experiment_types(), never this tuple directly.
EXPERIMENT_TYPES = (
    "hook",
    "title",
    "description",
    "thumbnail",
    "caption",
    "narration_style",
    "animation_style",
    "visual_pacing",
    "scene_ordering",
    "music_style",
    "sound_design",
    "cta_placement",
    "publishing_time",
    "publishing_schedule",
    "localization",
    "language",
    "brand_style",
    "character_style",
    "platform_formatting",
)

# Test architectures the A/B framework prepares for. Providers declare
# which modes they can execute on a real platform; everything else runs as
# a predicted (pre-publish) experiment inside the laboratory.
EXPERIMENT_MODES = (
    "ab",            # two variants
    "multivariate",  # three or more variants
    "sequential",    # variants tested one after another
    "platform",      # same content, per-platform comparison
    "regional",      # same content, per-region comparison
    "brand",         # same content, per-brand comparison
    "lifecycle",     # same content at different lifecycle moments
)


class ExperimentStatus:
    """Lifecycle of one laboratory experiment."""

    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    LOW_CONFIDENCE = "low_confidence"        # concluded, winner below the bar
    INSUFFICIENT_DATA = "insufficient_data"  # not enough variants/samples
    FAILED = "failed"
    CANCELLED = "cancelled"

    ALL = (
        DRAFT, SCHEDULED, RUNNING, COMPLETED,
        LOW_CONFIDENCE, INSUFFICIENT_DATA, FAILED, CANCELLED,
    )
    CONCLUDED = (COMPLETED, LOW_CONFIDENCE, INSUFFICIENT_DATA, FAILED, CANCELLED)


# One competing alternative under test.
VARIANT_FIELDS = (
    "variant_id",
    "experiment_type",       # EXPERIMENT_TYPES value
    "version",               # VARIANT_VERSION
    "content",               # str for text types, dict for structured types
    "label",
    "metadata",              # style, template, platform, notes, ...
    "generation_source",     # control | heuristic | upstream | provider | manual
    "confidence",            # 0-100 generation confidence
    "score",                 # 0-100 weighted composite (0 until scored)
    "score_breakdown",       # SCORING_INPUTS → 0-100
    "rank",                  # 1-based rank after ranking (0 until ranked)
    "created_at",
)

# A set of variants competing for the same decision.
VARIANT_GROUP_FIELDS = (
    "group_id",
    "experiment_type",
    "base_content",          # the incumbent/control content
    "variants",              # list of VARIANT_FIELDS dicts
    "warnings",              # validation findings (duplicates, gaps, ...)
    "created_at",
)

# One experiment — the unit of comparison the laboratory manages.
LAB_EXPERIMENT_FIELDS = (
    "experiment_id",
    "experiment_type",       # EXPERIMENT_TYPES value
    "mode",                  # EXPERIMENT_MODES value
    "name",
    "hypothesis",
    "status",                # ExperimentStatus value
    "variant_group",         # VARIANT_GROUP_FIELDS dict
    "runs",                  # list of EXPERIMENT_RUN_FIELDS dicts
    "result",                # EXPERIMENT_RESULT_FIELDS dict ({} until concluded)
    "platform",
    "region",
    "brand_id",
    "project_id",
    "provider",              # experiment provider name ("" = internal/predicted)
    "min_confidence",        # winner confidence floor for COMPLETED status
    "scheduled_for",         # ISO-8601 ("" = run on demand)
    "created_at",
    "completed_at",
)

# One execution of an experiment (concurrent experiments each accumulate
# their own runs; re-running with fresh context appends, never overwrites).
EXPERIMENT_RUN_FIELDS = (
    "run_id",
    "experiment_id",
    "scores",                # variant_id → composite score for this run
    "warnings",
    "started_at",
    "finished_at",
)

# The concluded outcome of one experiment.
EXPERIMENT_RESULT_FIELDS = (
    "winner",                # winning variant dict (VARIANT_FIELDS)
    "losers",                # remaining variants, best-first
    "ranked",                # every variant, best-first
    "confidence",            # 0-100 statistical confidence in the winner
    "expected_lift",         # winner score minus control/runner-up score
    "method",                # predicted | observed
    "evaluated_at",
)

# One structured recommendation — the ONLY thing the laboratory returns to
# the pipeline. Recommendations flow through the orchestrator and the
# ContentPackage `optimization_package` slot; never engine-to-engine.
OPTIMIZATION_RECOMMENDATION_FIELDS = (
    "recommendation_id",
    "experiment_type",
    "target_slot",           # the ContentPackage/idea field the winner improves
    "action",                # human-readable instruction
    "content",               # the recommended winning content
    "variant",               # full winning VARIANT_FIELDS dict
    "alternatives",          # next-best variants (ranked)
    "confidence",            # 0-100
    "expected_lift",
    "experiment_id",
    "source",                # optimization_lab
    "warnings",              # low confidence, conflicts, degraded inputs, ...
    "generated_at",
)

# The ContentPackage `optimization_package` slot (Agent 13's write zone).
OPTIMIZATION_PACKAGE_FIELDS = (
    "engine_version",
    "status",                # optimized | partial | skipped
    "recommendations",       # OPTIMIZATION_RECOMMENDATION_FIELDS dicts
    "best",                  # experiment_type → recommended content
    "experiments",           # experiment ids run for this item
    "confidence",            # 0-100 average recommendation confidence
    "generated_at",
)

# The aggregate report returned to the orchestrator on the
# `optimization_report` context key.
OPTIMIZATION_REPORT_FIELDS = (
    "report_version",
    "engine_version",
    "status",                # optimized | partial | no_items
    "items",
    "experiments_run",
    "variants_generated",
    "winning_variants",      # winners across all experiments (summaries)
    "losing_variants",       # confirmed losers (summaries)
    "average_confidence",
    "expected_lift",         # average expected lift across experiments
    "experiment_summary",    # per experiment_type counts + outcomes
    "historical_trends",     # what the learning bridge contributed
    "recommendations",       # every recommendation issued this run
    "warnings",
    "generated_at",
)

# Every input the scoring engine can blend. Weights live in
# OptimizationConfig.scoring_weights — data, not code — so the Learning
# Engine (or an operator) retunes them without touching scoring logic.
SCORING_INPUTS = (
    "psychology",
    "virality",
    "seo",
    "trend",
    "historical_performance",
    "brand_fit",
    "audience_match",
    "retention_prediction",
    "ctr_prediction",
    "engagement_prediction",
    "revenue_prediction",       # explicit placeholder until monetization lands
    "confidence",
    "platform_suitability",
    "localization_suitability",
)

DEFAULT_SCORING_WEIGHTS = {
    "psychology": 0.10,
    "virality": 0.10,
    "seo": 0.07,
    "trend": 0.05,
    "historical_performance": 0.12,
    "brand_fit": 0.05,
    "audience_match": 0.05,
    "retention_prediction": 0.12,
    "ctr_prediction": 0.12,
    "engagement_prediction": 0.08,
    "revenue_prediction": 0.02,
    "confidence": 0.04,
    "platform_suitability": 0.05,
    "localization_suitability": 0.03,
}

# experiment_type → the idea/ContentPackage field its winner improves.
TARGET_SLOTS = {
    "hook": "hook",
    "title": "title",
    "description": "description",
    "thumbnail": "thumbnail_plan",
    "caption": "captions",
    "narration_style": "audio_package.voice_style",
    "animation_style": "visual_package.style",
    "visual_pacing": "visual_package.pacing",
    "scene_ordering": "scene_breakdown",
    "music_style": "music_assets",
    "sound_design": "audio_package.sfx_plan",
    "cta_placement": "script_package.call_to_action",
    "publishing_time": "publishing_package.publish_time",
    "publishing_schedule": "publishing_package.schedule",
    "localization": "seo_package.localization",
    "language": "target_language",
    "brand_style": "brand_id",
    "character_style": "visual_package.character",
    "platform_formatting": "target_platforms",
}


def target_slot(experiment_type: str) -> str:
    """The package field a recommendation of this type improves."""
    return TARGET_SLOTS.get(experiment_type, experiment_type)
