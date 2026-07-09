"""Posting Strategy — ranked publish windows per platform and country.

Scores candidate windows from platform peak-engagement tables, adjusted by
country timezone, audience strength, competition, and trend velocity.
Deterministic today; live audience-analytics providers can replace the
tables later without changing the window contract.
"""

from __future__ import annotations

from engines.heuristics import clamp, stable_jitter, weighted_blend
from services.seo.localization import LOCALIZATION_TARGETS

# Platform → [(day, start_hour_local, end_hour_local, base engagement 0-100)].
_PLATFORM_WINDOWS = {
    "youtube": [
        ("friday", 17, 20, 82), ("saturday", 15, 18, 80),
        ("sunday", 14, 17, 78), ("wednesday", 16, 19, 72),
    ],
    "tiktok": [
        ("tuesday", 18, 21, 80), ("thursday", 19, 22, 82),
        ("saturday", 11, 14, 76), ("sunday", 19, 22, 78),
    ],
    "instagram": [
        ("monday", 11, 13, 74), ("wednesday", 11, 13, 78),
        ("friday", 10, 12, 76), ("sunday", 18, 21, 72),
    ],
    "facebook": [
        ("wednesday", 13, 15, 72), ("thursday", 13, 15, 70), ("sunday", 12, 14, 68),
    ],
    "x": [
        ("monday", 8, 10, 70), ("wednesday", 9, 11, 74), ("friday", 8, 10, 68),
    ],
    "linkedin": [
        ("tuesday", 8, 10, 78), ("wednesday", 9, 11, 76), ("thursday", 8, 10, 74),
    ],
    "pinterest": [
        ("saturday", 20, 23, 74), ("sunday", 20, 23, 72), ("friday", 15, 17, 66),
    ],
}


def recommend_publish_windows(
    platforms: "list | None" = None,
    country: str = "US",
    language: str = "en",
    audience_score: int = 50,
    competition_score: int = 50,
    trend_velocity: float = 0.5,
    limit: int = 8,
) -> "list[dict]":
    """Ranked publish windows (see PUBLISH_WINDOW_FIELDS), best first.

    `competition_score` follows the OS convention: higher = more open field.
    `trend_velocity` is 0.0-1.0 — fast trends favor the earliest windows.
    """
    platforms = [p for p in (platforms or ["youtube"]) if p in _PLATFORM_WINDOWS] or ["youtube"]
    target = next((t for t in LOCALIZATION_TARGETS if t[0] == country), None)
    known_locale = target is not None
    velocity = clamp(int(trend_velocity * 100), low=0, high=100)

    windows = []
    for platform in platforms:
        for slot_index, (day, start, end, base) in enumerate(_PLATFORM_WINDOWS[platform]):
            # Fast-moving trends reward publishing sooner: earlier table
            # slots (the platform's strongest windows) get the velocity boost.
            velocity_boost = velocity if slot_index == 0 else max(0, velocity - slot_index * 15)
            score = weighted_blend(
                {
                    "engagement": base,
                    "audience": audience_score,
                    "competition": competition_score,
                    "velocity": velocity_boost,
                },
                {"engagement": 0.45, "audience": 0.25, "competition": 0.15, "velocity": 0.15},
            )
            score = clamp(score + stable_jitter(f"{platform}:{day}:{start}:{country}", span=5))
            confidence = clamp(
                55 + (15 if known_locale else 0) + (10 if audience_score > 60 else 0), low=30, high=95
            )
            windows.append({
                "platform": platform,
                "country": country,
                "language": language,
                "day": day,
                "start_hour_local": start,
                "end_hour_local": end,
                "audience_score": audience_score,
                "competition_score": competition_score,
                "trend_velocity_score": velocity_boost,
                "score": score,
                "confidence": confidence,
                "rank": 0,
            })

    windows.sort(key=lambda w: (-w["score"], w["platform"], w["day"]))
    windows = windows[:limit]
    for rank, window in enumerate(windows, 1):
        window["rank"] = rank
    return windows
