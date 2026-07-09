"""Data models for the Voice & Audio Engine.

An `AudioSceneCue` is one fully sound-designed beat of a video — the
narration delivery (pace, pauses, emphasis), the sound effects, the music
section and energy, and the audio mood for a single scene. Cues serialize
to plain dicts because the workflow context (and everything Streamlit
touches) speaks JSON-safe dicts — the same convention as `ScenePlan` in
`services/visual/models.py`.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

# The components every scene audio cue must carry (mirrors the Visual
# Engine's REQUIRED_SCENE_COMPONENTS convention — tests assert against this).
REQUIRED_CUE_COMPONENTS = (
    "scene_number",
    "purpose",
    "emotion",
    "start_sec",
    "end_sec",
    "narration",
    "delivery",
    "target_wpm",
    "pace",
    "pauses",
    "emphasis",
    "sfx",
    "music",
    "mood",
    "retention_note",
)


@dataclass
class AudioSceneCue:
    """One sound-designed scene of the audio cue sheet."""

    scene_number: int
    purpose: str
    emotion: str = ""
    start_sec: float = 0.0
    end_sec: float = 0.0
    narration: str = ""
    delivery: str = ""
    target_wpm: int = 0
    pace: str = ""
    pauses: list = field(default_factory=list)  # [{"at", "duration_sec", "reason"}]
    emphasis: list = field(default_factory=list)  # words to stress in the read
    sfx: list = field(default_factory=list)  # [{"effect", "layer", "time_sec", "intensity", "source"}]
    music: dict = field(default_factory=dict)  # {"section", "energy", "ducking"}
    mood: str = ""
    retention_note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "AudioSceneCue":
        known = {key: value for key, value in data.items() if key in cls.__dataclass_fields__}
        return cls(**known)
