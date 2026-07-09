"""CompanyHealthMonitor — aggregate health signals for the executive layer."""

from __future__ import annotations

from services.executive.models import HealthLevel, _now_iso


class CompanyHealthMonitor:
    """Synthesize pipeline, analytics, and risk signals into health KPIs."""

    def assess(self, context: dict, decisions: list, risk_summary: dict) -> dict:
        analytics = context.get("analytics_summary") or {}
        learning = context.get("learning_report") or {}

        views = int(analytics.get("total_views", 0) or 0)
        retention = int(analytics.get("average_retention", 0) or 0)
        records = int(analytics.get("records", learning.get("records_analyzed", 0)) or 0)
        portfolio_risk = int(risk_summary.get("portfolio_risk_score", 50) or 50)

        score = self._health_score(views, retention, records, portfolio_risk, len(decisions))
        level = self._level(score, portfolio_risk)

        return {
            "level": level,
            "score": score,
            "kpis": {
                "total_views": views,
                "average_retention": retention,
                "analytics_records": records,
                "active_decisions": len(decisions),
                "portfolio_risk": portfolio_risk,
            },
            "signals": {
                "analytics_present": bool(analytics),
                "learning_present": bool(learning),
                "market_present": bool(context.get("market_opportunities")),
            },
            "generated_at": _now_iso(),
        }

    def _health_score(
        self, views: int, retention: int, records: int, risk: int, decisions: int,
    ) -> int:
        base = min(100, views // 1000 + retention // 2 + records * 2 + decisions * 3)
        return max(0, min(100, base - risk // 3))

    def _level(self, score: int, risk: int) -> str:
        if risk >= 75 or score < 20:
            return HealthLevel.CRITICAL
        if risk >= 55 or score < 40:
            return HealthLevel.WARNING
        if score >= 75:
            return HealthLevel.THRIVING
        if score >= 55:
            return HealthLevel.GROWING
        return HealthLevel.STABLE
