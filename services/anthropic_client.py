"""Reusable Anthropic client for diagnostics and lightweight text calls.

Reads ``ANTHROPIC_API_KEY`` from the shared credential stack (env / .env /
SecretManager). Never logs or returns the full API key.

Prefer the official ``anthropic`` SDK when installed; otherwise use the
stdlib HTTP path (same approach as ``AnthropicConnector``).
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from core.log import get_logger

logger = get_logger(__name__)

DEFAULT_MODEL = "claude-haiku-4-5-20251001"  # low-cost current Haiku for connectivity checks
DEFAULT_TIMEOUT_SEC = 30.0
ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"


def mask_anthropic_key(value: str) -> str:
    """Return ``sk-ant...XXXX`` style mask — never the full secret."""
    key = (value or "").strip()
    if not key:
        return ""
    if len(key) < 10:
        return "****"
    return f"{key[:6]}...{key[-4:]}"


def get_anthropic_api_key() -> str:
    """Resolve Anthropic key without printing it."""
    try:
        from services.provider_runtime.config import get_credential

        return (get_credential("ANTHROPIC_API_KEY") or "").strip()
    except Exception:  # noqa: BLE001
        import os

        return (os.getenv("ANTHROPIC_API_KEY") or "").strip()


@dataclass
class AnthropicTextResult:
    ok: bool
    text: str = ""
    model: str = ""
    error_type: str = ""
    error_message: str = ""
    latency_ms: int = 0
    sdk: str = ""


def anthropic_sdk_version() -> str | None:
    try:
        import anthropic

        return getattr(anthropic, "__version__", "unknown")
    except ImportError:
        return None


def get_client(*, timeout_sec: float = DEFAULT_TIMEOUT_SEC):
    """Return an official Anthropic SDK client when available, else None."""
    key = get_anthropic_api_key()
    if not key:
        raise ValueError("ANTHROPIC_API_KEY missing")
    try:
        from anthropic import Anthropic

        return Anthropic(api_key=key, timeout=timeout_sec)
    except ImportError:
        return None


def _classify_error(exc: BaseException, *, status: int | None = None, body: str = "") -> tuple[str, str]:
    """Map failures to a stable category + sanitized message (no secrets)."""
    key = get_anthropic_api_key()
    msg = str(exc)
    if key:
        msg = msg.replace(key, mask_anthropic_key(key))
    msg = msg[:500]
    name = type(exc).__name__
    lower = (msg + " " + body).lower()

    if not key:
        return "missing_key", "ANTHROPIC_API_KEY is not set"
    if status == 401 or "authentication" in lower or "invalid_api_key" in lower or "invalid x-api-key" in lower:
        return "authentication_error", msg or "Authentication failed"
    if status == 403 or "permission" in lower:
        return "invalid_key", msg or "Forbidden / invalid key permissions"
    if status == 404 or "not_found_error" in lower:
        return "other", msg or "Not found (check model id / endpoint)"
    if status == 429 or "rate_limit" in lower or "rate limit" in lower:
        return "rate_limit", msg or "Rate limited"
    if isinstance(exc, (TimeoutError, urllib.error.URLError)) or "timed out" in lower or "timeout" in lower:
        return "network_error", msg or "Network / timeout error"
    if "ImportError" in name or "module" in lower and "anthropic" in lower:
        return "sdk_version_mismatch", msg
    if status and status >= 500:
        return "network_error", msg or f"Upstream HTTP {status}"
    return "other", f"{name}: {msg}" if msg else name


def request_text(
    prompt: str,
    *,
    system: str = "You are a concise assistant.",
    model: str = DEFAULT_MODEL,
    max_tokens: int = 32,
    timeout_sec: float = DEFAULT_TIMEOUT_SEC,
) -> AnthropicTextResult:
    """Minimal reusable text request with timeout + exception handling."""
    import time

    key = get_anthropic_api_key()
    if not key:
        logger.warning("anthropic.request skipped — ANTHROPIC_API_KEY missing")
        return AnthropicTextResult(ok=False, error_type="missing_key", error_message="ANTHROPIC_API_KEY is not set")

    t0 = time.time()
    client = None
    try:
        client = get_client(timeout_sec=timeout_sec)
    except ValueError as exc:
        et, em = _classify_error(exc)
        return AnthropicTextResult(ok=False, error_type=et, error_message=em)

    # Official SDK path
    if client is not None:
        try:
            resp = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
            parts = []
            for block in getattr(resp, "content", []) or []:
                text = getattr(block, "text", None)
                if text:
                    parts.append(text)
            latency = int((time.time() - t0) * 1000)
            logger.info("anthropic.request ok sdk=anthropic model=%s latency_ms=%s", model, latency)
            return AnthropicTextResult(
                ok=True,
                text="".join(parts).strip(),
                model=model,
                latency_ms=latency,
                sdk=f"anthropic=={anthropic_sdk_version()}",
            )
        except Exception as exc:  # noqa: BLE001
            et, em = _classify_error(exc)
            logger.error("anthropic.request failed sdk=anthropic type=%s", et)
            return AnthropicTextResult(
                ok=False,
                error_type=et,
                error_message=em,
                latency_ms=int((time.time() - t0) * 1000),
                sdk=f"anthropic=={anthropic_sdk_version()}",
            )

    # Stdlib HTTP fallback (no vendor SDK required)
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": prompt}],
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        ANTHROPIC_MESSAGES_URL,
        data=data,
        method="POST",
        headers={
            "x-api-key": key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            raw = resp.read()
            body = json.loads(raw.decode("utf-8"))
            content = body.get("content") or []
            text = "".join(str(block.get("text") or "") for block in content if isinstance(block, dict))
            latency = int((time.time() - t0) * 1000)
            logger.info("anthropic.request ok sdk=http model=%s latency_ms=%s", model, latency)
            return AnthropicTextResult(
                ok=True,
                text=text.strip(),
                model=model,
                latency_ms=latency,
                sdk="http",
            )
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="replace")[:300]
        except Exception:  # noqa: BLE001
            body = ""
        et, em = _classify_error(exc, status=exc.code, body=body)
        if body and et != "missing_key":
            # Include sanitized body snippet for operators
            safe_body = body
            if key:
                safe_body = safe_body.replace(key, mask_anthropic_key(key))
            em = f"{em} | http={exc.code} body={safe_body[:200]}"
        logger.error("anthropic.request failed sdk=http type=%s status=%s", et, exc.code)
        return AnthropicTextResult(
            ok=False,
            error_type=et,
            error_message=em,
            latency_ms=int((time.time() - t0) * 1000),
            sdk="http",
        )
    except Exception as exc:  # noqa: BLE001
        et, em = _classify_error(exc)
        logger.error("anthropic.request failed sdk=http type=%s", et)
        return AnthropicTextResult(
            ok=False,
            error_type=et,
            error_message=em,
            latency_ms=int((time.time() - t0) * 1000),
            sdk="http",
        )


def connection_test() -> dict[str, Any]:
    """Minimal live connectivity check. Never includes the raw API key."""
    key = get_anthropic_api_key()
    found = bool(key)
    report: dict[str, Any] = {
        "key_found": found,
        "key_status": "✓ Anthropic API Key Found" if found else "✗ Anthropic API Key Missing",
        "key_masked": mask_anthropic_key(key) if found else "",
        "sdk_version": anthropic_sdk_version(),
        "sdk_installed": anthropic_sdk_version() is not None,
        "ok": False,
        "request_status": "✗ API request failed",
        "error_type": "",
        "error_message": "",
        "reply": "",
        "model": DEFAULT_MODEL,
        "latency_ms": 0,
        "transport": "",
    }
    if not found:
        report["error_type"] = "missing_key"
        report["error_message"] = "ANTHROPIC_API_KEY is not set in environment / .env"
        return report

    result = request_text(
        'Reply with exactly:\nAnthropic connection successful.',
        max_tokens=24,
        model=DEFAULT_MODEL,
    )
    report["latency_ms"] = result.latency_ms
    report["transport"] = result.sdk
    report["model"] = result.model or DEFAULT_MODEL
    if result.ok:
        report["ok"] = True
        report["request_status"] = "✓ API request succeeded"
        report["reply"] = result.text
    else:
        report["error_type"] = result.error_type
        report["error_message"] = result.error_message
        report["request_status"] = "✗ API request failed"
    return report
