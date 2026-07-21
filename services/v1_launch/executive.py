"""Phase 3–4 — Executive dashboard + launch recommendation."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.env import project_root
from services.v1_launch.library import ROOT, list_pilots
from services.validation_program.bottlenecks import build_recommendations, detect_bottlenecks

DASH_JSON = ROOT / "V1_LAUNCH_EXECUTIVE_DASHBOARD.json"
DASH_MD = project_root() / "V1_LAUNCH_EXECUTIVE_DASHBOARD.md"
REC_MD = project_root() / "V1_LAUNCH_RECOMMENDATION.md"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_executive_review() -> dict[str, Any]:
    rows = list_pilots(limit=100)
    n = len(rows)
    successes = sum(1 for r in rows if r.get("success"))
    deliverable = sum(1 for r in rows if r.get("video_exists") or r.get("deliverable_ok"))
    times = [int(r.get("elapsed_ms") or 0) for r in rows if r.get("elapsed_ms")]
    scores = [float(r["overall_score"]) for r in rows if r.get("overall_score") is not None]

    by_cat: dict[str, list[float]] = defaultdict(list)
    cat_success: dict[str, list[bool]] = defaultdict(list)
    for r in rows:
        cat = r.get("category") or "unknown"
        if r.get("overall_score") is not None:
            by_cat[cat].append(float(r["overall_score"]))
        cat_success[cat].append(bool(r.get("success")))

    cat_avgs = {c: round(sum(v) / len(v), 1) for c, v in by_cat.items() if v}
    strong = sorted(cat_avgs.items(), key=lambda kv: -kv[1])
    weak = sorted(cat_avgs.items(), key=lambda kv: kv[1])

    # Failure causes from failure logs
    fail_causes: Counter[str] = Counter()
    for r in rows:
        if r.get("video_exists"):
            continue
        fail_causes["missing_mp4"] += 1
        for f in r.get("failures") or []:
            if isinstance(f, dict):
                msg = str(f.get("warning") or f.get("error") or "unknown")[:100]
                fail_causes[msg] += 1

    # Bottlenecks using validation adapter shape
    bottleneck_rows = [
        {
            "success": r.get("success"),
            "measurements": r.get("measurements") or {},
            "metrics": r.get("metrics") or {},
            "failures": r.get("failures") or [],
        }
        for r in rows
    ]
    bottlenecks = detect_bottlenecks(bottleneck_rows)
    recommendations = build_recommendations(bottlenecks)

    # COO priority: publication deliverable always outranks creative micro-scores
    if n and (deliverable / max(1, n)) < 0.8:
        recommendations.insert(
            0,
            {
                "problem": "Production pipeline completes without a playable MP4",
                "evidence": f"deliverable_mp4_rate={round(deliverable / max(1, n), 3)} over {n} pilot runs; missing_mp4 count={fail_causes.get('missing_mp4', 0)}",
                "expected_improvement": "Stabilize existing ffmpeg/studio export path so production mode materializes verified MP4s (no new renderer)",
                "priority": "P0",
                "estimated_impact": 90,
                "department_hint": "export / studio_render",
                "architecture_change_allowed": False,
            },
        )
    if n and fail_causes.get("animation unavailable — continued", 0) >= max(1, n // 2):
        recommendations.insert(
            1 if recommendations and recommendations[0].get("priority") == "P0" else 0,
            {
                "problem": "Animation unavailable on most pilot runs",
                "evidence": f"animation_unavailable n={fail_causes.get('animation unavailable — continued')}",
                "expected_improvement": "Cap cinematic/motion scores when animation skips; use existing motion graphics path honestly",
                "priority": "P0",
                "estimated_impact": 40,
                "department_hint": "animation / studio_render",
                "architecture_change_allowed": False,
            },
        )
    recommendations = recommendations[:5]

    # Quality distribution buckets
    buckets = {"90+": 0, "80-89": 0, "70-79": 0, "<70": 0}
    for s in scores:
        if s >= 90:
            buckets["90+"] += 1
        elif s >= 80:
            buckets["80-89"] += 1
        elif s >= 70:
            buckets["70-79"] += 1
        else:
            buckets["<70"] += 1

    dash = {
        "generated_at": _now(),
        "program": "Generational V1 Launch — Executive Review",
        "videos_in_pilot": n,
        "target": 25,
        "production_success_rate": round(successes / max(1, n), 3),
        "deliverable_mp4_rate": round(deliverable / max(1, n), 3),
        "average_production_time_ms": round(sum(times) / len(times), 1) if times else None,
        "average_program_score": round(sum(scores) / len(scores), 1) if scores else None,
        "quality_distribution": buckets,
        "strongest_categories": [{"category": c, "average": a} for c, a in strong[:5]],
        "weakest_categories": [{"category": c, "average": a} for c, a in weak[:5]],
        "failure_causes": [{"cause": k, "count": v} for k, v in fail_causes.most_common(12)],
        "bottlenecks": bottlenecks,
        "top_5_improvements": recommendations,
        "publishing_enabled": False,
        "architecture_frozen": True,
    }
    return dash


def decide_launch_recommendation(dash: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    READY_FOR_LAUNCH | READY_WITH_MINOR_FIXES | NOT_READY

    Evidence-based from pilot — publication-ready means deliverable MP4 + quality floor.
    """
    dash = dash or build_executive_review()
    n = int(dash.get("videos_in_pilot") or 0)
    success_rate = float(dash.get("production_success_rate") or 0)
    mp4_rate = float(dash.get("deliverable_mp4_rate") or 0)
    avg_score = dash.get("average_program_score")
    avg_score_f = float(avg_score) if avg_score is not None else 0.0

    evidence: list[str] = [
        f"pilot_n={n}/25",
        f"success_rate={success_rate}",
        f"mp4_rate={mp4_rate}",
        f"average_program_score={avg_score}",
    ]

    # Thresholds for a media company, not a demo
    if n < 20:
        decision = "NOT_READY"
        rationale = "Pilot incomplete — need ≥20 scored productions for launch evidence."
    elif mp4_rate < 0.8:
        decision = "NOT_READY"
        rationale = (
            "Publication-ready MP4 rate below 80%. Generational cannot claim consistent "
            "publishable output until export materialization is reliable."
        )
    elif success_rate >= 0.9 and mp4_rate >= 0.9 and avg_score_f >= 80:
        decision = "READY_FOR_LAUNCH"
        rationale = "Pilot meets success, deliverable, and quality floors for V1 public launch (publishing still manual)."
    elif success_rate >= 0.75 and mp4_rate >= 0.8 and avg_score_f >= 75:
        decision = "READY_WITH_MINOR_FIXES"
        rationale = "Close to launch — resolve remaining export/reliability or scoring gaps before public launch."
    else:
        decision = "NOT_READY"
        rationale = "Pilot results do not meet publication-ready reliability / quality bars."

    top5 = dash.get("top_5_improvements") or []
    return {
        "generated_at": _now(),
        "decision": decision,
        "rationale": rationale,
        "evidence": evidence,
        "dashboard_snapshot": {
            "videos_in_pilot": n,
            "production_success_rate": success_rate,
            "deliverable_mp4_rate": mp4_rate,
            "average_program_score": avg_score,
            "strongest_categories": dash.get("strongest_categories"),
            "weakest_categories": dash.get("weakest_categories"),
            "failure_causes": (dash.get("failure_causes") or [])[:5],
        },
        "highest_impact_improvements": top5,
        "publishing_policy": "manual_review_only — no automatic publish",
    }


