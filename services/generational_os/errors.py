"""GenOS error classification — detect, log, retry, escalate."""

from __future__ import annotations

import re
from typing import Any

ERROR_CLASSES = (
    "provider_failure",
    "missing_assets",
    "render_failure",
    "voice_failure",
    "api_limit",
    "authentication",
    "network",
    "quality_failure",
    "unknown",
)

_PATTERNS: list[tuple[str, tuple[str, ...]]] = [
    ("api_limit", ("rate limit", "quota", "429", "insufficient_quota", "credits", "billing")),
    ("authentication", ("auth", "401", "403", "unauthorized", "invalid api key", "api_key")),
    ("network", ("timeout", "connection", "network", "dns", "temporarily unavailable", "502", "503")),
    ("voice_failure", ("elevenlabs", "tts", "narration", "voice synthes")),
    ("render_failure", ("ffmpeg", "render", "encode", "mux", "assemble_mp4")),
    ("missing_assets", ("missing file", "no asset", "not found", "no_approvable", "empty scenes")),
    ("quality_failure", ("qc_failed", "quality", "creative excellence", "validation failed")),
    ("provider_failure", ("provider", "openai", "dall-e", "youtube api", "upstream")),
]


def classify_error(error: str | Exception | None, *, context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Classify a failure for GenOS retry / escalate policy."""
    text = str(error or "").lower()
    ctx = context or {}
    matched = "unknown"
    for cls, needles in _PATTERNS:
        if any(n in text for n in needles):
            matched = cls
            break
    if matched == "unknown" and ctx.get("stage") == "voice_generation":
        matched = "voice_failure"
    if matched == "unknown" and ctx.get("stage") in ("rendering", "export"):
        matched = "render_failure"

    # Recoverable operational faults retry once/twice; auth + quality escalate
    retryable = matched in (
        "network",
        "api_limit",
        "provider_failure",
        "voice_failure",
        "render_failure",
        "missing_assets",
    )
    escalate = matched in ("authentication", "quality_failure") or (
        matched == "api_limit" and "billing" in text
    )
    return {
        "class": matched if matched in ERROR_CLASSES else "unknown",
        "message": str(error or "")[:400],
        "retryable": retryable,
        "escalate": escalate,
        "action": (
            "escalate"
            if escalate
            else ("retry" if retryable else "log_and_continue")
        ),
        "never_duplicate_completed": True,
        "context": {k: ctx.get(k) for k in ("stage", "production_id", "job_id") if k in ctx},
    }


def should_retry(classification: dict[str, Any], *, attempt: int, max_attempts: int = 2) -> bool:
    if attempt >= max_attempts:
        return False
    return bool(classification.get("retryable")) and not classification.get("escalate")
