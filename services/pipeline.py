"""Pipeline stage views derived from the engine registry.

The UI's "next steps" flow reads live engine metadata (icon, label,
readiness) from the registry, so it stays accurate as engines are
implemented — no hardcoded stage lists.
"""

from __future__ import annotations

from engines import registry

# The stages shown after ideation, in production order. Analytics and
# learning run continuously rather than per-video, so they're not shown
# as "next steps".
NEXT_STEP_KEYS = ["research", "seo", "script", "voice", "image", "video", "publishing"]


def next_stages() -> list:
    """Engine objects (with .icon/.label) for the post-ideation flow."""
    return [engine for engine in (registry.get_engine(key) for key in NEXT_STEP_KEYS) if engine]