def write_executive_artifacts() -> dict[str, Path]:
    dash = build_executive_review()
    rec = decide_launch_recommendation(dash)
    ROOT.mkdir(parents=True, exist_ok=True)
    DASH_JSON.write_text(json.dumps(dash, indent=2, default=str) + "\n", encoding="utf-8")
    (ROOT / "V1_LAUNCH_RECOMMENDATION.json").write_text(
        json.dumps(rec, indent=2, default=str) + "\n", encoding="utf-8"
    )

    lines = [
        "# V1 Launch Executive Dashboard",
        "",
        f"**Generated:** {dash['generated_at']}",
        f"**Pilot size:** {dash['videos_in_pilot']} / {dash['target']}",
        f"**Success rate:** {dash['production_success_rate']}",
        f"**MP4 deliverable rate:** {dash['deliverable_mp4_rate']}",
        f"**Avg production time (ms):** {dash['average_production_time_ms']}",
        f"**Avg program score:** {dash['average_program_score']}",
        "",
        "## Quality distribution",
        "",
    ]
    for k, v in (dash.get("quality_distribution") or {}).items():
        lines.append(f"- {k}: {v}")
    lines += ["", "## Strongest categories", ""]
    for c in dash.get("strongest_categories") or []:
        lines.append(f"- {c.get('category')}: {c.get('average')}")
    lines += ["", "## Weakest categories", ""]
    for c in dash.get("weakest_categories") or []:
        lines.append(f"- {c.get('category')}: {c.get('average')}")
    lines += ["", "## Failure causes", ""]
    for f in dash.get("failure_causes") or []:
        lines.append(f"- {f.get('cause')} (n={f.get('count')})")
    lines += ["", "## Top 5 improvements", ""]
    for i, r in enumerate(dash.get("top_5_improvements") or [], 1):
        lines.append(f"### {i}. [{r.get('priority')}] {r.get('problem')}")
        lines.append(f"- Evidence: {r.get('evidence')}")
        lines.append(f"- Expected: {r.get('expected_improvement')}")
        lines.append(f"- Impact: {r.get('estimated_impact')}")
        lines.append("")
    DASH_MD.write_text("\n".join(lines), encoding="utf-8")

    rec_lines = [
        "# V1 Launch Recommendation",
        "",
        f"**Decision:** `{rec['decision']}`",
        "",
        f"**Rationale:** {rec['rationale']}",
        "",
        "## Evidence",
        "",
    ]
    for e in rec.get("evidence") or []:
        rec_lines.append(f"- {e}")
    rec_lines += ["", "## Highest-impact improvements", ""]
    for r in rec.get("highest_impact_improvements") or []:
        rec_lines.append(f"- **{r.get('priority')}** — {r.get('problem')} (impact={r.get('estimated_impact')})")
    rec_lines += ["", f"_Publishing policy: {rec.get('publishing_policy')}_", ""]
    REC_MD.write_text("\n".join(rec_lines), encoding="utf-8")

    return {"dashboard_json": DASH_JSON, "dashboard_md": DASH_MD, "recommendation_md": REC_MD}
