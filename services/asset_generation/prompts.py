"""Prompt Compiler — structured creative requests become optimized prompts.

Two passes, both deterministic:

1. `compile_prompt(request, item)` builds ONE canonical, provider-agnostic
   `PROMPT_SPEC_FIELDS` dict from the structured request: subject, style
   pack fragment, lighting, camera/lens, composition, mood, emotion,
   color palette, aspect ratio, resolution, verbatim character reference
   blocks, environment references, brand style, and negative prompt.
2. `optimize_for_provider(spec, provider)` rewrites the canonical spec
   into the target backend's dialect using the provider's declared
   `prompt_style` hints (tagged vs natural language vs cinematic ordering,
   negative-prompt support, parameter suffixes) — the ONLY place provider
   dialects are applied, and they come from the adapter, never from
   engine code.

Determinism matters: identical requests must compile to identical prompts
so the asset cache fingerprints hold across runs.
"""

from __future__ import annotations

from services.asset_generation.characters import build_character_index, character_references_for
from services.asset_generation.styles import style_negative_fragment, style_prompt_fragment

# Baseline negatives applied to every generation, before style/config ones.
BASE_NEGATIVE_TERMS = (
    "low quality",
    "blurry",
    "distorted anatomy",
    "watermark",
    "text artifacts",
)


def compile_prompt(request: dict, item: "dict | None" = None) -> dict:
    """One canonical PROMPT_SPEC_FIELDS dict for one generation request."""
    item = item or {}
    style_id = str(request.get("style", ""))
    character_index = build_character_index(item)
    character_references = character_references_for(
        list(request.get("character_ids", []) or []), character_index
    )

    environment_references = []
    environment = str(request.get("environment", "") or "").strip()
    if environment:
        environment_references.append(environment)

    brand_style = _brand_style(item)

    subject = str(request.get("prompt") or request.get("description") or "").strip()
    fragments = [subject]
    style_fragment = style_prompt_fragment(style_id)
    if style_fragment:
        fragments.append(style_fragment)
    for key in ("lighting", "color_palette", "mood", "emotion"):
        value = str(request.get(key, "") or "").strip()
        if value:
            fragments.append(value)
    camera = str(request.get("camera", "") or "").strip()
    if camera:
        fragments.append(camera)
    fragments.extend(f"featuring {reference}" for reference in character_references)
    fragments.extend(f"set in {reference}" for reference in environment_references)
    if brand_style:
        fragments.append(brand_style)

    negatives = list(BASE_NEGATIVE_TERMS)
    style_negative = style_negative_fragment(style_id)
    if style_negative:
        negatives.append(style_negative)

    return {
        "prompt": ", ".join(fragment for fragment in fragments if fragment),
        "negative_prompt": ", ".join(negatives),
        "style": style_id,
        "lighting": str(request.get("lighting", "") or ""),
        "camera": camera,
        "lens": str(request.get("lens", "") or ""),
        "composition": str(request.get("composition", "") or ""),
        "mood": str(request.get("mood", "") or ""),
        "emotion": str(request.get("emotion", "") or ""),
        "color_palette": str(request.get("color_palette", "") or ""),
        "aspect_ratio": str(request.get("aspect_ratio", "") or ""),
        "resolution": str(request.get("resolution", "") or ""),
        "character_references": character_references,
        "environment_references": environment_references,
        "brand_style": brand_style,
        "provider": "",
        "provider_hints": {},
    }


def optimize_for_provider(spec: dict, provider) -> dict:
    """The canonical spec rewritten for one backend's prompt dialect.

    Returns a NEW spec dict (the canonical one is never mutated) with
    `provider`, `provider_hints`, and a dialect-shaped `prompt` /
    `negative_prompt`.
    """
    hints = dict(getattr(provider, "prompt_style", {}) or {})
    optimized = dict(spec)
    optimized["provider"] = getattr(provider, "name", "")
    optimized["provider_hints"] = hints

    dialect = hints.get("dialect", "plain")
    prompt = spec.get("prompt", "")

    if dialect == "cinematic":
        # Camera language leads for video models.
        camera_parts = [part for part in (spec.get("camera"), spec.get("lens")) if part]
        if camera_parts:
            prompt = ", ".join(camera_parts) + ", " + prompt
    elif dialect == "natural_language":
        prompt = _to_sentence(prompt)

    if not hints.get("supports_negative_prompt", True) and spec.get("negative_prompt"):
        prompt = f"{prompt}. Avoid: {spec['negative_prompt']}."
        optimized["negative_prompt"] = ""

    if hints.get("parameter_suffix") and spec.get("aspect_ratio"):
        prompt = f"{prompt} --ar {spec['aspect_ratio']}"

    optimized["prompt"] = prompt
    return optimized


def prompt_completeness(spec: dict) -> int:
    """0-100: how fully specified one compiled prompt is (QC signal)."""
    signals = (
        bool(spec.get("prompt")),
        bool(spec.get("style")),
        bool(spec.get("lighting")),
        bool(spec.get("color_palette")),
        bool(spec.get("mood") or spec.get("emotion")),
        bool(spec.get("aspect_ratio")),
        bool(spec.get("resolution")),
        bool(spec.get("negative_prompt")),
    )
    return int(round(100 * sum(signals) / len(signals)))


def _brand_style(item: dict) -> str:
    """The brand's visual constraint sentence, from package data only."""
    brand = str(item.get("brand_id") or item.get("brand") or "").strip()
    creative = item.get("creative_package") or {}
    brand_colors = (creative.get("color_lighting_plan") or {}).get("brand_colors", "")
    parts = []
    if brand:
        parts.append(f"{brand} brand style")
    if brand_colors:
        parts.append(f"brand colors: {brand_colors}")
    return ", ".join(str(part) for part in parts if part)


def _to_sentence(prompt: str) -> str:
    text = prompt.strip()
    if not text:
        return text
    return text[0].upper() + text[1:]
