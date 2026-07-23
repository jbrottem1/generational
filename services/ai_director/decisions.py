"""Executive creative decision engine — deterministic strategy selection.

Consumes upstream intelligence (psychology, script, visual, audio, trend,
market, analytics signals) and emits structured creative direction. Does NOT
duplicate Agent 12's storyboard logic or Agent 4's shot psychology — only
sets the production strategy downstream agents execute against.
"""

from __future__ import annotations

from services.ai_director.models import ProductionPriority
from services.ai_director.policies import (
    get_policies,
    learning_boost,
    quality_tier_for_score,
)

# Format keyword signals for deterministic selection.
_FORMAT_SIGNALS = {
    "documentary": ("documentary", "history", "biography", "archive", "investigation"),
    "educational": ("learn", "tutorial", "how to", "explained", "science", "guide", "lesson"),
    "cartoon": ("cartoon", "animated", "character", "kids", "mascot", "comic"),
    "cinematic": ("cinematic", "epic", "story", "drama", "film", "trailer"),
    "podcast": ("podcast", "interview", "conversation", "audio", "discussion"),
    "livestream": ("live", "stream", "real-time", "breaking", "watch live"),
    "long_form": ("deep dive", "full documentary", "long form", "feature", "hour"),
}

_ORIENTATION_BY_FORMAT = {
    "short_form": "vertical",
    "long_form": "horizontal",
    "documentary": "horizontal",
    "educational": "vertical",
    "cartoon": "vertical",
    "cinematic": "horizontal",
    "podcast": "horizontal",
    "livestream": "vertical",
}


def _signal_text(item: dict, context: dict) -> str:
    """Aggregate searchable text from item + context intelligence."""
    parts = [
        str(item.get("topic", "")),
        str(item.get("niche", "")),
        str(item.get("title", "")),
        str(item.get("hook", "")),
        " ".join(str(k) for k in item.get("keywords", [])),
        str(item.get("script", ""))[:500],
        str(item.get("script_package", {}).get("script", ""))[:300],
    ]
    # Trend / market intelligence from context.
    for rec in (context.get("opportunity_recommendations") or [])[:3]:
        parts.append(str(rec.get("recommended_format", "")))
        parts.append(str(rec.get("hook_direction", "")))
    for opp in (context.get("market_opportunities") or [])[:3]:
        parts.append(str(opp.get("recommended_content_type", "")))
        parts.append(str(opp.get("content_nature", "")))
    return " ".join(parts).lower()


def _score(item: dict) -> int:
    return max(
        int(item.get("opportunity_score", 0) or 0),
        int(item.get("virality_score", 0) or 0),
        int(item.get("quality_score", 0) or 0),
        int(item.get("psychology_score", 0) or 0),
    )


def select_format(item: dict, context: dict, policies: dict | None = None) -> str:
    """Short vs long-form, documentary, educational, cartoon, etc."""
    policies = policies or get_policies()
    explicit = str(item.get("format", item.get("production_format", ""))).strip()
    if explicit in policies["format_weights"]:
        return explicit

    signals = _signal_text(item, context)
    weights = dict(policies["format_weights"])

    for fmt, keywords in _FORMAT_SIGNALS.items():
        hits = sum(1 for kw in keywords if kw in signals)
        if hits:
            weights[fmt] = weights.get(fmt, 0.5) + hits * 0.3

    # Trend recommendation boost.
    for rec in (context.get("opportunity_recommendations") or [])[:1]:
        rec_fmt = str(rec.get("recommended_format", "")).lower().replace(" ", "_")
        if rec_fmt in weights:
            weights[rec_fmt] = weights[rec_fmt] + 0.5 + learning_boost("format", rec_fmt, policies)

    # Duration hint → short vs long.
    dur = int(item.get("target_duration_sec", 0) or 0)
    if dur > 180:
        weights["long_form"] = weights.get("long_form", 0.6) + 0.4
    elif 0 < dur <= 90:
        weights["short_form"] = weights.get("short_form", 1.0) + 0.3

    best = max(weights, key=lambda k: weights[k])
    # Default to short_form for faceless content OS unless signals say otherwise.
    if weights[best] < 0.5:
        return policies["fallbacks"].get("format", "short_form")
    return best if best != "long_form" or weights["long_form"] > weights.get("short_form", 1.0) else "short_form"


