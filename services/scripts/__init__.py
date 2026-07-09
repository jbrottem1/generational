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
from services.scripts.models import REQUIRED_VARIANT_COMPONENTS, PlatformSpec, ScriptVariant
from services.scripts.platforms import (
    DEFAULT_PLATFORM,
    PLATFORM_SPECS,
    SCRIPT_PLATFORMS,
    get_platform_spec,
)
from services.scripts.scorer import VARIANT_SCORE_WEIGHTS, rank_variants, score_variant
from services.scripts.structure import STRUCTURED_SCRIPT_FIELDS, build_structured_script

__all__ = [
    "DEFAULT_PLATFORM",
    "DEFAULT_VARIANT_COUNT",
    "PLATFORM_SPECS",
    "PlatformSpec",
    "REQUIRED_VARIANT_COMPONENTS",
    "SCRIPT_PLATFORMS",
    "STRUCTURED_SCRIPT_FIELDS",
    "ScriptVariant",
    "VARIANT_SCORE_WEIGHTS",
    "VARIANT_STYLES",
    "build_structured_script",
    "estimate_runtime_sec",
    "finalize_variant",
    "generate_script_package",
    "generate_variants",
    "get_platform_spec",
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
) -> dict:
    """Generate + score script variants for one idea; return a JSON-safe package."""
    variants = generate_variants(
        idea,
        platform=platform,
        subject=subject,
        niche=niche,
        research=research,
        variant_count=variant_count,
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
