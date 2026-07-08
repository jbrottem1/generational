"""Lightweight natural-language command parsing (keyword/regex based, no AI)."""

import re

from core.constants import NICHE_KEYWORDS, WORD_NUMBERS


def detect_niche(command: str) -> str:
    lower = f" {command.lower()} "
    for niche, keywords in NICHE_KEYWORDS.items():
        if any(keyword in lower for keyword in keywords):
            return niche
    return "General Content"


def detect_video_count(command: str) -> int:
    lower = command.lower()
    match = re.search(r"\b(\d+)\b", lower)
    if match:
        return int(match.group(1))
    for word, number in WORD_NUMBERS.items():
        if word in lower:
            return number
    return 10


def detect_subject(command: str, fallback: str) -> str:
    lower = command.lower()
    match = re.search(r"\babout (.+)", lower)
    if not match:
        match = re.search(r"\bfor (.+)", lower)
    if match:
        return match.group(1).strip(" .")
    return fallback


def build_goal(subject: str) -> str:
    return f"Create engaging short-form content about {subject}"
