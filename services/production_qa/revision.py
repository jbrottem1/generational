"""Revision routing — map failing PQA categories to owning engines."""

from __future__ import annotations

from services.production_qa.models import (
    CATEGORY_PASS_THRESHOLD,
    CRITICAL_BLOCK_FLOOR,
    REVISION_OWNERS,
    CategoryScore,
    RevisionRequest,
)

CRITICAL_CATEGORIES = frozenset({"research_accuracy", "evidence", "visuals", "educational_value"})


def build_revision_requests(
    categories: dict[str, CategoryScore],
    *,
    hard_fails: list[str] | None = None,
) -> list[RevisionRequest]:
    """Create structured revision requests for every category below the pass bar."""
    requests: list[RevisionRequest] = []
    hard_fails = hard_fails or []

    for key, cat in categories.items():
        if cat.score >= CATEGORY_PASS_THRESHOLD and not cat.corrections_required:
            continue
        if cat.score >= CATEGORY_PASS_THRESHOLD:
            continue

        severity = "block" if (
            key in CRITICAL_CATEGORIES and cat.score < CRITICAL_BLOCK_FLOOR
        ) or any(key in f or cat.label.lower() in f.lower() for f in hard_fails) else "revision"

        owners = list(REVISION_OWNERS.get(key) or REVISION_OWNERS.get("visuals") or ["quality"])
        message = cat.issues[0] if cat.issues else f"{cat.label} scored {cat.score} (< {CATEGORY_PASS_THRESHOLD})"
        requests.append(
            RevisionRequest(
                category=key,
                score=cat.score,
                target_engines=owners,
                severity=severity,
                message=message,
                corrections=list(cat.corrections_required or cat.issues),
            )
        )
    return requests


def group_revisions_by_engine(requests: list[RevisionRequest]) -> dict[str, list[dict]]:
    """Fan-out map: engine_key → list of revision payloads."""
    by_engine: dict[str, list[dict]] = {}
    for req in requests:
        payload = req.to_dict()
        for engine in req.target_engines:
            by_engine.setdefault(engine, []).append(payload)
    return by_engine
