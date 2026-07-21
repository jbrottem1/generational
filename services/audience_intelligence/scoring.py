"""Deterministic Audience Intelligence scoring from text + provider signals."""

from __future__ import annotations

import re
from typing import Any

from services.audience_intelligence.models import (
    FORMATS,
    AudienceProfile,
    CreativeDirectives,
    EngagementEstimates,
    PsychologicalDrivers,
    _clamp,
)

_CUE_BANKS: dict[str, tuple[re.Pattern[str], int, int]] = {
    # pattern, hit_boost, base_when_hit_floor
    "curiosity_potential": (re.compile(r"\b(why|how|what if|secret|hidden|mystery|never knew|explain\w*)\b", re.I), 22, 62),
    "surprise_level": (re.compile(r"\b(actually|wrong|myth|shocking|unexpected|twist|believe)\b", re.I), 20, 60),
    "emotional_intensity": (re.compile(r"\b(love|hate|tragic|amazing|devastat\w*|heartbreak|awe|outrage)\b", re.I), 18, 58),
    "controversy_level": (re.compile(r"\b(debate|controversial|vs|versus|scandal|ban|protest|divided)\b", re.I), 25, 55),
    "educational_value": (re.compile(r"\b(science\w*|learn|explain\w*|guide|research|study|history|facts|how)\b", re.I), 20, 68),
    "humor_potential": (re.compile(r"\b(funny|hilarious|joke|meme|absurd|ridiculous|comedy)\b", re.I), 22, 55),
    "fear_potential": (re.compile(r"\b(danger|deadly|fear|risk|threat|disaster|crash|attack|virus)\b", re.I), 24, 58),
    "inspiration_potential": (re.compile(r"\b(inspire\w*|hope|overcome|triumph|dream|achieve|hero)\b", re.I), 18, 55),
    "nostalgia": (re.compile(r"\b(retro|vintage|90s|80s|classic|childhood|remember when|old school)\b", re.I), 25, 58),
    "authority": (re.compile(r"\b(expert|scientist\w*|doctor|nasa|study|research|official|professor)\b", re.I), 18, 60),
    "novelty": (re.compile(r"\b(new|first|discover\w*|breakthrough|just|latest|never before|emerging)\b", re.I), 18, 58),
    "practical_usefulness": (re.compile(r"\b(how to|tips|hack|guide|use|save|fix|improve|beginner)\b", re.I), 20, 62),
    "visual_appeal": (re.compile(r"\b(see|look|visual|color|space|underwater|macro|cinematic|animation)\b", re.I), 15, 55),
    "discussion_potential": (re.compile(r"\b(debate|opinion|should|why do|comment|discuss|poll|unpopular)\b", re.I), 18, 55),
}

ATTENTION_WEIGHTS = {
    "curiosity_potential": 0.12,
    "surprise_level": 0.08,
    "emotional_intensity": 0.09,
    "educational_value": 0.10,
    "novelty": 0.07,
    "visual_appeal": 0.08,
    "discussion_potential": 0.06,
    "practical_usefulness": 0.06,
    "authority": 0.05,
    "inspiration_potential": 0.05,
    "humor_potential": 0.04,
    "fear_potential": 0.04,
    "controversy_level": 0.03,
    "nostalgia": 0.03,
    # engagement proxies folded in separately
}


def _blob(*parts: Any) -> str:
    return " ".join(str(p or "") for p in parts)


def score_psychological_drivers(text: str, *, signals: dict[str, Any] | None = None) -> PsychologicalDrivers:
    signals = signals or {}
    drivers = PsychologicalDrivers()
    for field, (pattern, boost, floor) in _CUE_BANKS.items():
        hits = len(pattern.findall(text))
        base = 38
        score = base + min(boost * hits, 45)
        if hits:
            score = max(score, floor)
        setattr(drivers, field, _clamp(score))

    # Provider signal overlays (structured only — never raw API)
    yt = signals.get("youtube") or {}
    news = signals.get("google_news") or {}
    if yt.get("educational") or yt.get("clickability"):
        drivers.educational_value = _clamp(0.6 * drivers.educational_value + 0.4 * int(yt.get("educational") or drivers.educational_value))
        drivers.curiosity_potential = _clamp(
            0.55 * drivers.curiosity_potential + 0.45 * int(yt.get("clickability") or drivers.curiosity_potential)
        )
        drivers.visual_appeal = _clamp(
            0.5 * drivers.visual_appeal + 0.5 * int(yt.get("thumbnail_quality") or drivers.visual_appeal)
        )
        drivers.novelty = _clamp(0.6 * drivers.novelty + 0.4 * int(yt.get("trend_momentum") or drivers.novelty))
    if news.get("psychology") or news.get("breaking_news"):
        drivers.emotional_intensity = _clamp(
            0.55 * drivers.emotional_intensity + 0.45 * int(news.get("psychology") or 50)
        )
        if int(news.get("breaking_news") or 0) >= 60:
            drivers.novelty = max(drivers.novelty, 65)
            drivers.discussion_potential = max(drivers.discussion_potential, 60)

    reddit = signals.get("reddit") or {}
    if reddit.get("discussion"):
        drivers.discussion_potential = _clamp(
            0.5 * drivers.discussion_potential + 0.5 * int(reddit["discussion"])
        )

    wiki = signals.get("wikipedia") or {}
    if wiki.get("authority"):
        drivers.authority = _clamp(0.5 * drivers.authority + 0.5 * int(wiki["authority"]))
        drivers.educational_value = max(drivers.educational_value, 60)

    return drivers


