"""Demo provider — deterministic placeholder content, no API needed.

Used directly when no API key is configured, and as the fallback content
source when a real provider fails.
"""

from __future__ import annotations

from core.ai.base import AIProvider, GenerationRequest, GenerationResult


def placeholder_ideas(niche: str, subject: str, count: int) -> list:
    niche_tag = niche.replace(" ", "").replace("&", "")
    subject_tag = (subject.split()[0] if subject.split() else niche).title()
    ideas = []
    for i in range(1, count + 1):
        ideas.append(
            {
                "title": f"{niche} Idea #{i}: The Truth About {subject.title()}",
                "hook": f"Did you know this about {subject}? [Placeholder hook #{i}]",
                "script": (
                    f"[0-3s] Hook: grab attention with a bold claim about {subject}. "
                    f"[4-20s] Deliver 2-3 quick, punchy insights on {subject} in the {niche} niche. "
                    f"[21-30s] Wrap up with a takeaway and tease the next video. (Placeholder script #{i})"
                ),
                "cta": "Follow for more like this!",
                "hashtags": [f"#{niche_tag}", f"#{subject_tag}", "#Shorts", "#Generational"],
                "thumbnail_concept": (
                    f"Bold text overlay reading '{subject.title()}' over a shocked/curious "
                    f"reaction face. (Placeholder concept)"
                ),
            }
        )
    return ideas


class DemoProvider(AIProvider):
    name = "demo"

    def is_available(self) -> bool:
        return True

    def generate_ideas(self, request: GenerationRequest) -> GenerationResult:
        ideas = placeholder_ideas(request.niche, request.subject, request.count)
        return GenerationResult(ideas=ideas, demo_mode=True)
