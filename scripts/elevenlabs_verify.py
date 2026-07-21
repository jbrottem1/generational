#!/usr/bin/env python3
"""ElevenLabs production narration — health, voices, synthesis, pipeline proof."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.env import load_application_env  # noqa: E402

load_application_env(create_if_missing=False)


def cmd_health(_: argparse.Namespace) -> int:
    from services.elevenlabs import verify_elevenlabs_authentication

    report = verify_elevenlabs_authentication(live_probe=True)
    print(json.dumps(report, indent=2))
    return 0 if report.get("ok") else 1


def cmd_voices(_: argparse.Namespace) -> int:
    from services.elevenlabs import list_elevenlabs_voices

    report = list_elevenlabs_voices()
    print(json.dumps(report, indent=2))
    return 0 if report.get("ok") else 1


def cmd_narrate(args: argparse.Namespace) -> int:
    from services.media_production.voice import synthesize_voice

    text = args.text
    if args.file:
        text = Path(args.file).read_text(encoding="utf-8")
    result = synthesize_voice(
        text,
        narrator=args.narrator,
        preferred_provider="elevenlabs",
        allow_fallback=args.allow_fallback,
    )
    summary = {
        "ok": result.get("ok"),
        "provider": result.get("provider"),
        "path": result.get("path"),
        "duration_sec": result.get("duration_sec"),
        "placeholder": result.get("placeholder"),
        "error": result.get("error"),
        "audio_qa": result.get("audio_qa"),
        "voice_package": {
            "provider": (result.get("voice_package") or {}).get("provider"),
            "official_narration_provider": (result.get("voice_package") or {}).get("official_narration_provider"),
            "narrator_profile": (result.get("voice_package") or {}).get("narrator_profile"),
            "voice_id": (result.get("voice_package") or {}).get("voice_id"),
            "model_id": (result.get("voice_package") or {}).get("model_id"),
            "path": (result.get("voice_package") or {}).get("path"),
        },
    }
    out = ROOT / "data" / "productions" / "_validation" / "elevenlabs" / "NARRATION_TEST.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    if result.get("path"):
        # copy sidecar marker
        (out.parent / "LAST_NARRATION_PATH.txt").write_text(str(result["path"]), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if result.get("ok") and result.get("provider") == "elevenlabs" else 1


def cmd_pipeline(args: argparse.Namespace) -> int:
    """End-to-end: voice stage via existing synthesize path used by ops."""
    import engines  # noqa: F401
    from services.media_production.voice import synthesize_voice

    script = (
        args.text
        or "Stop. Artificial intelligence is not a thinking brain. "
        "It is pattern matching at enormous scale. "
        "By the end of this short you will know the one claim that survives the evidence. "
        "AI predicts the next token. It does not understand the world the way you do. "
        "Share the myth you believed longest."
    )
    result = synthesize_voice(script, narrator=args.narrator, preferred_provider="elevenlabs")
    package = {
        "topic": args.topic,
        "narrator": args.narrator,
        "provider": result.get("provider"),
        "ok": result.get("ok"),
        "path": result.get("path"),
        "duration_sec": result.get("duration_sec"),
        "audio_qa": result.get("audio_qa"),
        "voice_package": result.get("voice_package"),
        "pipeline_stage": "voice_generation",
        "official_narration_provider": (result.get("voice_package") or {}).get("official_narration_provider"),
    }
    out_dir = ROOT / "data" / "productions" / "_validation" / "elevenlabs"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "PIPELINE_NARRATION_TEST.json").write_text(json.dumps(package, indent=2), encoding="utf-8")
    print(json.dumps({k: package[k] for k in ("ok", "provider", "path", "duration_sec", "official_narration_provider")}, indent=2))
    return 0 if package.get("ok") and package.get("provider") == "elevenlabs" else 1


def cmd_e2e(args: argparse.Namespace) -> int:
    """Live proof: auth → voices → narrate AI topic as Professor → QA."""
    from services.elevenlabs import validate_narration_audio, verify_elevenlabs_authentication
    from services.media_production.voice import synthesize_voice

    auth = verify_elevenlabs_authentication(live_probe=True)
    script = (
        "Stop — what you were taught about artificial intelligence is incomplete. "
        "Artificial intelligence is not a brain that understands. "
        "It is pattern matching at scale, predicting what comes next from data it has already seen. "
        "That one claim survives the hype. "
        "Share the myth you believed longest, then follow for the next demystifying short."
    )
    synth = synthesize_voice(
        script,
        narrator="professor",
        preferred_provider="elevenlabs",
        allow_fallback=False,
    )
    qa = synth.get("audio_qa") or validate_narration_audio((synth.get("voice_package") or {}).get("path"))
    report = {
        "topic": "What Artificial Intelligence Actually Is",
        "narrator": "professor",
        "target_length_sec": 45,
        "authentication": {
            "ok": auth.get("ok"),
            "api_key_loads": auth.get("api_key_loads"),
            "authentication_succeeds": auth.get("authentication_succeeds"),
            "voices_listable": auth.get("voices_listable"),
            "default_voice_exists": auth.get("default_voice_exists"),
        },
        "synthesis": {
            "ok": synth.get("ok"),
            "provider": synth.get("provider"),
            "path": synth.get("path"),
            "duration_sec": synth.get("duration_sec"),
            "placeholder": synth.get("placeholder"),
            "error": synth.get("error"),
        },
        "audio_qa": qa,
        "package_identifies_elevenlabs": (synth.get("voice_package") or {}).get("provider") == "elevenlabs",
        "passed": bool(
            auth.get("api_key_loads")
            and synth.get("ok")
            and synth.get("provider") == "elevenlabs"
            and qa.get("ok")
        ),
    }
    out_dir = ROOT / "data" / "productions" / "_validation" / "elevenlabs"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "E2E_VOICE_VERIFICATION.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (out_dir / "E2E_VOICE_VERIFICATION.md").write_text(
        "\n".join(
            [
                "# ElevenLabs E2E Voice Verification",
                "",
                f"**Passed: {report['passed']}**",
                f"- Auth OK: {auth.get('ok')}",
                f"- Provider: {synth.get('provider')}",
                f"- Path: `{synth.get('path')}`",
                f"- Duration: {synth.get('duration_sec')}s",
                f"- Audio QA: {qa.get('ok')}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="ElevenLabs production narration tools")
    sub = parser.add_subparsers(dest="command", required=True)

    p_health = sub.add_parser("health", help="Authentication / readiness health check")
    p_health.set_defaults(func=cmd_health)

    p_voices = sub.add_parser("voices", help="List ElevenLabs voices")
    p_voices.set_defaults(func=cmd_voices)

    p_nar = sub.add_parser("narrate", help="Generate a narration test clip")
    p_nar.add_argument("--text", default="Artificial intelligence is pattern matching at scale, not a thinking brain.")
    p_nar.add_argument("--file", default="")
    p_nar.add_argument("--narrator", default="professor")
    p_nar.add_argument("--allow-fallback", action="store_true")
    p_nar.set_defaults(func=cmd_narrate)

    p_pipe = sub.add_parser("pipeline", help="Pipeline narration test (same facade as ops voice stage)")
    p_pipe.add_argument("--topic", default="What Artificial Intelligence Actually Is")
    p_pipe.add_argument("--narrator", default="professor")
    p_pipe.add_argument("--text", default="")
    p_pipe.set_defaults(func=cmd_pipeline)

    p_e2e = sub.add_parser("e2e", help="End-to-end live voice verification")
    p_e2e.set_defaults(func=cmd_e2e)

    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