def select_orientation(item: dict, fmt: str, platforms: list, policies: dict | None = None) -> str:
    """Vertical vs horizontal vs square."""
    policies = policies or get_policies()
    explicit = str(item.get("orientation", item.get("aspect_ratio", ""))).strip().lower()
    if explicit in ("vertical", "horizontal", "square"):
        return explicit
    if explicit in ("9:16", "4:5"):
        return "vertical"
    if explicit in ("16:9", "21:9"):
        return "horizontal"

    if platforms:
        primary = platforms[0].get("platform", "")
        orient_map = policies.get("platform_orientation", {})
        if primary in orient_map:
            return orient_map[primary]

    return _ORIENTATION_BY_FORMAT.get(fmt, policies["fallbacks"].get("orientation", "vertical"))


def select_platforms(item: dict, context: dict, fmt: str, policies: dict | None = None) -> list:
    """Target platforms with priority and constraints."""
    policies = policies or get_policies()
    raw = (
        item.get("target_platforms")
        or item.get("platforms")
        or policies.get("default_platforms", ["youtube_shorts"])
    )
    if isinstance(raw, str):
        raw = [raw]

    max_dur_map = policies.get("platform_max_duration", {})
    orient_map = policies.get("platform_orientation", {})
    targets = []

    for index, platform in enumerate(raw[:5]):
        platform = str(platform).strip()
        if not platform:
            continue
        boost = learning_boost("platform", platform, policies)
        targets.append({
            "platform": platform,
            "priority": "primary" if index == 0 else "secondary",
            "aspect_ratio": "9:16" if orient_map.get(platform) == "vertical" else "16:9",
            "max_duration_sec": max_dur_map.get(platform, 60 if fmt == "short_form" else 600),
            "caption_required": platform in ("tiktok", "instagram_reels", "youtube_shorts", "linkedin"),
            "hook_style": "pattern_interrupt" if index == 0 else "context_setter",
            "_score": 1.0 + boost,
        })

    if not targets:
        platform = policies["default_platforms"][0]
        targets.append({
            "platform": platform,
            "priority": "primary",
            "aspect_ratio": "9:16",
            "max_duration_sec": 60,
            "caption_required": True,
            "hook_style": "pattern_interrupt",
            "_score": 1.0,
        })

    # Sort by learning boost but preserve primary.
    primary = targets[0]
    rest = sorted(targets[1:], key=lambda t: t.get("_score", 0), reverse=True)
    result = [primary] + rest
    for t in result:
        t.pop("_score", None)
    return result


def build_production_strategy(item: dict, context: dict, fmt: str, orientation: str) -> dict:
    """Full production strategy block."""
    policies = get_policies()
    signals = _signal_text(item, context)
    score = _score(item)

    # Emotional intensity from psychology.
    psych = item.get("behavioral_intelligence") or item.get("psychology_report") or {}
    arousal = int(psych.get("arousal_score", psych.get("emotional_intensity", 0)) or 0)
    bands = policies.get("emotion_bands", {})
    if arousal >= bands.get("extreme", 90):
        intensity = "extreme"
    elif arousal >= bands.get("high", 75):
        intensity = "high"
    elif arousal >= bands.get("moderate", 50):
        intensity = "moderate"
    else:
        intensity = "low" if score < 60 else "moderate"

    # Visual complexity from format + score.
    if fmt in ("cinematic", "documentary") or score >= 85:
        complexity = "cinematic" if score >= 90 else "rich"
    elif fmt in ("cartoon", "educational"):
        complexity = "standard"
    else:
        complexity = "minimal" if score < 55 else "standard"

    # Content class.
    if fmt == "documentary":
        content_class = "documentary"
    elif fmt == "educational":
        content_class = "educational"
    elif "brand" in signals or item.get("brand_id"):
        content_class = "branded"
    else:
        content_class = "entertainment"

    # Narrative mode from script shape.
    beats = len(item.get("scene_breakdown") or [])
    if beats >= 5:
        narrative_mode = "storytelling"
    elif "how to" in signals or fmt == "educational":
        narrative_mode = "tutorial"
    elif beats <= 2:
        narrative_mode = "explainer"
    else:
        narrative_mode = "montage"

    caption = "full" if orientation == "vertical" else "key_moments"
    if fmt == "podcast":
        caption = "minimal"

    thumb = "text_overlay" if fmt == "educational" else "mystery"
    if intensity in ("high", "extreme"):
        thumb = "face_hook" if "character" in signals else "before_after"

    publish = str(item.get("publish_mode", context.get("publish_mode", "scheduled")))
    if publish not in ("immediate", "scheduled", "batch", "test_variant"):
        publish = "scheduled"

    return {
        "format": fmt,
        "orientation": orientation,
        "content_class": content_class,
        "narrative_mode": narrative_mode,
        "emotional_intensity": intensity,
        "visual_complexity": complexity,
        "caption_strategy": caption,
        "thumbnail_strategy": thumb,
        "publishing_strategy": publish,
        "rationale": (
            f"Format '{fmt}' selected from topic signals and intelligence; "
            f"{orientation} orientation for primary platform; "
            f"{intensity} emotional intensity from psychology score {arousal or score}."
        ),
    }


