"""ExecutiveRiskEngine — portfolio and production risk scoring."""

from __future__ import annotations

from services.executive.models import HealthLevel


class ExecutiveRiskEngine:
    """Score operational and content risks from context signals."""

    def assess(self, context: dict, decisions: list) -> dict:
        opportunities = context.get("market_opportunities") or []
        avg_competition = self._average(
            [int(op.get("competition_score", op.get("competition", 50)) or 50) for op in opportunities]
        )
        avg_risk = self._average([int(d.get("risk_score", 50)) for d in decisions]) if decisions else 50

        threat_level = int(context.get("threat_report", {}).get("overall_threat", 0) or 0)
        portfolio_risk = int(round((avg_competition + avg_risk + threat_level) / 3))

        if portfolio_risk >= 75:
            level = HealthLevel.CRITICAL
        elif portfolio_risk >= 55:
            level = HealthLevel.WARNING
        elif portfolio_risk >= 35:
            level = HealthLevel.STABLE
        else:
            level = HealthLevel.GROWING

        return {
            "portfolio_risk_score": portfolio_risk,
            "level": level,
            "factors": {
                "competition": avg_competition,
                "decision_risk": avg_risk,
                "threat": threat_level,
            },
            "mitigations": self._mitigations(portfolio_risk, decisions),
        }

    def _mitigations(self, risk: int, decisions: list) -> list:
        tips = []
        if risk >= 60:
            tips.append("Diversify platforms and reduce single-topic concentration")
        if decisions and max(int(d.get("risk_score", 0)) for d in decisions) >= 70:
            tips.append("Defer highest-risk decisions until validation data arrives")
        if not tips:
            tips.append("Maintain current risk posture — monitor weekly")
        return tips

    @staticmethod
    def _average(values: list) -> int:
        return int(round(sum(values) / len(values))) if values else 0
