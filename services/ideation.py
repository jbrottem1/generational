"""Ideation service — turns a natural-language command into a content batch.

This is the first pipeline stage. It owns the full flow (parse command →
pick AI provider → generate → assemble result) so UI code only renders.
"""

from __future__ import annotations

from core import parsing
from core.ai import GenerationRequest, get_provider
from core.log import get_logger
from core.models import build_result

logger = get_logger(__name__)


def run_command(command: str, count: int, model: str) -> dict:
    """Parse a command and generate a content batch.

    Returns a result dict (see core.models.build_result) with an extra
    transient "error" key when generation fell back to demo content.
    """
    niche = parsing.detect_niche(command)
    video_count = parsing.detect_video_count(command)
    subject = parsing.detect_subject(command, fallback=niche.lower())
    goal = parsing.build_goal(subject)

    provider = get_provider()
    logger.info("Running command via provider '%s': %s", provider.name, command)
    generation = provider.generate_ideas(
        GenerationRequest(command=command, niche=niche, subject=subject, count=count, model=model)
    )

    result = build_result(
        command=command,
        niche=niche,
        video_count=video_count,
        goal=goal,
        ideas=generation.ideas,
        demo_mode=generation.demo_mode,
        model=model,
    )
    result["tokens_used"] = generation.tokens_used
    if generation.error:
        result["error"] = generation.error
    return result
