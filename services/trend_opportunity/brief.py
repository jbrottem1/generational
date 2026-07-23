"""Content strategy cards + automatic production briefs for Research / Ops."""

from __future__ import annotations

from typing import Any


def _title_case_topic(topic: str) -> str:
    t = (topic or "").strip()
    if not t:
        return "Untitled Science Short"
    if t[0].islower() or " " in t:
        # Prefer question / how-why forms
        low = t.lower()
        if low.startswith(("why ", "how ", "what ")):
            return t[0].upper() + t[1:]
        return f"Why {t[0].upper() + t[1:]} Changes Everything" if len(t) < 40 else t[0].upper() + t[1:]
    return t


def build_content_strategy(
    topic: str,
    *,
    category: str = "science",
    scores: dict[str, Any] | None = None,
    audience_intel: dict[str, Any] | None = None,
    platform: str = "youtube_shorts",
) -> dict[str, Any]:
    """Working titles, hooks, audience, world/style/narrator recommendations."""
    scores = scores or {}
    ai = audience_intel or {}
    creative = dict(ai.get("creative") or {})
    profile = dict(ai.get("audience_profile") or {})
    analysis = dict(scores.get("analysis") or scores)

    working = _title_case_topic(topic)
    alts = [
        f"The Truth About {topic}",
        f"Nobody Explains {topic} Like This",
        f"{topic} — In 45 Seconds",
        f"Stop Scrolling: {topic}",
        f"Scientists Know This About {topic}",
    ]

    primary_hook = creative.get("suggested_opening_hook") or ""
    if not primary_hook:
        core = topic.strip()
        low = core.lower()
        if low.startswith(("why ", "how ", "what ")):
            primary_hook = f"Stop — {core[0].lower() + core[1:] if core else 'this'}? The answer is stranger than it sounds."
        else:
            subject = topic.split()[0] if topic else "this"
            primary_hook = f"Stop — most people misunderstand {subject}. Here's what actually happens."
    backups = [
        f"What if everything you know about {topic} is slightly wrong?",
        f"In the next 10 seconds you'll see why {topic} matters.",
        f"This is the part about {topic} that never makes the textbook.",
    ]

    # World / style via existing systems when available
    world = "auto"
    world_type = ""
    try:
        from services.world_builder import select_world_type

        world_type = select_world_type(topic=topic, niche=category) or ""
        world = world_type or "auto"
    except Exception:  # noqa: BLE001
        if any(w in topic.lower() for w in ("ocean", "octopus", "marine", "fish")):
            world = "ocean_research_observatory"
        elif any(w in topic.lower() for w in ("space", "planet", "star")):
            world = "space_observatory"
        else:
            world = "ai_laboratory"

    style_key = "documentary"
    try:
        from services.visual_asset_director import resolve_style_profile

        style_key = resolve_style_profile(None, niche=category, topic=topic, world_type=str(world)).get("style_key") or "documentary"
    except Exception:  # noqa: BLE001
        style_key = "documentary"

    length = 45
    if float(analysis.get("evergreen_potential") or 0) > 80 and float(scores.get("educational_score") or 0) > 80:
        length = 50
    difficulty = "medium"
    diff_n = float(analysis.get("production_difficulty") or 50)
    if diff_n >= 70:
        difficulty = "hard"
    elif diff_n <= 40:
        difficulty = "easy"

    prod_minutes = {"easy": 25, "medium": 45, "hard": 75}.get(difficulty, 45)

    thumb = creative.get("best_thumbnail_style") or (
        f"Bold subject + short claim about {topic.split()[0] if topic else 'science'}"
    )

    return {
        "working_title": working,
        "alternative_titles": alts[:5],
        "primary_hook": primary_hook,
        "backup_hooks": backups[:3],
        "viewer_psychology_summary": profile.get("persona_summary")
        or "Curious general public seeking surprising, teachable science in under a minute.",
        "target_audience": profile.get("age_demographics") or "ages 16–44 · lifelong learners · Shorts scrollers",
        "recommended_platform": platform,
        "recommended_video_length_sec": length,
        "recommended_narrator": "professor",
        "recommended_world": world,
        "recommended_style_profile": style_key,
        "recommended_thumbnail_concept": thumb,
        "recommended_upload_time": "Tue–Thu 11:00–14:00 local peak for education Shorts",
        "estimated_difficulty": difficulty,
        "estimated_production_time_min": prod_minutes,
        "category": category,
        "topic": topic,
    }


