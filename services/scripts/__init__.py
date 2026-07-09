"""Script Generation service — the modular Script Engine.

Public API for turning any content idea into scored, platform-aware script
variants. The `script_generation` pipeline engine is a thin wrapper around
this module; it is equally usable standalone (e.g. re-scripting an approved
idea for a different platform):

    from services.scripts import generate_script_package

    package = generate_script_package(idea, platform="tiktok",
                                      subject="black holes", niche="Science")
    best = package["best_variant"]

Supported platforms: YouTube Shorts, TikTok, Instagram Reels, Facebook
Reels, X video, and long-form YouTube (`services/scripts/platforms.py`).
"""

from __future__ import annotations

from services.scripts.generator import (
    DEFAULT_VARIANT_COUNT,
    VARIANT_STYLES,
    estimate_runtime_sec,
    finalize_variant,
    generate_variants,
)
from services.scripts.hooks import HOOK_STYLES, generate_hook_candidates, rank_hooks
from services.scripts.models import (
    DEFAULT_LOCALE,
    REQUIRED_SCRIPT_SECTIONS,
    REQUIRED_SECTION_FIELDS,
    REQUIRED_VARIANT_COMPONENTS,
    SCRIPT_SECTION_KEYS,
    Locale,
    PlatformSpec,
    ScriptVariant,
)
from services.scripts.platforms import (
    DEFAULT_PLATFORM,
    PLATFORM_SPECS,
    SCRIPT_PLATFORMS,
    get_platform_spec,
)
from services.scripts.retention import build_retention_model
from services.scripts.scorer import VARIANT_SCORE_WEIGHTS, rank_variants, score_variant
from services.scripts.sections import SECTION_SPECS, build_section
from services.scripts.structure import STRUCTURED_SCRIPT_FIELDS, build_structured_script

__all__ = [
    "DEFAULT_LOCALE",
    "DEFAULT_PLATFORM",
    "DEFAULT_VARIANT_COUNT",
    "HOOK_STYLES",
    "Locale",
    "PLATFORM_SPECS",
    "PlatformSpec",
    "REQUIRED_SCRIPT_SECTIONS",
    "REQUIRED_SECTION_FIELDS",
    "REQUIRED_VARIANT_COMPONENTS",
    "SCRIPT_PLATFORMS",
    "SCRIPT_SECTION_KEYS",
    "SECTION_SPECS",
    "STRUCTURED_SCRIPT_FIELDS",
    "ScriptVariant",
    "VARIANT_SCORE_WEIGHTS",
    "VARIANT_STYLES",
    "build_retention_model",
    "build_section",
    "build_structured_script",
    "estimate_runtime_sec",
    "finalize_variant",
    "generate_hook_candidates",
    "generate_script_package",
    "generate_variants",
    "get_platform_spec",
    "rank_hooks",
    "rank_variants",
    "score_variant",
]


def generate_script_package(
    idea: dict,
    *,
    platform: str = DEFAULT_PLATFORM,
    subject: str = "",
    niche: str = "",
    research: "dict | None" = None,
    variant_count: int = DEFAULT_VARIANT_COUNT,
    locale: "Locale | dict | None" = None,
) -> dict:
    """Generate + score script variants for one idea; return a JSON-safe package."""
    variants = generate_variants(
        idea,
        platform=platform,
        subject=subject,
        niche=niche,
        research=research,
        variant_count=variant_count,
        locale=locale,
    )
    ranked = rank_variants(variants)
    best = ranked[0]
    spec = get_platform_spec(platform)
    return {
        "platform": spec.key,
        "variant_count": len(ranked),
        "variants": [variant.to_dict() for variant in ranked],
        "best_variant": best.to_dict(),
        "best_score": best.score,
        "structured_script": build_structured_script(idea, best, spec),
    }
