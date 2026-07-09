"""ExecutiveDecisionEngine — what to produce next with ROI and risk scoring."""

from __future__ import annotations

from services.executive.models import DecisionStatus, ExecutiveDecision, new_id


class ExecutiveDecisionEngine:
    """Turn market opportunities and context signals into ranked decisions."""

    def build_decisions(self, context: dict) -> list[dict]:
        opportunities = context.get("market_opportunities") or []
        if not opportunities:
            opportunities = self._fallback_from_packages(context)

        decisions = []
        for idx, op in enumerate(opportunities[:15]):
            decision = self._from_opportunity(op, idx, context)
            decisions.append(decision.to_dict())

        decisions.sort(key=lambda d: d["priority"], reverse=True)
        return decisions

    def _from_opportunity(self, op: dict, idx: int, context: dict) -> ExecutiveDecision:
        roi = int(op.get("roi_score", op.get("roi_estimate", 0)) or 0)
        views = int(op.get("expected_views", op.get("views_estimate", 0)) or 0)
        retention = int(op.get("retention_estimate", op.get("expected_retention", 55)) or 55)
        competition = int(op.get("competition_score", op.get("competition", 50)) or 50)
        opportunity_score = int(op.get("opportunity_score", op.get("priority", 50)) or 50)

        cost = max(10, 100 - roi // 2)
        revenue = max(views // 1000, roi)
        risk = min(100, max(0, competition + (100 - retention) // 2))
        confidence = min(100, max(20, opportunity_score - idx * 2))
        priority = min(100, max(0, int(round(roi * 0.4 + confidence * 0.3 + (100 - risk) * 0.3))))

        title = op.get("title") or op.get("topic") or context.get("topic") or "Untitled opportunity"
        platform = op.get("platform") or "youtube_shorts"

        return ExecutiveDecision(
            decision_id=new_id("dec"),
            title=str(title)[:120],
            topic=str(op.get("topic") or title)[:120],
            platform=str(platform),
            status=DecisionStatus.PROPOSED,
            roi_score=roi,
            views_estimate=views or max(1000, priority * 100),
            retention_estimate=retention,
            cost_estimate=cost,
            revenue_estimate=revenue,
            risk_score=risk,
            confidence=confidence,
            priority=priority,
            rationale=op.get("rationale") or f"Ranked #{idx + 1} from market intelligence",
            delegated_stage=self._stage_for_platform(platform),
        )

    def _fallback_from_packages(self, context: dict) -> list:
        items = context.get("unified_packages") or context.get("ideas") or []
        fallback = []
        for item in items[:5]:
            fallback.append({
                "title": item.get("title") or item.get("topic") or "Package item",
                "topic": item.get("topic", ""),
                "platform": (item.get("target_platforms") or ["youtube_shorts"])[0],
                "roi_score": int(item.get("opportunity_score", 50) or 50),
                "expected_views": int(item.get("virality_score", 0) or 0) * 100,
                "retention_estimate": int(item.get("quality_score", 55) or 55),
                "competition_score": int(item.get("competition_score", 50) or 50),
                "opportunity_score": int(item.get("opportunity_score", 50) or 50),
            })
        return fallback

    @staticmethod
    def _stage_for_platform(platform: str) -> str:
        mapping = {
            "youtube": "publish",
            "youtube_shorts": "publish",
            "tiktok": "publish",
            "instagram": "publish",
        }
        return mapping.get(platform, "research")
