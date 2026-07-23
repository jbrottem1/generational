"""V5 Production Blueprint — unified creative vision before any engine runs."""

from __future__ import annotations

from services.ai_director.competitor import analyze_competitors
from services.ai_director.styles import choose_production_style
from services.learning.predictions import predict_performance
from services.scripts.hooks import choose_hook_strategy


def clamp(value: float, low: int = 5, high: int = 98) -> int:
    """Local clamp — avoids importing engines.* (circular import with AiDirectorEngine)."""
    try:
        return int(max(low, min(high, float(value))))
    except (TypeError, ValueError):
        return int(low)


def _audience(candidate: dict) -> dict:
    ai = candidate.get("audience_intelligence") or {}
    psych = candidate.get("psychology") or {}
    dims = psych.get("dimensions") if isinstance(psych.get("dimensions"), dict) else psych
    return {
        "primary_audience": str(
            ai.get("primary_audience")
            or candidate.get("audience")
            or "General public ages 15–60"
        ),
        "target_age": str(ai.get("target_age") or candidate.get("target_age") or "15-60"),
        "knowledge_level": str(
            ai.get("knowledge_level") or candidate.get("knowledge_level") or "beginner_to_curious"
        ),
        "human_attention_score": int(ai.get("human_attention_score") or psych.get("viral_score") or 70),
        "psychology_dimensions": dims if isinstance(dims, dict) else {},
    }


def _platform(candidate: dict, context: dict) -> str:
    return str(
        candidate.get("platform")
        or context.get("platform")
        or (candidate.get("seo") or {}).get("platform")
        or "youtube_shorts"
    )


def _visual_direction(style: dict, candidate: dict) -> dict:
    topic = str(candidate.get("topic") or candidate.get("title") or "").lower()
    prefer_real = True
    modality = "hybrid_production"
    if any(w in topic for w in ("abstract", "math", "equation", "algorithm")):
        modality = "motion_graphics"
        prefer_real = False
    elif any(w in topic for w in ("space", "earth", "ocean", "wildlife", "history")):
        modality = "real_imagery_plus_graphics"
    elif "medical" in topic or "cell" in topic:
        modality = "medical_3d_animation"
        prefer_real = False
    return {
        "modality": modality,
        "prefer_real_imagery": prefer_real,
        "allow_illustrations": True,
        "allow_3d_animation": modality in ("medical_3d_animation", "hybrid_production"),
        "allow_motion_graphics": True,
        "allow_stock_footage": True,
        "prefer_government_imagery": True,
        "ai_imagery_policy": "only_when_authentic_unavailable",
        "hybrid_production": modality.startswith("hybrid") or modality.endswith("graphics"),
        "style_graphics": style.get("graphics"),
    }


def _emotion_curves(audience: dict) -> dict:
    psych = audience.get("psychology_dimensions") or {}
    curiosity = clamp(int(float(psych.get("curiosity_gap") or 78)), 50, 100)
    emotion = clamp(int(float(psych.get("emotional_intensity") or 72)), 50, 100)
    return {
        "emotion_curve": [
            {"t": 0.0, "intensity": 0.72},
            {"t": 0.12, "intensity": min(1.0, emotion / 100 + 0.15)},
            {"t": 0.45, "intensity": 0.78},
            {"t": 0.75, "intensity": min(1.0, emotion / 100)},
            {"t": 1.0, "intensity": 0.82},
        ],
        "curiosity_curve": [
            {"t": 0.0, "intensity": min(1.0, max(0.85, curiosity / 100))},
            {"t": 0.2, "intensity": 0.88},
            {"t": 0.55, "intensity": 0.72},
            {"t": 0.85, "intensity": 0.9},
            {"t": 1.0, "intensity": 0.78},
        ],
    }


def _editing_direction(style: dict, platform: str) -> dict:
    short = any(p in platform.lower() for p in ("shorts", "tiktok", "reels"))
    return {
        "average_cut_length_sec": 2.0 if short else 3.5,
        "max_static_hold_sec": 2.8 if short else 4.0,
        "visual_change_every_sec": 2.5 if short else 4.0,
        "transition_density": "high" if short else "medium",
        "movement_intensity": 0.88 if short else 0.65,
        "caption_frequency": "word_synced" if short else "sentence",
        "animation_density": "high",
        "kinetic_typography": True,
        "diagram_overlays": True,
        "graphic_density": style.get("graphics") or "rich",
        "visual_complexity": "rich" if short else "standard",
        "transitions_default": style.get("transitions") or "whip_cut_plus_match",
        "prefer_camera_motion_over_static": True,
    }


def _platform_strategy(platform: str) -> dict:
    presets = {
        "youtube_shorts": {"aspect": "9:16", "max_sec": 60, "hook_window_sec": 3, "seo_focus": "title_tags"},
        "tiktok": {"aspect": "9:16", "max_sec": 60, "hook_window_sec": 1.5, "seo_focus": "trend_sounds"},
        "instagram_reels": {"aspect": "9:16", "max_sec": 90, "hook_window_sec": 2, "seo_focus": "cover_frame"},
        "facebook_reels": {"aspect": "9:16", "max_sec": 90, "hook_window_sec": 2, "seo_focus": "shareability"},
        "x": {"aspect": "16:9", "max_sec": 140, "hook_window_sec": 2, "seo_focus": "thread_hook"},
        "pinterest": {"aspect": "2:3", "max_sec": 60, "hook_window_sec": 3, "seo_focus": "keyword_pin"},
        "linkedin": {"aspect": "16:9", "max_sec": 180, "hook_window_sec": 4, "seo_focus": "professional_insight"},
        "youtube_longform": {"aspect": "16:9", "max_sec": 720, "hook_window_sec": 8, "seo_focus": "search_intent"},
    }
    key = platform if platform in presets else "youtube_shorts"
    return {"platform": key, **presets[key], "optimization_notes": f"Direction tuned for {key}"}


