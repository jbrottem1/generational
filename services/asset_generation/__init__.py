"""Universal Asset Generation — Agent 14's asset production layer.

The generation department of the OS: transforms structured creative
requests (Creative Studio asset requirements, thumbnail concepts, scene
plans) into production-ready visual assets through swappable AI provider
adapters. Every image, illustration, thumbnail, texture, video clip, and
future media asset the platform uses originates here.

Public surface:
    from services.asset_generation import build_asset_package, generate_items
    from services.asset_generation import batch_generate, submit_generate
"""

from services.asset_generation.batch import batch_generate
from services.asset_generation.cache import (
    FINGERPRINT_FIELDS,
    cached_copy,
    compute_fingerprint,
    lookup_cached_asset,
)
from services.asset_generation.catalog import (
    CATALOG_VERSION,
    all_asset_types,
    asset_class_of,
    asset_type_ids,
    get_asset_type,
    register_asset_type,
    resolve_asset_type,
)
from services.asset_generation.characters import (
    build_character_index,
    character_reference,
    character_references_for,
    scene_character_map,
)
from services.asset_generation.config import (
    SELECTION_STRATEGIES,
    AssetGenerationConfig,
    configure,
    get_asset_generation_config,
    reset_asset_generation_config,
)
from services.asset_generation.generator import generate_asset
from services.asset_generation.metadata import build_asset_metadata
from services.asset_generation.models import (
    ASSET_FIELDS,
    ASSET_GENERATION_ENGINE_VERSION,
    ASSET_METADATA_FIELDS,
    ASSET_PACKAGE_FIELDS,
    ASSET_PACKAGE_VERSION,
    ASSET_QUALITY_FIELDS,
    ASSET_SUMMARY_FIELDS,
    ASSET_VERSION_FIELDS,
    BATCH_RESULT_FIELDS,
    GENERATION_JOB_FIELDS,
    GENERATION_REQUEST_FIELDS,
    PROMPT_SPEC_FIELDS,
    USAGE_EVENT_FIELDS,
    AssetStatus,
    JobStatus,
    PackageReadiness,
)
from services.asset_generation.package import (
    build_asset_package,
    collect_generation_items,
    generate_items,
)
from services.asset_generation.prompts import (
    compile_prompt,
    optimize_for_provider,
    prompt_completeness,
)
from services.asset_generation.quality import (
    check_safety,
    package_readiness,
    validate_asset,
    validate_asset_package,
)
from services.asset_generation.queue import (
    ASSET_JOB_TYPES,
    JOB_TYPE_BATCH,
    JOB_TYPE_GENERATE,
    JOB_TYPE_PACKAGE,
    ensure_asset_job_handlers,
    run_generate,
    submit_batch,
    submit_generate,
    submit_package,
)
from services.asset_generation.registry import AssetRegistry, get_asset_registry
from services.asset_generation.requests import collect_generation_requests
from services.asset_generation.selection import (
    STRATEGY_WEIGHTS,
    candidate_providers,
    score_provider,
    select_providers,
    selection_overview,
)
from services.asset_generation.styles import (
    STYLE_PACK_FIELDS,
    all_style_packs,
    get_style_pack,
    register_style_pack,
    style_negative_fragment,
    style_prompt_fragment,
)
from services.asset_generation.usage import (
    UsageTracker,
    get_usage_tracker,
    reset_usage_tracker,
    summarize_jobs,
)

__all__ = [
    "ASSET_FIELDS",
    "ASSET_GENERATION_ENGINE_VERSION",
    "ASSET_JOB_TYPES",
    "ASSET_METADATA_FIELDS",
    "ASSET_PACKAGE_FIELDS",
    "ASSET_PACKAGE_VERSION",
    "ASSET_QUALITY_FIELDS",
    "ASSET_SUMMARY_FIELDS",
    "ASSET_VERSION_FIELDS",
    "BATCH_RESULT_FIELDS",
    "CATALOG_VERSION",
    "FINGERPRINT_FIELDS",
    "GENERATION_JOB_FIELDS",
    "GENERATION_REQUEST_FIELDS",
    "JOB_TYPE_BATCH",
    "JOB_TYPE_GENERATE",
    "JOB_TYPE_PACKAGE",
    "PROMPT_SPEC_FIELDS",
    "SELECTION_STRATEGIES",
    "STRATEGY_WEIGHTS",
    "STYLE_PACK_FIELDS",
    "USAGE_EVENT_FIELDS",
    "AssetGenerationConfig",
    "AssetRegistry",
    "AssetStatus",
    "JobStatus",
    "PackageReadiness",
    "UsageTracker",
    "all_asset_types",
    "all_style_packs",
    "asset_class_of",
    "asset_type_ids",
    "batch_generate",
    "build_asset_metadata",
    "build_asset_package",
    "build_character_index",
    "cached_copy",
    "candidate_providers",
    "character_reference",
    "character_references_for",
    "check_safety",
    "collect_generation_items",
    "collect_generation_requests",
    "compile_prompt",
    "compute_fingerprint",
    "configure",
    "ensure_asset_job_handlers",
    "generate_asset",
    "generate_items",
    "get_asset_generation_config",
    "get_asset_registry",
    "get_asset_type",
    "get_style_pack",
    "get_usage_tracker",
    "lookup_cached_asset",
    "optimize_for_provider",
    "package_readiness",
    "prompt_completeness",
    "register_asset_type",
    "register_style_pack",
    "reset_asset_generation_config",
    "reset_usage_tracker",
    "resolve_asset_type",
    "run_generate",
    "scene_character_map",
    "score_provider",
    "select_providers",
    "selection_overview",
    "style_negative_fragment",
    "style_prompt_fragment",
    "submit_batch",
    "submit_generate",
    "submit_package",
    "summarize_jobs",
    "validate_asset",
    "validate_asset_package",
]
