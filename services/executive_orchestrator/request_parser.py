"""Parse one-line studio commands into structured production briefs."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any


PLATFORM_ALIASES = {
    "youtube shorts": "youtube_shorts",
    "youtube short": "youtube_shorts",
    "shorts": "youtube_shorts",
    "short": "youtube_shorts",
    "tiktok": "tiktok",
    "instagram": "instagram_reels",
    "instagram reels": "instagram_reels",
    "reels": "instagram_reels",
    "facebook": "facebook",
    "facebook reels": "facebook_reels",
    "x": "x",
    "twitter": "x",
    "linkedin": "linkedin",
    "pinterest": "pinterest",
    "youtube": "youtube",
    "long-form": "youtube_long",
    "long form": "youtube_long",
    "longform": "youtube_long",
    "documentary": "youtube_long",
}


@dataclass
class ProductionBrief:
    """Normalized one-command request."""

    raw_command: str
    topic: str
    platforms: list[str] = field(default_factory=lambda: ["youtube_shorts"])
    primary_platform: str = "youtube_shorts"
    runtime_sec: int = 60
    format: str = "short"  # short | documentary | long_form
    category: str = "science"
    goal: str = "educate"
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _extract_runtime(text: str) -> int | None:
    patterns = [
        (r"(\d+(?:\.\d+)?)\s*(?:hour|hr|hrs|hours)\b", 3600.0),
        (r"(\d+(?:\.\d+)?)\s*(?:minute|min|mins|minutes)\b", 60.0),
        (r"(\d+(?:\.\d+)?)\s*(?:second|sec|secs|seconds)\b", 1.0),
        (r"\b(\d+)\s*s\b", 1.0),
        (r"\b(\d+)\s*m\b", 60.0),
    ]
    lower = text.lower()
    for pattern, mult in patterns:
        m = re.search(pattern, lower)
        if m:
            return max(5, int(float(m.group(1)) * mult))
    return None


def _extract_platforms(text: str) -> list[str]:
    lower = text.lower()
    found: list[str] = []
    # Longer phrases first
    for phrase in sorted(PLATFORM_ALIASES.keys(), key=len, reverse=True):
        if phrase in lower:
            plat = PLATFORM_ALIASES[phrase]
            if plat not in found:
                found.append(plat)
    return found


def _extract_topic(text: str) -> str:
    cleaned = text.strip()
    # Strip leading create/make/produce verbs
    cleaned = re.sub(
        r"^(?:please\s+)?(?:create|make|produce|generate|build|film|shoot)\s+",
        "",
        cleaned,
        flags=re.I,
    )
    # Drop runtime / platform clauses commonly used as wrappers
    cleaned = re.sub(
        r"\b(?:a|an)\s+\d+(?:\.\d+)?\s*(?:second|sec|secs|seconds|minute|min|mins|minutes|hour|hr|hrs|hours)\b",
        "",
        cleaned,
        flags=re.I,
    )
    cleaned = re.sub(
        r"\b(?:youtube\s+shorts?|shorts?|tiktok|instagram(?:\s+reels)?|reels|facebook(?:\s+reels)?|"
        r"linkedin|pinterest|twitter|\bx\b|long[- ]?form(?:\s+documentary)?|documentary)\b",
        "",
        cleaned,
        flags=re.I,
    )
    cleaned = re.sub(
        r"\b(?:video|explainer|short|clip|episode|piece)\b",
        "",
        cleaned,
        flags=re.I,
    )
    cleaned = re.sub(r"\b(?:explaining|about|on|regarding|covering)\b", " ", cleaned, flags=re.I)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .,:;-")
    cleaned = re.sub(r"^(?:a|an|the)\s+", "", cleaned, flags=re.I).strip()
    return cleaned or text.strip()


def _infer_format(platforms: list[str], runtime_sec: int, text: str) -> str:
    lower = text.lower()
    if "documentary" in lower or "long-form" in lower or "long form" in lower:
        return "documentary"
    if any(p in ("youtube_long",) for p in platforms) or runtime_sec >= 480:
        return "documentary" if "documentary" in lower or runtime_sec >= 600 else "long_form"
    if any(p in ("youtube_shorts", "tiktok", "instagram_reels") for p in platforms) or runtime_sec <= 90:
        return "short"
    return "long_form"


def _default_runtime(platforms: list[str], fmt: str) -> int:
    if fmt == "documentary":
        return 720
    if fmt == "long_form":
        return 480
    if "tiktok" in platforms or "instagram_reels" in platforms or "youtube_shorts" in platforms:
        return 60
    return 180


def parse_production_request(command: str, *, category: str = "science") -> ProductionBrief:
    """Turn a free-form instruction into a ProductionBrief."""
    text = (command or "").strip()
    if not text:
        return ProductionBrief(raw_command="", topic="untitled", notes=["empty_command"])

    platforms = _extract_platforms(text)
    runtime = _extract_runtime(text)
    topic = _extract_topic(text)
    fmt = _infer_format(platforms or ["youtube_shorts"], runtime or 60, text)

    if not platforms:
        if fmt == "documentary":
            platforms = ["youtube"]
        elif fmt == "long_form":
            platforms = ["youtube"]
        else:
            platforms = ["youtube_shorts"]

    if runtime is None:
        runtime = _default_runtime(platforms, fmt)

    # Shorts / TikTok / Reels clamp
    notes: list[str] = []
    if any(p in ("youtube_shorts", "tiktok", "instagram_reels") for p in platforms) and runtime > 180:
        notes.append(f"clamped_runtime_for_short_form:{runtime}->60")
        runtime = 60
        fmt = "short"

    primary = platforms[0]
    return ProductionBrief(
        raw_command=text,
        topic=topic,
        platforms=platforms,
        primary_platform=primary,
        runtime_sec=int(runtime),
        format=fmt,
        category=category,
        goal="educate",
        notes=notes,
    )
