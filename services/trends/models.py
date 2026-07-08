"""Universal trend data models — every provider normalizes into these.

Downstream systems (scoring, ranking, UI, future prediction engines) consume
ONLY these shapes, never provider-specific payloads. This is the contract
that lets trend providers be plug-and-play.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Trend:
    """One normalized trend signal from any provider."""

    topic: str
    keywords: list[str] = field(default_factory=list)
    growth_pct: float = 0.0        # period-over-period growth percentage
    search_volume: int = 0         # estimated monthly searches / views
    velocity: float = 0.0          # 0-1 rate of acceleration
    competition: float = 0.5       # 0-1, higher = more saturated
    freshness: float = 0.5         # 0-1, higher = newer signal
    category: str = "general"
    country: str = "US"
    language: str = "en"
    platform: str = ""             # where the trend is happening
    source: str = ""               # provider key that supplied it
    timestamp: str = field(default_factory=_now_iso)
    confidence: float = 0.5        # 0-1 provider confidence in the signal
    trend_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Trend":
        return cls(
            topic=data.get("topic", ""),
            keywords=list(data.get("keywords", [])),
            growth_pct=float(data.get("growth_pct", 0)),
            search_volume=int(data.get("search_volume", 0)),
            velocity=float(data.get("velocity", 0)),
            competition=float(data.get("competition", 0.5)),
            freshness=float(data.get("freshness", 0.5)),
            category=data.get("category", "general"),
            country=data.get("country", "US"),
            language=data.get("language", "en"),
            platform=data.get("platform", ""),
            source=data.get("source", ""),
            timestamp=data.get("timestamp", _now_iso()),
            confidence=float(data.get("confidence", 0.5)),
            trend_id=data.get("trend_id", uuid.uuid4().hex[:12]),
        )


@dataclass
class Opportunity:
    """A scored trend — the unit that moves through opportunity ranking."""

    trend: Trend
    opportunity_score: int          # 0-100 blended score
    factors: dict = field(default_factory=dict)  # per-factor breakdown (0-100 each)

    def to_dict(self) -> dict:
        return {
            "trend": self.trend.to_dict(),
            "opportunity_score": self.opportunity_score,
            "factors": self.factors,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Opportunity":
        return cls(
            trend=Trend.from_dict(data.get("trend", {})),
            opportunity_score=int(data.get("opportunity_score", 0)),
            factors=dict(data.get("factors", {})),
        )
