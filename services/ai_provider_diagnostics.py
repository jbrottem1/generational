"""AI provider diagnostics — OpenAI + Anthropic status without exposing secrets."""

from __future__ import annotations

from typing import Any

from core.log import get_logger

logger = get_logger(__name__)


def _mask_openai(value: str) -> str:
    key = (value or "").strip()
    if not key:
        return ""
    if len(key) < 10:
        return "****"
    return f"{key[:6]}...{key[-4:]}"


def openai_key_status() -> dict[str, Any]:
    try:
        from core.ai.openai_provider import get_api_key

        key = (get_api_key() or "").strip()
    except Exception:  # noqa: BLE001
        import os

        key = (os.getenv("OPENAI_API_KEY") or "").strip()
    return {
        "provider": "openai",
        "key_found": bool(key),
        "key_status": "✓ OpenAI API Key Found" if key else "✗ OpenAI API Key Missing",
        "key_masked": _mask_openai(key) if key else "",
    }


def openai_connection_test() -> dict[str, Any]:
    """Lightweight OpenAI ping (models.list). Does not change generation paths."""
    status = openai_key_status()
    report = {
        **status,
        "ok": False,
        "request_status": "✗ API request failed",
        "error_type": "",
        "error_message": "",
        "latency_ms": 0,
    }
    if not status["key_found"]:
        report["error_type"] = "missing_key"
        report["error_message"] = "OPENAI_API_KEY is not set"
        return report
    try:
        import time

        from core.ai.openai_provider import get_api_key
        from openai import OpenAI

        t0 = time.time()
        client = OpenAI(api_key=get_api_key())
        _ = client.models.list()
        report["ok"] = True
        report["request_status"] = "✓ API request succeeded"
        report["latency_ms"] = int((time.time() - t0) * 1000)
    except Exception as exc:  # noqa: BLE001
        msg = str(exc)
        key = ""
        try:
            from core.ai.openai_provider import get_api_key

            key = get_api_key()
            if key:
                msg = msg.replace(key, _mask_openai(key))
        except Exception:  # noqa: BLE001
            pass
        name = type(exc).__name__
        lower = msg.lower()
        if "insufficient_quota" in lower or "429" in lower:
            et = "rate_limit"
        elif "auth" in lower or "invalid_api_key" in lower or name == "AuthenticationError":
            et = "authentication_error"
        elif "timeout" in lower or "connection" in lower:
            et = "network_error"
        else:
            et = "other"
        report["error_type"] = et
        report["error_message"] = f"{name}: {msg[:400]}"
        logger.error("openai.diagnostic_failed type=%s", et)
    return report


def anthropic_key_status() -> dict[str, Any]:
    from services.anthropic_client import get_anthropic_api_key, mask_anthropic_key

    key = get_anthropic_api_key()
    return {
        "provider": "anthropic",
        "key_found": bool(key),
        "key_status": "✓ Anthropic API Key Found" if key else "✗ Anthropic API Key Missing",
        "key_masked": mask_anthropic_key(key) if key else "",
    }


def anthropic_connection_test() -> dict[str, Any]:
    from services.anthropic_client import connection_test

    return connection_test()


def run_ai_provider_diagnostics(*, live: bool = False) -> dict[str, Any]:
    """Aggregate OpenAI + Anthropic diagnostics. Set live=True to hit the APIs."""
    openai = openai_connection_test() if live else {**openai_key_status(), "ok": None, "request_status": "not_run"}
    anthropic = anthropic_connection_test() if live else {**anthropic_key_status(), "ok": None, "request_status": "not_run"}
    return {
        "openai": openai,
        "anthropic": anthropic,
        "live": live,
    }
