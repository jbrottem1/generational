"""Content calendar + report writers."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "data" / "trend_opportunity" / "reports"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_content_calendar(opportunities: list[dict[str, Any]], *, days: int = 14) -> dict[str, Any]:
    """Schedule top opportunities across the next N days."""
    start = datetime.now(timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0)
    slots = []
    for i, opp in enumerate(opportunities[:days]):
        day = start + timedelta(days=i)
        slots.append(
            {
                "date": day.date().isoformat(),
                "recommended_upload_time": (opp.get("strategy") or {}).get("recommended_upload_time"),
                "topic": opp.get("topic"),
                "working_title": (opp.get("strategy") or {}).get("working_title"),
                "platform": (opp.get("strategy") or {}).get("recommended_platform") or "youtube_shorts",
                "priority": opp.get("production_priority"),
                "overall_opportunity_score": opp.get("overall_opportunity_score"),
                "opportunity_id": opp.get("opportunity_id"),
                "status": opp.get("status"),
            }
        )
    return {
        "generated_at": _now(),
        "horizon_days": days,
        "slots": slots,
        "note": "Advisory calendar — Publishing Intelligence remains publish authority",
    }


def write_outputs(
    *,
    top_opportunities: list[dict[str, Any]],
    opportunity_report: dict[str, Any],
    trend_report_md: str,
    production_briefs: list[dict[str, Any]],
    calendar: dict[str, Any],
    out_dir: Path | None = None,
) -> dict[str, str]:
    """Write mission artifacts under data/trend_opportunity/reports (and copies of canonical names)."""
    base = out_dir or OUT_DIR
    base.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    paths = {}

    def dump(name: str, data: Any) -> str:
        path = base / name
        if name.endswith(".md"):
            path.write_text(str(data), encoding="utf-8")
        else:
            path.write_text(json.dumps(data, indent=2, default=str) + "\n", encoding="utf-8")
        paths[name] = str(path)
        return str(path)

    dump("TOP_OPPORTUNITIES.json", {"generated_at": _now(), "count": len(top_opportunities), "opportunities": top_opportunities})
    dump("OPPORTUNITY_REPORT.json", opportunity_report)
    dump("TREND_REPORT.md", trend_report_md)
    # PRODUCTION_BRIEF.md for #1
    brief0 = production_briefs[0] if production_briefs else {}
    md_brief = format_production_brief_md(brief0)
    dump("PRODUCTION_BRIEF.md", md_brief)
    dump("CONTENT_CALENDAR.json", calendar)
    # Also stamp archive copies
    dump(f"TOP_OPPORTUNITIES_{stamp}.json", {"generated_at": _now(), "opportunities": top_opportunities})
    if production_briefs:
        dump("PRODUCTION_BRIEFS.json", {"count": len(production_briefs), "briefs": production_briefs})
    return paths


def format_production_brief_md(brief: dict[str, Any]) -> str:
    if not brief:
        return "# Production Brief\n\n_No brief generated._\n"
    lines = [
        "# Production Brief",
        "",
        f"**Topic:** {brief.get('topic')}",
        f"**Working Title:** {brief.get('working_title')}",
        f"**Platform:** {brief.get('platform')}",
        f"**Duration:** {brief.get('duration_sec') or brief.get('duration')}s",
        f"**Opportunity Score:** {brief.get('overall_opportunity_score')}",
        f"**Manual editing required:** {brief.get('manual_editing_required')}",
        "",
        "## Objective",
        "",
        str(brief.get("objective") or ""),
        "",
        "## Hook",
        "",
        str(brief.get("hook") or ""),
        "",
        "## Target Audience",
        "",
        str(brief.get("target_audience") or ""),
        "",
        "## Research Goals",
        "",
    ]
    for g in brief.get("research_goals") or []:
        lines.append(f"- {g}")
    lines += [
        "",
        "## Production Specs",
        "",
        f"- **World:** {brief.get('world_selection')}",
        f"- **Narrator:** {brief.get('narrator')}",
        f"- **Style:** {brief.get('style')}",
        f"- **Visual direction:** {brief.get('visual_direction')}",
        f"- **Thumbnail:** {brief.get('thumbnail_direction')}",
        "",
        "## Pipeline Command",
        "",
        "```",
        str(brief.get("command") or ""),
        "```",
        "",
        "_Feeds Research Engine → Psychology → Script → … without manual editing._",
        "",
    ]
    return "\n".join(lines)


def format_trend_report_md(report: dict[str, Any]) -> str:
    lines = [
        "# Trend Report",
        "",
        f"**Category:** {report.get('category')}",
        f"**Generated:** {report.get('generated_at')}",
        f"**Signals:** {report.get('signal_count')} trends from {len(report.get('sources') or {})} sources",
        f"**Ranked opportunities:** {report.get('ranked_count')}",
        f"**Accepted:** {report.get('accepted_count')} · **Rejected:** {report.get('rejected_count')}",
        "",
        "## Top opportunities",
        "",
    ]
    for i, opp in enumerate(report.get("top_opportunities") or [], 1):
        lines.append(
            f"{i}. **{opp.get('topic')}** — score {opp.get('overall_opportunity_score')} "
            f"(priority {opp.get('production_priority')})"
        )
    lines += ["", "## Provider interfaces", ""]
    for p in report.get("provider_interfaces") or []:
        lines.append(
            f"- `{p.get('mission_key')}` → {p.get('provider_key')} "
            f"({'available' if p.get('available') else 'stub/offline'})"
        )
    lines += ["", "_Trend & Opportunity Intelligence — executive layer only._", ""]
    return "\n".join(lines)
