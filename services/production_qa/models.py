"""Production Quality Assurance — report contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

Decision = Literal["APPROVE", "REQUEST_REVISION", "BLOCK_EXPORT"]

# Documentary-level floor: below this → do not publish
CATEGORY_PASS_THRESHOLD = 90
OVERALL_PASS_THRESHOLD = 90
CRITICAL_BLOCK_FLOOR = 70

PQA_CATEGORIES = (
    "research_accuracy",
    "evidence",
    "visuals",
    "typography",
    "annotations",
    "cinematography",
    "retention",
    "render_quality",
    "optimization",
    "audio",
    "narration",
    "synchronization",
    "educational_value",
    "psychology",
    "seo",
)

PLATFORM_KEYS = (
    "youtube",
    "youtube_shorts",
    "tiktok",
    "instagram_reels",
    "facebook",
    "pinterest",
    "linkedin",
    "x",
)

# Category → engine(s) that own the fix
REVISION_OWNERS: dict[str, list[str]] = {
    "research_accuracy": ["research", "citation", "critic"],
    "evidence": ["evidence_intelligence", "visual_intelligence"],
    "visuals": ["visual_intelligence", "image", "asset_manager", "studio_render"],
    "typography": ["subtitle", "visual_planning", "render_package", "studio_render"],
    "annotations": ["evidence_intelligence", "animation", "visual_intelligence"],
    "cinematography": ["cinematography", "viewer_retention", "animation", "studio_render"],
    "retention": ["viewer_retention", "script_generation", "cinematography", "voice_audio"],
    "render_quality": ["studio_render", "render_package", "timeline", "cinematography"],
    "optimization": ["optimization_lab", "ranking", "critic", "revision"],
    "audio": ["voice_audio", "voice", "narration", "viewer_retention"],
    "narration": ["script_generation", "narration", "script", "viewer_retention"],
    "synchronization": ["timeline", "subtitle", "animation", "studio_render"],
    "educational_value": ["script_generation", "critic", "psychology"],
    "psychology": ["psychology", "audience_intelligence", "attention_graph", "viewer_retention"],
    "seo": ["seo", "seo_optimization"],
    "platform_compliance": ["seo", "publishing", "render_package"],
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class CategoryScore:
    key: str
    label: str
    score: int
    confidence: float = 0.7
    passed: bool = False
    details: dict[str, Any] = field(default_factory=dict)
    issues: list[str] = field(default_factory=list)
    corrections_required: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.score = int(max(0, min(100, self.score)))
        self.passed = self.score >= CATEGORY_PASS_THRESHOLD

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RevisionRequest:
    category: str
    score: int
    target_engines: list[str]
    severity: Literal["revision", "block"]
    message: str
    corrections: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PlatformReady:
    platform: str
    ready: bool
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProductionQAReport:
    """Unified editor-in-chief report for one production / idea."""

    title: str = ""
    idea_id: str = ""
    overall_score: int = 0
    decision: Decision = "BLOCK_EXPORT"
    categories: dict[str, CategoryScore] = field(default_factory=dict)
    platform_ready: list[PlatformReady] = field(default_factory=list)
    revision_requests: list[RevisionRequest] = field(default_factory=list)
    hard_fails: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    predicted_metrics: dict[str, Any] = field(default_factory=dict)
    sources_checked: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now)
    version: str = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "idea_id": self.idea_id,
            "overall_score": self.overall_score,
            "decision": self.decision,
            "passed": self.decision == "APPROVE",
            "categories": {k: v.to_dict() for k, v in self.categories.items()},
            "scores": {k: v.score for k, v in self.categories.items()},
            "platform_ready": {p.platform: p.ready for p in self.platform_ready},
            "platform_ready_detail": [p.to_dict() for p in self.platform_ready],
            "revision_requests": [r.to_dict() for r in self.revision_requests],
            "hard_fails": list(self.hard_fails),
            "warnings": list(self.warnings),
            "predicted_metrics": dict(self.predicted_metrics),
            "sources_checked": list(self.sources_checked),
            "created_at": self.created_at,
            "version": self.version,
            "report_markdown": format_report_markdown(self),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProductionQAReport":
        cats: dict[str, CategoryScore] = {}
        raw_cats = data.get("categories") or {}
        for key, val in raw_cats.items():
            if isinstance(val, dict):
                cats[key] = CategoryScore(
                    key=val.get("key") or key,
                    label=val.get("label") or key,
                    score=int(val.get("score") or 0),
                    confidence=float(val.get("confidence") or 0.7),
                    details=dict(val.get("details") or {}),
                    issues=list(val.get("issues") or []),
                    corrections_required=list(val.get("corrections_required") or []),
                )
        platforms = [
            PlatformReady(
                platform=p.get("platform", ""),
                ready=bool(p.get("ready")),
                reasons=list(p.get("reasons") or []),
            )
            for p in (data.get("platform_ready_detail") or [])
            if isinstance(p, dict)
        ]
        revisions = [
            RevisionRequest(
                category=r.get("category", ""),
                score=int(r.get("score") or 0),
                target_engines=list(r.get("target_engines") or []),
                severity=r.get("severity") or "revision",
                message=r.get("message") or "",
                corrections=list(r.get("corrections") or []),
            )
            for r in (data.get("revision_requests") or [])
            if isinstance(r, dict)
        ]
        return cls(
            title=str(data.get("title") or ""),
            idea_id=str(data.get("idea_id") or ""),
            overall_score=int(data.get("overall_score") or 0),
            decision=data.get("decision") or "BLOCK_EXPORT",
            categories=cats,
            platform_ready=platforms,
            revision_requests=revisions,
            hard_fails=list(data.get("hard_fails") or []),
            warnings=list(data.get("warnings") or []),
            predicted_metrics=dict(data.get("predicted_metrics") or {}),
            sources_checked=list(data.get("sources_checked") or []),
            created_at=str(data.get("created_at") or _now()),
            version=str(data.get("version") or "1.0.0"),
        )


def format_report_markdown(report: ProductionQAReport) -> str:
    lines = [
        "# Production Quality Report",
        "",
        f"**Overall Score:** {report.overall_score}",
        f"**Decision:** {report.decision}",
        "",
    ]
    for key in PQA_CATEGORIES:
        cat = report.categories.get(key)
        if not cat:
            continue
        lines.append(f"- {cat.label}: {cat.score}")
    lines.append("")
    lines.append("## Platform Ready")
    for p in report.platform_ready:
        mark = "✓" if p.ready else "✗"
        lines.append(f"- {mark} {p.platform}")
    if report.revision_requests:
        lines.append("")
        lines.append("## Revision Requests")
        for r in report.revision_requests:
            engines = ", ".join(r.target_engines)
            lines.append(f"- [{r.severity}] {r.category} ({r.score}) → {engines}: {r.message}")
    return "\n".join(lines)