def select_creative_style(item: dict, fmt: str) -> dict:
    """High-level creative style direction."""
    niche = str(item.get("niche", "")).lower()
    style_map = {
        "science": ("science_visualization", "Scientific Clarity", "informative", "curious"),
        "history": ("documentary_grain", "Historical Documentary", "authoritative", "reflective"),
        "finance": ("minimal_corporate", "Corporate Minimal", "confident", "serious"),
        "entertainment": ("cinematic_bold", "Cinematic Bold", "engaging", "exciting"),
    }
    for key, preset in style_map.items():
        if key in niche or key in str(item.get("topic", "")).lower():
            return {
                "style_id": preset[0],
                "label": preset[1],
                "tone": preset[2],
                "mood": preset[3],
                "color_direction": "brand-aligned" if item.get("brand_id") else "topic-appropriate",
                "typography_direction": "bold sans" if fmt == "short_form" else "editorial serif",
            }
    return {
        "style_id": "minimal_modern",
        "label": "Minimal Modern",
        "tone": "conversational",
        "mood": "engaging",
        "color_direction": "high-contrast accents",
        "typography_direction": "clean sans-serif",
    }


def select_visual_style(item: dict, creative_style: dict, fmt: str) -> dict:
    """Visual production style — consumed by Creative Studio, not duplicated."""
    lighting = "natural documentary" if fmt == "documentary" else "studio three-point"
    if fmt == "cartoon":
        lighting = "flat illustrative"
    return {
        "style_id": creative_style["style_id"],
        "label": creative_style["label"],
        "lighting": lighting,
        "texture": "clean digital" if fmt in ("short_form", "educational") else "cinematic grain",
        "reference_mood": creative_style["mood"],
    }


def select_animation_style(fmt: str, complexity: str) -> dict:
    """Animation technique and motion language."""
    if fmt == "cartoon":
        technique, motion = "2d", "bouncy expressive"
    elif fmt == "cinematic":
        technique, motion = "live_action", "slow deliberate"
    elif fmt == "podcast":
        technique, motion = "motion_graphics", "subtle ambient"
    elif complexity == "minimal":
        technique, motion = "motion_graphics", "clean kinetic"
    else:
        technique, motion = "mixed_media", "dynamic layered"
    return {
        "style_id": f"{technique}_{fmt}",
        "technique": technique,
        "motion_language": motion,
        "transition_style": "hard cuts" if fmt == "short_form" else "dissolves and matched cuts",
    }


def build_camera_plan(fmt: str, orientation: str, intensity: str) -> dict:
    """Camera language plan — direction for Visual Intelligence / Creative Studio."""
    if fmt == "documentary":
        grammar = "observational handheld"
        shots = ["wide establishing", "medium interview", "detail insert"]
    elif fmt == "short_form":
        grammar = "mobile-native dynamic"
        shots = ["close-up hook", "medium explain", "wide context", "close-up payoff"]
    else:
        grammar = "cinematic coverage"
        shots = ["establishing wide", "medium two-shot", "close-up emphasis", "over-shoulder"]

    movement = "static with punch-ins" if intensity == "low" else "motivated movement"
    if fmt == "short_form":
        movement = "fast push-ins and whip pans"

    return {
        "camera_grammar": grammar,
        "dominant_shot_types": shots,
        "movement_profile": movement,
        "lens_character": "wide for vertical" if orientation == "vertical" else "standard cinematic",
    }


def build_pacing(fmt: str, item: dict, context: dict) -> dict:
    """Scene pacing — tempo, cut rate, retention curve."""
    presets = {
        "slow": {"tempo": "slow", "scene_target_sec": 8.0, "cuts_per_minute": 8},
        "measured": {"tempo": "measured", "scene_target_sec": 6.0, "cuts_per_minute": 10},
        "dynamic": {"tempo": "dynamic", "scene_target_sec": 4.0, "cuts_per_minute": 15},
        "rapid": {"tempo": "rapid", "scene_target_sec": 2.5, "cuts_per_minute": 24},
    }
    tempo = "dynamic" if fmt == "short_form" else "measured"
    if fmt == "documentary":
        tempo = "slow"
    elif fmt == "livestream":
        tempo = "rapid"

    for rec in (context.get("opportunity_recommendations") or [])[:1]:
        dur = int(rec.get("recommended_duration_sec", 0) or 0)
        if 0 < dur <= 45:
            tempo = "rapid"
        elif dur > 120:
            tempo = "slow"

    base = dict(presets[tempo])
    base["retention_curve"] = {
        "hook_density": "high" if fmt == "short_form" else "moderate",
        "mid_hold": "pattern_interrupts" if tempo in ("dynamic", "rapid") else "narrative_build",
        "payoff_punch": "strong" if fmt != "podcast" else "moderate",
    }
    return base


