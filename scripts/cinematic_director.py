#!/usr/bin/env python3
"""AI Cinematic Director CLI — build/validate direction packages."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.env import load_application_env  # noqa: E402

load_application_env(create_if_missing=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="AI Cinematic Director")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("direct", help="Build cinematic direction package from script/topic")
    p.add_argument("--topic", required=True)
    p.add_argument("--script", default="")
    p.add_argument("--file", default="", help="Path to script text file")
    p.add_argument("--niche", default="biology")
    p.add_argument("--platform", default="youtube_shorts")
    p.add_argument("--out", default="")

    p = sub.add_parser("validate", help="Validate an existing package JSON")
    p.add_argument("path")

    p = sub.add_parser("palettes", help="List niche color palettes")

    args = parser.parse_args()

    if args.cmd == "palettes":
        from services.cinematic_director import COLOR_PALETTES

        print(json.dumps(COLOR_PALETTES, indent=2))
        return 0

    if args.cmd == "validate":
        from services.cinematic_director import validate_cinematic_direction

        data = json.loads(Path(args.path).read_text(encoding="utf-8"))
        print(json.dumps(validate_cinematic_direction(data), indent=2))
        return 0 if validate_cinematic_direction(data).get("ok") else 1

    script = args.script
    if args.file:
        script = Path(args.file).read_text(encoding="utf-8")
    if not script:
        script = (
            f"{args.topic}. "
            "Stop — here's what almost nobody notices. "
            "The reveal changes how you see it. "
            "Follow for the next myth we unpack."
        )

    from services.cinematic_director import build_cinematic_direction_package, direct_candidate

    candidate = {
        "title": args.topic,
        "topic": args.topic,
        "script": script,
        "niche": args.niche,
        "platform": args.platform,
    }
    directed = direct_candidate(candidate, script=script, niche=args.niche)
    package = directed.get("cinematic_direction_package") or build_cinematic_direction_package(
        candidate, script=script, niche=args.niche, platform=args.platform
    )

    out = Path(args.out) if args.out else (
        ROOT / "data" / "productions" / "_validation" / "cinematic_director" / "CINEMATIC_DIRECTION_PACKAGE.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(package, indent=2) + "\n", encoding="utf-8")
    md = out.with_suffix(".md")
    md.write_text(_md(package), encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": (package.get("validation") or {}).get("ok"),
                "shots": len(package.get("shot_list") or []),
                "niche": package.get("niche"),
                "validation": package.get("validation"),
                "path": str(out),
                "md": str(md),
            },
            indent=2,
        )
    )
    return 0 if (package.get("validation") or {}).get("ok") else 1


def _md(package: dict) -> str:
    lines = [
        "# Cinematic Direction Package",
        "",
        f"**Topic:** {package.get('topic')}",
        f"**Niche:** {package.get('niche')}",
        f"**Validation:** {(package.get('validation') or {}).get('ok')}",
        "",
        "## Shot list",
        "",
    ]
    for s in package.get("shot_list") or []:
        lines.append(
            f"- **{s.get('scene_id')}** · `{s.get('camera')}` · {s.get('composition')} · "
            f"{s.get('lighting')} · motion={s.get('movement_score')} · {s.get('director_note')}"
        )
    lines += ["", "## Color", "", f"```json\n{json.dumps(package.get('color'), indent=2)}\n```", ""]
    lines += ["", "## Director notes", ""]
    for n in package.get("director_notes") or []:
        lines.append(f"- {n}")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
