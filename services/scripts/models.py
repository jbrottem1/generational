"""Data models for the Script Generation Engine.

A `ScriptVariant` is one complete, platform-aware telling of a content idea —
a list of structured narrative sections (primary hook through call-to-action)
plus every production cue (B-roll, AI visual prompts, sound effects, music
style, retention checkpoints, estimated runtime, retention model). A
`PlatformSpec` is the format contract for one distribution platform (runtime
window, pacing, tone, CTA style). A `Locale` carries language / region /
dialect so translation can plug in later without touching the engine.

All are dataclasses that serialize to plain dicts, because the workflow
context (and everything Streamlit touches) speaks JSON-safe dicts.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

# The thirteen storytelling components every generated script must carry.
# These are flat legacy views derived from `sections` — downstream engines
# (Visual Intelligence, Voice & Audio, Threat Detection) read them directly.
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

# The structured narrative sections every script is broken into, in order.
# `pattern_interrupt` is an internal micro-beat between the two hooks; the
# other eight are the canonical cinematic storytelling sections.
SCRIPT_SECTION_KEYS = (
    "primary_hook",
    "pattern_interrupt",
    "curiosity_hook",
    "context",
    "escalation",
    "evidence",
    "emotional_peak",
    "resolution",
    "call_to_action",
)

# The eight sections that must always be present and non-empty.
REQUIRED_SCRIPT_SECTIONS = tuple(k for k in SCRIPT_SECTION_KEYS if k != "pattern_interrupt")

# Every section dict carries these annotations.
REQUIRED_SECTION_FIELDS = (
    "key",
    "label",
    "narration",
    "estimated_duration_sec",
    "emotional_intensity",
    "attention_score",
    "visual_intent",
    "broll_type",
    "caption_emphasis",
)


@dataclass
class Locale:
    """Language / region / dialect target for a script.

    Generation is English-only today, but every variant and structured
    script carries its locale so a future Translation Engine can rewrite
    narration per market without changing any engine contracts.
    """

    language: str = "en"
    region: str = "US"
    dialect: str = "general"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_value(cls, value) -> "Locale":
        """Accept a Locale, a dict, or None (falls back to the default)."""
        if isinstance(value, Locale):
            return value
        if isinstance(value, dict):
            known = {k: v for k, v in value.items() if k in cls.__dataclass_fields__ and v}
            return cls(**known)
        return cls()


DEFAULT_LOCALE = Locale()


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
    """One scored, production-ready script telling of a content idea.

    `sections` is the canonical structure: an ordered list of section dicts
    (see `REQUIRED_SECTION_FIELDS`), each with narration, timing, emotional
    intensity, attention score, and visual/caption direction. The flat
    fields (hook, curiosity_loop, core_story, ...) are derived views kept
    for every downstream consumer that predates the section architecture.
    """

    variant_id: str
    style: str
    style_label: str
    platform: str
    hook: str = ""
    hook_style: str = ""
    alternate_hooks: list = field(default_factory=list)
    sections: list = field(default_factory=list)
    pattern_interrupt: str = ""
    curiosity_loop: str = ""
    core_story: str = ""
    emotional_progression: list = field(default_factory=list)
    retention_checkpoints: list = field(default_factory=list)
    retention_model: dict = field(default_factory=dict)
    call_to_action: str = ""
    seo_keywords: list = field(default_factory=list)
    broll_suggestions: list = field(default_factory=list)
    visual_prompts: list = field(default_factory=list)
    sound_effects: list = field(default_factory=list)
    music_style: str = ""
    estimated_runtime_sec: int = 0
    full_script: str = ""
    locale: dict = field(default_factory=lambda: DEFAULT_LOCALE.to_dict())
    score: int = 0
    score_breakdown: dict = field(default_factory=dict)
    source: str = "heuristic"  # "heuristic" or "ai"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ScriptVariant":
        known = {key: value for key, value in data.items() if key in cls.__dataclass_fields__}
        return cls(**known)

    def get_section(self, key: str) -> dict:
        """Return the named section dict, or an empty dict if absent."""
        for section in self.sections:
            if section.get("key") == key:
                return section
        return {}
