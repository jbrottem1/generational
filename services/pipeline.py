"""Content pipeline stage registry.

Single source of truth for the stages a piece of content moves through on
its way from idea to published video. Each future stage (research, SEO,
voice, video, publishing, analytics, self-improvement) gets implemented as
its own service module and flipped to available here — the UI and any
orchestration code read from this registry rather than hardcoding stages.
"""

from __future__ import annotations


class Stage:
    def __init__(self, key: str, icon: str, label: str, available: bool = False) -> None:
        self.key = key
        self.icon = icon
        self.label = label
        self.available = available


STAGES = [
    Stage("ideation", "💡", "Ideation", available=True),
    Stage("research", "🔍", "Research"),
    Stage("seo", "🔑", "SEO"),
    Stage("script", "📝", "Script"),
    Stage("voice", "🎙️", "Voice"),
    Stage("visuals", "🎨", "Visuals"),
    Stage("edit", "✂️", "Edit"),
    Stage("publish", "📤", "Publish"),
    Stage("analytics", "📊", "Analytics"),
    Stage("self_improvement", "🧠", "Self-Improve"),
]


def next_stages() -> list:
    """The stages shown as 'next steps' after ideation, in order."""
    return [stage for stage in STAGES if stage.key not in ("ideation", "analytics", "self_improvement")]