def build_shot_plan(item: dict, pacing: dict, fmt: str) -> dict:
    """High-level shot plan — beat structure, not scene-by-scene storyboard."""
    beats = item.get("scene_breakdown") or []
    beat_count = len(beats) or max(3, int(pacing["scene_target_sec"] * pacing["cuts_per_minute"] / 60))
    key_beats = []
    positions = ["hook", "development", "payoff"]
    if beat_count >= 5:
        positions = ["hook", "context", "escalation", "climax", "payoff"]

    for index, position in enumerate(positions[:min(len(positions), beat_count)]):
        key_beats.append({
            "position": position,
            "shot_type": "close-up" if position == "hook" else "medium",
            "purpose": f"{position} beat — retain attention" if fmt == "short_form" else f"{position} narrative beat",
        })

    return {
        "total_shots": beat_count,
        "shot_progression": "establish → develop → emphasize → resolve",
        "key_beats": key_beats,
        "b_roll_ratio": 0.3 if fmt == "documentary" else 0.15,
    }


def build_character_plan(item: dict, fmt: str) -> dict:
    """Character selection strategy — defers cast details to Character Universe."""
    brand = item.get("brand_id") or item.get("brand")
    if fmt == "cartoon" or brand:
        strategy = "branded_mascot" if brand else "ensemble"
    elif fmt == "podcast":
        strategy = "narrator_only"
    elif fmt in ("documentary", "educational"):
        strategy = "narrator_only"
    else:
        strategy = "none"

    selected = []
    if item.get("character_ids"):
        selected = list(item["character_ids"])
    elif strategy == "narrator_only":
        selected = ["narrator"]

    return {
        "cast_strategy": strategy,
        "selected_characters": selected,
        "consistency_rules": "visual_signature must match across all scenes",
        "brand_alignment": str(brand) if brand else "none",
    }


def build_music_plan(fmt: str, intensity: str) -> dict:
    """Music direction — consumed by Voice & Audio / Post-Production."""
    direction_map = {
        "documentary": "ambient",
        "educational": "upbeat",
        "cinematic": "cinematic",
        "cartoon": "upbeat",
        "podcast": "none",
        "livestream": "tense",
    }
    direction = direction_map.get(fmt, "cinematic" if intensity in ("high", "extreme") else "ambient")
    return {
        "direction": direction,
        "tempo_bpm_range": [90, 120] if direction == "upbeat" else [60, 90],
        "instrumentation": "orchestral" if direction == "cinematic" else "electronic minimal",
        "sync_to_beats": fmt == "short_form",
    }


def build_narration_plan(item: dict, fmt: str) -> dict:
    """Voice selection and delivery — defers synthesis to Voice Engine."""
    audio = item.get("audio_package") or {}
    voice = audio.get("voice_style") or {}
    voice_id = voice.get("name") or voice.get("voice_id") or "narrator_default"

    delivery_map = {
        "documentary": "authoritative",
        "educational": "warm",
        "cinematic": "dramatic",
        "podcast": "conversational",
    }
    return {
        "voice_selection": voice_id,
        "delivery_style": delivery_map.get(fmt, "conversational"),
        "pacing_wpm": 160 if fmt == "short_form" else 140,
        "emphasis_beats": ["hook", "revelation", "payoff"],
    }


def build_editing_plan(fmt: str, orientation: str, caption: str) -> dict:
    """Editing style — consumed by Post-Production."""
    style = "jump_cut" if fmt == "short_form" else "cinematic"
    if fmt == "documentary":
        style = "documentary"
    return {
        "style": style,
        "transition_grammar": "hard cuts on beats" if style == "jump_cut" else "dissolves and J-cuts",
        "color_grade_direction": "high contrast punch" if fmt == "short_form" else "natural filmic",
        "caption_style": "bold kinetic" if caption == "full" else "minimal lower-third",
        "platform_cuts": {"vertical": "9:16 safe", "horizontal": "16:9 cinematic"},
    }