def estimate_engagement(
    drivers: PsychologicalDrivers,
    *,
    signals: dict[str, Any] | None = None,
    recommended_type: str = "short",
) -> EngagementEstimates:
    signals = signals or {}
    yt = signals.get("youtube") or {}
    news = signals.get("google_news") or {}

    ctr = _clamp(
        0.35 * drivers.curiosity_potential
        + 0.25 * drivers.surprise_level
        + 0.20 * drivers.visual_appeal
        + 0.20 * int(yt.get("clickability") or 50)
    )
    retention = _clamp(
        0.35 * drivers.educational_value
        + 0.25 * drivers.curiosity_potential
        + 0.20 * drivers.authority
        + 0.20 * int(yt.get("educational") or 50)
    )
    share = _clamp(
        0.30 * drivers.emotional_intensity
        + 0.25 * drivers.surprise_level
        + 0.20 * drivers.humor_potential
        + 0.15 * drivers.inspiration_potential
        + 0.10 * drivers.discussion_potential
    )
    comment = _clamp(0.45 * drivers.discussion_potential + 0.30 * drivers.controversy_level + 0.25 * drivers.curiosity_potential)
    rewatch = _clamp(0.40 * drivers.educational_value + 0.30 * drivers.practical_usefulness + 0.30 * drivers.novelty)
    subs = _clamp(0.35 * drivers.authority + 0.35 * drivers.educational_value + 0.30 * retention)
    series = _clamp(0.40 * drivers.educational_value + 0.30 * drivers.curiosity_potential + 0.30 * rewatch)
    evergreen = _clamp(
        0.40 * drivers.educational_value
        + 0.30 * drivers.practical_usefulness
        + 0.30 * int(yt.get("evergreen") or news.get("evergreen") or 45)
    )
    decay = _clamp(int(news.get("breaking_news") or 30) * 0.7 + (100 - evergreen) * 0.3)
    intl = _clamp(0.40 * drivers.visual_appeal + 0.30 * drivers.novelty + 0.30 * (70 if drivers.educational_value >= 60 else 45))

    length_map = {
        "short": 40,
        "breaking_news": 50,
        "animation": 55,
        "series": 280,
        "long_form": 480,
        "documentary": 600,
    }
    watch = int(yt.get("expected_watch_time_sec") or length_map.get(recommended_type, 45))
    # Scale watch by retention
    watch = int(max(20, watch * (0.7 + retention / 300)))

    return EngagementEstimates(
        ctr_potential=ctr,
        average_watch_time_sec=watch,
        retention_probability=retention,
        shareability=share,
        comment_probability=comment,
        rewatch_probability=rewatch,
        subscriber_conversion=subs,
        series_potential=series,
        evergreen_potential=evergreen,
        breaking_news_decay=decay,
        international_appeal=intl,
    )


def human_attention_score(drivers: PsychologicalDrivers, engagement: EngagementEstimates) -> int:
    psych = sum(getattr(drivers, k) * w for k, w in ATTENTION_WEIGHTS.items())
    eng = (
        0.25 * engagement.ctr_potential
        + 0.25 * engagement.retention_probability
        + 0.20 * engagement.shareability
        + 0.15 * engagement.comment_probability
        + 0.15 * engagement.rewatch_probability
    )
    return _clamp(0.55 * psych + 0.45 * eng)


def build_audience_profile(drivers: PsychologicalDrivers, *, category: str = "general") -> AudienceProfile:
    if drivers.educational_value >= 70 and drivers.authority >= 60:
        sophistication = "curious"
        difficulty = "intermediate"
        age = "25-44 primary"
        motivation = "mastery"
    elif drivers.humor_potential >= 60 or drivers.novelty >= 65:
        sophistication = "general"
        difficulty = "beginner"
        age = "16-29 primary"
        motivation = "entertainment"
    elif drivers.fear_potential >= 60 or drivers.controversy_level >= 55:
        sophistication = "general"
        difficulty = "beginner"
        age = "18-40 primary"
        motivation = "vigilance"
    else:
        sophistication = "general"
        difficulty = "intermediate" if "science" in category.lower() or "edu" in category.lower() else "beginner"
        age = "18-34 primary"
        motivation = "learn"

    secondary = []
    if drivers.curiosity_potential >= 60:
        secondary.append("curiosity")
    if drivers.practical_usefulness >= 60:
        secondary.append("utility")
    if drivers.inspiration_potential >= 55:
        secondary.append("inspiration")
    if drivers.discussion_potential >= 60:
        secondary.append("debate")

    persona = (
        f"{age.split()[0]} viewers seeking {motivation}; "
        f"{sophistication} sophistication; {difficulty} difficulty."
    )
    return AudienceProfile(
        age_demographics=age,
        audience_sophistication=sophistication,
        difficulty_level=difficulty,
        primary_motivation=motivation,
        secondary_motivations=secondary[:4],
        persona_summary=persona,
    )


