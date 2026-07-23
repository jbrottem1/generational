"""Executive Validation Dashboard."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.env import project_root
from services.validation_program.bottlenecks import build_recommendations, detect_bottlenecks
from services.validation_program.catalog import CATEGORIES, build_validation_catalog
from services.validation_program.library import LIB_ROOT, list_validations

DASHBOARD_JSON = LIB_ROOT / "EXECUTIVE_VALIDATION_DASHBOARD.json"
DASHBOARD_MD = project_root() / "VALIDATION_EXECUTIVE_DASHBOARD.md"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_executive_dashboard() -> dict[str, Any]:
    rows = list_validations(limit=500)
    catalog = build_validation_catalog()
    bottlenecks = detect_bottlenecks(rows)
    recommendations = build_recommendations(bottlenecks)

    def avg(key: str) -> float | None:
        vals = [float(r[key]) for r in rows if r.get(key) is not None]
        return round(sum(vals) / len(vals), 1) if vals else None

    by_cat: dict[str, list[float]] = {c: [] for c in CATEGORIES}
    for r in rows:
        cat = r.get("category") or ""
        if cat in by_cat and r.get("overall_score") is not None:
            by_cat[cat].append(float(r["overall_score"]))
    cat_avgs = {
        c: round(sum(v) / len(v), 1) for c, v in by_cat.items() if v
    }
    top_cats = sorted(cat_avgs.items(), key=lambda kv: -kv[1])
    weak_cats = sorted(cat_avgs.items(), key=lambda kv: kv[1])

    times = [int(r.get("elapsed_ms") or 0) for r in rows if r.get("elapsed_ms")]
    renders = [int(r.get("render_ms") or 0) for r in rows if r.get("render_ms")]

    highest = recommendations[0] if recommendations else None

    dashboard = {
        "generated_at": _now(),
        "program": "Generational V1 Validation Program",
        "target_videos": 100,
        "videos_produced": len(rows),
        "videos_remaining": max(0, 100 - len(rows)),
        "catalog_size": len(catalog),
        "average_creative_score": avg("creative_score"),
        "average_program_score": avg("overall_score"),
        "average_production_time_ms": round(sum(times) / len(times), 1) if times else None,
        "average_render_time_ms": round(sum(renders) / len(renders), 1) if renders else None,
        "average_viewer_prediction": avg("viewer_prediction"),
        "average_opportunity_score": avg("opportunity_score"),
        "average_hook_score": avg("hook_score"),
        "failure_rate": bottlenecks.get("failure_rate"),
        "success_rate": bottlenecks.get("success_rate"),
        "top_performing_categories": [{"category": c, "average": a} for c, a in top_cats[:5]],
        "weakest_categories": [{"category": c, "average": a} for c, a in weak_cats[:5]],
        "highest_priority_improvement": highest,
        "bottlenecks": bottlenecks,
        "recommendations": recommendations,
        "library_path": str(LIB_ROOT),
        "note": "Architecture frozen — recommendations tune existing departments only",
    }
    return dashboard


def write_executive_dashboard() -> dict[str, Path]:
    dash = build_executive_dashboard()
    LIB_ROOT.mkdir(parents=True, exist_ok=True)
    DASHBOARD_JSON.write_text(json.dumps(dash, indent=2, default=str) + "\n", encoding="utf-8")

    lines = [
        "# Validation Executive Dashboard",
        "",
        f"**Generated:** {dash['generated_at']}",
        f"**Videos produced:** {dash['videos_produced']} / {dash['target_videos']}",
        f"**Success rate:** {dash['success_rate']}",
        f"**Failure rate:** {dash['failure_rate']}",
        "",
        "## Averages",
        "",
        f"- Program score: {dash['average_program_score']}",
        f"- Creative score: {dash['average_creative_score']}",
        f"- Production time (ms): {dash['average_production_time_ms']}",
        f"- Render time (ms): {dash['average_render_time_ms']}",
        f"- Viewer prediction: {dash['average_viewer_prediction']}",
        f"- Opportunity score: {dash['average_opportunity_score']}",
        f"- Hook score: {dash['average_hook_score']}",
        "",
        "## Top categories",
        "",
    ]
    for c in dash.get("top_performing_categories") or []:
        lines.append(f"- {c['category']}: {c['average']}")
    lines += ["", "## Weakest categories", ""]
    for c in dash.get("weakest_categories") or []:
        lines.append(f"- {c['category']}: {c['average']}")
    hi = dash.get("highest_priority_improvement") or {}
    lines += [
        "",
        "## Highest priority improvement",
        "",
        f"**Problem:** {hi.get('problem')}",
        f"**Evidence:** {hi.get('evidence')}",
        f"**Expected improvement:** {hi.get('expected_improvement')}",
        f"**Priority:** {hi.get('priority')} · **Impact:** {hi.get('estimated_impact')}",
        "",
        "_No architecture redesign. Tune existing departments only._",
        "",
    ]
    DASHBOARD_MD.write_text("\n".join(lines), encoding="utf-8")
    return {"json": DASHBOARD_JSON, "markdown": DASHBOARD_MD}
