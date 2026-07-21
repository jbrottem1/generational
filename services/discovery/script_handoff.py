"""Map Discovery Engine queue items → Agent 3 Script Generation context.

Discovery never talks to ScriptGenerationEngine directly. Orchestrators
call `queue_item_to_script_context` (or `brief_to_script_context`) to seed
candidates, target_platform, and research.opportunity_score.

Audience Intelligence (when present) supplies the opening hook, format,
thumbnail style, and Human Attention Score without replacing discovery.
"""

from __future__ import annotations

from typing import Any


VIDEO_TYPE_TO_PLATFORM = {
    "short": "youtube_shorts",
    "long_form": "youtube_long",
    "series": "youtube_long",
    "live_update": "youtube_shorts",
    "breaking_news": "youtube_shorts",
    "documentary": "youtube_long",
    "animation": "youtube_shorts",
}


def brief_to_script_context(
    topic: str,
    brief: dict[str, Any],
    *,
    extra: dict[str, Any] | None = None,
    audience_intelligence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a minimal intelligence-pipeline context for Agent 3."""
    ai = audience_intelligence or {}
    creative = ai.get("creative") or {}
    engagement = ai.get("engagement") or {}
    profile = ai.get("audience_profile") or {}

    vtype = str(
        creative.get("recommended_video_format")
        or brief.get("recommended_video_type")
        or "short"
    )
    platform = str(
        brief.get("target_platform")
        or VIDEO_TYPE_TO_PLATFORM.get(vtype, "youtube_shorts")
    )
    hook = str(creative.get("suggested_opening_hook") or "") or _hook_for_type(topic, vtype)
    angle = str(brief.get("reasoning") or "")[:280]
    watch = int(
        engagement.get("average_watch_time_sec")
        or brief.get("expected_watch_time_sec")
        or 45
    )
    candidate = {
        "title": topic[:120],
        "hook": hook,
        "angle": angle or f"Educational explainer on {topic}",
        "discovery_brief": dict(brief),
        "recommended_video_type": str(brief.get("recommended_video_type") or vtype),
        "recommended_video_format": vtype,
        "estimated_runtime_hint_sec": watch,
        "thumbnail_style": str(creative.get("best_thumbnail_style") or ""),
        "human_attention_score": int(ai.get("human_attention_score") or 0),
    }
    if ai:
        candidate["audience_intelligence"] = ai

    context: dict[str, Any] = {
        "command": f"Create a {vtype.replace('_', ' ')} video about {topic}",
        "subject": topic,
        "target_platform": platform,
        "candidates": [candidate],
        "research": {
            "summary": angle,
            "opportunity_score": int(brief.get("overall_opportunity_score") or 0),
            "unified_discovery_score": int(brief.get("unified_discovery_score") or 0),
            "estimated_audience": int(brief.get("estimated_audience") or 0),
            "expected_click_through_potential": int(
                engagement.get("ctr_potential")
                or brief.get("expected_click_through_potential")
                or 0
            ),
            "estimated_competition": float(brief.get("estimated_competition") or 0.5),
            "confidence": float(brief.get("confidence") or ai.get("confidence") or 0),
            "cross_reference": dict(brief.get("cross_reference") or ai.get("cross_reference") or {}),
            "human_attention_score": int(ai.get("human_attention_score") or 0),
            "audience_profile": profile,
            "important_facts": [],
        },
        "trend_keywords": _keywords_from_topic(topic),
        "discovery_fed": True,
        "human_attention_score": int(ai.get("human_attention_score") or 0),
    }
    if ai:
        context["audience_intelligence"] = ai
        try:
            from services.audience_intelligence.adapters import script_generation_guidance

            context["audience_script_guidance"] = script_generation_guidance(ai)
        except Exception:  # noqa: BLE001
            pass
    if extra:
        context.update(extra)
    return context


def queue_item_to_script_context(item: dict[str, Any] | Any) -> dict[str, Any]:
    """Accept QueueItem or its to_dict() payload."""
    data = item.to_dict() if hasattr(item, "to_dict") else dict(item or {})
    brief = dict(data.get("production_brief") or {})
    if not brief:
        brief = {
            "overall_opportunity_score": int(data.get("trend_score") or 0),
            "unified_discovery_score": int(data.get("discovery_score") or 0),
            "confidence": float(data.get("confidence_score") or 0),
            "reasoning": f"Queued discovery topic: {data.get('topic')}",
            "recommended_video_type": _infer_type_from_length(data.get("recommended_length_sec") or {}),
            "estimated_audience": int(data.get("estimated_audience") or 0),
            "expected_click_through_potential": 50,
            "expected_watch_time_sec": int(
                (data.get("recommended_length_sec") or {}).get("max")
                or (data.get("recommended_length_sec") or {}).get("min")
                or 45
            ),
            "estimated_competition": float(data.get("competition") or 0.5),
            "target_platform": "youtube_shorts",
            "cross_reference": {},
        }
    packages = data.get("platform_packages") or {}
    primary = packages.get(brief.get("target_platform")) or packages.get("youtube_shorts") or {}
    if isinstance(primary, dict) and primary.get("title"):
        topic = str(primary.get("title") or data.get("topic") or "")
        brief.setdefault("reasoning", primary.get("hook") or brief.get("reasoning"))
    else:
        topic = str(data.get("topic") or "")
    return brief_to_script_context(
        topic,
        brief,
        audience_intelligence=data.get("audience_intelligence") or {},
        extra={
            "discovery_queue_id": data.get("queue_id"),
            "platform_packages": packages,
            "series_id": data.get("series_id"),
        },
    )


def _infer_type_from_length(length: dict[str, Any]) -> str:
    mx = int(length.get("max") or length.get("min") or 45)
    if mx <= 60:
        return "short"
    if mx >= 300:
        return "long_form"
    return "short"


def _hook_for_type(topic: str, vtype: str) -> str:
    if vtype in ("live_update", "breaking_news"):
        return f"What just happened with {topic} — and why it matters."
    if vtype == "series":
        return f"Episode 1: the one thing most people get wrong about {topic}."
    if vtype in ("long_form", "documentary"):
        return f"By the end of this, you'll actually understand {topic}."
    if vtype == "animation":
        return f"Watch this once — you'll never forget how {topic} works."
    return f"In 45 seconds: the clearest explanation of {topic}."


def _keywords_from_topic(topic: str) -> list[str]:
    return [w.lower() for w in topic.replace("-", " ").split() if len(w) > 2][:8]
