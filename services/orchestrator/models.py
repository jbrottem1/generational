"""Orchestration data models — the contracts of the operating system layer.

`ProductionPackage` is the ONE standardized object that flows out of the
pipeline. Field rules (non-negotiable):

- Future engines only ADD fields — never remove or rename existing ones.
- Unknown fields survive round-trips via `extras`, so packages written by a
  newer version of the system are never truncated by an older one.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class StageStatus:
    """Outcome of one orchestrated stage."""

    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


@dataclass
class StageReport:
    """Diagnostics for one stage run — what centralized logging records."""

    stage: str
    status: str = StageStatus.SUCCESS
    started_at: str = ""
    finished_at: str = ""
    duration_ms: int = 0
    confidence: int = 0                      # 0-100 stage confidence
    warnings: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    diagnostics: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "stage": self.stage,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_ms": self.duration_ms,
            "confidence": self.confidence,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "diagnostics": dict(self.diagnostics),
        }


# The canonical field set. ORDER MATTERS ONLY FOR DOCS; the contract is the
# names. Future engines append here (and only append).
PRODUCTION_PACKAGE_FIELDS = [
    "project_id",
    "brand",
    "language",
    "target_country",
    "platforms",
    "trend_score",
    "competition_score",
    "psychology_score",
    "attention_score",
    "hook",
    "script",
    "scene_breakdown",
    "visual_assets",
    "voice_assets",
    "music_assets",
    "captions",
    "thumbnail_plan",
    "seo_package",
    "quality_score",
    "publish_ready",
    "analytics_placeholder",
]


@dataclass
class ProductionPackage:
    """The unified data model that flows through every stage of the OS."""

    project_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    brand: str = ""
    language: str = "en"
    target_country: str = "US"
    platforms: list = field(default_factory=list)
    trend_score: int = 0
    competition_score: int = 0
    psychology_score: int = 0
    attention_score: int = 0
    hook: str = ""
    script: str = ""
    scene_breakdown: list = field(default_factory=list)
    visual_assets: dict = field(default_factory=dict)
    voice_assets: dict = field(default_factory=dict)
    music_assets: dict = field(default_factory=dict)
    captions: dict = field(default_factory=dict)
    thumbnail_plan: list = field(default_factory=list)
    seo_package: dict = field(default_factory=dict)
    quality_score: int = 0
    publish_ready: bool = False
    analytics_placeholder: dict = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    extras: dict = field(default_factory=dict)   # additive fields land here

    def to_dict(self) -> dict:
        data = {name: getattr(self, name) for name in PRODUCTION_PACKAGE_FIELDS}
        data["created_at"] = self.created_at
        data.update(self.extras)  # future fields are first-class in the dict
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "ProductionPackage":
        known = {name: data[name] for name in PRODUCTION_PACKAGE_FIELDS if name in data}
        extras = {
            key: value
            for key, value in data.items()
            if key not in PRODUCTION_PACKAGE_FIELDS and key != "created_at"
        }
        return cls(created_at=data.get("created_at", _now_iso()), extras=extras, **known)


@dataclass
class PipelineResult:
    """What `run_full_pipeline` returns — one object, everything traceable."""

    status: str                              # StageStatus value for the run
    packages: "list[ProductionPackage]" = field(default_factory=list)
    stage_reports: "list[StageReport]" = field(default_factory=list)
    context: dict = field(default_factory=dict)
    error: str = ""

    @property
    def succeeded(self) -> bool:
        return self.status != StageStatus.FAILED

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "error": self.error,
            "packages": [pkg.to_dict() for pkg in self.packages],
            "stage_reports": [report.to_dict() for report in self.stage_reports],
        }
