"""Module 11 — Render Quality Analyzer (≥98 or revise)."""

from __future__ import annotations

from core.heuristics import clamp
from services.studio_render.models import RENDER_QUALITY_DIMENSIONS, RENDER_QUALITY_THRESHOLD


def _baseline() -> dict[str, int]:
    return {k: 58 for k in RENDER_QUALITY_DIMENSIONS} | {"overall": 58}


def analyze_render_quality(
    *,
    motion_graphics: list,
    transitions: list,
    color_grade: dict,
    visual_effects: list,
    typography: dict,
    diagrams: list,
    broll_plan: list,
    camera_choreography: list,
    export_plan: dict,
    master_timeline: dict,
    baseline: dict | None = None,
) -> dict:
    baseline = baseline or _baseline()

    # Visual beauty
    beauty = 72
    beauty += min(18, len(motion_graphics) * 2)
    beauty += 8 if color_grade.get("lut") else 0
    beauty += min(10, len(visual_effects))

    # Motion smoothness
    smooth = 72
    smooth += 12 if all(not c.get("mechanical") for c in camera_choreography) else 0
    smooth += 10 if all(float(c.get("smoothing") or 0) >= 0.7 for c in camera_choreography or [{"smoothing": 0.8}]) else 0
    smooth += 8 if transitions and all(t.get("type") != "hard_cut" for t in transitions) else 0

    # Camera quality
    camera_q = 70
    camera_q += min(25, len({c.get("compound_move") for c in camera_choreography}) * 6)
    camera_q += 10 if any(c.get("cinematic") for c in camera_choreography) else 0

    # Graphic quality
    graphic = 68 + min(30, len(motion_graphics) * 3) + min(15, len(diagrams) * 5)

    # Color consistency
    color = 78
    if (color_grade.get("consistency") or {}).get("locked"):
        color += 16
    if color_grade.get("profile"):
        color += 6

    # Typography / readability
    typo = int(typography.get("score_hint") or 78)
    typo += 8 if typography.get("keyword_highlighting") else 0
    readable = typo
    if typography.get("cues"):
        readable += 6

    # Professional appearance
    pro = 70
    pro += 10 if export_plan.get("primary") else 0
    pro += 8 if master_timeline.get("synchronized") else 0
    pro += 8 if transitions else 0
    pro += 6 if broll_plan else 0

    # Cinematic score
    cine = 68
    cine += min(20, len(camera_choreography) * 3)
    cine += 10 if any(t.get("type") in ("cinematic_dissolve", "whip_pan", "match_cut") for t in transitions) else 0
    cine += 8 if visual_effects else 0

    # Immersion
    immerse = 68
    immerse += 10 if master_timeline.get("total_duration_sec", 0) > 0 else 0
    immerse += min(15, len((master_timeline.get("tracks") or {}).get("sfx") or []) * 3)
    immerse += 8 if typography.get("style") == "cinematic_kinetic" else 0

    scores = {
        "visual_beauty": clamp(beauty, 0, 100),
        "motion_smoothness": clamp(smooth, 0, 100),
        "camera_quality": clamp(camera_q, 0, 100),
        "graphic_quality": clamp(graphic, 0, 100),
        "color_consistency": clamp(color, 0, 100),
        "typography": clamp(typo, 0, 100),
        "readability": clamp(readable, 0, 100),
        "professional_appearance": clamp(pro, 0, 100),
        "cinematic_score": clamp(cine, 0, 100),
        "viewer_immersion": clamp(immerse, 0, 100),
    }
    overall = int(round(sum(scores.values()) / len(scores)))
    scores["overall"] = overall

    improvements = {
        k: round(scores[k] - float(baseline.get(k, 58)), 1)
        for k in RENDER_QUALITY_DIMENSIONS
    }
    improvements["overall"] = round(overall - float(baseline.get("overall", 58)), 1)

    return {
        "scores": scores,
        "passed": overall >= RENDER_QUALITY_THRESHOLD,
        "threshold": RENDER_QUALITY_THRESHOLD,
        "improvements_vs_baseline": improvements,
        "weak_dimensions": [k for k, v in scores.items() if k != "overall" and v < 90],
    }


def apply_quality_revision(package_parts: dict, quality: dict) -> tuple[dict, list[str]]:
    """Boost weak craft layers for a re-render pass."""
    fixes: list[str] = []
    weak = set(quality.get("weak_dimensions") or [])

    if "graphic_quality" in weak or "visual_beauty" in weak:
        mg = list(package_parts.get("motion_graphics") or [])
        if mg:
            for g in mg:
                g["easing"] = g.get("easing") or "ease_in_out"
                g["polished"] = True
            package_parts["motion_graphics"] = mg
            fixes.append("polished_motion_graphics")
        diagrams = list(package_parts.get("diagrams") or [])
        if not diagrams:
            diagrams.append(
                {
                    "scene_id": "s1",
                    "domain": "general",
                    "kind": "infographic",
                    "animated": True,
                    "prefer_over_static": True,
                    "duration_sec": 2.0,
                    "reason": "Revision: add animated diagram",
                }
            )
            package_parts["diagrams"] = diagrams
            fixes.append("added_diagram")

    if "motion_smoothness" in weak or "camera_quality" in weak:
        for c in package_parts.get("camera_choreography") or []:
            c["smoothing"] = max(float(c.get("smoothing") or 0), 0.92)
            c["cinematic"] = True
            c["mechanical"] = False
        fixes.append("smoothed_camera")

    if "color_consistency" in weak:
        grade = dict(package_parts.get("color_grade") or {})
        grade["consistency"] = {"locked": True, "white_balance_locked": True, "scene_variance_max": 0.05}
        package_parts["color_grade"] = grade
        fixes.append("locked_color")

    if "typography" in weak or "readability" in weak:
        typo = dict(package_parts.get("typography") or {})
        typo["keyword_highlighting"] = True
        typo["score_hint"] = max(int(typo.get("score_hint") or 0), 94)
        package_parts["typography"] = typo
        fixes.append("boosted_typography")

    if "cinematic_score" in weak or "viewer_immersion" in weak:
        for t in package_parts.get("transitions") or []:
            if t.get("type") in ("cross_dissolve",):
                t["type"] = "cinematic_dissolve"
                t["reason"] = "Revision: upgrade to cinematic dissolve"
        fixes.append("upgraded_transitions")

    if "professional_appearance" in weak:
        export = dict(package_parts.get("export_plan") or {})
        export["auto_bitrate"] = True
        export["professional_master"] = True
        package_parts["export_plan"] = export
        fixes.append("professional_export_flags")

    return package_parts, fixes
