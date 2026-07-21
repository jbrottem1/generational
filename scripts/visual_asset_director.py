#!/usr/bin/env python3
"""Visual Asset Director CLI — evaluate, direct, validate, styles."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    p = argparse.ArgumentParser(description="Visual Asset Director")
    sub = p.add_subparsers(dest="cmd", required=True)

    e = sub.add_parser("evaluate", help="Evaluate one image")
    e.add_argument("path")
    e.add_argument("--style", default="documentary")
    e.add_argument("--purpose", default="")
    e.add_argument("--aspect", default="9:16")

    d = sub.add_parser("direct", help="Build VISUAL_PACKAGE for a scene directory or candidate JSON")
    d.add_argument("--topic", default="")
    d.add_argument("--niche", default="biology")
    d.add_argument("--style", default="")
    d.add_argument("--scenes-dir", default="")
    d.add_argument("--candidate-json", default="")
    d.add_argument("--world-json", default="")
    d.add_argument("--out", default="")
    d.add_argument("--platform", default="youtube_shorts")

    v = sub.add_parser("validate", help="Validate VISUAL_PACKAGE JSON")
    v.add_argument("path")

    sub.add_parser("styles", help="List style library")

    c = sub.add_parser("compare", help="Before/after baseline vs directed on a scenes dir")
    c.add_argument("--scenes-dir", required=True)
    c.add_argument("--topic", default="Untitled")
    c.add_argument("--niche", default="biology")
    c.add_argument("--style", default="documentary")
    c.add_argument("--out", default="")

    args = p.parse_args()

    if args.cmd == "styles":
        from services.visual_asset_director import list_styles

        print(json.dumps(list_styles(), indent=2))
        return 0

    if args.cmd == "evaluate":
        from services.visual_asset_director import evaluate_candidate, resolve_style_profile

        profile = resolve_style_profile(args.style)
        out = evaluate_candidate(
            args.path,
            scene={"purpose": args.purpose},
            style_profile=profile,
            target_aspect=args.aspect,
        )
        print(json.dumps(out, indent=2, default=str))
        return 0 if out.get("approved") else 1

    if args.cmd == "validate":
        from services.visual_asset_director import validate_visual_package

        data = json.loads(Path(args.path).read_text(encoding="utf-8"))
        result = validate_visual_package(data)
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok") else 1

    if args.cmd == "direct":
        from services.visual_asset_director import build_visual_package

        candidate = {}
        if args.candidate_json:
            candidate = json.loads(Path(args.candidate_json).read_text(encoding="utf-8"))
        world = None
        if args.world_json:
            world = json.loads(Path(args.world_json).read_text(encoding="utf-8"))
        pkg = build_visual_package(
            candidate,
            topic=args.topic or candidate.get("topic") or "",
            niche=args.niche,
            style=args.style or None,
            platform=args.platform,
            world_package=world,
            fallback_scene_dirs=[args.scenes_dir] if args.scenes_dir else None,
            out_path=args.out or None,
        )
        print(json.dumps(pkg, indent=2, default=str))
        return 0 if (pkg.get("validation") or {}).get("ok") else 1

    if args.cmd == "compare":
        from services.visual_asset_director import (
            build_visual_package,
            evaluate_candidate,
            resolve_style_profile,
            score_baseline_vs_directed,
        )

        scenes_dir = Path(args.scenes_dir)
        files = sorted(p for p in scenes_dir.iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"))
        profile = resolve_style_profile(args.style, niche=args.niche, topic=args.topic)
        # BEFORE: locked index assignment (production as-shipped)
        before_scenes = [{"scene_id": f"scene_{i:02d}", "purpose": f.stem, "image": str(f)} for i, f in enumerate(files)]
        before = build_visual_package(
            {"topic": args.topic, "scenes": before_scenes},
            topic=args.topic,
            niche=args.niche,
            style=args.style,
            fallback_scene_dirs=[scenes_dir],
            write=False,
        )
        # Force before scores from index-matched evaluates only
        per = {}
        for i, f in enumerate(files):
            ev = evaluate_candidate(str(f), scene={"purpose": f.stem}, style_profile=profile)
            per[f"scene_{i:02d}"] = ev["scorecard"]
        before["visual_scores"]["per_scene"] = per
        if per:
            before["visual_scores"]["mean_overall_professional_quality"] = round(
                sum(float(c["overall_professional_quality"]) for c in per.values()) / len(per), 1
            )
        before["visual_scores"]["approved_count"] = sum(
            1 for f in files if evaluate_candidate(str(f), scene={"purpose": f.stem}, style_profile=profile)["approved"]
        )

        # AFTER: director selects best across pool per scene
        after = build_visual_package(
            {"topic": args.topic},
            topic=args.topic,
            niche=args.niche,
            style=args.style,
            fallback_scene_dirs=[scenes_dir],
            out_path=args.out or None,
            write=True,
        )
        comparison = score_baseline_vs_directed(before, after)
        out = {"before": before["visual_scores"], "after": after["visual_scores"], "comparison": comparison, "path": after.get("path")}
        print(json.dumps(out, indent=2, default=str))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
