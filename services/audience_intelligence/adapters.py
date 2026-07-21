"""Adapters — Audience Intelligence → Agent 3 Script Generation guidance."""

from __future__ import annotations

from typing import Any

from services.audience_intelligence.models import AudienceIntelligenceReport, FORMATS


FORMAT_TO_PLATFORM = {
    "short": "youtube_shorts",
    "breaking_news": "youtube_shorts",
    "animation": "youtube_shorts",
    "series": "youtube_long",
    "long_form": "youtube_long",
    "documentary": "youtube_long",
}


def script_generation_guidance(report: AudienceIntelligenceReport | dict[str, Any]) -> dict[str, Any]:
    """Compact guidance block for ScriptGenerationEngine / handoff."""
    if isinstance(report, dict):
        report = AudienceIntelligenceReport.from_dict(report)
    fmt = report.creative.recommended_video_format
    if fmt not in FORMATS:
        fmt = "short"
    return {
        "human_attention_score": report.human_attention_score,
        "suggested_opening_hook": report.creative.suggested_opening_hook,
        "psychological_hooks": list(report.creative.psychological_hooks),
        "best_thumbnail_style": report.creative.best_thumbnail_style,
        "recommended_video_format": fmt,
        "recommended_video_length_sec": dict(report.creative.recommended_video_length_sec),
        "target_platform": FORMAT_TO_PLATFORM.get(fmt, "youtube_shorts"),
        "ctr_potential": report.engagement.ctr_potential,
        "retention_probability": report.engagement.retention_probability,
        "shareability": report.engagement.shareability,
        "audience_sophistication": report.audience_profile.audience_sophistication,
        "difficulty_level": report.audience_profile.difficulty_level,
        "age_demographics": report.audience_profile.age_demographics,
        "confidence": report.confidence,
    }


def apply_guidance_to_script_context(context: dict[str, Any], report: AudienceIntelligenceReport | dict[str, Any]) -> dict[str, Any]:
    """Merge Audience Intelligence into an Agent 3 context dict (additive)."""
    if isinstance(report, dict):
        report = AudienceIntelligenceReport.from_dict(report)
    guidance = script_generation_guidance(report)
    context["audience_intelligence"] = report.to_dict()
    context["audience_script_guidance"] = guidance
    context["human_attention_score"] = report.human_attention_score

    platform = guidance["target_platform"]
    if platform:
        context["target_platform"] = platform

    research = dict(context.get("research") or {})
    research["human_attention_score"] = report.human_attention_score
    research["ctr_potential"] = report.engagement.ctr_potential
    research["retention_probability"] = report.engagement.retention_probability
    research["audience_profile"] = report.audience_profile.to_dict()
    context["research"] = research

    candidates = list(context.get("candidates") or [])
    if candidates:
        c0 = dict(candidates[0])
        c0["hook"] = report.creative.suggested_opening_hook or c0.get("hook")
        c0["audience_intelligence"] = report.to_dict()
        c0["human_attention_score"] = report.human_attention_score
        c0["recommended_video_format"] = report.creative.recommended_video_format
        c0["estimated_runtime_hint_sec"] = report.engagement.average_watch_time_sec
        c0["thumbnail_style"] = report.creative.best_thumbnail_style
        candidates[0] = c0
        context["candidates"] = candidates
    return context
