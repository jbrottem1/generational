#!/usr/bin/env python3
"""Self-test Visual Asset Director on Why Octopuses Have Three Hearts (before vs after)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SCENES = Path.home() / "Desktop/AI Start-UP/Videos/Shorts/Science/Biology/Why Octopuses Have Three Hearts/Assets/scenes"
ASSETS = SCENES.parent
WORLD = ASSETS / "WORLD_PACKAGE.json"
REPORTS = ASSETS.parent / "Reports"
TOPIC = "Why Octopuses Have Three Hearts"


def main() -> int:
    from services.visual_asset_director import (
        attach_visual_package_to_candidate,
        build_visual_package,
        evaluate_candidate,
        resolve_style_profile,
        score_baseline_vs_directed,
    )

    if not SCENES.exists():
        print(json.dumps({"ok": False, "error": f"missing scenes: {SCENES}"}))
        return 1

    files = sorted(p for p in SCENES.iterdir() if p.suffix.lower() == ".png")
    profile = resolve_style_profile("documentary", niche="biology", topic=TOPIC, world_type="ocean_research_observatory")
    world = json.loads(WORLD.read_text(encoding="utf-8")) if WORLD.exists() else {
        "world_id": "WORLD-OCEAN_RESEARCH_OBSERVATORY",
        "world_type": "ocean_research_observatory",
    }

    # BEFORE — production assignment as shipped (index-locked)
    before_per = {}
    before_approved = 0
    for i, f in enumerate(files):
        ev = evaluate_candidate(str(f), scene={"purpose": f.stem, "beat": f.stem}, style_profile=profile)
        before_per[f"scene_{i:02d}"] = ev["scorecard"]
        if ev["approved"]:
            before_approved += 1
    before_mean = round(
        sum(float(c["overall_professional_quality"]) for c in before_per.values()) / max(1, len(before_per)),
        1,
    )
    before_pkg = {
        "visual_scores": {
            "per_scene": before_per,
            "mean_overall_professional_quality": before_mean,
            "approved_count": before_approved,
            "approval_rate": round(before_approved / max(1, len(files)), 3),
        },
        "continuity_report": {"continuity_score": 70.0},
    }

    # AFTER — director with full pool + world continuity
    after = build_visual_package(
        {
            "topic": TOPIC,
            "category": "biology",
            "platform": "youtube_shorts",
            "character_references": [{"name": "Professor", "role": "educator", "continuity_lock": True}],
        },
        topic=TOPIC,
        niche="biology",
        style="documentary",
        platform="youtube_shorts",
        world_package=world,
        fallback_scene_dirs=[SCENES],
        character_refs=[{"name": "Professor", "role": "educator", "continuity_lock": True}],
        production_id="octopus_three_hearts_vad_selftest",
        out_path=ASSETS / "VISUAL_PACKAGE.json",
        write=True,
    )

    comparison = score_baseline_vs_directed(before_pkg, after)

    # Creative Excellence before/after (compose existing system)
    ce_before = ce_after = None
    try:
        from services.creative_excellence import review_production_creative_excellence

        base_cand = {
            "topic": TOPIC,
            "platform": "youtube_shorts",
            "visual_package": {
                "scenes": [
                    {"scene_id": f"scene_{i:02d}", "purpose": f.stem, "image": str(f)}
                    for i, f in enumerate(files)
                ]
            },
        }
        ce_before = review_production_creative_excellence(
            base_cand,
            production_report={"topic": TOPIC},
            production_id="octopus_vad_before",
            topic=TOPIC,
        )
        directed = attach_visual_package_to_candidate(base_cand, after)
        ce_after = review_production_creative_excellence(
            directed,
            production_report={"topic": TOPIC, "visual_asset_direction": directed.get("visual_asset_direction")},
            production_id="octopus_vad_after",
            topic=TOPIC,
        )
    except Exception as exc:  # noqa: BLE001
        ce_before = {"error": str(exc)[:200]}
        ce_after = {"error": str(exc)[:200]}

    def _ce_score(payload):
        if not isinstance(payload, dict) or payload.get("error"):
            return None
        sc = payload.get("scorecard") or {}
        return sc.get("creative_excellence_score") or payload.get("creative_excellence_score")

    report = {
        "topic": TOPIC,
        "scenes_dir": str(SCENES),
        "visual_package_path": after.get("path"),
        "style_profile": after.get("style_profile"),
        "before": before_pkg["visual_scores"],
        "after": after.get("visual_scores"),
        "comparison": comparison,
        "continuity_after": after.get("continuity_report"),
        "thumbnail_candidate": after.get("thumbnail_candidate"),
        "rejection_reasons_summary": after.get("rejection_reasons_summary"),
        "validation": after.get("validation"),
        "creative_excellence": {
            "before": _ce_score(ce_before),
            "after": _ce_score(ce_after),
            "delta": (
                round(float(_ce_score(ce_after)) - float(_ce_score(ce_before)), 2)
                if _ce_score(ce_before) is not None and _ce_score(ce_after) is not None
                else None
            ),
            "after_recommendation": (ce_after or {}).get("single_recommendation")
            if isinstance(ce_after, dict)
            else None,
        },
        "improvements_measured": {
            "visual_consistency": (after.get("continuity_report") or {}).get("continuity_score"),
            "professional_appearance": (after.get("visual_scores") or {}).get(
                "mean_overall_professional_quality"
            ),
            "thumbnail_quality": (after.get("thumbnail_candidate") or {}).get("thumbnail_appeal"),
            "educational_clarity_mean": comparison.get("dimension_deltas", {}).get("educational_clarity"),
            "cinematic_ready_scenes": sum(
                1 for m in (after.get("asset_manifest") or []) if m.get("cinematic_ready")
            ),
            "gate_rejected_count": len(after.get("rejected_assets") or []),
        },
    }

    REPORTS.mkdir(parents=True, exist_ok=True)
    out_json = REPORTS / "VISUAL_ASSET_DIRECTOR_SELFTEST.json"
    out_md = REPORTS / "VISUAL_ASSET_DIRECTOR_SELFTEST.md"
    out_json.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")

    md = [
        "# Visual Asset Director — Self-Test",
        "",
        f"**Topic:** {TOPIC}",
        f"**Package:** `{after.get('path')}`",
        "",
        "## Before vs After",
        "",
        f"| Metric | Before | After | Δ |",
        f"|--------|-------:|------:|--:|",
        f"| Mean professional quality | {before_mean} | {(after.get('visual_scores') or {}).get('mean_overall_professional_quality')} | {comparison.get('deltas', {}).get('mean_overall_professional_quality')} |",
        f"| Approved assets | {before_approved} | {(after.get('visual_scores') or {}).get('approved_count')} | {comparison.get('deltas', {}).get('approved_count')} |",
        f"| Continuity | 70.0 | {(after.get('continuity_report') or {}).get('continuity_score')} | — |",
        f"| Creative Excellence | {_ce_score(ce_before)} | {_ce_score(ce_after)} | {(report.get('creative_excellence') or {}).get('delta')} |",
        "",
        "## Dimension deltas (director selection)",
        "",
    ]
    for k, v in (comparison.get("dimension_deltas") or {}).items():
        md.append(f"- **{k}:** {v}")
    md += [
        "",
        "## Gatekeeper summary",
        "",
        f"- Thumbnail candidate appeal: {(after.get('thumbnail_candidate') or {}).get('thumbnail_appeal')}",
        f"- Rejection reasons: {after.get('rejection_reasons_summary')}",
        f"- Validation: {after.get('validation')}",
        "",
        "_Visual Asset Director reviews every frame before cinematic/render. No renderer changes._",
        "",
    ]
    out_md.write_text("\n".join(md), encoding="utf-8")
    print(json.dumps({"ok": True, "report": str(out_json), "markdown": str(out_md), **{k: report[k] for k in ("before", "after", "creative_excellence", "improvements_measured")}}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
