"""Editorial philosophy for Generational motivational media."""

from __future__ import annotations

MISSION_STATEMENT = (
    "Produce world-class motivational YouTube Shorts and long-form content that "
    "helps people become disciplined, resilient, mentally stronger, and more "
    "capable — leaving every viewer ready to get off the couch and take action."
)

EMOTIONAL_OUTCOME = "I am getting off this couch and taking action."

EDITORIAL_PHILOSOPHY = {
    "objective": "transformation",
    "not_objective": "empty entertainment or viral hype",
    "combine": (
        "psychology",
        "storytelling",
        "philosophy",
        "real history",
        "science",
        "authentic human struggle",
        "practical action",
    ),
    "forbid": (
        "empty inspiration",
        "loud hype",
        "disconnected slogans",
        "generic AI motivation",
        "fabricated history",
        "fabricated biographies",
        "fabricated statistics",
        "fabricated quotations",
    ),
    "prefer_references": (
        "history",
        "psychology",
        "neuroscience",
        "sports",
        "military leadership",
        "engineering",
        "business",
        "medicine",
        "exploration",
        "space",
        "science",
        "literature",
        "philosophy",
        "biographies",
        "entrepreneurship",
    ),
    "quotation_policy": (
        "Use brief, accurately attributed quotations only when legally appropriate. "
        "Prefer public-domain authors, classical philosophers, and verified "
        "historical writings. Never fabricate or silently alter quotations. "
        "If a quotation cannot be confidently verified, summarize the person's "
        "documented philosophy in original language instead."
    ),
}

WRITING_STANDARD = (
    "emotionally intelligent",
    "factually responsible",
    "logically connected",
    "cinematic",
    "conversational",
    "natural to speak aloud",
    "high-retention",
    "emotionally memorable",
)

REJECT_CRITERIA = (
    "disconnected ideas",
    "robotic tone",
    "vague inspiration",
    "unsupported claims",
    "quotation-only scripts",
    "cannot be summarized in one sentence",
    "missing struggle or application",
    "no path to immediate action",
)


def ai_editorial_system_prompt() -> str:
    """Compact system prompt fragment for AI script enhancement."""
    return (
        "You write motivational scripts for Generational — a trusted educational "
        "motivational studio. Objective: transformation, not hype. Every script "
        "must follow Hook → Struggle → Real-life example → Lesson → Application → "
        "Memorable ending. Viewer psychology: Curiosity → Recognition → Reflection → "
        f"Hope → Determination → Immediate Action. Emotional outcome: \"{EMOTIONAL_OUTCOME}\" "
        "Never invent historical events, biographies, statistics, or quotations. "
        "If a quote is not verified, paraphrase the documented idea instead. "
        "Every sentence must connect to the next and advance one central idea."
    )
