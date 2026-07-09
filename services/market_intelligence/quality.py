"""Department quality gate — only valid, trustworthy opportunities ship.

Validates the assembled MarketOpportunity batch (the raw signal batch is
already cleaned upstream by `services/trend_intelligence/quality.py`):

- duplicate opportunities        → collapsed, highest priority survives
- invalid forecasts              → dropped (validate_forecast findings)
- missing signals                → dropped (no topic / no provenance)
- low confidence                 → dropped below the configured gate
- conflicting recommendations    → repaired (publish_immediately + delay /
                                   monitor cannot coexist; priority order wins)
- provider failures              → reported (counts from the discovery pass)

Everything degrades gracefully: findings are reported, never raised.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from core.log import get_logger, log_event
from services.market_intelligence.config import (
    MarketIntelligenceConfig,
    get_market_intelligence_config,
)
from services.market_intelligence.forecasting import validate_forecast
from services.market_intelligence.models import STRATEGIC_ACTION, MarketOpportunity

logger = get_logger(__name__)

_WORD_RE = re.compile(r"[a-z0-9]+")

# Action pairs that cannot both be recommended for one opportunity.
_CONFLICTING_ACTIONS = (
    (STRATEGIC_ACTION.PUBLISH_IMMEDIATELY, STRATEGIC_ACTION.DELAY),
    (STRATEGIC_ACTION.PUBLISH_IMMEDIATELY, STRATEGIC_ACTION.MONITOR),
)


@dataclass
class ValidationReport:
    total: int = 0
    kept: int = 0
    dropped: dict = field(default_factory=lambda: {
        "duplicate": 0, "invalid_forecast": 0, "missing_signals": 0, "low_confidence": 0,
    })
    repaired_conflicts: int = 0
    findings: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "kept": self.kept,
            "dropped": dict(self.dropped),
            "dropped_total": sum(self.dropped.values()),
            "repaired_conflicts": self.repaired_conflicts,
            "findings": list(self.findings),
        }


def _topic_key(opportunity: MarketOpportunity) -> str:
    return " ".join(_WORD_RE.findall(opportunity.topic.lower())) + f"|{opportunity.platform}"


def _repair_actions(opportunity: MarketOpportunity, report: ValidationReport) -> None:
    """Conflicting strategic actions: the earlier (higher-priority) one wins."""
    actions = list(opportunity.strategic_actions)
    for first, second in _CONFLICTING_ACTIONS:
        if first in actions and second in actions:
            loser = second if actions.index(first) < actions.index(second) else first
            actions.remove(loser)
            report.repaired_conflicts += 1
            report.findings.append(
                f"conflicting actions on '{opportunity.topic}': dropped {loser}"
            )
    opportunity.strategic_actions = actions


def validate_opportunities(
    opportunities: "list[MarketOpportunity]",
    config: "MarketIntelligenceConfig | None" = None,
    provider_failures: int = 0,
) -> "tuple[list[MarketOpportunity], ValidationReport]":
    """Filter/repair the batch. Returns (kept, report). Never raises."""
    config = config or get_market_intelligence_config()
    report = ValidationReport(total=len(opportunities))
    if provider_failures:
        report.findings.append(f"provider_failures: {provider_failures}")

    kept: "list[MarketOpportunity]" = []
    seen: "dict[str, int]" = {}
    for opportunity in opportunities:
        if not opportunity.topic or not opportunity.signals.get("source"):
            report.dropped["missing_signals"] += 1
            continue

        forecast_problems = validate_forecast(opportunity.forecast)
        if forecast_problems:
            report.dropped["invalid_forecast"] += 1
            report.findings.extend(
                f"'{opportunity.topic}': {problem}" for problem in forecast_problems
            )
            continue

        if opportunity.confidence < config.min_confidence:
            report.dropped["low_confidence"] += 1
            continue

        key = _topic_key(opportunity)
        if key in seen:
            index = seen[key]
            if opportunity.priority > kept[index].priority:
                kept[index] = opportunity
            report.dropped["duplicate"] += 1
            continue

        _repair_actions(opportunity, report)
        seen[key] = len(kept)
        kept.append(opportunity)

    report.kept = len(kept)
    log_event(
        logger, "market_intelligence.validated",
        total=report.total, kept=report.kept,
        dropped=sum(report.dropped.values()), repaired=report.repaired_conflicts,
    )
    return kept, report