def build_production_blueprint(candidate: dict, context: dict | None = None) -> dict:
    """Complete Production Blueprint — required before downstream engines run."""
    context = context or {}
    style = choose_production_style(candidate, context)
    audience = _audience(candidate)
    platform = _platform(candidate, context)
    curves = _emotion_curves(audience)
    competitors = analyze_competitors(candidate)
    editing = _editing_direction(style, platform)
    visual = _visual_direction(style, candidate)
    platform_strategy = _platform_strategy(platform)

    psych_dims = audience.get("psychology_dimensions") or {}
    hook_strategy = choose_hook_strategy(
        topic=str(candidate.get("topic") or candidate.get("title") or ""),
        psychology=psych_dims if isinstance(psych_dims, dict) else {},
        competitor_hook_styles=list(competitors.get("hook_styles") or competitors.get("preferred_hook_styles") or []),
        niche=str(candidate.get("niche") or competitors.get("niche") or ""),
    )

    length = int(
        candidate.get("duration_sec")
        or platform_strategy.get("max_sec")
        or 60
    )
    if platform_strategy.get("max_sec"):
        length = min(length, int(platform_strategy["max_sec"]))

    prediction = predict_performance(
        topic=str(candidate.get("title") or candidate.get("topic") or ""),
        niche=str(candidate.get("niche") or candidate.get("topic") or ""),
        platform=platform,
        runtime_sec=length,
        psychology_score=float(audience.get("human_attention_score") or 70),
        seo_score=float((candidate.get("seo") or {}).get("score") or 70),
        qa_score=float(candidate.get("quality_score") or 80),
    )

    educational_goal = str(
        candidate.get("educational_goal")
        or f"Help viewers understand {candidate.get('topic') or candidate.get('title') or 'the topic'} clearly in under {length}s"
    )
    entertainment_goal = str(
        candidate.get("entertainment_goal")
        or "Sustain curiosity and emotional engagement through the full runtime"
    )

    blueprint = {
        "blueprint_version": "5.0",
        "topic": str(candidate.get("topic") or candidate.get("title") or ""),
        "primary_audience": audience["primary_audience"],
        "target_age": audience["target_age"],
        "knowledge_level": audience["knowledge_level"],
        "platform": platform,
        "video_length_sec": length,
        "educational_goal": educational_goal,
        "entertainment_goal": entertainment_goal,
        "emotion_curve": curves["emotion_curve"],
        "curiosity_curve": curves["curiosity_curve"],
        "retention_targets": {
            "at_3s": 0.92,
            "at_10s": 0.80,
            "at_mid": 0.68,
            "completion": 0.58,
        },
        "hook_strategy": hook_strategy,
        "hook_window_sec": platform_strategy.get("hook_window_sec", 3),
        "visual_style": style.get("label"),
        "production_style_id": style.get("style_id"),
        "animation_style": style.get("motion"),
        "color_palette": style.get("colors"),
        "narration_style": style.get("narration"),
        "music_style": style.get("music"),
        "camera_style": style.get("camera"),
        "editing_style": editing,
        "thumbnail_strategy": {
            "layout": "question_overlay",
            "claim_words_max": 5,
            "contrast": "high",
            "focal_point": "single_subject_center",
            "curiosity_prompt": True,
            "simplicity": "one_claim_one_subject",
            "readability": "bold_safe_zone",
        },
        "seo_strategy": {
            "title_pattern": "curiosity_plus_clarity",
            "tags_min": 8,
            "description_hook_first": True,
        },
        "publishing_time": {
            "recommendation": "evening_local_peak",
            "avoid": ["early_morning_low_traffic"],
        },
        "expected_competition": {
            "level": "high" if competitors.get("avg_views", 0) > 300_000 else "moderate",
            "niche": competitors.get("niche"),
            "top_creators": competitors.get("top_creators"),
        },
        "expected_difficulty": "high" if competitors.get("avg_views", 0) > 500_000 else "medium",
        "expected_ctr": max(float(prediction.get("expected_ctr") or 0), 7.5),
        "expected_watch_time_sec": max(float(prediction.get("expected_watch_time_sec") or 0), length * 0.68),
        "expected_completion_rate": max(float(prediction.get("expected_audience_retention") or 0), 62.0),
        "visual_direction": visual,
        "narration_direction": {
            "persona": style.get("narration"),
            "traits": ["clear", "confident", "human", "engaging_educator", "emotional_variation"],
            "avoid": ["robotic_cadence", "monotone", "flat_read"],
            "hook_energy": "high",
            "payoff_pause_sec": 0.7,
        },
        "music_direction": {
            "style": style.get("music"),
            "duck_under_narration": True,
            "duck_db": -10,
            "intensity_follows_emotion_curve": True,
            "hook_sting": True,
            "payoff_swell": True,
            "sfx_on_pacing_changes": True,
        },
        "shareability_direction": {
            "require_share_verb_in_cta": True,
            "emotional_peak_before_cta": True,
            "tag_prompt": True,
        },
        "platform_strategy": platform_strategy,
        "competitor_analysis": competitors,
        "style_library_entry": style,
        "production_plan": {
            "engines_must_follow_blueprint": True,
            "no_independent_style_assumptions": True,
            "handoff_order": [
                "script_generation",
                "visual_intelligence",
                "cinematography",
                "viewer_retention",
                "voice_audio",
                "studio_render",
                "optimization_lab",
            ],
        },
        "rationale": style.get("rationale"),
    }
    return blueprint
