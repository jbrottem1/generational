#!/usr/bin/env python3
"""CLI — Generational Virtual Film Director."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _demo() -> dict:
    return {
        "topic": "Are Leprechauns Real? The Truth Behind Ireland's Tiny Tricksters",
        "world_package": {"world_type": "Irish misty countryside"},
        "visual_package": {
            "scenes": [
                {
                    "scene_number": 1,
                    "purpose": "hook",
                    "length_sec": 3,
                    "narration": "What if I told you millions know the name leprechaun?",
                    "subject": "leprechaun legend",
                },
                {
                    "scene_number": 2,
                    "purpose": "story_beat",
                    "length_sec": 3.5,
                    "narration": "In Irish folklore a solitary fairy often works as a shoemaker.",
                },
                {
                    "scene_number": 3,
                    "purpose": "story_beat",
                    "length_sec": 3.5,
                    "narration": "Celtic traditions place otherworld beings among the mounds of the forest.",
                },
                {
                    "scene_number": 4,
                    "purpose": "payoff",
                    "length_sec": 3,
                    "narration": "The word likely comes from Old Irish luchorpán — a little body.",
                },
            ]
        },
    }


def cmd_selftest(_: argparse.Namespace) -> int:
    from services.virtual_film_director import build_virtual_film_director_package, direct_candidate

    pkg = build_virtual_film_director_package(_demo(), write=True)
    out = direct_candidate(_demo(), write=False)
    print(
        json.dumps(
            {
                "ok": True,
                "decision": (pkg.get("director_review") or {}).get("decision"),
                "approved": (pkg.get("director_review") or {}).get("approved"),
                "path": pkg.get("path"),
                "out_dir": pkg.get("out_dir"),
                "artifacts": list((pkg.get("artifacts") or {}).keys()),
                "rhythm": (pkg.get("emotional_timeline") or {}).get("rhythm"),
                "directed_by_vfd": out.get("directed_by_vfd"),
                "shots": [
                    {
                        "n": s.get("scene_number"),
                        "language": s.get("shot_language"),
                        "emotion": s.get("emotion"),
                        "beat": s.get("emotional_beat"),
                        "ready": s.get("ready"),
                    }
                    for s in pkg.get("shot_plan") or []
                ],
            },
            indent=2,
        )
    )
    return 0 if (pkg.get("director_review") or {}).get("approved") else 2


def cmd_direct(args: argparse.Namespace) -> int:
    from services.virtual_film_director import build_virtual_film_director_package

    cand = _demo()
    if args.candidate and Path(args.candidate).is_file():
        cand = json.loads(Path(args.candidate).read_text(encoding="utf-8"))
    if args.topic:
        cand["topic"] = args.topic
    out_dir = Path(args.out_dir) if args.out_dir else None
    pkg = build_virtual_film_director_package(
        cand, topic=str(cand.get("topic") or ""), write=True, out_dir=out_dir
    )
    print(json.dumps(pkg.get("summary"), indent=2))
    print(f"Package: {pkg.get('path')}")
    for k, v in (pkg.get("artifacts") or {}).items():
        print(f"  {k}: {v}")
    return 0 if (pkg.get("director_review") or {}).get("approved") else 2


def main() -> int:
    p = argparse.ArgumentParser(description="Virtual Film Director")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("selftest")
    s.set_defaults(func=cmd_selftest)
    d = sub.add_parser("direct")
    d.add_argument("--topic", default="")
    d.add_argument("--candidate", default="")
    d.add_argument("--out-dir", default="")
    d.set_defaults(func=cmd_direct)
    args = p.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
