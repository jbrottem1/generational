"""EpisodeDesignPackage assembly — per-item output for the Episode Design Engine."""

from __future__ import annotations

from datetime import datetime, timezone

from services.episode_design.blueprint import build_lesson_blueprint
from services.episode_design.models import (
    EPISODE_DESIGN_ENGINE_VERSION,
    EPISODE_DESIGN_PACKAGE_VERSION,
    EpisodeDesignStatus,
)
from services.episode_design.retention import build_retention_review
from services.episode_design.series import build_series_design


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _episode_design_status(retention_score: int, blockers: list) -> str:
    if blockers:
        return EpisodeDesignStatus.INCOMPLETE
    if retention_score >= 75:
        return EpisodeDesignStatus.READY
    if retention_score >= 50:
        return EpisodeDesignStatus.NEEDS_REVIEW
    return EpisodeDesignStatus.DEGRADED


def _upstream_slots_read(item: dict) -> list:
    """Return which upstream content slots were present in the item."""
    candidates = [
        "script", "hook", "script_package", "visual_package", "audio_package",
        "quality_score", "psychology_score", "research", "research_package",
        "director_package", "scene_breakdown",
    ]
    return [k for k in candidates if item.get(k)]


def collect_episode_design_items(context: dict) -> "tuple[list, str]":
    """Items this engine should process — mirrors ai_director collection order."""
    packages = context.get("unified_packages") or []
    if packages:
        return list(packages), "unified_packages"
    for key in ("ideas", "selected_ideas", "candidates"):
        items = context.get(key) or []
        if items:
            return list(items), key
    return [], ""


def build_episode_design_package(item: dict, context: dict | None = None) -> dict:
    """One complete EpisodeDesignPackage for one content item.

    Reads (never mutates): script, hook, quality_score, psychology_score,
    visual_package, script_package, scene_breakdown, research.
    Writes only: item["episode_design_package"].
    """
    context = context or {}
    blockers: list[str] = []

    blueprint = build_lesson_blueprint(item, context)
    retention = build_retention_review(item, blueprint)
    series = build_series_design(item, context)

    retention_score = retention["scores"].get("overall_score", 0)
    upstream = _upstream_slots_read(item)

    status = _episode_design_status(retention_score, blockers)
    confidence = retention_score

    design_questions = retention.get("strategic_answers", {})
    revisions = retention.get("revisions", [])

    package = {
        "episode_design_package_version": EPISODE_DESIGN_PACKAGE_VERSION,
        "engine_version": EPISODE_DESIGN_ENGINE_VERSION,
        "project_id": str(item.get("project_id", "")),
        "lesson_blueprint": blueprint,
        "retention_review": retention,
        "series_design": series,
        "design_questions": design_questions,
        "revision_notes": revisions,
        "upstream_slots_read": upstream,
        "validation": {
            "status": status,
            "confidence": confidence,
            "blockers": blockers,
        },
        "episode_design_diagnostics": {
            "retention_score": retention_score,
            "revision_count": len(revisions),
            "series_type": series.get("series_type"),
            "blueprint_beats": len(blueprint.get("beats", [])),
            "upstream_slots": upstream,
        },
        "generated_at": _now_iso(),
    }

    return package


def run_episode_design_engine(context: dict) -> dict:
    """Build EpisodeDesignPackages for all items in context.

    Returns context updates — never mutates unowned slots.
    Empty context → no_items summary. Per-item failure → degraded package,
    siblings continue.
    """
    from core.log import get_logger, log_event
    logger = get_logger(__name__)

    items, source_key = collect_episode_design_items(context)

    if not items:
        summary = _build_summary([], items=0)
        summary["reason"] = "No content in context — nothing to design."
        return {
            "episode_design_summary": summary,
            "episode_design_packages": [],
        }

    packages = []
    for item in items:
        try:
            package = build_episode_design_package(item, context)
            item["episode_design_package"] = package
        except Exception as exc:  # noqa: BLE001 - one bad item never stops the engine
            package = {
                "engine_version": EPISODE_DESIGN_ENGINE_VERSION,
                "project_id": str(item.get("project_id", "")),
                "validation": {
                    "status": EpisodeDesignStatus.INCOMPLETE,
                    "confidence": 0,
                    "blockers": [f"episode design failed: {exc}"],
                },
            }
            log_event(
                logger, "episode_design.item_failed", level=30,
                project_id=str(item.get("project_id", "")), error=str(exc)[:120],
            )
        packages.append(package)

    summary = _build_summary(packages, items=len(items))
    playbook_update = _strengthen_playbook(packages, context)
    if playbook_update:
        summary["playbook"] = playbook_update

    log_event(
        logger, "episode_design.completed",
        items=len(items), packages=len(packages),
        ready=summary["ready"], source=source_key or "none",
    )

    updates: dict = {
        "episode_design_summary": summary,
        "episode_design_packages": packages,
    }
    if source_key:
        updates[source_key] = context.get(source_key, [])
    return updates


def _strengthen_playbook(packages: list, context: dict) -> dict:
    """Feed high-scoring lessons into the Generational Episode Playbook."""
    from services.episode_design.playbook import get_playbook

    data_dir = context.get("episode_playbook_dir")
    try:
        playbook = get_playbook(data_dir=data_dir)
    except Exception:  # noqa: BLE001
        return {}

    recorded = 0
    for package in packages:
        score = int((package.get("episode_design_diagnostics") or {}).get("retention_score") or 0)
        if score < 70:
            continue
        niche = str((package.get("lesson_blueprint") or {}).get("niche") or "general")
        topic = str((package.get("lesson_blueprint") or {}).get("topic") or "lesson")
        revisions = package.get("revision_notes") or []
        strengths = ["retention_ready"] if score >= 75 else []
        weaknesses = [str(r)[:120] for r in revisions[:3] if r]
        pattern_id = playbook.record_pattern(
            pattern_name=f"{niche} educational flow",
            niche=niche,
            description=f"Canonical 7-beat blueprint applied to '{topic}'.",
            strengths=strengths,
            weaknesses=weaknesses,
        )
        playbook.record_success(
            pattern_id,
            project_id=str(package.get("project_id") or ""),
            retention_score=score,
        )
        recorded += 1
    return playbook.summary() if recorded else {}


def _build_summary(packages: list, items: int) -> dict:
    validations = [pkg.get("validation", {}) for pkg in packages]
    statuses = [v.get("status", EpisodeDesignStatus.INCOMPLETE) for v in validations]
    scores = [
        int(pkg.get("episode_design_diagnostics", {}).get("retention_score", 0))
        for pkg in packages
        if pkg.get("episode_design_diagnostics")
    ]
    niches = sorted({
        pkg.get("lesson_blueprint", {}).get("niche", "")
        for pkg in packages
        if pkg.get("lesson_blueprint")
    } - {""})

    overall = "designed"
    if not packages:
        overall = "no_items"
    elif statuses.count(EpisodeDesignStatus.INCOMPLETE) == len(packages) and packages:
        overall = "degraded"

    return {
        "engine_version": EPISODE_DESIGN_ENGINE_VERSION,
        "status": overall,
        "items": items,
        "packages": len(packages),
        "ready": statuses.count(EpisodeDesignStatus.READY),
        "needs_review": statuses.count(EpisodeDesignStatus.NEEDS_REVIEW),
        "degraded": statuses.count(EpisodeDesignStatus.DEGRADED),
        "incomplete": statuses.count(EpisodeDesignStatus.INCOMPLETE),
        "average_retention_score": int(round(sum(scores) / len(scores))) if scores else 0,
        "niches": niches,
        "generated_at": _now_iso(),
    }
