"""AI content generation with graceful Demo Mode fallback.

If a valid OpenAI API key is available (env var or session override), real
content is generated via the OpenAI Chat Completions API. If not — or if the
API call fails for any reason — Generational falls back to clean placeholder
data instead of crashing.
"""

from __future__ import annotations

import json

import streamlit as st

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - openai should always be installed
    OpenAI = None

import os


def get_api_key() -> str | None:
    session_key = (st.session_state.get("openai_api_key_override") or "").strip()
    if session_key:
        return session_key
    env_key = os.getenv("OPENAI_API_KEY")
    return env_key.strip() if env_key else None


def is_demo_mode() -> bool:
    return not bool(get_api_key())


def _placeholder_ideas(niche: str, subject: str, count: int) -> list[dict]:
    ideas = []
    niche_tag = niche.replace(" ", "").replace("&", "")
    subject_tag = (subject.split()[0] if subject.split() else niche).title()
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


def _build_prompt(command: str, niche: str, subject: str, count: int) -> tuple[str, str]:
    system_prompt = (
        "You are Generational, an expert short-form (faceless) content strategist. "
        "You always respond with valid, minified JSON only — no prose, no markdown fences."
    )
    user_prompt = (
        f'Original user command: "{command}"\n'
        f'Niche: "{niche}"\n'
        f'Subject: "{subject}"\n\n'
        f"Generate exactly {count} unique, viral-worthy short-form video content ideas. "
        "Respond with JSON matching exactly this shape:\n"
        "{\n"
        '  "ideas": [\n'
        "    {\n"
        '      "title": "catchy video title",\n'
        '      "hook": "first 1-2 sentence viral hook",\n'
        '      "script": "full 15-30 second voiceover script",\n'
        '      "cta": "short call to action",\n'
        '      "hashtags": ["#tag1", "#tag2", "#tag3"],\n'
        '      "thumbnail_concept": "one sentence describing a thumbnail concept"\n'
        "    }\n"
        "  ]\n"
        "}"
    )
    return system_prompt, user_prompt


def generate_content(command: str, niche: str, subject: str, count: int, model: str) -> dict:
    """Returns a dict with keys: ideas, demo_mode, tokens_used, and optionally error."""
    api_key = get_api_key()

    if not api_key or OpenAI is None:
        return {"ideas": _placeholder_ideas(niche, subject, count), "demo_mode": True, "tokens_used": 0}

    try:
        client = OpenAI(api_key=api_key)
        system_prompt, user_prompt = _build_prompt(command, niche, subject, count)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.9,
        )
        raw_content = response.choices[0].message.content
        data = json.loads(raw_content)
        ideas = data.get("ideas") or []
        if not ideas:
            raise ValueError("The model returned no ideas.")

        tokens_used = 0
        if getattr(response, "usage", None):
            tokens_used = getattr(response.usage, "total_tokens", 0) or 0

        return {"ideas": ideas[:count], "demo_mode": False, "tokens_used": tokens_used}
    except Exception as exc:  # noqa: BLE001 - any failure should gracefully fall back
        return {
            "ideas": _placeholder_ideas(niche, subject, count),
            "demo_mode": True,
            "tokens_used": 0,
            "error": str(exc),
        }
