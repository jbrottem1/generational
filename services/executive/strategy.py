"""ExecutiveStrategy — vision, brands, channels, campaigns, growth themes."""

from __future__ import annotations

from services.executive.models import _now_iso


class ExecutiveStrategy:
    """Company-level strategic framing consumed by planner and reports."""

    def build(self, context: dict) -> dict:
        topic = context.get("topic") or context.get("trend_subject") or "general content"
        category = context.get("trend_category", "general")
        opportunities = context.get("market_opportunities") or []

        platforms = sorted({
            str(op.get("platform", ""))
            for op in opportunities
            if op.get("platform")
        })
        if not platforms:
            platforms = ["youtube_shorts", "tiktok"]

        return {
            "vision": f"Build a dominant {category} media brand around {topic}",
            "brands": [
                {
                    "brand_id": context.get("brand_id") or "default",
                    "name": context.get("brand") or "Generational",
                    "focus": category,
                }
            ],
            "channels": [
                {"platform": platform, "priority": idx + 1}
                for idx, platform in enumerate(platforms[:5])
            ],
            "campaigns": self._campaigns(opportunities, topic),
            "growth_themes": self._growth_themes(opportunities, category),
            "generated_at": _now_iso(),
        }

    def _campaigns(self, opportunities: list, topic: str) -> list:
        campaigns = []
        for idx, op in enumerate(opportunities[:5]):
            campaigns.append({
                "campaign_id": f"camp_{idx + 1}",
                "title": op.get("title") or op.get("topic") or topic,
                "platform": op.get("platform", ""),
                "priority": int(op.get("priority", 50)),
                "roi_estimate": int(op.get("roi_score", op.get("roi_estimate", 0)) or 0),
            })
        if not campaigns:
            campaigns.append({
                "campaign_id": "camp_default",
                "title": topic,
                "platform": "youtube_shorts",
                "priority": 50,
                "roi_estimate": 50,
            })
        return campaigns

    def _growth_themes(self, opportunities: list, category: str) -> list:
        themes = sorted({
            str(op.get("content_type") or op.get("niche") or category)
            for op in opportunities
            if op.get("content_type") or op.get("niche")
        })
        if not themes:
            themes = [category, "evergreen", "trending"]
        return [{"theme": theme, "weight": max(10, 100 - idx * 15)} for idx, theme in enumerate(themes[:5])]
