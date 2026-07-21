"""Audience Intelligence models — structured JSON only."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


def _clamp(value: float, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, int(round(value))))


PSYCH_FIELDS = (
    "curiosity_potential",
    "surprise_level",
    "emotional_intensity",
    "controversy_level",
    "educational_value",
    "humor_potential",
    "fear_potential",
    "inspiration_potential",
    "nostalgia",
    "authority",
    "novelty",
    "practical_usefulness",
    "visual_appeal",
    "discussion_potential",
)

FORMATS = ("short", "long_form", "series", "breaking_news", "documentary", "animation")


@dataclass
class PsychologicalDrivers:
    """Why humans click, watch, and share — 0–100 each."""

    curiosity_potential: int = 50
    surprise_level: int = 50
    emotional_intensity: int = 50
    controversy_level: int = 30
    educational_value: int = 50
    humor_potential: int = 30
    fear_potential: int = 25
    inspiration_potential: int = 40
    nostalgia: int = 25
    authority: int = 45
    novelty: int = 50
    practical_usefulness: int = 45
    visual_appeal: int = 50
    discussion_potential: int = 45

    def to_dict(self) -> dict[str, int]:
        return {k: int(getattr(self, k)) for k in PSYCH_FIELDS}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PsychologicalDrivers":
        base = cls()
        return cls(**{k: _clamp((data or {}).get(k, getattr(base, k))) for k in PSYCH_FIELDS})


@dataclass
class EngagementEstimates:
    ctr_potential: int = 50
    average_watch_time_sec: int = 45
    retention_probability: int = 50
    shareability: int = 50
    comment_probability: int = 45
    rewatch_probability: int = 40
    subscriber_conversion: int = 35
    series_potential: int = 40
    evergreen_potential: int = 45
    breaking_news_decay: int = 30
    international_appeal: int = 50

    def to_dict(self) -> dict[str, int]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EngagementEstimates":
        base = cls()
        data = data or {}
        kwargs: dict[str, int] = {}
        for k in asdict(base):
            raw = data.get(k, getattr(base, k))
            kwargs[k] = int(raw) if k == "average_watch_time_sec" else _clamp(raw)
        return cls(**kwargs)


@dataclass
class AudienceProfile:
    age_demographics: str = "18-34 primary"
    audience_sophistication: str = "general"
    difficulty_level: str = "intermediate"
    primary_motivation: str = "learn"
    secondary_motivations: list[str] = field(default_factory=list)
    persona_summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AudienceProfile":
        data = data or {}
        return cls(
            age_demographics=str(data.get("age_demographics") or "18-34 primary"),
            audience_sophistication=str(data.get("audience_sophistication") or "general"),
            difficulty_level=str(data.get("difficulty_level") or "intermediate"),
            primary_motivation=str(data.get("primary_motivation") or "learn"),
            secondary_motivations=list(data.get("secondary_motivations") or []),
            persona_summary=str(data.get("persona_summary") or ""),
        )


@dataclass
class CreativeDirectives:
    psychological_hooks: list[str] = field(default_factory=list)
    suggested_opening_hook: str = ""
    best_thumbnail_style: str = "bold_text_over_visual"
    recommended_video_length_sec: dict[str, int] = field(default_factory=lambda: {"min": 30, "max": 55})
    recommended_video_format: str = "short"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CreativeDirectives":
        data = data or {}
        fmt = str(data.get("recommended_video_format") or "short")
        if fmt not in FORMATS:
            fmt = "short"
        return cls(
            psychological_hooks=list(data.get("psychological_hooks") or []),
            suggested_opening_hook=str(data.get("suggested_opening_hook") or ""),
            best_thumbnail_style=str(data.get("best_thumbnail_style") or "bold_text_over_visual"),
            recommended_video_length_sec=dict(
                data.get("recommended_video_length_sec") or {"min": 30, "max": 55}
            ),
            recommended_video_format=fmt,
        )


@dataclass
class AudienceIntelligenceReport:
    """Full Audience Intelligence output — structured JSON only."""

    topic: str = ""
    human_attention_score: int = 50
    psychological_drivers: PsychologicalDrivers = field(default_factory=PsychologicalDrivers)
    engagement: EngagementEstimates = field(default_factory=EngagementEstimates)
    audience_profile: AudienceProfile = field(default_factory=AudienceProfile)
    creative: CreativeDirectives = field(default_factory=CreativeDirectives)
    cross_reference: dict[str, Any] = field(default_factory=dict)
    provider_signals: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.5
    reasoning: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "topic": self.topic,
            "human_attention_score": int(self.human_attention_score),
            "psychological_drivers": self.psychological_drivers.to_dict(),
            "engagement": self.engagement.to_dict(),
            "audience_profile": self.audience_profile.to_dict(),
            "creative": self.creative.to_dict(),
            "cross_reference": dict(self.cross_reference),
            "provider_signals": dict(self.provider_signals),
            "confidence": round(float(self.confidence), 4),
            "reasoning": self.reasoning,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AudienceIntelligenceReport":
        data = data or {}
        return cls(
            topic=str(data.get("topic") or ""),
            human_attention_score=_clamp(data.get("human_attention_score", 50)),
            psychological_drivers=PsychologicalDrivers.from_dict(data.get("psychological_drivers") or {}),
            engagement=EngagementEstimates.from_dict(data.get("engagement") or {}),
            audience_profile=AudienceProfile.from_dict(data.get("audience_profile") or {}),
            creative=CreativeDirectives.from_dict(data.get("creative") or {}),
            cross_reference=dict(data.get("cross_reference") or {}),
            provider_signals=dict(data.get("provider_signals") or {}),
            confidence=float(data.get("confidence") or 0.5),
            reasoning=str(data.get("reasoning") or ""),
        )
