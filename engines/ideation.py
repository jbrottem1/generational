"""Ideation engine — stage 2: produce a wide pool of candidate ideas.

Generates `candidate_count` (default 20) title+hook+angle concepts for the
downstream psychology scoring and ranking stages to filter. Uses the AI
provider when available, with a deterministic angle-archetype fallback.
"""

from __future__ import annotations

from core import parsing
from core.ai import get_provider
from core.constants import CANDIDATE_IDEAS
from core.log import get_logger, log_event
from engines.base import Engine

logger = get_logger(__name__)

# Proven short-form angle archetypes used for Demo Mode candidates.
ANGLES = [
    ("The hidden truth", "Nobody tells you this about {s}, and it changes everything."),
    ("The #1 mistake", "The biggest mistake people make with {s} — and how to avoid it."),
    ("The science says", "A study on {s} found something that surprised even the researchers."),
    ("The myth", "Everything you've heard about {s} is actually a myth."),
    ("The 3-second test", "You can test your {s} in 3 seconds. Here's how."),
    ("The counterintuitive fix", "The fix for {s} is the exact opposite of what you'd expect."),
    ("The famous example", "How one famous case of {s} changed how experts think about it."),
    ("The timeline", "What happens to you after 1 day, 1 week, and 1 year of {s}."),
    ("The comparison", "{s} vs what actually works — the difference is shocking."),
    ("The insider secret", "Experts quietly use this {s} trick every single day."),
    ("The warning sign", "If you notice this, {s} is already affecting you."),
    ("The origin story", "The strange story of how {s} was discovered."),
    ("The 80/20", "20% of what you do about {s} drives 80% of the results."),
    ("The instant reframe", "One sentence that changes how you see {s} forever."),
    ("The challenge", "I tried beating {s} for 7 days. Day 3 broke me."),
    ("The question", "Why does {s} happen to smart people the most?"),
    ("The number", "The 5 stages of {s} — most people get stuck at stage 2."),
    ("The future", "What {s} will look like in 10 years, according to the data."),
    ("The confession", "The uncomfortable truth about {s} nobody wants to admit."),
    ("The quick win", "The 10-second habit that neutralizes {s}."),
]


class IdeationEngine(Engine):
    key = "ideation"
    label = "Ideation"
    icon = "💡"
    description = "Generate a wide pool of candidate content concepts."

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        command = context["command"]
        niche = context.get("niche") or parsing.detect_niche(command)
        subject = context.get("subject") or parsing.detect_subject(command, fallback=niche.lower())
        candidate_count = context.get("candidate_count", CANDIDATE_IDEAS)

        candidates = self._provider_candidates(context, command, niche, subject, candidate_count)
        if candidates is None:
            candidates = self._heuristic_candidates(niche, subject, candidate_count)

        log_event(logger, "ideation.candidates_generated", count=len(candidates), niche=niche)
        return {"niche": niche, "subject": subject, "candidates": candidates}

    def _provider_candidates(
        self, context: dict, command: str, niche: str, subject: str, count: int
    ) -> "list | None":
        provider = get_provider()
        system = (
            "You are a viral short-form content ideation expert. "
            "Respond with valid minified JSON only."
        )
        user = (
            f'Command: "{command}"\nNiche: "{niche}"\nSubject: "{subject}"\n'
            f"Research summary: {context.get('research', {}).get('summary', 'n/a')}\n\n"
            f"Generate exactly {count} distinct candidate video concepts. Respond with JSON:\n"
            '{"candidates": [{"title": "catchy title", "hook": "1-2 sentence opening hook",'
            ' "angle": "the angle archetype in 2-4 words"}]}'
        )
        data, tokens = provider.generate_json(system, user, context.get("model", ""))
        if data is None:
            if provider.name != "demo":
                context["error"] = "AI ideation call failed; used heuristic fallback."
            return None
        context["tokens_used"] = context.get("tokens_used", 0) + tokens
        candidates = [c for c in data.get("candidates", []) if c.get("title") and c.get("hook")]
        return candidates[:count] or None

    def _heuristic_candidates(self, niche: str, subject: str, count: int) -> list:
        candidates = []
        for index in range(count):
            angle_name, hook_template = ANGLES[index % len(ANGLES)]
            candidates.append(
                {
                    "title": f"{angle_name}: {subject.title()} ({niche})",
                    "hook": hook_template.format(s=subject),
                    "angle": angle_name,
                }
            )
        return candidates
