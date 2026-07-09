"""Variant generation and validation for the Optimization Laboratory.

Generates competing alternatives for any experiment type — deterministic
heuristic recombinations of the base content (the same Demo Mode
convention every other engine follows), plus pass-through of variants
upstream engines already produced (script variants, thumbnail concepts,
optimized titles). Every variant carries a unique id, version, metadata,
generation source, and generation confidence.

Validation flags duplicates, missing/empty content, and undersized groups
— findings are warnings the caller degrades on, never exceptions.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from engines.heuristics import stable_jitter
from services.optimization.config import all_experiment_types, get_optimization_config
from services.optimization.models import VARIANT_VERSION


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_variant(
    experiment_type: str,
    content,
    label: str = "",
    metadata: "dict | None" = None,
    generation_source: str = "heuristic",
    confidence: int = 50,
) -> dict:
    """One VARIANT_FIELDS dict — the atom of every experiment."""
    return {
        "variant_id": f"var_{uuid.uuid4().hex[:10]}",
        "experiment_type": experiment_type,
        "version": VARIANT_VERSION,
        "content": content,
        "label": label or f"{experiment_type}_variant",
        "metadata": dict(metadata or {}),
        "generation_source": generation_source,
        "confidence": int(confidence),
        "score": 0,
        "score_breakdown": {},
        "rank": 0,
        "created_at": _now_iso(),
    }


# --------------------------------------------------------------- templates
#
# Deterministic style transforms per experiment type. Text types rewrite
# the base string through named angles; structured types emit style dicts.
# Real generative backends can replace these through the provider layer
# without changing any caller.

_TEXT_ANGLES = [
    ("question", "What if {base}?", 62),
    ("secret", "The secret behind {base}", 60),
    ("negative", "Why {base} is not what you think", 58),
    ("numbered", "3 things nobody tells you about {base}", 57),
    ("challenge", "Everything you know about {base} is wrong", 56),
    ("urgency", "Before you scroll past: {base}", 52),
    ("identity", "If you care about {base}, watch this", 52),
    ("story", "Here's what happened when we looked into {base}", 50),
    ("authority", "Researchers just explained {base}", 55),
    ("payoff", "{base} — and here's why it matters", 51),
    ("contrast", "{base} vs. what actually works", 53),
    ("curiosity", "Nobody talks about this part of {base}", 58),
    ("direct", "{base}", 48),
    ("reveal", "We finally know the truth about {base}", 54),
    ("visual", "Watch what happens with {base}", 51),
    ("community", "We tested {base} so you don't have to", 50),
    ("myth", "The biggest myth about {base}", 57),
    ("timeline", "{base}: what changes in the next 30 days", 49),
    ("emotion", "This changes how you'll see {base} forever", 55),
    ("proof", "The data behind {base} surprised everyone", 54),
    ("insider", "What insiders know about {base}", 53),
    ("mistake", "The #1 mistake people make with {base}", 56),
    ("simple", "{base}, explained simply", 47),
    ("stakes", "Why {base} matters more than you think", 52),
    ("first", "The first thing to understand about {base}", 49),
]

_STYLE_VARIANTS = {
    "thumbnail": [
        ("close_up_face", {"composition": "close-up face", "emotion": "shock"}),
        ("bold_text", {"composition": "bold 3-word text", "emotion": "curiosity"}),
        ("before_after", {"composition": "split before/after", "emotion": "surprise"}),
        ("object_focus", {"composition": "hero object on clean background", "emotion": "intrigue"}),
        ("arrow_highlight", {"composition": "arrow + circled detail", "emotion": "urgency"}),
        ("contrast_colors", {"composition": "high-contrast complementary colors", "emotion": "energy"}),
        ("minimal", {"composition": "single subject, negative space", "emotion": "calm authority"}),
        ("reaction", {"composition": "reaction face + subject", "emotion": "empathy"}),
        ("number_overlay", {"composition": "large number overlay", "emotion": "specificity"}),
        ("question_mark", {"composition": "subject + question mark", "emotion": "curiosity"}),
        ("dark_mode", {"composition": "dark background, neon accent", "emotion": "mystery"}),
        ("zoomed_detail", {"composition": "extreme zoom on detail", "emotion": "novelty"}),
        ("side_by_side", {"composition": "two subjects side by side", "emotion": "comparison"}),
        ("hand_pointing", {"composition": "hand pointing at subject", "emotion": "direction"}),
        ("progress_bar", {"composition": "progress/transformation bar", "emotion": "anticipation"}),
        ("red_circle", {"composition": "red circle around anomaly", "emotion": "alarm"}),
        ("text_top", {"composition": "text banner top third", "emotion": "clarity"}),
        ("emoji_accent", {"composition": "single emoji accent", "emotion": "playfulness"}),
        ("depth_blur", {"composition": "sharp subject, blurred depth", "emotion": "focus"}),
        ("collage", {"composition": "three-panel collage", "emotion": "abundance"}),
        ("silhouette", {"composition": "backlit silhouette", "emotion": "drama"}),
        ("macro_texture", {"composition": "macro texture background", "emotion": "tactility"}),
        ("warning_style", {"composition": "warning-tape framing", "emotion": "caution"}),
        ("bright_face", {"composition": "bright face + bold color block", "emotion": "positivity"}),
        ("freeze_frame", {"composition": "mid-action freeze frame", "emotion": "kinetic energy"}),
    ],
    "narration_style": [
        ("documentary", {"tone": "measured authority", "pace": "medium"}),
        ("conversational", {"tone": "friendly direct-address", "pace": "medium-fast"}),
        ("dramatic", {"tone": "high-tension storytelling", "pace": "variable"}),
        ("energetic", {"tone": "upbeat hype", "pace": "fast"}),
        ("calm_explainer", {"tone": "soft reassuring teacher", "pace": "slow"}),
        ("whisper", {"tone": "intimate low-volume", "pace": "slow"}),
        ("news_anchor", {"tone": "crisp broadcast", "pace": "medium"}),
        ("first_person", {"tone": "personal confession", "pace": "medium"}),
    ],
    "animation_style": [
        ("kinetic_type", {"style": "kinetic typography"}),
        ("smooth_zoom", {"style": "slow push-in zooms"}),
        ("whip_pan", {"style": "whip-pan scene transitions"}),
        ("parallax", {"style": "2.5D parallax stills"}),
        ("stop_motion", {"style": "stop-motion rhythm"}),
        ("glitch", {"style": "glitch cut accents"}),
    ],
    "visual_pacing": [
        ("rapid", {"cuts_per_10s": 6, "profile": "rapid"}),
        ("standard", {"cuts_per_10s": 4, "profile": "standard"}),
        ("breathing", {"cuts_per_10s": 2, "profile": "breathing room"}),
        ("accelerating", {"cuts_per_10s": 3, "profile": "slow start, fast finish"}),
        ("front_loaded", {"cuts_per_10s": 5, "profile": "fast hook, steady body"}),
    ],
    "music_style": [
        ("cinematic_rise", {"genre": "cinematic", "energy": "building"}),
        ("lofi", {"genre": "lo-fi", "energy": "low"}),
        ("electronic_pulse", {"genre": "electronic", "energy": "high"}),
        ("orchestral", {"genre": "orchestral", "energy": "medium"}),
        ("percussion_only", {"genre": "percussion", "energy": "medium-high"}),
        ("no_music", {"genre": "none", "energy": "none"}),
    ],
    "sound_design": [
        ("whoosh_accents", {"sfx": "whoosh transitions"}),
        ("ui_ticks", {"sfx": "tick/pop emphasis"}),
        ("ambient_bed", {"sfx": "ambient environmental bed"}),
        ("impact_hits", {"sfx": "impact hits on reveals"}),
        ("minimal", {"sfx": "narration-only, sparse accents"}),
    ],
    "cta_placement": [
        ("end_standard", {"position": "end", "style": "direct ask"}),
        ("end_soft", {"position": "end", "style": "soft invitation"}),
        ("mid_roll", {"position": "middle", "style": "mid-content reminder"}),
        ("early_tease", {"position": "first_third", "style": "early tease + end ask"}),
        ("comment_bait", {"position": "end", "style": "question for comments"}),
        ("follow_loop", {"position": "end", "style": "series follow loop"}),
        ("pinned_comment", {"position": "pinned_comment", "style": "CTA in pinned comment"}),
        ("caption_only", {"position": "caption", "style": "CTA in caption text"}),
        ("double_tap", {"position": "middle", "style": "engagement action ask"}),
        ("no_cta", {"position": "none", "style": "no explicit CTA"}),
    ],
    "publishing_time": [
        ("morning_commute", {"hour_utc": 12, "window": "morning commute"}),
        ("lunch", {"hour_utc": 17, "window": "lunch break"}),
        ("after_school", {"hour_utc": 20, "window": "after school"}),
        ("prime_time", {"hour_utc": 0, "window": "evening prime time (US)"}),
        ("late_night", {"hour_utc": 3, "window": "late night"}),
        ("weekend_morning", {"hour_utc": 14, "window": "weekend morning"}),
    ],
    "publishing_schedule": [
        ("daily", {"cadence": "daily", "posts_per_week": 7}),
        ("weekdays", {"cadence": "weekdays", "posts_per_week": 5}),
        ("three_per_week", {"cadence": "mwf", "posts_per_week": 3}),
        ("burst", {"cadence": "3-day burst then rest", "posts_per_week": 3}),
    ],
    "localization": [
        ("none", {"strategy": "source language only"}),
        ("captions_translated", {"strategy": "translated captions"}),
        ("full_dub", {"strategy": "dubbed narration (placeholder)"}),
        ("regional_metadata", {"strategy": "localized titles/descriptions"}),
    ],
    "language": [
        ("en", {"language": "en"}),
        ("es", {"language": "es"}),
        ("pt", {"language": "pt"}),
        ("hi", {"language": "hi"}),
        ("fr", {"language": "fr"}),
        ("de", {"language": "de"}),
    ],
    "brand_style": [
        ("bold_saturated", {"palette": "bold saturated", "voice": "confident"}),
        ("clean_minimal", {"palette": "clean minimal", "voice": "expert"}),
        ("warm_editorial", {"palette": "warm editorial", "voice": "storyteller"}),
        ("high_contrast", {"palette": "black/white + accent", "voice": "provocative"}),
    ],
    "character_style": [
        ("faceless_voiceover", {"presenter": "none", "style": "faceless voiceover"}),
        ("animated_host", {"presenter": "animated character", "style": "mascot host"}),
        ("ai_avatar", {"presenter": "ai avatar", "style": "virtual presenter (placeholder)"}),
        ("hands_only", {"presenter": "hands only", "style": "demonstration"}),
    ],
    "platform_formatting": [
        ("shorts_vertical", {"platform": "youtube_shorts", "format": "9:16 <60s"}),
        ("tiktok_native", {"platform": "tiktok", "format": "9:16 native text"}),
        ("reels_polished", {"platform": "instagram", "format": "9:16 polished"}),
        ("long_form", {"platform": "youtube", "format": "16:9 long-form"}),
    ],
    "scene_ordering": [
        ("chronological", {"order": "chronological"}),
        ("payoff_first", {"order": "payoff first, then how"}),
        ("cold_open", {"order": "cold open mid-action"}),
        ("question_loop", {"order": "question → evidence → answer"}),
        ("reverse", {"order": "end state first, rewind"}),
    ],
}

_TEXT_TYPES = ("hook", "title", "description", "caption")


def _text_variants(experiment_type: str, base: str, count: int) -> list:
    base_text = (base or "this topic").strip().rstrip(".!?")
    offset = stable_jitter(f"{experiment_type}:{base_text}", span=len(_TEXT_ANGLES))
    variants = []
    for index in range(count):
        angle, template, confidence = _TEXT_ANGLES[(offset + index) % len(_TEXT_ANGLES)]
        text = template.format(base=base_text)
        if experiment_type == "description":
            text = f"{text}. {base_text.capitalize()} — the full story, sources included."
        elif experiment_type == "caption":
            text = f"{text} 👇 Save this for later."
        variants.append(
            make_variant(
                experiment_type,
                text,
                label=angle,
                metadata={"angle": angle, "template": template},
                generation_source="heuristic",
                confidence=confidence,
            )
        )
    return variants


def _style_variants(experiment_type: str, count: int) -> list:
    styles = _STYLE_VARIANTS.get(experiment_type, [])
    variants = []
    for index in range(min(count, len(styles)) if styles else 0):
        label, payload = styles[index]
        variants.append(
            make_variant(
                experiment_type,
                dict(payload),
                label=label,
                metadata={"style": label},
                generation_source="heuristic",
                confidence=50 + stable_jitter(f"{experiment_type}:{label}", span=12),
            )
        )
    return variants


def generate_variants(
    experiment_type: str,
    base_content="",
    count: "int | None" = None,
    upstream_variants: "list | None" = None,
    config=None,
) -> dict:
    """A VARIANT_GROUP_FIELDS dict: control + generated + upstream variants.

    The base content always joins as the "control" variant so every
    experiment measures against the incumbent. Unknown experiment types
    raise ValueError (register future types via
    `configure(extra_experiment_types=[...])`).
    """
    config = config or get_optimization_config()
    if experiment_type not in all_experiment_types(config):
        raise ValueError(
            f"Unknown experiment type {experiment_type!r}. "
            f"Valid: {all_experiment_types(config)} "
            "(register future types via configure(extra_experiment_types=...))."
        )
    count = count if count is not None else config.variant_count(experiment_type)
    count = max(2, min(int(count), config.max_variants_per_type))

    variants: list = []
    if base_content:
        variants.append(
            make_variant(
                experiment_type, base_content, label="control",
                metadata={"role": "control"},
                generation_source="control", confidence=60,
            )
        )
    for upstream in upstream_variants or []:
        content = upstream.get("content", upstream) if isinstance(upstream, dict) else upstream
        variants.append(
            make_variant(
                experiment_type, content,
                label=str(upstream.get("label", "upstream")) if isinstance(upstream, dict) else "upstream",
                metadata=dict(upstream.get("metadata", {})) if isinstance(upstream, dict) else {},
                generation_source="upstream",
                confidence=int(upstream.get("confidence", 55)) if isinstance(upstream, dict) else 55,
            )
        )

    remaining = max(0, count - len(variants))
    if experiment_type in _TEXT_TYPES:
        variants.extend(_text_variants(experiment_type, str(base_content), remaining))
    else:
        generated = _style_variants(experiment_type, remaining)
        if not generated and remaining and not variants:
            # Future/unstyled type with no base: still produce a minimal pair
            # so the experiment framework stays usable.
            generated = [
                make_variant(experiment_type, {"option": chr(ord("a") + i)}, label=f"option_{i}")
                for i in range(max(2, remaining))
            ]
        variants.extend(generated)

    group = {
        "group_id": f"grp_{uuid.uuid4().hex[:10]}",
        "experiment_type": experiment_type,
        "base_content": base_content,
        "variants": variants,
        "warnings": [],
        "created_at": _now_iso(),
    }
    group["warnings"] = validate_variant_group(group)
    return group


# -------------------------------------------------------------- validation


def _normalize(content) -> str:
    if isinstance(content, dict):
        return " ".join(f"{k}={v}" for k, v in sorted(content.items())).lower()
    return " ".join(str(content).lower().split())


def _similarity(a: str, b: str) -> float:
    """Cheap token-overlap similarity (Jaccard) — no dependencies."""
    tokens_a, tokens_b = set(a.split()), set(b.split())
    if not tokens_a or not tokens_b:
        return 1.0 if tokens_a == tokens_b else 0.0
    return len(tokens_a & tokens_b) / len(tokens_a | tokens_b)


def find_duplicates(variants: list, threshold: "float | None" = None) -> list:
    """(variant_id_a, variant_id_b) pairs whose contents near-duplicate."""
    threshold = threshold if threshold is not None else get_optimization_config().duplicate_similarity
    normalized = [(v["variant_id"], _normalize(v.get("content", ""))) for v in variants]
    pairs = []
    for i in range(len(normalized)):
        for j in range(i + 1, len(normalized)):
            if _similarity(normalized[i][1], normalized[j][1]) >= threshold:
                pairs.append((normalized[i][0], normalized[j][0]))
    return pairs


def validate_variant_group(group: dict) -> list:
    """Quality findings for one variant group (empty list = valid).

    Findings are warnings the experiment manager degrades on — duplicates
    are dropped, empty-content variants excluded, undersized groups become
    INSUFFICIENT_DATA experiments. Never raises.
    """
    problems = []
    variants = group.get("variants", [])
    if len(variants) < 2:
        problems.append("group has fewer than two variants — nothing to compare")
    empty = [v["variant_id"] for v in variants if not _normalize(v.get("content", ""))]
    if empty:
        problems.append(f"variants with empty content: {', '.join(empty)}")
    duplicates = find_duplicates(variants)
    if duplicates:
        pairs = "; ".join(f"{a}≈{b}" for a, b in duplicates)
        problems.append(f"near-duplicate variants: {pairs}")
    ids = [v["variant_id"] for v in variants]
    if len(ids) != len(set(ids)):
        problems.append("variant ids are not unique")
    return problems


def dedupe_variants(variants: list, threshold: "float | None" = None) -> list:
    """Variants with near-duplicates removed (first occurrence wins)."""
    duplicates = find_duplicates(variants, threshold=threshold)
    drop = {b for _a, b in duplicates}
    return [v for v in variants if v["variant_id"] not in drop]
