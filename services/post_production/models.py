"""Data contracts for the Post-Production & Intelligent Editing Engine (Agent 17).

Field tuples are the testable contract (same convention as Render, Asset
Generation, and Creative Studio). Everything the engine emits is a plain
JSON-safe dict.

Contract rules (DATA_CONTRACTS.md): additive-only from 1.0 on.
"""

from __future__ import annotations

POST_PRODUCTION_ENGINE_VERSION = "1.0.0"
POST_PRODUCTION_PACKAGE_VERSION = "1.0"


class PackageReadiness:
    """Lifecycle of one PostProductionPackage."""

    READY = "ready"
    NEEDS_REVIEW = "needs_review"
    INCOMPLETE = "incomplete"

    ALL = (READY, NEEDS_REVIEW, INCOMPLETE)


class EditStatus:
    """Outcome vocabulary for post-production planning."""

    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


# Master editing timeline — tracks, layers, clips, markers.
EDIT_TIMELINE_FIELDS = (
    "timeline_id",
    "total_duration_sec",
    "fps",
    "tracks",              # list of TRACK_FIELDS dicts
    "markers",             # list of MARKER_FIELDS dicts
    "metadata",
)

TRACK_FIELDS = (
    "track_id",
    "track_type",          # video | audio | caption | effect | transition | graphics
    "layer",
    "clips",               # list of CLIP_FIELDS dicts
    "muted",
    "locked",
)

CLIP_FIELDS = (
    "clip_id",
    "asset_ref",
    "start_time",
    "end_time",
    "duration",
    "in_point",
    "out_point",
    "transition_in",
    "transition_out",
    "effects",
    "metadata",
)

MARKER_FIELDS = (
    "marker_id",
    "time",
    "label",
    "marker_type",         # cut | beat | cta | chapter | note
    "metadata",
)

# Scene cut decisions — pacing, jump cuts, dead space removal.
SCENE_CUT_FIELDS = (
    "scene_id",
    "original_start",
    "original_end",
    "edited_start",
    "edited_end",
    "cut_type",            # jump_cut | trim | hold | speed_ramp | freeze
    "reason",
    "pacing_score",
)

# Finalized audio mix — enriches render audio_mix_plan, does not replace it.
AUDIO_MIX_FINAL_FIELDS = (
    "source_plan",         # reference to render audio_mix_plan
    "dialogue_level_db",
    "music_level_db",
    "sfx_level_db",
    "ducking",
    "normalization",
    "loudness_target",
    "fade_in_sec",
    "fade_out_sec",
    "effects",             # compression, EQ, limiter, noise_reduction
    "platform_targets",
)

# Caption timeline — animated captions, highlights, themes.
CAPTION_TIMELINE_FIELDS = (
    "mode",                # word_by_word | sentence | animated
    "language",
    "entries",             # list of CAPTION_ENTRY_FIELDS
    "theme",
    "burn_in",
    "export_formats",      # srt | vtt | ass | burned
)

CAPTION_ENTRY_FIELDS = (
    "entry_id",
    "start_time",
    "end_time",
    "text",
    "highlight_words",
    "emoji",
    "style_override",
)

SUBTITLE_STYLING_FIELDS = (
    "preset",
    "font",
    "size_pct",
    "fill",
    "stroke",
    "stroke_width_px",
    "emphasis_fill",
    "animation",
    "position",
    "safe_area",
)

# Motion graphics — intros, outros, CTAs, branding.
MOTION_GRAPHIC_FIELDS = (
    "graphic_id",
    "graphic_type",        # intro | outro | lower_third | cta | watermark | end_screen
    "start_time",
    "end_time",
    "template",
    "content",
    "animation",
)

TRANSITION_PLAN_FIELDS = (
    "transition_id",
    "from_clip",
    "to_clip",
    "time",
    "type",                # cut | crossfade | wipe | zoom | glitch
    "duration_sec",
)

EFFECT_PLAN_FIELDS = (
    "effect_id",
    "clip_ref",
    "effect_type",         # motion_blur | glow | lens_flare | particles | speed_ramp | zoom
    "start_time",
    "end_time",
    "parameters",
)

COLOR_GRADING_FIELDS = (
    "preset",
    "lut",
    "brightness",
    "contrast",
    "saturation",
    "white_balance",
    "hdr_prep",
    "brand_lut",
    "corrections",         # per-scene overrides
)

QUALITY_ISSUE_FIELDS = (
    "issue_id",
    "severity",            # error | warning | info
    "category",            # cut | asset | caption | audio | sync | continuity | timing | export
    "message",
    "time",
    "scene_id",
)

QUALITY_REPORT_FIELDS = (
    "status",
    "score",
    "issues",              # list of QUALITY_ISSUE_FIELDS
    "checks_passed",
    "checks_failed",
    "ready_for_export",
)

PUBLISHING_METADATA_FIELDS = (
    "title",
    "description",
    "tags",
    "chapters",
    "end_screen",
    "cards",
    "platform_overrides",
)

EXPORT_PRESET_FIELDS = (
    "preset_id",
    "name",
    "resolution",
    "aspect_ratio",
    "orientation",         # vertical | horizontal | square
    "container",
    "video_codec",
    "audio_codec",
    "fps",
    "hdr",
    "platform",
)

PLATFORM_EXPORT_FIELDS = (
    "platform",
    "aspect_ratio",
    "safe_zones",
    "caption_placement",
    "intro_length_sec",
    "outro_length_sec",
    "cta_timing",
    "export_preset_id",
)

PROVIDER_INSTRUCTION_FIELDS = (
    "provider",
    "operation",
    "parameters",
    "priority",
    "notes",
)

# The complete PostProductionPackage written to ContentPackage.post_production_package.
POST_PRODUCTION_PACKAGE_FIELDS = (
    "post_production_package_version",
    "engine_version",
    "project_id",
    "title",
    "edit_timeline",
    "scene_cuts",
    "audio_mix",
    "caption_timeline",
    "subtitle_styling",
    "motion_graphics",
    "transitions",
    "effects",
    "color_grading",
    "quality_report",
    "publishing_metadata",
    "provider_instructions",
    "platform_exports",
    "export_presets",
    "production_readiness",
    "validation",
    "generated_at",
)

POST_PRODUCTION_SUMMARY_FIELDS = (
    "engine_version",
    "status",
    "items",
    "packages",
    "ready",
    "needs_review",
    "incomplete",
    "average_readiness",
    "issues_found",
    "generated_at",
)
