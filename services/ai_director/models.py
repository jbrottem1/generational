"""Data contracts for the AI Director (Agent 18).

Field tuples are the testable contract (same convention as Creative Studio,
Asset Generation, and Post-Production). Everything the Director emits is a
plain JSON-safe dict.

Contract rules (DATA_CONTRACTS.md): additive-only from 1.0 on.
"""

from __future__ import annotations

AI_DIRECTOR_ENGINE_VERSION = "1.0.0"
DIRECTOR_PACKAGE_VERSION = "1.0"


class DirectorStatus:
    """Lifecycle of one DirectorPackage."""

    READY = "ready"
    NEEDS_REVIEW = "needs_review"
    DEGRADED = "degraded"
    INCOMPLETE = "incomplete"

    ALL = (READY, NEEDS_REVIEW, DEGRADED, INCOMPLETE)


class ProductionPriority:
    """How urgently this production should move through the pipeline."""

    URGENT = "urgent"
    HIGH = "high"
    STANDARD = "standard"
    LOW = "low"

    ALL = (URGENT, HIGH, STANDARD, LOW)


# The DirectorPackage — executive creative direction for the full production
# pipeline. Agents 12–17 consume this; the Director never generates assets.
DIRECTOR_PACKAGE_FIELDS = (
    "director_package_version",
    "engine_version",
    "project_id",
    "production_strategy",       # PRODUCTION_STRATEGY_FIELDS dict
    "target_platforms",          # list of PLATFORM_TARGET_FIELDS dicts
    "creative_style",            # CREATIVE_STYLE_FIELDS dict
    "visual_style",              # VISUAL_STYLE_FIELDS dict
    "animation_style",           # ANIMATION_STYLE_FIELDS dict
    "camera_plan",               # CAMERA_PLAN_FIELDS dict
    "pacing",                    # PACING_FIELDS dict
    "shot_plan",                 # SHOT_PLAN_FIELDS dict
    "character_plan",            # CHARACTER_PLAN_FIELDS dict
    "music_plan",                # MUSIC_PLAN_FIELDS dict
    "narration_plan",            # NARRATION_PLAN_FIELDS dict
    "editing_plan",              # EDITING_PLAN_FIELDS dict
    "optimization_hints",        # list of OPTIMIZATION_HINT_FIELDS dicts
    "asset_requirements",        # high-level asset needs (not generation specs)
    "expected_runtime",          # EXPECTED_RUNTIME_FIELDS dict
    "quality_targets",           # QUALITY_TARGET_FIELDS dict
    "production_priority",       # ProductionPriority value
    "orchestration_notes",         # per-agent guidance for Agents 12–17
    "upstream_alignment",        # how Director reconciled upstream packages
    "validation",                # quality-control findings
    "director_diagnostics",      # decision trace, policy version, signals used
    "generated_at",
)

PRODUCTION_STRATEGY_FIELDS = (
    "format",                    # short_form | long_form | documentary | educational |
                                 # cartoon | cinematic | podcast | livestream
    "orientation",               # vertical | horizontal | square
    "content_class",             # entertainment | educational | documentary | news |
                                 # branded | experimental
    "narrative_mode",            # storytelling | explainer | listicle | interview |
                                 # montage | tutorial
    "emotional_intensity",       # low | moderate | high | extreme
    "visual_complexity",         # minimal | standard | rich | cinematic
    "caption_strategy",          # full | key_moments | minimal | none
    "thumbnail_strategy",        # face_hook | text_overlay | mystery | before_after |
                                 # split_screen
    "publishing_strategy",       # immediate | scheduled | batch | test_variant
    "rationale",                 # why these choices were made
)

PLATFORM_TARGET_FIELDS = (
    "platform",
    "priority",                  # primary | secondary | repurpose
    "aspect_ratio",
    "max_duration_sec",
    "caption_required",
    "hook_style",
)

CREATIVE_STYLE_FIELDS = (
    "style_id",
    "label",
    "tone",
    "mood",
    "color_direction",
    "typography_direction",
)

VISUAL_STYLE_FIELDS = (
    "style_id",
    "label",
    "lighting",
    "texture",
    "reference_mood",
)

ANIMATION_STYLE_FIELDS = (
    "style_id",
    "technique",                 # 2d | 3d | motion_graphics | mixed_media | live_action
    "motion_language",
    "transition_style",
)

CAMERA_PLAN_FIELDS = (
    "camera_grammar",
    "dominant_shot_types",
    "movement_profile",
    "lens_character",
)

PACING_FIELDS = (
    "tempo",                     # slow | measured | dynamic | rapid
    "scene_target_sec",
    "cuts_per_minute",
    "retention_curve",           # hook_density | mid_hold | payoff_punch
)

SHOT_PLAN_FIELDS = (
    "total_shots",
    "shot_progression",
    "key_beats",                 # list of {position, shot_type, purpose}
    "b_roll_ratio",
)

CHARACTER_PLAN_FIELDS = (
    "cast_strategy",             # none | narrator_only | ensemble | branded_mascot
    "selected_characters",       # character_ids or roles
    "consistency_rules",
    "brand_alignment",
)

MUSIC_PLAN_FIELDS = (
    "direction",                 # ambient | cinematic | upbeat | tense | none
    "tempo_bpm_range",
    "instrumentation",
    "sync_to_beats",
)

NARRATION_PLAN_FIELDS = (
    "voice_selection",           # voice_id or style descriptor
    "delivery_style",            # conversational | authoritative | dramatic | warm
    "pacing_wpm",
    "emphasis_beats",
)

EDITING_PLAN_FIELDS = (
    "style",                     # jump_cut | cinematic | documentary | montage
    "transition_grammar",
    "color_grade_direction",
    "caption_style",
    "platform_cuts",             # per-platform edit variants
)

OPTIMIZATION_HINT_FIELDS = (
    "dimension",                 # title | hook | thumbnail | duration | platform
    "hint",
    "confidence",                # 0-100
    "source",                    # analytics | trend | market | policy
)

EXPECTED_RUNTIME_FIELDS = (
    "target_sec",
    "min_sec",
    "max_sec",
    "chapter_markers",
)

QUALITY_TARGET_FIELDS = (
    "minimum_score",
    "production_tier",           # draft | standard | premium | flagship
    "qc_gates",                  # list of gate names downstream must pass
)

ORCHESTRATION_NOTES_FIELDS = (
    "creative_studio",           # guidance for Agent 12
    "character_universe",        # guidance for Agent 15
    "asset_generation",          # guidance for Agent 14
    "animation",                 # guidance for Agent 16
    "render",                    # guidance for Agent 6
    "post_production",           # guidance for Agent 17
)

UPSTREAM_ALIGNMENT_FIELDS = (
    "packages_consumed",         # which upstream slots were present
    "conflicts_detected",        # list of conflict descriptions
    "conflicts_resolved",        # how Director resolved them
    "degradation_applied",       # list of graceful degradations
)

DIRECTOR_SUMMARY_FIELDS = (
    "engine_version",
    "status",                    # directed | no_items | degraded
    "items",
    "packages",
    "ready",
    "needs_review",
    "degraded",
    "incomplete",
    "formats",
    "platforms",
    "average_confidence",
    "generated_at",
)


def director_status(confidence: int, blockers: list, degraded: bool) -> str:
    """Map confidence + findings onto a DirectorStatus."""
    if blockers:
        return DirectorStatus.INCOMPLETE
    if degraded:
        return DirectorStatus.DEGRADED
    if confidence >= 80:
        return DirectorStatus.READY
    return DirectorStatus.NEEDS_REVIEW
