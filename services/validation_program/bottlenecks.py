"""Bottleneck detection + optimization recommendations (advisory only)."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from services.validation_program.catalog import MEASUREMENT_DIMENSIONS
from services.validation_program.library import list_validations


def detect_bottlenecks(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Identify slowest modules, weakest creative dims, failure patterns."""
    rows = rows if rows is not None else list_validations(limit=500)
    if not rows:
        return {
            "slowest_modules": [],
            "weakest_creative_modules": [],
            "highest_failure_rate_stages": [],
            "common_rendering_problems": [],
            "common_visual_issues": [],
            "common_narration_issues": [],
            "common_scripting_issues": [],
            "common_research_issues": [],
            "sample_size": 0,
        }

    stage_totals: dict[str, list[int]] = defaultdict(list)
    dim_totals: dict[str, list[float]] = defaultdict(list)
    fail_stages: Counter[str] = Counter()
    render_msgs: Counter[str] = Counter()
    visual_msgs: Counter[str] = Counter()
    narr_msgs: Counter[str] = Counter()
    script_msgs: Counter[str] = Counter()
    research_msgs: Counter[str] = Counter()

    for row in rows:
        metrics = row.get("metrics") or {}
        stage_ms = {}
        if isinstance(metrics, dict):
            stage_ms = metrics.get("stage_ms") or {}
        for stage, ms in (stage_ms or {}).items():
            try:
                stage_totals[str(stage)].append(int(ms))
            except (TypeError, ValueError):
                pass

        measurements = row.get("measurements") or {}
        for dim in MEASUREMENT_DIMENSIONS:
            if dim in measurements:
                try:
                    dim_totals[dim].append(float(measurements[dim]))
                except (TypeError, ValueError):
                    pass

        for fail in row.get("failures") or []:
            if not isinstance(fail, dict):
                continue
            stage = str(fail.get("stage") or "unknown")
            fail_stages[stage] += 1
            msg = str(fail.get("error") or fail.get("warning") or "").lower()
            if stage in ("rendering", "export") or "ffmpeg" in msg or "mp4" in msg or "render" in msg:
                render_msgs[msg[:120] or stage] += 1
            if stage in ("media_collection", "scene_builder", "animation") or "visual" in msg or "image" in msg:
                visual_msgs[msg[:120] or stage] += 1
            if stage in ("voice_generation", "music_sound") or "voice" in msg or "eleven" in msg or "narrat" in msg:
                narr_msgs[msg[:120] or stage] += 1
            if stage in ("script_generator", "studio_director") or "script" in msg or "hook" in msg:
                script_msgs[msg[:120] or stage] += 1
            if stage == "research" or "research" in msg or "source" in msg:
                research_msgs[msg[:120] or stage] += 1

        # Infer from weak dimensions
        if float(measurements.get("visual_quality") or 100) < 70:
            visual_msgs["low_visual_quality_score"] += 1
        if float(measurements.get("narration_quality") or 100) < 70:
            narr_msgs["low_narration_quality_score"] += 1
        if float(measurements.get("hook_strength") or 100) < 70:
            script_msgs["weak_hook_strength"] += 1
        if float(measurements.get("research_accuracy") or 100) < 70:
            research_msgs["weak_research_accuracy"] += 1

    def avg_map(src: dict[str, list[float | int]], *, reverse_high_bad: bool = True) -> list[dict[str, Any]]:
        out = []
        for k, vals in src.items():
            if not vals:
                continue
            out.append({"module": k, "average": round(sum(vals) / len(vals), 1), "samples": len(vals)})
        out.sort(key=lambda r: (-r["average"] if reverse_high_bad else r["average"]))
        return out

    slowest = avg_map(stage_totals, reverse_high_bad=True)[:8]
    # Weakest creative = lowest average scores
    weakest = []
    for dim, vals in dim_totals.items():
        weakest.append({"module": dim, "average": round(sum(vals) / len(vals), 1), "samples": len(vals)})
    weakest.sort(key=lambda r: r["average"])

    failures_total = sum(1 for r in rows if not r.get("success"))
    return {
        "sample_size": len(rows),
        "failure_rate": round(failures_total / max(1, len(rows)), 3),
        "success_rate": round(1 - (failures_total / max(1, len(rows))), 3),
        "slowest_modules": slowest,
        "weakest_creative_modules": weakest[:10],
        "highest_failure_rate_stages": [
            {"stage": s, "count": c} for s, c in fail_stages.most_common(10)
        ],
        "common_rendering_problems": [{"issue": i, "count": c} for i, c in render_msgs.most_common(8)],
        "common_visual_issues": [{"issue": i, "count": c} for i, c in visual_msgs.most_common(8)],
        "common_narration_issues": [{"issue": i, "count": c} for i, c in narr_msgs.most_common(8)],
        "common_scripting_issues": [{"issue": i, "count": c} for i, c in script_msgs.most_common(8)],
        "common_research_issues": [{"issue": i, "count": c} for i, c in research_msgs.most_common(8)],
    }


