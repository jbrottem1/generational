"""Studio production execution — delegates to Orchestrator via ideation adapter."""

from __future__ import annotations

import re

from core.constants import DEFAULT_PUBLISH_THRESHOLD
from services.studio.models import STUDIO_PLATFORMS, platform_label

_LONGFORM_PATTERNS = (
    r"\b\d+\s*(hour|hr|minute|min)\b",
    r"\bdocumentary\b",
    r"\bpodcast\b",
    r"\baudiobook\b",
    r"\bcourse\b",
    r"\bseries\b",
    r"\bchannel\b",
    r"\bcampaign\b",
    r"\bfeature\b",
    r"\blong[\s-]?form\b",
)


def is_longform_command(command: str) -> bool:
    lowered = command.lower()
    return any(re.search(pattern, lowered) for pattern in _LONGFORM_PATTERNS)


def build_settings_preview(command: str, settings: dict) -> dict:
    """Summarize production settings before execution."""
    platform = settings.get("platform", "youtube_shorts")
    return {
        "command": command,
        "platform": platform_label(platform),
        "platform_id": platform,
        "video_length_sec": settings.get("video_length_sec", 60),
        "video_length_label": _format_duration(settings.get("video_length_sec", 60)),
        "voice": settings.get("voice", "ai"),
        "narrator": settings.get("narrator", "documentary"),
        "visual_style": settings.get("visual_style", "cinematic"),
        "camera_style": settings.get("camera_style", "dynamic"),
        "music_style": settings.get("music_style", "uplifting"),
        "pacing": settings.get("pacing", "dynamic"),
        "target_audience": settings.get("target_audience", "general"),
        "language": settings.get("language", "en"),
        "brand": settings.get("brand", ""),
        "character_set": settings.get("character_set", ""),
        "creative_style": settings.get("creative_style", "narrative_arc"),
        "quality_level": settings.get("quality_level", "standard"),
        "budget_usd": settings.get("budget_usd", 0.0),
        "preferred_providers": settings.get("preferred_providers", []),
        "longform": is_longform_command(command),
        "video_count": _detect_count(command),
    }


def _format_duration(seconds: int) -> str:
    if seconds >= 3600:
        hours = seconds // 3600
        mins = (seconds % 3600) // 60
        return f"{hours}h {mins}m" if mins else f"{hours}h"
    if seconds >= 60:
        return f"{seconds // 60}m"
    return f"{seconds}s"


def _detect_count(command: str) -> int:
    from core import parsing
    return parsing.detect_video_count(command)


def run_studio_production(
    command: str,
    settings: dict,
    *,
    model: str = "gpt-4o-mini",
    threshold: int = DEFAULT_PUBLISH_THRESHOLD,
    research_settings: "dict | None" = None,
    project_name: "str | None" = None,
) -> dict:
    """Run the full pipeline via the Orchestrator (ideation adapter)."""
    from services import ideation

    platform = settings.get("platform", "youtube_shorts")
    count = _detect_count(command)
    if count < 1:
        count = 1

    context_extra = {
        "voice_mode": settings.get("voice", "ai"),
        "voice_profile_id": settings.get("narrator", ""),
        "studio_settings": settings,
        "platform": platform,
        "video_length_sec": settings.get("video_length_sec", 60),
        "visual_style": settings.get("visual_style", ""),
        "music_style": settings.get("music_style", ""),
        "pacing": settings.get("pacing", ""),
        "target_audience": settings.get("target_audience", ""),
        "language": settings.get("language", "en"),
        "brand": settings.get("brand", ""),
        "quality_level": settings.get("quality_level", "standard"),
        "preferred_providers": settings.get("preferred_providers", []),
    }

    result = ideation.run_command(
        command,
        count=count,
        model=model,
        threshold=threshold,
        voice_mode=settings.get("voice", "ai"),
        voice_profile_id=settings.get("narrator", ""),
        research_settings=research_settings,
        project_name=project_name,
        context_extra=context_extra,
    )
    result["studio_settings"] = settings
    result["platform"] = platform
    result["settings_preview"] = build_settings_preview(command, settings)
    return result


def submit_longform_job(
    command: str,
    settings: dict,
    *,
    model: str = "gpt-4o-mini",
    project_name: str = "",
) -> dict:
    """Submit a checkpointed long-form job via ProviderRuntime execution engine."""
    from core.jobs import get_queue
    from services.provider_runtime.longform import LONGFORM_JOB_TYPE, RuntimeExecutionEngine

    engine = RuntimeExecutionEngine()
    production_type = settings.get("platform", "documentary")
    checkpoint = engine.start_production(
        command,
        production_type=production_type,
        options={
            "model": model,
            "project_name": project_name,
            "context_extra": {
                "studio_settings": settings,
                "platform": settings.get("platform", "youtube_shorts"),
            },
        },
    )

    queue = get_queue()
    job = queue.submit(LONGFORM_JOB_TYPE, {
        "job_id": checkpoint.job_id,
        "command": command,
        "model": model,
        "project_name": project_name,
        "studio_settings": settings,
    })

    return {
        "job_id": job.id,
        "checkpoint_id": checkpoint.job_id,
        "status": checkpoint.status,
        "command": command,
        "longform": True,
    }
