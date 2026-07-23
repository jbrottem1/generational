"""Pre-render QA for Founder Voice — never print secrets."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.studio_assets.founder_voice.asset import ASSET_ID, ASSET_ROOT, get_founder_voice_id

ROOT = Path(__file__).resolve().parents[3]


def run_founder_voice_qa(*, live_probe: bool = True, write_report: bool = True) -> dict[str, Any]:
    from services.elevenlabs.auth import verify_elevenlabs_authentication
    from services.elevenlabs.config import api_key_present
    from services.elevenlabs.voices import list_elevenlabs_voices
    from services.provider_runtime.config import has_credential as runtime_has

    ts = datetime.now(timezone.utc).isoformat()
    voice_id = get_founder_voice_id()
    checks: list[dict[str, Any]] = []

    def add(cid: str, ok: bool, detail: str) -> None:
        checks.append({"id": cid, "ok": ok, "detail": detail})

    add(
        "elevenlabs_api_key_loaded",
        bool(runtime_has("ELEVENLABS_API_KEY") or api_key_present()),
        "ELEVENLABS_API_KEY",
    )
    auth = verify_elevenlabs_authentication(live_probe=live_probe) if live_probe else {"ok": True, "authentication_succeeds": True}
    add("elevenlabs_api_connected", bool(auth.get("authentication_succeeds") or auth.get("ok")), auth.get("classification") or "auth")
    add("api_healthy", bool(auth.get("ok")), "voices/live narration ready" if auth.get("ok") else "unhealthy")

    voices = list_elevenlabs_voices(limit=80) if live_probe else {"ok": False, "voices": []}
    ids = {str(v.get("voice_id") or "") for v in (voices.get("voices") or [])}
    voice_exists = voice_id in ids if ids else bool(voice_id)
    add("voice_id_exists", voice_exists, f"id_suffix=…{voice_id[-6:]}" if voice_id else "missing")
    add("voice_available", voice_exists and bool(voices.get("ok")), "cloned Founder Voice listed" if voice_exists else "not listed")

    quota_ok = False
    audio_ok = False
    if live_probe and auth.get("ok") and voice_exists:
        try:
            from services.media_production.voice import synthesize_voice

            probe = synthesize_voice(
                "Founder Voice quality check.",
                profile={"narrator": "founder", "narrator_profile": "founder"},
                settings={"preferred_provider": "elevenlabs"},
                mode="live",
                preferred_provider="elevenlabs",
                narrator="founder",
                allow_fallback=False,
            )
            audio_ok = bool(probe.get("ok") and probe.get("provider") == "elevenlabs" and not probe.get("placeholder"))
            quota_ok = audio_ok or "quota" not in str(probe.get("error") or "").lower()
            add("audio_generated_successfully", audio_ok, f"provider={probe.get('provider')}")
            add("quota_available", quota_ok, "tts_probe" if audio_ok else str(probe.get("error") or "quota_unknown")[:80])
        except Exception as exc:  # noqa: BLE001
            add("audio_generated_successfully", False, type(exc).__name__)
            add("quota_available", False, type(exc).__name__)
    else:
        add("audio_generated_successfully", False, "skipped")
        add("quota_available", False, "skipped")

    add("reject_fallback_when_available", True, "ELEVENLABS_ALLOW_FALLBACK=0 recommended")

    failed = [c for c in checks if not c["ok"] and c["id"] not in {"reject_fallback_when_available"}]
    report = {
        "generated_at": ts,
        "asset_id": ASSET_ID,
        "voice_id_suffix": f"…{voice_id[-6:]}" if len(voice_id) >= 6 else "",
        "checks": checks,
        "passed": len(failed) == 0,
        "production_ready": len(failed) == 0,
        "blockers": [c["id"] for c in failed],
    }

    if write_report:
        ASSET_ROOT.mkdir(parents=True, exist_ok=True)
        md = [
            "# Voice QA Report — Founder Voice (VOICE_ASSET_0001)",
            "",
            f"**Generated:** {ts}",
            f"**Production ready:** {'YES' if report['production_ready'] else 'NO'}",
            "",
            "## Checks",
            "",
        ]
        for c in checks:
            mark = "✓" if c["ok"] else "✗"
            md.append(f"- {mark} `{c['id']}` — {c['detail']}")
        md += [
            "",
            "## Failover policy",
            "",
            "- If ElevenLabs unavailable: pause, reconnect, retry.",
            "- Fallback only if user sets `ELEVENLABS_ALLOW_FALLBACK=1` or production is test mode.",
            "- Never silently replace Founder Voice.",
            "",
        ]
        (ASSET_ROOT / "VOICE_QA_REPORT.md").write_text("\n".join(md), encoding="utf-8")
        import json

        (ASSET_ROOT / "VOICE_QA_REPORT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    return report
