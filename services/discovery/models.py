"""Discovery Engine models — ranked production opportunities before any script.

These shapes are the contract between continuous discovery and production.
Nothing downstream should depend on raw provider payloads.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class DiscoveryScore:
    """Educational trust-aware topic score (0–100 factors)."""

    total: int = 0
    search_demand: int = 0
    growth_velocity: int = 0
    audience_engagement: int = 0
    geographic_reach: int = 0
    longevity: int = 0
    educational_value: int = 0
    virality_potential: int = 0
    brand_alignment: int = 0
    factual_confidence: int = 0
    visual_asset_readiness: int = 0
    competition_openness: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class VerificationReport:
    """Breaking-news / factual confidence gate before production."""

    status: str = "verified"  # verified | developing | deferred | rejected
    confidence: float = 0.0
    confirmed_facts: list[str] = field(default_factory=list)
    developing_claims: list[str] = field(default_factory=list)
    rumor_flags: list[str] = field(default_factory=list)
    sources: list[dict[str, Any]] = field(default_factory=list)
    defer_reason: str = ""
    checked_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def production_allowed(self) -> bool:
        return self.status == "verified" and self.confidence >= 0.72


@dataclass
class SeriesRecommendation:
    """Topical authority plan when related opportunities cluster."""

    series_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    subject_area: str = ""
    title: str = ""
    episode_topics: list[str] = field(default_factory=list)
    formats: list[str] = field(default_factory=list)  # series | playlist | documentary | shorts
    rationale: str = ""
    priority: int = 50

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PlatformPackage:
    """Platform-specific discovery metadata — never identical across platforms."""

    platform: str
    title: str
    description: str
    keywords: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    hashtags: list[str] = field(default_factory=list)
    hook: str = ""
    call_to_action: str = ""
    thumbnail_concept: str = ""
    recommended_length_sec: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class QueueItem:
    """One continuously ranked production opportunity."""

    topic: str
    trend_score: int
    discovery_score: int
    estimated_audience: int
    growth_rate: float
    competition: float
    recommended_length_sec: dict[str, int]
    publishing_priority: int
    confidence_score: float
    category: str = "general"
    lifecycle: str = "emerging"
    verification: dict[str, Any] = field(default_factory=dict)
    platform_packages: dict[str, Any] = field(default_factory=dict)
    series_id: str | None = None
    sources: list[str] = field(default_factory=list)
    factors: dict[str, int] = field(default_factory=dict)
    status: str = "queued"  # queued | deferred | ready | in_production | published
    # YouTube Search Intelligence + multi-source unified brief for Agent 3
    production_brief: dict[str, Any] = field(default_factory=dict)
    recommended_video_type: str = "short"
    overall_opportunity_score: int = 0
    audience_intelligence: dict[str, Any] = field(default_factory=dict)
    human_attention_score: int = 0
    queue_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    updated_at: str = field(default_factory=_now_iso)
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QueueItem":
        return cls(
            topic=str(data.get("topic") or ""),
            trend_score=int(data.get("trend_score") or 0),
            discovery_score=int(data.get("discovery_score") or 0),
            estimated_audience=int(data.get("estimated_audience") or 0),
            growth_rate=float(data.get("growth_rate") or 0),
            competition=float(data.get("competition") or 0.5),
            recommended_length_sec=dict(data.get("recommended_length_sec") or {}),
            publishing_priority=int(data.get("publishing_priority") or 0),
            confidence_score=float(data.get("confidence_score") or 0),
            category=str(data.get("category") or "general"),
            lifecycle=str(data.get("lifecycle") or "emerging"),
            verification=dict(data.get("verification") or {}),
            platform_packages=dict(data.get("platform_packages") or {}),
            series_id=data.get("series_id"),
            sources=list(data.get("sources") or []),
            factors=dict(data.get("factors") or {}),
            status=str(data.get("status") or "queued"),
            production_brief=dict(data.get("production_brief") or {}),
            recommended_video_type=str(data.get("recommended_video_type") or "short"),
            overall_opportunity_score=int(data.get("overall_opportunity_score") or 0),
            audience_intelligence=dict(data.get("audience_intelligence") or {}),
            human_attention_score=int(data.get("human_attention_score") or 0),
            queue_id=str(data.get("queue_id") or uuid.uuid4().hex[:12]),
            updated_at=str(data.get("updated_at") or _now_iso()),
            created_at=str(data.get("created_at") or _now_iso()),
        )
