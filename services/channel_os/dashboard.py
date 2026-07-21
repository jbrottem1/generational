"""Channel Dashboard — multi-brand operating board."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.env import project_root
from services.channel_os.store import ROOT, list_channel_productions, list_profiles

DASHBOARD_JSON = ROOT / "CHANNEL_DASHBOARD.json"
DASHBOARD_MD = project_root() / "CHANNEL_DASHBOARD.md"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_channel_dashboard() -> dict[str, Any]:
    profiles = list_profiles(status=None)
    active = [p for p in profiles if p.get("status") == "active"]
    productions = list_channel_productions(limit=100)

    published = sum(int((p.get("metrics") or {}).get("videos_published") or 0) for p in profiles)
    scheduled = sum(int((p.get("metrics") or {}).get("videos_scheduled") or 0) for p in profiles)

    creative_vals = [
        float((p.get("metrics") or {}).get("average_creative_score"))
        for p in profiles
        if (p.get("metrics") or {}).get("average_creative_score") is not None
    ]

    # Top topics from recent productions
    topic_counts: dict[str, int] = {}
    for row in productions:
        t = str(row.get("topic") or "")
        if t:
            topic_counts[t] = topic_counts.get(t, 0) + 1
    top_topics = sorted(topic_counts.items(), key=lambda kv: -kv[1])[:10]

    # Lessons from analytics_history / audience soft notes
    lessons: list[str] = []
    for p in profiles:
        for event in reversed(list(p.get("analytics_history") or [])[-3:]):
            lessons.append(
                f"{p.get('brand_name')}: {event.get('topic')} · score={event.get('creative_score')}"
            )

    # Channel health: active + recent success rate
    channel_health = []
    for p in active:
        ch_id = p.get("channel_id")
        rows = [r for r in productions if r.get("channel_id") == ch_id]
        succ = sum(1 for r in rows if r.get("success"))
        channel_health.append(
            {
                "channel_id": ch_id,
                "brand_name": p.get("brand_name"),
                "status": p.get("status"),
                "videos_published": (p.get("metrics") or {}).get("videos_published"),
                "average_creative_score": (p.get("metrics") or {}).get("average_creative_score"),
                "success_rate": round(succ / max(1, len(rows)), 3) if rows else None,
                "publishing_status": p.get("publishing_status"),
                "monetization_status": p.get("monetization_status"),
                "health": "healthy" if (not rows or succ == len(rows)) else "watch",
            }
        )

    estimated_revenue = sum(float((p.get("metrics") or {}).get("estimated_revenue") or 0) for p in profiles)

    # Publishing queue placeholder from profile schedules
    publishing_queue = []
    for p in active:
        for platform, slot in (p.get("upload_schedule") or {}).items():
            publishing_queue.append(
                {
                    "channel_id": p.get("channel_id"),
                    "brand_name": p.get("brand_name"),
                    "platform": platform,
                    "slot": slot,
                    "status": p.get("publishing_status"),
                }
            )

    growth = []
    for p in profiles:
        m = p.get("metrics") or {}
        growth.append(
            {
                "brand_name": p.get("brand_name"),
                "followers": m.get("followers") or 0,
                "total_views": m.get("total_views") or 0,
                "videos_published": m.get("videos_published") or 0,
            }
        )

    return {
        "generated_at": _now(),
        "program": "Generational Multi-Channel Media OS",
        "active_channels": len(active),
        "total_channels": len(profiles),
        "videos_published": published,
        "videos_scheduled": scheduled,
        "growth_metrics": growth,
        "average_creative_score": round(sum(creative_vals) / len(creative_vals), 1) if creative_vals else None,
        "top_performing_topics": [{"topic": t, "count": c} for t, c in top_topics],
        "publishing_queue": publishing_queue[:30],
        "channel_health": channel_health,
        "estimated_revenue": estimated_revenue,  # placeholder
        "recent_lessons_learned": lessons[:12],
        "channels": [
            {
                "channel_id": p.get("channel_id"),
                "brand_name": p.get("brand_name"),
                "platforms": p.get("platforms"),
                "topic_categories": p.get("topic_categories"),
                "narrator_profile": p.get("narrator_profile"),
                "status": p.get("status"),
                "metrics": p.get("metrics"),
            }
            for p in profiles
        ],
        "library_root": str(ROOT),
        "architecture_frozen": True,
    }


def write_channel_dashboard() -> dict[str, Path]:
    dash = build_channel_dashboard()
    ROOT.mkdir(parents=True, exist_ok=True)
    DASHBOARD_JSON.write_text(json.dumps(dash, indent=2, default=str) + "\n", encoding="utf-8")

    lines = [
        "# Channel Dashboard — Multi-Channel Media OS",
        "",
        f"**Generated:** {dash['generated_at']}",
        f"**Active channels:** {dash['active_channels']} / {dash['total_channels']}",
        f"**Videos published:** {dash['videos_published']}",
        f"**Videos scheduled:** {dash['videos_scheduled']}",
        f"**Average creative score:** {dash['average_creative_score']}",
        f"**Estimated revenue (placeholder):** {dash['estimated_revenue']}",
        "",
        "## Channel health",
        "",
    ]
    for h in dash.get("channel_health") or []:
        lines.append(
            f"- **{h.get('brand_name')}** · {h.get('health')} · published={h.get('videos_published')} · "
            f"creative={h.get('average_creative_score')} · success={h.get('success_rate')}"
        )
    lines += ["", "## Top topics", ""]
    for t in dash.get("top_performing_topics") or []:
        lines.append(f"- {t.get('topic')} ({t.get('count')})")
    lines += ["", "## Publishing queue", ""]
    for q in (dash.get("publishing_queue") or [])[:15]:
        lines.append(f"- {q.get('brand_name')} · {q.get('platform')} · {q.get('slot')} · {q.get('status')}")
    lines += ["", "## Recent lessons", ""]
    for lesson in dash.get("recent_lessons_learned") or []:
        lines.append(f"- {lesson}")
    lines += ["", "_Architecture frozen. Shared production pipeline; independent brand identities._", ""]
    DASHBOARD_MD.write_text("\n".join(lines), encoding="utf-8")
    return {"json": DASHBOARD_JSON, "markdown": DASHBOARD_MD}