def build_production_brief(
    topic: str,
    *,
    strategy: dict[str, Any] | None = None,
    scores: dict[str, Any] | None = None,
    category: str = "science",
    objective: str = "",
) -> dict[str, Any]:
    """Complete brief that feeds Research Engine + Studio Ops with zero manual editing."""
    strategy = strategy or build_content_strategy(topic, category=category, scores=scores)
    scores = scores or {}
    overall = float(scores.get("overall_opportunity_score") or 0)

    objective = objective or (
        f"Produce a high-retention educational {strategy.get('recommended_platform')} video that teaches "
        f"{topic} with a curiosity-first open and clear scientific payoff."
    )

    length = int(strategy.get("recommended_video_length_sec") or 45)
    platform = str(strategy.get("recommended_platform") or "youtube_shorts")
    narrator = str(strategy.get("recommended_narrator") or "professor")
    style = str(strategy.get("recommended_style_profile") or "documentary")
    hook = str(strategy.get("primary_hook") or "")

    # Natural-language command Research / Ops already understand
    command = (
        f"Create a {length} second {platform.replace('_', ' ')} video about {topic} "
        f"in a {style} educational style, narrator {narrator}. "
        f"Open with this hook: {hook}"
    )

    brief = {
        "package_type": "trend_opportunity_production_brief",
        "version": "1.0.0",
        "topic": topic,
        "objective": objective,
        "target_audience": strategy.get("target_audience"),
        "hook": hook,
        "research_goals": [
            f"Verify core scientific facts for: {topic}",
            "Collect 3 teachable mechanisms or misconceptions",
            "Find 2 high-authority sources (peer-reviewed or museum/edu)",
            "Identify one vivid concrete example for visual storytelling",
        ],
        "world_selection": strategy.get("recommended_world"),
        "narrator": narrator,
        "style": style,
        "visual_direction": (
            f"Style profile `{style}`; maintain world `{strategy.get('recommended_world')}`; "
            "high educational clarity; cinematic-ready stills via Visual Asset Director."
        ),
        "thumbnail_direction": strategy.get("recommended_thumbnail_concept"),
        "platform": platform,
        "duration": length,
        "duration_sec": length,
        "working_title": strategy.get("working_title"),
        "alternative_titles": strategy.get("alternative_titles"),
        "backup_hooks": strategy.get("backup_hooks"),
        "overall_opportunity_score": overall,
        "scores": scores.get("scores") or scores,
        "analysis": scores.get("analysis"),
        "command": command,
        "studio_ops_fields": {
            "topic": topic,
            "platform": platform,
            "length_sec": length,
            "style": style if style != "documentary" else "educational",
            "narrator": narrator,
            "command": command,
            "constraints": {
                "world": strategy.get("recommended_world"),
                "style_profile": style,
                "from_trend_opportunity": True,
                "opportunity_score": overall,
            },
        },
        "feeds": ["research_engine", "psychology_engine", "production_operations"],
        "manual_editing_required": False,
        "note": "Auto-generated — ready for Research Engine and run_studio_ops without manual edits",
    }
    return brief


def to_studio_brief_kwargs(production_brief: dict[str, Any]) -> dict[str, Any]:
    fields = dict(production_brief.get("studio_ops_fields") or {})
    return {
        "topic": fields.get("topic") or production_brief.get("topic"),
        "platform": fields.get("platform") or production_brief.get("platform") or "youtube_shorts",
        "length_sec": int(fields.get("length_sec") or production_brief.get("duration_sec") or 45),
        "style": fields.get("style") or "educational",
        "narrator": fields.get("narrator") or production_brief.get("narrator") or "professor",
        "command": fields.get("command") or production_brief.get("command") or "",
        "constraints": dict(fields.get("constraints") or {}),
    }
