"""Platform Adaptation — one creative package, per-platform variations.

Each platform profile (PLATFORM_ADAPTATION_FIELDS) adapts aspect ratio,
safe zones, visual pacing, the opening seconds, and CTA placement — the
creative decisions that differ per feed. Registry-based: future platforms
are one `register_platform_profile()` call. Publishing (Agent 7) owns
metadata/scheduling; this module owns only the CREATIVE variation.
"""

from __future__ import annotations

_PROFILES: "dict[str, dict]" = {}


def register_platform_profile(profile: dict) -> dict:
    stored = {
        "platform": profile["platform"],
        "aspect_ratio": profile.get("aspect_ratio", "9:16"),
        "resolution": profile.get("resolution", "1080x1920"),
        "safe_zones": profile.get("safe_zones", {}),
        "visual_pacing": profile.get("visual_pacing", ""),
        "opening_seconds": profile.get("opening_seconds", ""),
        "cta_placement": profile.get("cta_placement", ""),
        "max_duration_sec": float(profile.get("max_duration_sec", 60)),
        "notes": profile.get("notes", ""),
    }
    _PROFILES[stored["platform"]] = stored
    return stored


def get_platform_profile(platform: str) -> "dict | None":
    return _PROFILES.get(platform)


def platform_ids() -> "list[str]":
    return list(_PROFILES.keys())


def build_platform_adaptations(item: dict, storyboard: "list[dict]") -> "list[dict]":
    """Per-platform creative variations for one production.

    Targets the item's platforms (`target_platforms` / `platforms`),
    falling back to every registered profile. Each adaptation carries the
    profile plus production-specific pacing and hook guidance.
    """
    targets = [
        str(platform)
        for platform in (item.get("target_platforms") or item.get("platforms") or [])
        if str(platform) in _PROFILES
    ] or list(_PROFILES.keys())

    total = round(
        sum(float(scene.get("estimated_duration_sec", 0) or 0) for scene in storyboard), 1
    )
    hook_scene = storyboard[0] if storyboard else {}

    adaptations = []
    for platform in targets:
        profile = dict(_PROFILES[platform])
        fits = total <= profile["max_duration_sec"]
        profile["notes"] = " ".join(
            part
            for part in (
                profile["notes"],
                f"cut duration {total}s exceeds the {profile['max_duration_sec']}s ceiling — "
                f"tighten development beats" if not fits else "",
                f"hook scene {hook_scene.get('scene_id', '')} carries the "
                f"opening-seconds treatment" if hook_scene else "",
            )
            if part
        )
        adaptations.append(profile)
    return adaptations


# --------------------------------------------------------------- built-ins

_BUILTINS = (
    {
        "platform": "youtube",
        "aspect_ratio": "9:16",
        "resolution": "1080x1920",
        "safe_zones": {"bottom": "35% — captions + UI", "right": "15% — action rail"},
        "visual_pacing": "dynamic — but hold beats long enough for rewatch value",
        "opening_seconds": "first 2s must state the promise; title overlay by second 1",
        "cta_placement": "endcard subscribe lockup, final 2 seconds",
        "max_duration_sec": 60,
        "notes": "Shorts feed — loops count; land the payoff so the loop re-hooks.",
    },
    {
        "platform": "youtube_shorts",
        "aspect_ratio": "9:16",
        "resolution": "1080x1920",
        "safe_zones": {"bottom": "35% — captions + UI", "right": "15% — action rail"},
        "visual_pacing": "dynamic — but hold beats long enough for rewatch value",
        "opening_seconds": "first 2s must state the promise; title overlay by second 1",
        "cta_placement": "endcard subscribe lockup, final 2 seconds",
        "max_duration_sec": 60,
        "notes": "Shorts feed — loops count; land the payoff so the loop re-hooks.",
    },
    {
        "platform": "tiktok",
        "aspect_ratio": "9:16",
        "resolution": "1080x1920",
        "safe_zones": {"bottom": "30% — captions + sound bar", "right": "20% — engagement rail"},
        "visual_pacing": "rapid — a visible change every 1.5-2s or the swipe wins",
        "opening_seconds": "cold-open mid-action in the first second; no logos, no intros",
        "cta_placement": "spoken CTA over the payoff beat, never a static endcard",
        "max_duration_sec": 60,
        "notes": "Native-feel wins — polish reads as an ad; keep texture and energy.",
    },
    {
        "platform": "instagram",
        "aspect_ratio": "9:16",
        "resolution": "1080x1920",
        "safe_zones": {"bottom": "25% — caption overlay", "top": "10% — username chrome"},
        "visual_pacing": "dynamic with aesthetic holds — beauty frames earn saves",
        "opening_seconds": "strongest visual frame first; aesthetic quality IS the hook",
        "cta_placement": "save/share prompt in the caption zone at the payoff",
        "max_duration_sec": 90,
        "notes": "Reels — design for silent-with-captions viewing first.",
    },
    {
        "platform": "instagram_reels",
        "aspect_ratio": "9:16",
        "resolution": "1080x1920",
        "safe_zones": {"bottom": "25% — caption overlay", "top": "10% — username chrome"},
        "visual_pacing": "dynamic with aesthetic holds — beauty frames earn saves",
        "opening_seconds": "strongest visual frame first; aesthetic quality IS the hook",
        "cta_placement": "save/share prompt in the caption zone at the payoff",
        "max_duration_sec": 90,
        "notes": "Reels — design for silent-with-captions viewing first.",
    },
    {
        "platform": "facebook",
        "aspect_ratio": "9:16",
        "resolution": "1080x1920",
        "safe_zones": {"bottom": "25% — captions + reactions"},
        "visual_pacing": "measured — older median audience, fewer cuts, clearer text",
        "opening_seconds": "context-first hook; assume autoplay muted",
        "cta_placement": "share prompt at the payoff — shares drive Facebook reach",
        "max_duration_sec": 90,
        "notes": "Larger on-screen text than other platforms.",
    },
    {
        "platform": "x",
        "aspect_ratio": "16:9",
        "resolution": "1920x1080",
        "safe_zones": {"bottom": "15% — timeline chrome"},
        "visual_pacing": "rapid — timeline scroll is fastest here",
        "opening_seconds": "the claim on screen as text in the first frame",
        "cta_placement": "reply/repost prompt as closing text card",
        "max_duration_sec": 140,
        "notes": "Feed autoplays muted in-timeline — text carries the story.",
    },
    {
        "platform": "linkedin",
        "aspect_ratio": "1:1",
        "resolution": "1080x1080",
        "safe_zones": {"bottom": "20% — captions + reaction bar"},
        "visual_pacing": "measured and confident — credibility over adrenaline",
        "opening_seconds": "lead with the professional insight, not the drama",
        "cta_placement": "comment-prompt question as the closing card",
        "max_duration_sec": 180,
        "notes": "Square framing; professional tone; data visuals outperform.",
    },
)

for _profile in _BUILTINS:
    register_platform_profile(_profile)
