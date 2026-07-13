"""Knowledge Atlas data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

VISUAL_TYPES = frozenset({
    "photograph",
    "microscope",
    "histology",
    "medical_imaging",
    "satellite",
    "astronomical",
    "fossil",
    "specimen",
    "diagram",
    "map",
    "geological_cross_section",
    "chart",
    "document",
    "illustration",
    "animation",
    "comparison",
    "timelapse",
})

DOMAINS = frozenset({
    "biology",
    "botany",
    "microbiology",
    "anatomy",
    "histology",
    "ecology",
    "evolution",
    "astronomy",
    "physics",
    "chemistry",
    "engineering",
    "geology",
    "meteorology",
    "history",
    "technology",
    "medicine",
    "wildlife",
    "oceanography",
})


@dataclass
class AtlasAsset:
    asset_id: str
    topic: str
    keywords: tuple[str, ...]
    description: str
    source: str
    license: str
    path: str
    category: str
    visual_type: str
    quality_score: float
    suggested_uses: tuple[str, ...]
    date_added: str
    reuse_count: int
    concepts: tuple[str, ...] = field(default_factory=tuple)
    species: str = ""
    scientific_name: str = ""
    credit: str = ""
    width: int = 0
    height: int = 0
    compare_with: tuple[str, ...] = field(default_factory=tuple)
    demo_ids: tuple[str, ...] = field(default_factory=tuple)
    fingerprint: str = ""
    reuse_history: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "topic": self.topic,
            "keywords": list(self.keywords),
            "species": self.species,
            "scientific_name": self.scientific_name,
            "description": self.description,
            "source": self.source,
            "license": self.license,
            "resolution": {"width": self.width, "height": self.height},
            "path": self.path,
            "category": self.category,
            "visual_type": self.visual_type,
            "quality_score": self.quality_score,
            "suggested_uses": list(self.suggested_uses),
            "date_added": self.date_added,
            "reuse_count": self.reuse_count,
            "reuse_history": list(self.reuse_history),
            "concepts": list(self.concepts),
            "credit": self.credit,
            "compare_with": list(self.compare_with),
            "demo_ids": list(self.demo_ids),
            "fingerprint": self.fingerprint,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> AtlasAsset:
        res = raw.get("resolution") or {}
        return cls(
            asset_id=str(raw["asset_id"]),
            topic=str(raw.get("topic") or ""),
            keywords=tuple(str(k) for k in (raw.get("keywords") or [])),
            species=str(raw.get("species") or ""),
            scientific_name=str(raw.get("scientific_name") or ""),
            description=str(raw.get("description") or ""),
            source=str(raw.get("source") or ""),
            license=str(raw.get("license") or ""),
            path=str(raw.get("path") or ""),
            category=str(raw.get("category") or "biology"),
            visual_type=str(raw.get("visual_type") or "photograph"),
            quality_score=float(raw.get("quality_score") or 0.0),
            suggested_uses=tuple(str(u) for u in (raw.get("suggested_uses") or [])),
            date_added=str(raw.get("date_added") or ""),
            reuse_count=int(raw.get("reuse_count") or 0),
            reuse_history=tuple(str(h) for h in (raw.get("reuse_history") or [])),
            concepts=tuple(str(c) for c in (raw.get("concepts") or [])),
            credit=str(raw.get("credit") or ""),
            width=int(res.get("width") or raw.get("width") or 0),
            height=int(res.get("height") or raw.get("height") or 0),
            compare_with=tuple(str(c) for c in (raw.get("compare_with") or [])),
            demo_ids=tuple(str(d) for d in (raw.get("demo_ids") or [])),
            fingerprint=str(raw.get("fingerprint") or ""),
        )
