#!/usr/bin/env python3
"""Voice Studio CLI — list, sample, score, recommend, compare ElevenLabs voices.

Does not modify the production pipeline or publish content.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.env import load_application_env  # noqa: E402

load_application_env(create_if_missing=False)


def cmd_list(_: argparse.Namespace) -> int:
    from services.elevenlabs.voices import list_elevenlabs_voices
    from services.voice_studio.profiles import list_profile_catalog

    voices = list_elevenlabs_voices(limit=100)
    print(json.dumps({"voices": voices, "profiles": list_profile_catalog()}, indent=2))
    return 0 if voices.get("ok") else 1


def cmd_sample(args: argparse.Namespace) -> int:
    from services.elevenlabs.voices import list_elevenlabs_voices
    from services.voice_studio.sampler import DEFAULT_SAMPLE_TEXT, generate_samples_for_voices

    voices = list_elevenlabs_voices(limit=100)
    if not voices.get("ok"):
        print(json.dumps(voices, indent=2))
        return 1
    rows = generate_samples_for_voices(voices.get("voices") or [], text=args.text or DEFAULT_SAMPLE_TEXT, mode="sample_15s")
    # Optional local playback (macOS) when --play
    played = 0
    if args.play:
        afplay = Path("/usr/bin/afplay")
        player = str(afplay) if afplay.exists() else ""
        for row in rows:
            path = row.get("path")
            if not player or not path or not Path(path).exists():
                continue
            subprocess.run([player, path], check=False)
            played += 1
    out = {
        "count": len(rows),
        "ok_count": sum(1 for r in rows if r.get("ok")),
        "played": played,
        "samples": rows,
    }
    dest = ROOT / "data" / "voice_studio" / "samples" / "SAMPLE_BATCH.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps({"count": out["count"], "ok_count": out["ok_count"], "played": played, "manifest": str(dest)}, indent=2))
    return 0 if out["ok_count"] else 1


def cmd_score(_: argparse.Namespace) -> int:
    from services.elevenlabs.voices import list_elevenlabs_voices
    from services.voice_studio.scoring import score_voice_dimensions

    voices = list_elevenlabs_voices(limit=100)
    if not voices.get("ok"):
        print(json.dumps(voices, indent=2))
        return 1
    scored = [score_voice_dimensions(v) for v in (voices.get("voices") or [])]
    scored.sort(key=lambda r: -float(r.get("overall") or 0))
    print(json.dumps({"count": len(scored), "scores": scored}, indent=2))
    return 0


def cmd_recommend(args: argparse.Namespace) -> int:
    from services.elevenlabs.voices import list_elevenlabs_voices
    from services.voice_studio.recommend import apply_recommendations_to_config, recommend_voices_for_profiles
    from services.voice_studio.scoring import score_voice_dimensions

    voices = list_elevenlabs_voices(limit=100)
    if not voices.get("ok"):
        print(json.dumps(voices, indent=2))
        return 1
    scored = [score_voice_dimensions(v) for v in (voices.get("voices") or [])]
    recs = recommend_voices_for_profiles(scored, top_n=3)
    applied = {}
    if args.apply:
        applied = apply_recommendations_to_config(recs, write_default=True)
    print(json.dumps({"recommendations": recs, "config_applied": applied}, indent=2))
    return 0


def cmd_set_default(args: argparse.Namespace) -> int:
    from services.voice_studio.config_store import set_default_voice_id, set_profile_voice_id

    if args.profile:
        result = set_profile_voice_id(args.profile, args.voice_id, also_default=args.also_default)
    else:
        result = set_default_voice_id(args.voice_id)
    print(json.dumps(result, indent=2))
    print("Tip: prefer ELEVENLABS_DEFAULT_VOICE_ID / ELEVENLABS_VOICE_* in .env for runtime overrides.")
    return 0 if result.get("ok") else 1


def cmd_select(args: argparse.Namespace) -> int:
    from services.voice_studio.content_routing import select_narrator_profile

    result = select_narrator_profile(
        content_type=args.content_type,
        niche=args.niche,
        narrator=args.narrator,
        style=args.style,
    )
    print(json.dumps(result, indent=2))
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    from services.voice_studio.comparison import run_voice_comparison
    from services.voice_studio.sampler import COMPARISON_TEXT

    report = run_voice_comparison(
        text=args.text or COMPARISON_TEXT,
        apply_config=not args.no_apply,
        limit=args.limit,
    )
    summary = {
        "ok": report.get("ok"),
        "voice_count": report.get("voice_count"),
        "top3_shorts": (report.get("recommendations") or {}).get("educational_youtube_shorts_top3"),
        "artifacts_dir": report.get("artifacts_dir"),
        "latest_report_md": report.get("latest_report_md"),
        "error": report.get("error"),
    }
    print(json.dumps(summary, indent=2))
    return 0 if report.get("ok") else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Generational Voice Studio")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("list", help="List ElevenLabs voices + narrator profiles")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("sample", help="Generate ~15s samples for every available voice")
    p.add_argument("--text", default="")
    p.add_argument("--play", action="store_true", help="Play samples locally via afplay when available")
    p.set_defaults(func=cmd_sample)

    p = sub.add_parser("score", help="Score all available voices (metadata + optional acoustics)")
    p.set_defaults(func=cmd_score)

    p = sub.add_parser("recommend", help="Recommend best voice per narrator profile")
    p.add_argument("--apply", action="store_true", help="Write recommendations into PROFILE_VOICES.json")
    p.set_defaults(func=cmd_recommend)

    p = sub.add_parser("set-default", help="Set default or profile voice ID in configuration")
    p.add_argument("--voice-id", required=True)
    p.add_argument("--profile", default="", help="Profile key (e.g. professor). Empty = global default")
    p.add_argument("--also-default", action="store_true")
    p.set_defaults(func=cmd_set_default)

    p = sub.add_parser("select", help="Select narrator profile from content type")
    p.add_argument("--content-type", default="")
    p.add_argument("--niche", default="")
    p.add_argument("--narrator", default="")
    p.add_argument("--style", default="")
    p.set_defaults(func=cmd_select)

    p = sub.add_parser("compare", help="Full comparison: same text for every voice + report")
    p.add_argument("--text", default="")
    p.add_argument("--limit", type=int, default=100)
    p.add_argument("--no-apply", action="store_true", help="Do not write PROFILE_VOICES.json")
    p.set_defaults(func=cmd_compare)

    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
