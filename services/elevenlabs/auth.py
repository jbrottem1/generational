"""ElevenLabs authentication verification — production readiness gate."""

from __future__ import annotations

import os
from typing import Any

from services.elevenlabs.config import get_elevenlabs_config
from services.elevenlabs.voices import list_elevenlabs_voices


def classify_auth_error(message: str) -> str:
    err = (message or "").lower()
    if not err.strip():
        return "UNKNOWN_ERROR"
    if "missing" in err and "key" in err:
        return "MISSING_API_KEY"
    if "401" in err or "unauthorized" in err or ("invalid" in err and "key" in err):
        return "INVALID_API_KEY"
    if "missing_permissions" in err or "permission" in err or "403" in err:
        return "PERMISSION_ERROR"
    if "429" in err or "rate" in err:
        return "RATE_LIMITED"
    if "quota" in err or "payment" in err:
        return "QUOTA_EXHAUSTED"
    if "timeout" in err or "network" in err or "status=0" in err or "unreachable" in err:
        return "NETWORK_ERROR"
    return "UNKNOWN_ERROR"


def verify_elevenlabs_authentication(*, live_probe: bool = True) -> dict[str, Any]:
    """Verify API key loads, auth succeeds, voices list, default voice exists.

    Narration keys may lack ``user_read``; success is proven via reachable
    ``/voices`` (or SDK voice list), not solely ``/user``.
    """
    cfg = get_elevenlabs_config()
    report: dict[str, Any] = {
        "ok": False,
        "api_key_loads": bool(cfg["api_key_configured"]),
        "authentication_succeeds": False,
        "voices_listable": False,
        "default_voice_exists": False,
        "live_narration_ready": False,
        "default_voice_id": cfg["default_voice_id"],
        "default_voice_configured": bool((os.environ.get("ELEVENLABS_DEFAULT_VOICE_ID") or "").strip()),
        "model_id": cfg["model_id"],
        "provider": "elevenlabs",
        "classification": "MISSING_API_KEY",
        "checks": [],
        "errors": [],
        "warnings": [],
    }

    if not report["api_key_loads"]:
        report["checks"].append({"id": "api_key_loads", "ok": False, "detail": "ELEVENLABS_API_KEY missing"})
        report["errors"].append("Set ELEVENLABS_API_KEY in project-root .env")
        report["classification"] = "MISSING_API_KEY"
        return report
    report["checks"].append({"id": "api_key_loads", "ok": True, "detail": "configured"})

    if not live_probe:
        report["ok"] = True
        report["authentication_succeeds"] = True
        report["classification"] = "AUTHENTICATED"
        report["checks"].append({"id": "live_probe", "ok": True, "detail": "skipped"})
        return report

    auth_ok = False
    try:
        from services.provider_runtime.connectors.voice import ElevenLabsConnector

        conn = ElevenLabsConnector()
        voices_probe = conn.http(
            "GET", "/voices", timeout_sec=20.0, retries=1, headers={"Accept": "application/json"}
        )
        if voices_probe.ok:
            auth_ok = True
        else:
            user_probe = conn.http(
                "GET", "/user", timeout_sec=15.0, retries=0, headers={"Accept": "application/json"}
            )
            if user_probe.ok:
                auth_ok = True
            else:
                detail = ""
                body = user_probe.body if isinstance(user_probe.body, dict) else {}
                if isinstance(body.get("detail"), dict):
                    detail = str(body["detail"].get("status") or body["detail"].get("message") or "")
                    if "missing_permissions" in detail.lower():
                        report["warnings"].append(
                            "API key lacks user_read; narration uses voices/TTS endpoints instead"
                        )
                report["errors"].append(
                    f"voices HTTP {voices_probe.status}; user HTTP {user_probe.status} {detail}".strip()
                )
    except Exception as exc:  # noqa: BLE001
        report["errors"].append(f"auth error: {exc}"[:200])

    voices = list_elevenlabs_voices(limit=100)
    report["voices_listable"] = bool(voices.get("ok"))
    report["voice_count"] = int(voices.get("count") or 0)
    report["voices_source"] = voices.get("source")
    if voices.get("ok"):
        auth_ok = True
    elif not auth_ok:
        report["errors"].append(str(voices.get("error") or "voices list failed"))

    report["authentication_succeeds"] = auth_ok
    report["checks"].append({"id": "authentication", "ok": auth_ok, "detail": "voices/sdk probe"})
    report["checks"].append(
        {"id": "voices_listable", "ok": report["voices_listable"], "detail": f"n={report.get('voice_count', 0)}"}
    )

    ids = {str(v.get("voice_id") or "") for v in (voices.get("voices") or [])}
    default_id = cfg["default_voice_id"]
    report["default_voice_exists"] = (default_id in ids) if ids else bool(default_id)
    report["checks"].append(
        {
            "id": "default_voice_exists",
            "ok": report["default_voice_exists"],
            "detail": (default_id[:8] + "…") if len(default_id) > 8 else default_id,
        }
    )

    report["live_narration_ready"] = bool(
        report["api_key_loads"] and report["authentication_succeeds"] and report["voices_listable"]
    )
    report["ok"] = report["live_narration_ready"]
    if report["ok"]:
        report["classification"] = "AUTHENTICATED"
    else:
        report["classification"] = classify_auth_error(" ".join(report["errors"]))
    return report
