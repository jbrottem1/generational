#!/usr/bin/env python3
"""Creative Performance Lab CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.env import load_application_env  # noqa: E402

load_application_env(create_if_missing=False)


def _print(data: dict) -> None:
    print(json.dumps(data, indent=2, default=str))


def cmd_create(args: argparse.Namespace) -> int:
    from services.creative_performance_lab import create_experiment

    exp = create_experiment(
        topic=args.topic,
        platform=args.platform,
        audience=args.audience,
        video_length_sec=args.length,
        variables_tested=[args.variable],
        hypothesis=args.hypothesis,
        number_of_variants=args.variants,
    )
    _print(exp)
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    from services.creative_performance_lab import run_controlled_experiment

    result = run_controlled_experiment(
        topic=args.topic,
        platform=args.platform,
        audience=args.audience,
        video_length_sec=args.length,
        variables_tested=[args.variable],
        hypothesis=args.hypothesis,
        number_of_variants=args.variants,
        narrator_profile=args.narrator,
        style=args.style,
        publish=False,
    )
    summary = {
        "experiment_id": result["experiment"]["experiment_id"],
        "status": result["experiment"]["status"],
        "predicted_winner": (result.get("comparison") or {}).get("recommended_variant"),
        "variant_mp4s": [v.get("mp4_path") for v in result.get("variants") or []],
        "comparison_md": f"data/creative_performance_lab/experiments/{result['experiment']['experiment_id']}/COMPARISON_REPORT.md",
        "human_review": f"data/creative_performance_lab/experiments/{result['experiment']['experiment_id']}/HUMAN_REVIEW.json",
        "publishing": "disabled",
    }
    _print(summary)
    return 0


def cmd_review(args: argparse.Namespace) -> int:
    path = ROOT / "data" / "creative_performance_lab" / "experiments" / args.experiment_id / "HUMAN_REVIEW.json"
    if not path.exists():
        print(json.dumps({"ok": False, "error": "HUMAN_REVIEW.json missing"}))
        return 1
    _print(json.loads(path.read_text(encoding="utf-8")))
    return 0


def cmd_select(args: argparse.Namespace) -> int:
    from services.creative_performance_lab import record_human_review

    scores = {}
    if args.scores:
        for part in args.scores.split(","):
            label, val = part.split(":")
            scores[label.strip()] = float(val)
    packet = record_human_review(
        args.experiment_id,
        scores=scores or None,
        notes={"reviewer": args.notes} if args.notes else None,
        preferred_winner=args.winner,
        override_prediction=args.override,
        decision=args.decision,
    )
    _print({"ok": True, "status": packet.get("status"), "preferred_winner": packet.get("preferred_winner")})
    return 0


def cmd_attach(args: argparse.Namespace) -> int:
    from services.creative_performance_lab import attach_published_video

    exp = attach_published_video(
        args.experiment_id,
        variant_label=args.variant,
        platform_video_id=args.video_id,
        platform=args.platform,
    )
    _print({"ok": True, "publishing_ids": exp.get("publishing_ids")})
    return 0


def cmd_analytics(args: argparse.Namespace) -> int:
    from services.creative_performance_lab import refresh_analytics

    _print(refresh_analytics(args.experiment_id))
    return 0


def cmd_evaluate(args: argparse.Namespace) -> int:
    from services.creative_performance_lab import evaluate_experiment, promote_experiment_learning

    result = evaluate_experiment(args.experiment_id)
    promoted = None
    if args.promote:
        promoted = promote_experiment_learning(args.experiment_id)
    _print({"result": result, "promoted": promoted})
    return 0


def cmd_learnings(args: argparse.Namespace) -> int:
    from services.creative_performance_lab import search_learnings

    _print({"learnings": search_learnings(topic=args.topic, platform=args.platform, limit=args.limit)})
    return 0


def cmd_guide(args: argparse.Namespace) -> int:
    from services.creative_performance_lab import guidance_for_production

    _print(
        guidance_for_production(
            topic=args.topic,
            platform=args.platform,
            audience=args.audience,
            duration_sec=args.length,
            narrator_profile=args.narrator,
        )
    )
    return 0


def cmd_dashboard(_: argparse.Namespace) -> int:
    from services.creative_performance_lab import build_creative_performance_board

    _print(build_creative_performance_board())
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Creative Performance Lab")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("create", help="Create experiment definition")
    c.add_argument("--topic", required=True)
    c.add_argument("--platform", default="youtube_shorts")
    c.add_argument("--audience", default="general_public")
    c.add_argument("--length", type=int, default=45)
    c.add_argument("--variable", default="hook_structure")
    c.add_argument("--hypothesis", default="")
    c.add_argument("--variants", type=int, default=3)
    c.set_defaults(func=cmd_create)

    c = sub.add_parser("run", help="Generate controlled variants + comparison (no publish)")
    c.add_argument("--topic", required=True)
    c.add_argument("--platform", default="youtube_shorts")
    c.add_argument("--audience", default="general_public")
    c.add_argument("--length", type=int, default=45)
    c.add_argument("--variable", default="hook_structure")
    c.add_argument("--hypothesis", default="")
    c.add_argument("--variants", type=int, default=3)
    c.add_argument("--narrator", default="professor")
    c.add_argument("--style", default="educational")
    c.set_defaults(func=cmd_run)

    c = sub.add_parser("review", help="Open human review package")
    c.add_argument("experiment_id")
    c.set_defaults(func=cmd_review)

    c = sub.add_parser("select", help="Record human selection / scores")
    c.add_argument("experiment_id")
    c.add_argument("--winner", default="")
    c.add_argument("--scores", default="", help="A:8,B:7,C:9")
    c.add_argument("--notes", default="")
    c.add_argument("--override", action="store_true")
    c.add_argument("--decision", default="approve")
    c.set_defaults(func=cmd_select)

    c = sub.add_parser("attach", help="Attach published platform video ID")
    c.add_argument("experiment_id")
    c.add_argument("--variant", required=True)
    c.add_argument("--video-id", required=True)
    c.add_argument("--platform", default="youtube_shorts")
    c.set_defaults(func=cmd_attach)

    c = sub.add_parser("analytics", help="Refresh analytics for attached videos")
    c.add_argument("experiment_id")
    c.set_defaults(func=cmd_analytics)

    c = sub.add_parser("evaluate", help="Evaluate prediction vs reality")
    c.add_argument("experiment_id")
    c.add_argument("--promote", action="store_true", help="Write knowledge if evidence sufficient")
    c.set_defaults(func=cmd_evaluate)

    c = sub.add_parser("learnings", help="View learned patterns")
    c.add_argument("--topic", default="")
    c.add_argument("--platform", default="")
    c.add_argument("--limit", type=int, default=20)
    c.set_defaults(func=cmd_learnings)

    c = sub.add_parser("guide", help="Pre-production guidance from learnings")
    c.add_argument("--topic", required=True)
    c.add_argument("--platform", default="youtube_shorts")
    c.add_argument("--audience", default="general_public")
    c.add_argument("--length", type=int, default=45)
    c.add_argument("--narrator", default="professor")
    c.set_defaults(func=cmd_guide)

    c = sub.add_parser("dashboard", help="Print CPL board JSON")
    c.set_defaults(func=cmd_dashboard)

    args = p.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
