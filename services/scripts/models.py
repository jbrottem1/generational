"""Data models for the Script Generation Engine.

A `ScriptVariant` is one complete, platform-aware telling of a content idea —
hook through call-to-action, plus every production cue (B-roll, AI visual
prompts, sound effects, music style, retention checkpoints, estimated
runtime). A `PlatformSpec` is the format contract for one distribution
platform (runtime window, pacing, tone, CTA style).

Both are dataclasses that serialize to plain dicts, because the workflow
context (and everything Streamlit touches) speaks JSON-safe dicts.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

# The thirteen storytelling components every generated script must carry.
REQUIRED_VARIANT_COMPONENTS = (
    "hook",
    "pattern_interrupt",
    "curiosity_loop",
    "core_story",
    "emotional_progression",
    "retention_checkpoints",
    "call_to_action",
    "seo_keywords",
    "broll_suggestions",
    "visual_prompts",
    "sound_effects",
    "music_style",
    "estimated_runtime_sec",
)


@dataclass
class PlatformSpec:
    """Format contract for one distribution platform."""

    key: str
    label: str
    aspect_ratio: str
    min_runtime_sec: int
    max_runtime_sec: int
    words_per_minute: int
    tone: str
    hook_window_sec: int
    cta_style: str

    @property
    def target_runtime_sec(self) -> int:
        """Aim just past the low end of the window — retention beats length."""
        return int(self.min_runtime_sec + 0.35 * (self.max_runtime_sec - self.min_runtime_sec))

    @property
    def target_words(self) -> int:
        return int(self.words_per_minute * self.target_runtime_sec / 60)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["target_runtime_sec"] = self.target_runtime_sec
        return data


@dataclass
class ScriptVariant:
    """One scored, production-ready script telling of a content idea."""

    variant_id: str
    style: str
    style_label: str
    platform: str
    hook: str = ""
    pattern_interrupt: str = ""
    curiosity_loop: str = ""
    core_story: str = ""
    emotional_progression: list = field(default_factory=list)
    retention_checkpoints: list = field(default_factory=list)
    call_to_action: str = ""
    seo_keywords: list = field(default_factory=list)
    broll_suggestions: list = field(default_factory=list)
    visual_prompts: list = field(default_factory=list)
    sound_effects: list = field(default_factory=list)
    music_style: str = ""
    estimated_runtime_sec: int = 0
    full_script: str = ""
    score: int = 0
    score_breakdown: dict = field(default_factory=dict)
    source: str = "heuristic"  # "heuristic" or "ai"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ScriptVariant":
        known = {key: value for key, value in data.items() if key in cls.__dataclass_fields__}
        return cls(**known)
