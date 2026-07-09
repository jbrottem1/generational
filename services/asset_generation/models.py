"""Data contracts for the Universal Asset Generation Engine (Agent 14).

Field tuples are the testable contract (same convention as the Render,
Publishing, Analytics, and Creative Studio engines). Everything the
engine emits is a plain JSON-safe dict so the workflow context,
ContentPackage slots, and the UI can carry it without conversion.

Contract rules (DATA_CONTRACTS.md): additive-only from 1.0 on — append
fields freely, never remove, rename, or repurpose existing ones.
"""

from __future__ import annotations

ASSET_GENERATION_ENGINE_VERSION = "1.0.0"

# Version of the AssetPackage written into each ContentPackage
# `asset_package` slot.
ASSET_PACKAGE_VERSION = "1.0"


class AssetStatus:
    """Lifecycle of one generated asset."""

    GENERATED = "generated"       # freshly produced by a provider
    CACHED = "cached"             # served from the asset cache (no generation)
    PLACEHOLDER = "placeholder"   # deterministic mock output (Demo Mode)
    BLOCKED = "blocked"           # safety rules stopped generation
    FAILED = "failed"             # every provider attempt failed

    ALL = (GENERATED, CACHED, PLACEHOLDER, BLOCKED, FAILED)


class JobStatus:
    """Outcome of one generation job."""

    SUCCEEDED = "succeeded"
    CACHE_HIT = "cache_hit"
    BLOCKED = "blocked"
    FAILED = "failed"

    ALL = (SUCCEEDED, CACHE_HIT, BLOCKED, FAILED)


class PackageReadiness:
    """Lifecycle of one AssetPackage (same vocabulary as the Creative
    Studio's production readiness, so Render can gate on either)."""

    READY = "ready"
    NEEDS_REVIEW = "needs_review"
    INCOMPLETE = "incomplete"

    ALL = (READY, NEEDS_REVIEW, INCOMPLETE)


# One normalized generation request — what the engine plans to generate.
# Built from Creative Studio asset requirements, thumbnail concepts, and
# (fallback) scene breakdowns; every request is provider-agnostic.
GENERATION_REQUEST_FIELDS = (
    "asset_id",
    "project_id",
    "scene_id",
    "asset_type",              # catalog type id (catalog.py)
    "asset_class",             # image | video | three_d
    "category",                # scene_visual | character | background | ...
    "description",
    "prompt",                  # the raw creative prompt (pre-compilation)
    "style",                   # style id the asset must respect
    "priority",                # required | recommended | optional
    "reusable",                # True → shareable across scenes/productions
    "aspect_ratio",
    "resolution",
    "duration_sec",            # video/animation targets ("" / 0 for stills)
    "character_ids",           # persistent characters that must appear
    "lighting",
    "color_palette",
    "mood",
    "emotion",
    "camera",
    "brand_id",
    "source",                  # creative_studio | thumbnail | fallback
)

# One compiled prompt specification — the Prompt Compiler's output, in
# canonical form; provider optimization rewrites `prompt` per dialect.
PROMPT_SPEC_FIELDS = (
    "prompt",
    "negative_prompt",
    "style",
    "lighting",
    "camera",
    "lens",
    "composition",
    "mood",
    "emotion",
    "color_palette",
    "aspect_ratio",
    "resolution",
    "character_references",    # visual signatures embedded verbatim
    "environment_references",
    "brand_style",
    "provider",                # "" until optimized for a specific backend
    "provider_hints",          # the dialect metadata the optimizer applied
)

# One generated asset reference — what providers return, quality-checked
# and registered. This is the atom of the AssetPackage.
ASSET_FIELDS = (
    "asset_id",
    "asset_type",
    "asset_class",
    "scene_id",
    "project_id",
    "uri",
    "provider",
    "model",
    "format",
    "width",
    "height",
    "duration_sec",
    "prompt_spec",             # PROMPT_SPEC_FIELDS dict actually used
    "fingerprint",             # content-address of the request (cache key)
    "version",                 # 1, 2, 3... — regenerations append versions
    "status",                  # AssetStatus value
    "placeholder",
    "cached",
    "quality",                 # ASSET_QUALITY_FIELDS dict
    "reusable",
    "priority",
    "category",
    "created_at",
)

# One registry version entry — every regeneration of an asset_id is kept.
ASSET_VERSION_FIELDS = (
    "version",
    "fingerprint",
    "uri",
    "provider",
    "status",
    "created_at",
)

# One generation job — the auditable record of how one request was served.
GENERATION_JOB_FIELDS = (
    "job_id",
    "asset_id",
    "asset_type",
    "asset_class",
    "provider",                # the provider that ultimately served it
    "providers_tried",         # selection order actually attempted
    "attempts",
    "status",                  # JobStatus value
    "cache_hit",
    "cost_estimate",
    "error",
    "created_at",
)

# Per-asset quality analysis — findings, never exceptions.
ASSET_QUALITY_FIELDS = (
    "status",                  # passed | warning | failed
    "confidence",              # 0-100 generation confidence
    "checks",                  # name → pass/fail detail
    "warnings",
    "blockers",
    "safety_flags",
    "duplicate_of",            # asset_id this duplicates ("" = unique)
)

# The AssetPackage — the complete generated-asset deliverable written into
# each ContentPackage `asset_package` slot.
ASSET_PACKAGE_FIELDS = (
    "asset_package_version",
    "engine_version",
    "project_id",
    "assets",                  # list of ASSET_FIELDS dicts (everything)
    "scene_assets",            # scene_id → [asset_ids]
    "character_assets",        # character/reference-sheet asset ids
    "thumbnail_assets",        # thumbnail asset ids
    "marketing_assets",        # logos, branding, marketing graphic ids
    "video_assets",            # video-class asset ids
    "generation_jobs",         # list of GENERATION_JOB_FIELDS dicts
    "provider_usage",          # provider name → assets served
    "selection_strategy",      # the strategy the run used
    "cache_report",            # {hits, misses, reuse_ratio}
    "cost_report",             # {estimated_total, limit, within_budget, rerouted}
    "quality_report",          # aggregate QC over all assets
    "validation",              # package-level findings (never raises)
    "readiness",               # {score, status, blockers}
    "asset_diagnostics",       # counts by type/class/status
    "generated_at",
)

# The aggregate summary returned to the orchestrator on the
# `asset_generation_summary` context key.
ASSET_SUMMARY_FIELDS = (
    "engine_version",
    "status",                  # generated | no_items
    "items",
    "packages",
    "assets_generated",
    "cache_hits",
    "placeholders",
    "failures",
    "providers_used",
    "ready",
    "needs_review",
    "incomplete",
    "average_readiness",
    "generated_at",
)


def readiness_status(score: int, blockers: list) -> str:
    """Map a 0-100 readiness score + blockers onto a PackageReadiness."""
    if blockers:
        return PackageReadiness.INCOMPLETE
    if score >= 80:
        return PackageReadiness.READY
    return PackageReadiness.NEEDS_REVIEW
