"""Asset video script generator — Phase 1A.

Turns an existing content asset into a validated 30–90 second short-form
script. Uses the shared OpenAI provider (`core.ai.get_provider`); never
duplicates API clients. Malformed JSON is retried once, then falls back to a
deterministic heuristic script in demo mode.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from core.ai import get_provider, is_demo_mode
from core.log import get_logger
from core.script_models import (
    MAX_TARGET_DURATION,
    MIN_TARGET_DURATION,
    ProgressCallback,
    ScriptGenerationResult,
    ScriptSegment,
    VideoScript,
    validate_script_payload,
)

logger = get_logger(__name__)

DEFAULT_MODEL = "gpt-4o-mini"
MAX_ATTEMPTS = 2

SYSTEM_PROMPT = (
    "You are an elite short-form video scriptwriter for YouTube Shorts, TikTok, "
    "and Instagram Reels. Write tight, high-retention voiceover scripts with no "
    "filler and no generic introductions. Respond with valid minified JSON only — "
    "no markdown fences, no prose."
)


def _asset_context(asset: dict[str, Any], project: dict[str, Any] | None = None) -> dict[str, str]:
    project = project or {}
    platform = (
        project.get("platform")
        or (project.get("studio_settings") or {}).get("platform")
        or asset.get("script_platform")
        or "youtube_shorts"
    )
    return {
        "title": str(asset.get("title") or "Untitled"),
        "hook": str(asset.get("hook") or ""),
        "description": str(asset.get("description") or asset.get("cta") or ""),
        "existing_script": str(asset.get("script") or ""),
        "keywords": ", ".join(str(k) for k in (asset.get("keywords") or asset.get("suggested_seo_keywords") or [])),
        "hashtags": ", ".join(str(h) for h in (asset.get("hashtags") or [])),
        "thumbnail": str(asset.get("thumbnail_concept") or ""),
        "niche": str(project.get("niche") or "General"),
        "platform": str(platform),
    }


def build_generation_prompt(asset: dict[str, Any], project: dict[str, Any] | None = None) -> tuple[str, str]:
    """Return (system, user) prompts for structured script generation."""
    ctx = _asset_context(asset, project)
    user = (
        f"Create a complete short-form video script from this content asset.\n\n"
        f"Title: {ctx['title']}\n"
        f"Hook: {ctx['hook']}\n"
        f"Description: {ctx['description']}\n"
        f"Keywords: {ctx['keywords']}\n"
        f"Hashtags: {ctx['hashtags']}\n"
        f"Thumbnail concept: {ctx['thumbnail']}\n"
        f"Niche: {ctx['niche']}\n"
        f"Target platform: {ctx['platform']}\n"
    )
    if ctx["existing_script"]:
        user += f"Existing draft (improve, do not copy filler): {ctx['existing_script'][:600]}\n"

    user += (
        "\nRequirements:\n"
        f"- Target duration: {MIN_TARGET_DURATION}–{MAX_TARGET_DURATION} seconds\n"
        "- Powerful opening hook in the first 1–2 seconds (segment 1, end_time ≤ 3)\n"
        "- Natural voiceover narration for short-form vertical video\n"
        "- Emotional pacing with a clear primary emotion\n"
        "- Curiosity gaps and pattern interrupts / retention hooks every 5–8 seconds\n"
        "- Strong payoff before the CTA\n"
        "- Natural call to action at the end\n"
        "- NO filler, NO 'Welcome back', NO generic intros\n"
        "- Language tuned for YouTube Shorts, TikTok, and Instagram Reels\n\n"
        "Respond with JSON exactly matching this schema:\n"
        "{\n"
        '  "title": "string",\n'
        '  "target_duration_seconds": 60,\n'
        '  "tone": "mysterious",\n'
        '  "primary_emotion": "curiosity",\n'
        '  "script_summary": "one sentence summary",\n'
        '  "segments": [\n'
        "    {\n"
        '      "segment_number": 1,\n'
        '      "start_time": 0,\n'
        '      "end_time": 2,\n'
        '      "segment_type": "hook",\n'
        '      "voiceover": "opening line",\n'
        '      "emotion": "curiosity",\n'
        '      "delivery": "quiet and suspenseful",\n'
        '      "retention_device": "open loop"\n'
        "    }\n"
        "  ],\n"
        '  "full_voiceover": "complete narration as one string",\n'
        '  "call_to_action": "natural CTA",\n'
        '  "estimated_word_count": 130\n'
        "}\n"
        "segment_type must be one of: hook, context, escalation, evidence, payoff, "
        "cta, pattern_interrupt, retention_hook, story_beat.\n"
        "Segments must be contiguous from 0 to the target duration."
    )
    return SYSTEM_PROMPT, user


def _heuristic_script(asset: dict[str, Any], project: dict[str, Any] | None = None) -> VideoScript:
    """Deterministic fallback when AI is unavailable or returns invalid JSON."""
    ctx = _asset_context(asset, project)
    title = ctx["title"]
    hook = ctx["hook"] or f"Nobody explains {title.lower()} like this."
    target = 60
    cta = str(asset.get("cta") or "Follow for the next part — you will want to see this.")

    body_bits = []
    if ctx["description"]:
        body_bits.append(ctx["description"])
    if ctx["existing_script"] and ctx["existing_script"] not in body_bits:
        body_bits.append(ctx["existing_script"])
    if not body_bits:
        body_bits.append(
            f"Here is what most people miss about {title.lower()}: the obvious story is not the real one."
        )

    # Build ~8 segments with retention hooks every ~6 seconds.
    timeline = [
        (0, 2, "hook", hook, "curiosity", "punchy and immediate", "pattern interrupt"),
        (2, 8, "context", body_bits[0][:180], "intrigue", "steady and clear", "open loop"),
        (8, 14, "retention_hook", "And the next part is the one people replay.", "tension", "lean in", "direct address"),
        (14, 22, "escalation", body_bits[-1][:220] if body_bits else "The pattern compounds faster than you think.", "surprise", "building pace", "visual switch"),
        (22, 30, "evidence", "The data keeps pointing to the same conclusion — once you see it, you cannot unsee it.", "clarity", "measured authority", "stat reveal"),
        (30, 38, "retention_hook", "But here is the detail almost everyone skips.", "curiosity", "conspiratorial", "open loop"),
        (38, 50, "payoff", f"That is why {title.lower()} changes how you should think about this.", "revelation", "peak energy then pause", "emotional peak"),
        (50, target, "cta", cta, "resolve", "warm and direct", "clear ask"),
    ]

    segments = [
        ScriptSegment(
            segment_number=i + 1,
            start_time=float(start),
            end_time=float(end),
            segment_type=seg_type,
            voiceover=text.strip(),
            emotion=emotion,
            delivery=delivery,
            retention_device=device,
        )
        for i, (start, end, seg_type, text, emotion, delivery, device) in enumerate(timeline)
    ]
    full_voiceover = " ".join(segment.voiceover for segment in segments)
    return VideoScript(
        title=title,
        target_duration_seconds=target,
        tone="cinematic educational",
        primary_emotion="curiosity",
        script_summary=f"A high-retention short on {title.lower()}.",
        segments=segments,
        full_voiceover=full_voiceover,
        call_to_action=cta,
        estimated_word_count=len(full_voiceover.split()),
        generated_at=datetime.now(timezone.utc).isoformat(),
        source="heuristic",
    )


def _parse_response(raw: dict[str, Any] | None) -> tuple[VideoScript | None, list[str]]:
    if raw is None:
        return None, ["Provider returned no data"]
    return validate_script_payload(raw)


def generate_video_script(
    asset: dict[str, Any],
    project: dict[str, Any] | None = None,
    *,
    model: str = "",
    on_progress: ProgressCallback | None = None,
    force_heuristic: bool = False,
) -> ScriptGenerationResult:
    """Generate and validate a video script for one asset."""

    def _status(message: str) -> None:
        if on_progress:
            on_progress(message)

    _status("Preparing asset context")
    project = project or {}
    resolved_model = model or str(project.get("model") or DEFAULT_MODEL)
    system, user = build_generation_prompt(asset, project)

    if force_heuristic or is_demo_mode():
        _status("Structuring retention segments")
        script = _heuristic_script(asset, project)
        _status("Validating script")
        validated, errors = validate_script_payload(script.to_dict())
        if validated is None:
            logger.error("Heuristic script failed validation: %s", errors)
            return ScriptGenerationResult(ok=False, error="; ".join(errors), attempts=1, demo_mode=True)
        _status("Saving project")
        return ScriptGenerationResult(ok=True, script=validated, attempts=1, demo_mode=True)

    provider = get_provider()
    tokens_total = 0

    for attempt in range(1, MAX_ATTEMPTS + 1):
        if attempt == 1:
            _status("Generating the opening hook")
        else:
            _status("Retrying script generation")

        raw, tokens = provider.generate_json(system, user, resolved_model)
        tokens_total += tokens

        _status("Structuring retention segments")
        script, errors = _parse_response(raw)
        if script is not None:
            script.generated_at = datetime.now(timezone.utc).isoformat()
            script.source = "ai"
            _status("Validating script")
            logger.info(
                "asset_script.generated | asset=%s segments=%s words=%s attempt=%s",
                asset.get("asset_id"),
                len(script.segments),
                script.estimated_word_count,
                attempt,
            )
            _status("Saving project")
            return ScriptGenerationResult(
                ok=True,
                script=script,
                tokens_used=tokens_total,
                attempts=attempt,
                demo_mode=False,
            )

        logger.warning(
            "asset_script.invalid_json | asset=%s attempt=%s errors=%s raw=%s",
            asset.get("asset_id"),
            attempt,
            errors,
            json.dumps(raw)[:400] if raw else None,
        )
        if attempt >= MAX_ATTEMPTS:
            break

    # Last resort: heuristic so the user always gets something usable in demo/dev.
    _status("Structuring retention segments")
    fallback = _heuristic_script(asset, project)
    validated, errors = validate_script_payload(fallback.to_dict())
    if validated:
        logger.info("asset_script.heuristic_fallback | asset=%s", asset.get("asset_id"))
        _status("Saving project")
        return ScriptGenerationResult(
            ok=True,
            script=validated,
            tokens_used=tokens_total,
            attempts=MAX_ATTEMPTS,
            demo_mode=True,
            error="AI output was invalid; used structured fallback.",
        )

    return ScriptGenerationResult(
        ok=False,
        error="Script generation failed after retry. " + "; ".join(errors),
        tokens_used=tokens_total,
        attempts=MAX_ATTEMPTS,
        demo_mode=is_demo_mode(),
    )
