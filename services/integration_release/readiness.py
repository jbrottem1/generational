"""Composite release readiness for Agent 28."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from services.integration_release.audit import SUBSYSTEMS, audit_subsystems


def _department_scores(audit: list[dict[str, Any]]) -> dict[str, float]:
    by_owner: dict[int, list[str]] = {}
    for row in audit:
        owner = int(row.get("owner") or 0)
        status = row.get("production_readiness") or "review"
        by_owner.setdefault(owner, []).append(status)
    scores: dict[str, float] = {}
    dept_names = {
        0: "Executive",
        1: "Engineering",
        4: "Visual Intelligence",
        6: "Render",
        7: "Publishing",
        16: "Animation",
        19: "Platform",
        20: "Studio UI",
        26: "Character Systems",
        27: "Knowledge Standards",
    }
    for owner, statuses in by_owner.items():
        ready = sum(1 for s in statuses if s == "ready")
        scores[dept_names.get(owner, f"agent_{owner}")] = round(
            100 * ready / max(1, len(statuses)), 1
        )
    return scores


def build_release_dashboard() -> dict[str, Any]:
    """Executive release dashboard snapshot."""
    audit = audit_subsystems(quick=True)
    dept = _department_scores(audit)

    # Test baseline (from last full run — update via CI)
    test_baseline = {
        "passed": 933,
        "failed": 13,
        "total": 946,
        "pass_rate_pct": round(933 / 946 * 100, 1),
        "target_pass_rate_pct": 98.5,
    }

    blockers = [
        "13 pytest failures (render_engine, research_engine, engines, workflows, project workspace)",
        "Live OAuth / API keys absent in default environment",
        "Phoneme lip-sync still amplitude stub",
        "Atlas UI browser not shipped (Platform backlog)",
    ]

    overall = round(
        (
            test_baseline["pass_rate_pct"] * 0.35
            + sum(dept.values()) / max(1, len(dept)) * 0.40
            + 85 * 0.25  # architecture / RC1 evidence weight
        ),
        1,
    )

    return {
        "schema_version": 1,
        "owner_agent": 28,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall_readiness_score": overall,
        "readiness_band": (
            "production_candidate" if overall >= 85 else "integration_review"
        ),
        "department_readiness": dept,
        "test_baseline": test_baseline,
        "critical_blockers": blockers,
        "subsystem_audit": audit,
        "upcoming_releases": ["1.0.0-rc3 Foundation + Reality + Atlas integration"],
        "technical_debt_count": 8,
        "foundation_shorts_status": {
            "project_reality": "approved",
            "knowledge_atlas": "approved",
            "batesian_series": "3/3 QC pass",
        },
    }
