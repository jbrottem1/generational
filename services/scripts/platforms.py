"""Platform format specs for the Script Generation Engine.

Every supported distribution platform is one `PlatformSpec` entry — runtime
window, narration pacing, tone, hook window, and CTA style. Specs are data,
not code: adding a platform (or tuning one from real analytics via the
future Learning Engine) never touches generation or scoring logic.
"""

from __future__ import annotations

from services.scripts.models import PlatformSpec

DEFAULT_PLATFORM = "youtube_shorts"

PLATFORM_SPECS = {
    "youtube_shorts": PlatformSpec(
        key="youtube_shorts",
        label="YouTube Shorts",
        aspect_ratio="9:16",
        min_runtime_sec=20,
        max_runtime_sec=58,
        words_per_minute=160,
        tone=(
            "calm, intelligent motivational storytelling — struggle to action, "
            "no empty hype, every line earns the next"
        ),
        hook_window_sec=3,
        cta_style="invite one concrete action today + subscribe for the next lesson",
    ),
    "tiktok": PlatformSpec(
        key="tiktok",
        label="TikTok",
        aspect_ratio="9:16",
        min_runtime_sec=15,
        max_runtime_sec=45,
        words_per_minute=170,
        tone="conversational and raw — talk like a friend spilling a secret",
        hook_window_sec=2,
        cta_style="comment bait + follow for part two",
    ),
    "instagram_reels": PlatformSpec(
        key="instagram_reels",
        label="Instagram Reels",
        aspect_ratio="9:16",
        min_runtime_sec=15,
        max_runtime_sec=60,
        words_per_minute=155,
        tone="polished and aspirational — aesthetic visuals, save-worthy value",
        hook_window_sec=3,
        cta_style="save this + share with someone who needs it",
    ),
    "facebook_reels": PlatformSpec(
        key="facebook_reels",
        label="Facebook Reels",
        aspect_ratio="9:16",
        min_runtime_sec=20,
        max_runtime_sec=60,
        words_per_minute=145,
        tone="warm and story-led — broad-audience clarity, no jargon",
        hook_window_sec=3,
        cta_style="share + tag a friend",
    ),
    "x_video": PlatformSpec(
        key="x_video",
        label="X (Twitter) Video",
        aspect_ratio="16:9",
        min_runtime_sec=15,
        max_runtime_sec=140,
        words_per_minute=165,
        tone="sharp and contrarian — thesis-first, debate-ready",
        hook_window_sec=2,
        cta_style="repost + reply with your take",
    ),
    "youtube_long": PlatformSpec(
        key="youtube_long",
        label="YouTube Long-form",
        aspect_ratio="16:9",
        min_runtime_sec=300,
        max_runtime_sec=720,
        words_per_minute=150,
        tone=(
            "documentary-depth motivational essay — verified examples, "
            "psychology, and a practical application the viewer can start today"
        ),
        hook_window_sec=15,
        cta_style="subscribe + comment one action you'll take + end-screen next lesson",
    ),
}

SCRIPT_PLATFORMS = list(PLATFORM_SPECS)


def get_platform_spec(platform: str) -> PlatformSpec:
    """Resolve a platform key to its spec, falling back to the default."""
    return PLATFORM_SPECS.get(platform, PLATFORM_SPECS[DEFAULT_PLATFORM])