def build_creative_directives(
    topic: str,
    drivers: PsychologicalDrivers,
    engagement: EngagementEstimates,
    *,
    discovery_type: str | None = None,
) -> CreativeDirectives:
    hooks: list[str] = []
    if drivers.curiosity_potential >= 55:
        hooks.append("curiosity_gap")
    if drivers.surprise_level >= 55:
        hooks.append("expectation_violation")
    if drivers.fear_potential >= 55:
        hooks.append("threat_salience")
    if drivers.inspiration_potential >= 55:
        hooks.append("aspirational_identity")
    if drivers.educational_value >= 60:
        hooks.append("clear_payoff_promise")
    if drivers.humor_potential >= 55:
        hooks.append("pattern_interrupt_humor")
    if drivers.authority >= 60:
        hooks.append("expert_validation")
    if not hooks:
        hooks = ["curiosity_gap", "clear_payoff_promise"]

    opening = _opening_hook(topic, drivers, hooks)

    # Thumbnail style
    if drivers.fear_potential >= 60:
        thumb = "high_contrast_warning_visual"
    elif drivers.educational_value >= 65 and drivers.authority >= 55:
        thumb = "clean_diagram_with_bold_question"
    elif drivers.surprise_level >= 60:
        thumb = "before_after_split_reveal"
    elif drivers.humor_potential >= 60:
        thumb = "expressive_face_plus_overlay_text"
    else:
        thumb = "bold_text_over_visual"

    fmt = _recommend_format(drivers, engagement, discovery_type)
    lengths = {
        "short": {"min": 30, "max": 55},
        "breaking_news": {"min": 30, "max": 90},
        "animation": {"min": 45, "max": 120},
        "series": {"min": 240, "max": 480},
        "long_form": {"min": 480, "max": 720},
        "documentary": {"min": 600, "max": 1200},
    }
    return CreativeDirectives(
        psychological_hooks=hooks[:6],
        suggested_opening_hook=opening,
        best_thumbnail_style=thumb,
        recommended_video_length_sec=dict(lengths.get(fmt, lengths["short"])),
        recommended_video_format=fmt,
    )


def _recommend_format(
    drivers: PsychologicalDrivers,
    engagement: EngagementEstimates,
    discovery_type: str | None,
) -> str:
    if discovery_type in FORMATS:
        # Map discovery live_update → breaking_news
        if discovery_type == "live_update":
            return "breaking_news"
        if discovery_type == "long_form":
            return "long_form" if engagement.evergreen_potential < 70 else "documentary"
        return discovery_type
    if engagement.breaking_news_decay >= 65 and drivers.novelty >= 60:
        return "breaking_news"
    if engagement.series_potential >= 70 and drivers.educational_value >= 65:
        return "series"
    if drivers.educational_value >= 75 and engagement.evergreen_potential >= 70 and drivers.visual_appeal >= 55:
        return "documentary"
    if drivers.visual_appeal >= 70 and drivers.educational_value >= 55 and engagement.average_watch_time_sec <= 120:
        return "animation"
    if engagement.average_watch_time_sec >= 240 or drivers.educational_value >= 70:
        return "long_form"
    return "short"


def _opening_hook(topic: str, drivers: PsychologicalDrivers, hooks: list[str]) -> str:
    t = topic.strip() or "this"
    if "curiosity_gap" in hooks and "expectation_violation" in hooks:
        return f"Everything you think you know about {t} is incomplete — here's the missing piece."
    if "threat_salience" in hooks:
        return f"Most people ignore this about {t} until it's too late."
    if "expert_validation" in hooks:
        return f"Scientists keep repeating one fact about {t} — and almost nobody listens."
    if "aspirational_identity" in hooks:
        return f"Once you understand {t}, you can't unsee how the world works."
    if "pattern_interrupt_humor" in hooks:
        return f"The weirdest true thing about {t} sounds like a joke — until it isn't."
    if drivers.practical_usefulness >= 60:
        return f"In the next minute, you'll know how to actually use {t}."
    return f"Stop scrolling — the clearest explanation of {t} starts now."
