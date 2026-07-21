"""Improvement Roadmap — highest-impact content quality fixes only."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def write_improvement_roadmap(summary: dict, out_dir: Path | None = None) -> Path:
    out_dir = Path(out_dir or (ROOT / "data" / "productions" / "_validation" / "content_validation"))
    out_dir.mkdir(parents=True, exist_ok=True)

    weaknesses = list(summary.get("weakness_ranking") or [])
    averages = summary.get("average_scores") or {}
    # Top 7 only — mission asks to focus, avoid architecture
    top = weaknesses[:7]

    roadmap = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "objective": "Outperform average human educational shorts with publishable Generational videos",
        "principle": "No new engines. Improve content outcomes via existing pipeline knobs.",
        "publish_ready_pct": summary.get("publish_ready_pct"),
        "average_overall": averages.get("overall_production_score"),
        "priorities": [
            {
                "rank": i + 1,
                "weakness": w.get("label"),
                "impact": w.get("impact"),
                "frequency": w.get("count"),
                "avg_dimension_score": w.get("avg_score"),
                "domains_affected": w.get("domains"),
                "action": w.get("fix_hint"),
                "owner_surface": _owner_for(w.get("id") or ""),
            }
            for i, w in enumerate(top)
        ],
        "explicitly_out_of_scope": [
            "New architecture layers",
            "New production engines",
            "Additional orchestration frameworks",
            "Provider vendor rewrites",
        ],
        "success_metric": "≥90% of validation productions publish-ready with overall score ≥98",
    }

    json_path = out_dir / "IMPROVEMENT_ROADMAP.json"
    json_path.write_text(json.dumps(roadmap, indent=2), encoding="utf-8")

    md_path = ROOT / "IMPROVEMENT_ROADMAP.md"
    lines = [
        "# Improvement Roadmap",
        "",
        f"Generated: {roadmap['generated_at']}",
        "",
        "Generational Architecture V1 is feature-complete. This roadmap is **content-quality only**.",
        "",
        f"- Current publish-ready rate: **{roadmap['publish_ready_pct']}%**",
        f"- Average overall production score: **{roadmap['average_overall']}**",
        "",
        "## Highest-impact improvements",
        "",
    ]
    if not top:
        lines.append("No systemic weaknesses below threshold — maintain quality bars and increase real MP4 export coverage.")
    for p in roadmap["priorities"]:
        lines.extend(
            [
                f"### {p['rank']}. {p['weakness']}",
                "",
                f"- Impact weight: {p['impact']}",
                f"- Frequency across domains: {p['frequency']}",
                f"- Avg dimension score: {p['avg_dimension_score']}",
                f"- Domains: {', '.join(p.get('domains_affected') or []) or '—'}",
                f"- Action: {p['action']}",
                f"- Touch existing surface: `{p['owner_surface']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Do not do",
            "",
            "- Build additional infrastructure",
            "- Create additional production engines",
            "- Redesign orchestration",
            "",
            "## Mission success",
            "",
            "Consistently ship videos ready for public publishing with minimal or no manual edits.",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")
    # Mirror into validation folder
    (out_dir / "IMPROVEMENT_ROADMAP.md").write_text(md_path.read_text(encoding="utf-8"), encoding="utf-8")
    return md_path


def _owner_for(weakness_id: str) -> str:
    owners = {
        "weak_hook": "psychology / script_generation / ai_director hook plan",
        "static_visuals": "visual_intelligence / cinematography / studio_render",
        "weak_animation": "studio_render / cinematography / animation",
        "voice_pacing": "voice_audio / narration / voice",
        "caption_timing": "subtitle / viewer_retention captions",
        "music_transitions": "voice_audio music plan / ops music_sound",
        "thumbnail_clarity": "ai_director thumbnail_strategy / seo thumbnails",
        "seo_packaging": "seo / seo_optimization",
        "educational_depth": "research / evidence_intelligence / citation",
        "retention_drop": "viewer_retention / script_generation pacing",
        "rendering_speed": "studio_render caching / optimization_lab loops",
        "low_shareability": "psychology share dims / script CTA",
    }
    return owners.get(weakness_id, "production_operations report feedback")