def build_recommendations(bottlenecks: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """
    Advisory improvements only — NEVER redesign architecture.

    Each recommendation: Problem, Evidence, Expected Improvement, Priority, Estimated Impact.
    """
    bottlenecks = bottlenecks or detect_bottlenecks()
    recs: list[dict[str, Any]] = []

    for w in (bottlenecks.get("weakest_creative_modules") or [])[:5]:
        if float(w.get("average") or 100) >= 80:
            continue
        dim = w["module"]
        recs.append(
            {
                "problem": f"Low average {dim.replace('_', ' ')} across validation runs",
                "evidence": f"Mean score {w['average']} over {w['samples']} productions",
                "expected_improvement": f"Raising {dim} toward 85+ via department tuning (not pipeline redesign)",
                "priority": "P0" if float(w["average"]) < 65 else "P1",
                "estimated_impact": round(max(5, 90 - float(w["average"])), 1),
                "department_hint": _department_for_dim(dim),
                "architecture_change_allowed": False,
            }
        )

    for s in (bottlenecks.get("slowest_modules") or [])[:3]:
        if float(s.get("average") or 0) < 5000:
            continue
        recs.append(
            {
                "problem": f"Slow module: {s['module']}",
                "evidence": f"Average {s['average']} ms over {s['samples']} runs",
                "expected_improvement": "Reduce cycle time via caching/timeouts inside existing module",
                "priority": "P1",
                "estimated_impact": min(40, round(float(s["average"]) / 1000, 1)),
                "department_hint": s["module"],
                "architecture_change_allowed": False,
            }
        )

    for issue in (bottlenecks.get("common_rendering_problems") or [])[:2]:
        recs.append(
            {
                "problem": "Recurring rendering / export issue",
                "evidence": f"{issue['issue']} (n={issue['count']})",
                "expected_improvement": "Stabilize existing ffmpeg/export path; verify media materialization before export gate",
                "priority": "P0",
                "estimated_impact": 35,
                "department_hint": "renderer",
                "architecture_change_allowed": False,
            }
        )

    if not recs:
        recs.append(
            {
                "problem": "Insufficient validation sample for strong optimization signal",
                "evidence": f"sample_size={bottlenecks.get('sample_size')}",
                "expected_improvement": "Continue the 100-video program to strengthen confidence",
                "priority": "P2",
                "estimated_impact": 10,
                "department_hint": "validation_program",
                "architecture_change_allowed": False,
            }
        )

    recs.sort(key=lambda r: (-float(r.get("estimated_impact") or 0), r.get("priority") or "P9"))
    return recs


def _department_for_dim(dim: str) -> str:
    mapping = {
        "research_accuracy": "research",
        "psychology_effectiveness": "psychology",
        "hook_strength": "script / psychology",
        "story_flow": "script",
        "educational_clarity": "research / script",
        "world_continuity": "world_builder",
        "visual_quality": "visual_asset_director",
        "cinematic_quality": "cinematic_director",
        "narration_quality": "voice_studio",
        "caption_accuracy": "captions",
        "audio_mix": "voice_studio / music",
        "thumbnail_appeal": "publishing_intelligence",
        "packaging": "publishing_intelligence",
        "overall_professionalism": "creative_excellence",
    }
    return mapping.get(dim, "production_operations")