def build_optimization_hints(item: dict, context: dict) -> list:
    """Hints from trend, market, and analytics for downstream optimization."""
    hints = []
    for rec in (context.get("opportunity_recommendations") or [])[:2]:
        hints.append({
            "dimension": "hook",
            "hint": rec.get("hook_direction", ""),
            "confidence": int(rec.get("confidence_score", 70) or 70),
            "source": "trend",
        })
        if rec.get("thumbnail_direction"):
            hints.append({
                "dimension": "thumbnail",
                "hint": rec["thumbnail_direction"],
                "confidence": int(rec.get("confidence_score", 65) or 65),
                "source": "trend",
            })

    for opp in (context.get("market_opportunities") or [])[:1]:
        hints.append({
            "dimension": "platform",
            "hint": f"Priority platform: {opp.get('platform', '')}",
            "confidence": int(opp.get("confidence", 60) or 60),
            "source": "market",
        })

    analytics = item.get("analytics_package") or item.get("learning_metadata") or {}
    if analytics.get("top_performing_format"):
        hints.append({
            "dimension": "format",
            "hint": f"Analytics favors {analytics['top_performing_format']}",
            "confidence": 75,
            "source": "analytics",
        })

    return [h for h in hints if h.get("hint")]


def build_asset_requirements(fmt: str, complexity: str, shot_plan: dict) -> list:
    """High-level asset needs — Agent 14 expands into generation specs."""
    requirements = [
        {"category": "hero_visual", "priority": "required", "count": 1},
        {"category": "b_roll", "priority": "recommended", "count": max(1, shot_plan["total_shots"] // 3)},
    ]
    if fmt == "cartoon":
        requirements.append({"category": "character_art", "priority": "required", "count": 2})
    if complexity in ("rich", "cinematic"):
        requirements.append({"category": "environment_plate", "priority": "recommended", "count": 1})
    if fmt != "podcast":
        requirements.append({"category": "thumbnail", "priority": "required", "count": 3})
    return requirements


def build_expected_runtime(fmt: str, pacing: dict, platforms: list) -> dict:
    """Target runtime with platform constraints."""
    scene_sec = pacing["scene_target_sec"]
    if fmt == "short_form":
        target = min(60, scene_sec * 8)
    elif fmt == "long_form":
        target = min(600, scene_sec * 20)
    elif fmt == "podcast":
        target = 900
    else:
        target = scene_sec * 12

    platform_max = min(p.get("max_duration_sec", target) for p in platforms) if platforms else target
    target = min(target, platform_max)

    return {
        "target_sec": round(target, 1),
        "min_sec": round(target * 0.8, 1),
        "max_sec": round(min(target * 1.2, platform_max), 1),
        "chapter_markers": fmt in ("long_form", "documentary", "educational"),
    }


def build_quality_targets(item: dict) -> dict:
    """Quality gates and production tier."""
    score = _score(item)
    tier = quality_tier_for_score(score)
    gates = ["script_qc", "visual_qc", "audio_qc"]
    if tier in ("premium", "flagship"):
        gates.extend(["continuity_qc", "brand_qc"])
    return {
        "minimum_score": max(60, score - 10),
        "production_tier": tier,
        "qc_gates": gates,
    }


def select_production_priority(item: dict, context: dict) -> str:
    """How urgently this production should proceed."""
    for rec in (context.get("opportunity_recommendations") or [])[:1]:
        if str(rec.get("recommended_platform", "")).startswith("breaking"):
            return ProductionPriority.URGENT
        if int(rec.get("priority_score", 0) or 0) >= 90:
            return ProductionPriority.HIGH

    score = _score(item)
    if score >= 85:
        return ProductionPriority.HIGH
    if score >= 60:
        return ProductionPriority.STANDARD
    return ProductionPriority.LOW


def build_orchestration_notes(strategy: dict, fmt: str) -> dict:
    """Per-agent guidance for Agents 12–17 — structured direction, not execution."""
    return {
        "creative_studio": (
            f"Execute {fmt} production with {strategy['visual_complexity']} visual complexity; "
            f"respect {strategy['orientation']} orientation and {strategy['narrative_mode']} mode."
        ),
        "character_universe": (
            f"Cast strategy: see character_plan; brand alignment: {strategy.get('content_class', 'general')}."
        ),
        "asset_generation": (
            f"Generate assets per asset_requirements; tier: see quality_targets.production_tier."
        ),
        "animation": (
            f"Apply animation_style technique; sync motion to pacing tempo."
        ),
        "render": (
            f"Render for {strategy['orientation']} at expected_runtime target; "
            f"apply camera_plan grammar."
        ),
        "post_production": (
            f"Edit with editing_plan style; caption_strategy: {strategy['caption_strategy']}; "
            f"color grade per editing_plan.color_grade_direction."
        ),
    }
