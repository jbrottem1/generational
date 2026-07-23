"""Production brief — structured + natural-language studio intake."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from services.executive_orchestrator.request_parser import PLATFORM_ALIASES, parse_production_request


@dataclass
class StudioBrief:
    """Canonical Production Operations input."""

    topic: str
    platform: str = "youtube_shorts"
    length_sec: int = 60
    style: str = "educational"
    narrator: str = "professor"
    voice: str = "default"
    quality_target: float = 98.0
    constraints: dict[str, Any] = field(default_factory=dict)
    command: str = ""
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_command(self) -> str:
        if self.command.strip():
            return self.command.strip()
        plat = self.platform.replace("_", " ")
        return (
            f"Create a {self.length_sec} second {plat} video about {self.topic} "
            f"in a {self.style} style, narrator {self.narrator}."
        )


def _norm_platform(value: str) -> str:
    raw = (value or "youtube_shorts").strip().lower()
    if raw in PLATFORM_ALIASES.values():
        return raw
    return PLATFORM_ALIASES.get(raw, PLATFORM_ALIASES.get(raw.replace("_", " "), raw.replace(" ", "_")))


def build_studio_brief(
    *,
    topic: str = "",
    platform: str = "youtube_shorts",
    length_sec: int | None = None,
    style: str = "educational",
    narrator: str = "professor",
    voice: str = "default",
    quality_target: float = 98.0,
    constraints: dict | None = None,
    command: str = "",
    **extra: Any,
) -> StudioBrief:
    """Accept structured fields and/or a free-text command."""
    parsed = None
    if command.strip():
        parsed = parse_production_request(command)
    topic_final = (topic or (parsed.topic if parsed else "") or "Untitled").strip()
    plat = _norm_platform(platform or (parsed.primary_platform if parsed else "youtube_shorts"))
    length = int(length_sec if length_sec is not None else (parsed.runtime_sec if parsed else 60))
    return StudioBrief(
        topic=topic_final,
        platform=plat,
        length_sec=max(5, length),
        style=str(style or "educational"),
        narrator=str(narrator or "founder"),
        voice=str(voice or "default"),
        quality_target=float(quality_target or 98),
        constraints=dict(constraints or {}),
        command=command.strip(),
        raw=dict(extra),
    )


def brief_to_context(brief: StudioBrief) -> dict[str, Any]:
    """Seed shared pipeline context from the studio brief (additive)."""
    cmd = brief.to_command()
    narrator_profile = {}
    try:
        from services.elevenlabs.voices import resolve_narrator_profile

        narrator_profile = resolve_narrator_profile(brief.narrator, style=brief.style)
    except Exception:  # noqa: BLE001
        narrator_profile = {}
    return {
        "command": cmd,
        "subject": brief.topic,
        "topic": brief.topic,
        "platform": brief.platform,
        "target_platform": brief.platform,
        "platforms": [brief.platform],
        "video_length_sec": brief.length_sec,
        "duration_sec": brief.length_sec,
        "target_runtime_sec": brief.length_sec,
        "production_style": brief.style,
        "style": brief.style,
        "narration_style": brief.narrator,
        "narrator": brief.narrator,
        "voice_preference": brief.voice,
        "quality_target": brief.quality_target,
        "ops_constraints": brief.constraints,
        "studio_brief": brief.to_dict(),
        "preferred_voice_provider": "elevenlabs",
        "elevenlabs_narrator_profile": narrator_profile,
        "voice_profile_hint": {
            "provider_voice_id": narrator_profile.get("provider_voice_id"),
            "narrator_profile": narrator_profile.get("profile_key"),
            "style": brief.style,
        },
    }
