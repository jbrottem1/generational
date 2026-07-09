"""ExecutiveReporter — daily through annual and specialized reports."""

from __future__ import annotations

from services.executive.models import EXECUTIVE_ENGINE_VERSION, ReportKind, _now_iso


class ExecutiveReporter:
    """Generate the executive report suite from plan and health data."""

    def build_all(self, plan: dict, health: dict, context: dict) -> dict:
        base = {
            "topic": context.get("topic") or plan.get("observations", {}).get("topic", ""),
            "decisions": len(plan.get("decisions") or []),
            "health_level": health.get("level"),
            "health_score": health.get("score", 0),
        }

        reports = {
            ReportKind.DAILY: self._period_report("daily", base, plan),
            ReportKind.WEEKLY: self._period_report("weekly", base, plan),
            ReportKind.MONTHLY: self._period_report("monthly", base, plan),
            ReportKind.QUARTERLY: self._period_report("quarterly", base, plan),
            ReportKind.ANNUAL: self._period_report("annual", base, plan),
            ReportKind.CAMPAIGN: self._campaign_report(plan, context),
            ReportKind.GROWTH: self._growth_report(plan, health),
            ReportKind.EXECUTIVE_SUMMARY: self._executive_summary(plan, health),
            ReportKind.PRODUCTION: self._production_report(context, plan),
            ReportKind.FINANCIAL: self._financial_report(plan),
        }

        return {
            "engine_version": EXECUTIVE_ENGINE_VERSION,
            "reports": reports,
            "generated_at": _now_iso(),
        }

    def _period_report(self, period: str, base: dict, plan: dict) -> dict:
        return {
            "period": period,
            "summary": f"{period.title()} executive review for {base.get('topic') or 'portfolio'}",
            "decisions_reviewed": base["decisions"],
            "top_priority": (plan.get("priorities") or ["—"])[0],
            "health_level": base["health_level"],
        }

    def _campaign_report(self, plan: dict, context: dict) -> dict:
        campaigns = plan.get("strategy", {}).get("campaigns") or []
        return {
            "campaigns": campaigns[:5],
            "market_report_present": bool(context.get("market_intelligence_report")),
            "active_campaigns": len(campaigns),
        }

    def _growth_report(self, plan: dict, health: dict) -> dict:
        themes = plan.get("strategy", {}).get("growth_themes") or []
        return {
            "themes": themes,
            "health_score": health.get("score", 0),
            "goals": plan.get("goals") or [],
        }

    def _executive_summary(self, plan: dict, health: dict) -> dict:
        decisions = plan.get("decisions") or []
        avg_priority = (
            int(round(sum(d.get("priority", 0) for d in decisions) / len(decisions)))
            if decisions else 0
        )
        return {
            "vision": plan.get("vision", ""),
            "health_level": health.get("level"),
            "decisions": len(decisions),
            "average_priority": avg_priority,
            "top_actions": plan.get("priorities", [])[:3],
        }

    def _production_report(self, context: dict, plan: dict) -> dict:
        packages = context.get("unified_packages") or []
        return {
            "packages_in_context": len(packages),
            "publish_ready": sum(1 for p in packages if p.get("publish_ready")),
            "planned_stages": sorted({
                d.get("delegated_stage", "")
                for d in (plan.get("decisions") or [])
                if d.get("delegated_stage")
            }),
        }

    def _financial_report(self, plan: dict) -> dict:
        decisions = plan.get("decisions") or []
        total_revenue = sum(int(d.get("revenue_estimate", 0)) for d in decisions)
        total_cost = sum(int(d.get("cost_estimate", 0)) for d in decisions)
        return {
            "revenue_estimate": total_revenue,
            "cost_estimate": total_cost,
            "roi_weighted": (
                int(round(sum(d.get("roi_score", 0) for d in decisions) / len(decisions)))
                if decisions else 0
            ),
            "budget_plan": plan.get("resource_plan", {}).get("budget_total", 0),
        }
