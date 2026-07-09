"""Learning bridge — Analytics history calibrates every market prediction.

Reads Agent 9's analytics store (real post-publish outcomes) and distills
it into calibration factors the department applies everywhere:

- `historical_performance` (0-1)  → opportunity ranking (per category)
- `roi_calibration` (0.5-1.5)     → ROI estimates scale with real results
- `confidence_calibration`        → forecast confidence earns trust from
                                    evidence volume
- `competition_calibration`       → observed engagement corrects the
                                    competition heuristics
- `historical_similarity` (0-1)   → how closely a candidate matches our
                                    proven winners (category + platform)

With no history yet every factor is neutral — the department behaves
exactly as before learning data arrives, and it never raises.
"""

from __future__ import annotations

from core.log import get_logger, log_event
from services.trend_intelligence.history import historical_performance_for

logger = get_logger(__name__)

NEUTRAL_CALIBRATION = {
    "historical_performance": 0.5,
    "roi_calibration": 1.0,
    "confidence_calibration": 1.0,
    "competition_calibration": 1.0,
    "evidence_records": 0,
    "winner_profiles": [],
}

_MAX_RECORDS = 300
_WINNER_SCORE = 70          # performance score at/above which a record is a "winner"


def _safe_records(analytics_store=None) -> list:
    try:
        if analytics_store is None:
            from services.analytics import get_analytics_store

            analytics_store = get_analytics_store()
        return analytics_store.list_records(limit=_MAX_RECORDS)
    except Exception as exc:  # noqa: BLE001 - learning must never break intelligence
        log_event(logger, "market_intelligence.learning_read_failed", level=30, error=str(exc))
        return []


def _performance(record: dict) -> "float | None":
    try:
        from services.analytics import performance_score

        metrics = record.get("metrics") or {}
        if not metrics or record.get("metrics_status") != "collected":
            return None
        return float(performance_score(metrics))
    except Exception:  # noqa: BLE001
        return None


def build_calibration(
    category: str = "general",
    analytics_store=None,
    knowledge_base=None,
) -> dict:
    """One calibration dict per discovery pass. Deterministic, never raises."""
    records = _safe_records(analytics_store)
    scored = [(r, p) for r in records if (p := _performance(r)) is not None]

    if not scored:
        calibration = dict(NEUTRAL_CALIBRATION)
        calibration["historical_performance"] = historical_performance_for(
            category, knowledge_base
        )
        return calibration

    scores = [p for _, p in scored]
    average = sum(scores) / len(scores)          # 0-100
    # Evidence-weighted trust: 10+ collected records = full calibration weight.
    evidence_weight = min(1.0, len(scored) / 10.0)

    # Real outcomes above/below the neutral 50 push ROI and competition
    # estimates up/down, damped by how much evidence exists.
    outcome_shift = (average - 50.0) / 100.0     # -0.5 .. +0.5
    roi_calibration = round(1.0 + outcome_shift * evidence_weight, 3)
    competition_calibration = round(1.0 + outcome_shift * 0.5 * evidence_weight, 3)
    confidence_calibration = round(0.9 + 0.2 * evidence_weight, 3)

    winners = [
        {
            "niche": (record.get("niche") or "").lower(),
            "platform": (record.get("platform") or "").lower(),
            "topic": record.get("topic", ""),
            "performance": performance,
        }
        for record, performance in scored
        if performance >= _WINNER_SCORE
    ]

    calibration = {
        "historical_performance": historical_performance_for(category, knowledge_base),
        "roi_calibration": max(0.5, min(1.5, roi_calibration)),
        "confidence_calibration": max(0.5, min(1.2, confidence_calibration)),
        "competition_calibration": max(0.6, min(1.4, competition_calibration)),
        "evidence_records": len(scored),
        "winner_profiles": winners[:50],
    }
    log_event(
        logger, "market_intelligence.calibration_built",
        evidence=len(scored), winners=len(winners),
        roi_calibration=calibration["roi_calibration"],
    )
    return calibration


def historical_similarity(category: str, platform: str, calibration: dict) -> float:
    """0-1: how closely (category, platform) matches our proven winners.

    0.5 = no history (neutral). Higher = we've won here before.
    """
    winners = calibration.get("winner_profiles") or []
    if not winners:
        return 0.5
    category = (category or "").lower()
    platform = (platform or "").lower()
    matches = sum(
        1
        for winner in winners
        if winner.get("niche", "").startswith(category[:6]) or winner.get("platform") == platform
    )
    return round(min(1.0, 0.5 + matches / (2.0 * len(winners))), 3)
