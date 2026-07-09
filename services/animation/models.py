"""Data contracts for the Animation & Cinematic Production Engine (Agent 16).

Field tuples are the testable contract (same convention as Creative Studio,
Asset Generation, Render, and Analytics). Everything the engine emits is a
plain JSON-safe dict so the workflow context, ContentPackage slots, and the
UI can carry it without conversion.

Contract rules (DATA_CONTRACTS.md): additive-only from 1.0 on — append
fields freely, never remove, rename, or repurpose existing ones.

The Animation Engine does NOT render final video. It produces a complete
`animation_package` — timeline, camera, character motion, facial, lip sync,
VFX, transitions, audio sync, and provider instructions — that downstream
render / post-production stages execute.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

ANIMATION_ENGINE_VERSION = "1.0.0"
ANIMATION_PACKAGE_VERSION = "1.0"


class ReadinessStatus:
    """Lifecycle of one animation production package."""

    READY = "ready"
    NEEDS_REVIEW = "needs_review"
    INCOMPLETE = "incomplete"

    ALL = (READY, NEEDS_REVIEW, INCOMPLETE)


class CameraShotType:
    """Supported camera framings."""

    WIDE = "wide"
    MEDIUM = "medium"
    CLOSE_UP = "close_up"
    EXTREME_CLOSE_UP = "extreme_close_up"
    DRONE = "drone"
    ORBIT = "orbit"
    TRACKING = "tracking"
    DOLLY = "dolly"
    CRANE = "crane"
    HANDHELD = "handheld"
    FIRST_PERSON = "first_person"
    OVER_THE_SHOULDER = "over_the_shoulder"
    TOP_DOWN = "top_down"
    ESTABLISHING = "establishing"
    CUSTOM = "custom"

    ALL = (
        WIDE, MEDIUM, CLOSE_UP, EXTREME_CLOSE_UP, DRONE, ORBIT, TRACKING,
        DOLLY, CRANE, HANDHELD, FIRST_PERSON, OVER_THE_SHOULDER, TOP_DOWN,
        ESTABLISHING, CUSTOM,
    )


class CameraMovement:
    """Supported camera movements."""

    PAN = "pan"
    TILT = "tilt"
    ZOOM = "zoom"
    PUSH = "push"
    PULL = "pull"
    ORBIT = "orbit"
    TRUCK = "truck"
    PEDESTAL = "pedestal"
    CRANE = "crane"
    DOLLY = "dolly"
    SMOOTH_FOLLOW = "smooth_follow"
    STATIC = "static"
    CUSTOM = "custom"

    ALL = (
        PAN, TILT, ZOOM, PUSH, PULL, ORBIT, TRUCK, PEDESTAL, CRANE, DOLLY,
        SMOOTH_FOLLOW, STATIC, CUSTOM,
    )


class CharacterAction:
    """Supported character body / performance actions."""

    WALKING = "walking"
    RUNNING = "running"
    TALKING = "talking"
    GESTURE = "gesture"
    EYE_MOVEMENT = "eye_movement"
    BLINKING = "blinking"
    BREATHING = "breathing"
    IDLE = "idle"
    HAND_MOVEMENT = "hand_movement"
    OBJECT_INTERACTION = "object_interaction"
    ENTRANCE = "entrance"
    EXIT = "exit"

    ALL = (
        WALKING, RUNNING, TALKING, GESTURE, EYE_MOVEMENT, BLINKING,
        BREATHING, IDLE, HAND_MOVEMENT, OBJECT_INTERACTION, ENTRANCE, EXIT,
    )


class FacialExpression:
    """Supported facial expression targets."""

    NEUTRAL = "neutral"
    SMILE = "smile"
    FEAR = "fear"
    SURPRISE = "surprise"
    ANGER = "anger"
    CONFUSION = "confusion"
    CURIOSITY = "curiosity"
    CUSTOM = "custom"

    ALL = (NEUTRAL, SMILE, FEAR, SURPRISE, ANGER, CONFUSION, CURIOSITY, CUSTOM)


class TransitionType:
    """Supported scene / shot transitions."""

    CUT = "cut"
    FADE = "fade"
    DISSOLVE = "dissolve"
    WHIP = "whip"
    BLUR = "blur"
    MATCH_CUT = "match_cut"
    ZOOM = "zoom_transition"
    OBJECT = "object_transition"
    CUSTOM = "custom"

    ALL = (CUT, FADE, DISSOLVE, WHIP, BLUR, MATCH_CUT, ZOOM, OBJECT, CUSTOM)


class EffectType:
    """Supported visual / particle effect families (plugin-extensible)."""

    SMOKE = "smoke"
    FIRE = "fire"
    RAIN = "rain"
    SNOW = "snow"
    FOG = "fog"
    DUST = "dust"
    MAGIC = "magic"
    ENERGY = "energy"
    EXPLOSION = "explosion"
    WATER = "water"
    LIGHTING = "lighting"
    CUSTOM = "custom"

    ALL = (
        SMOKE, FIRE, RAIN, SNOW, FOG, DUST, MAGIC, ENERGY, EXPLOSION,
        WATER, LIGHTING, CUSTOM,
    )


# ---------------------------------------------------------------------------
# Package field contracts
# ---------------------------------------------------------------------------

ANIMATION_PACKAGE_FIELDS = (
    "animation_package_version",
    "engine_version",
    "project_id",
    "config",                    # resolved AnimationConfig snapshot
    "timeline",                  # master production timeline
    "scene_timing",              # per-scene timing entries
    "camera_plan",               # cinematic camera plan
    "character_motion",          # body / blocking / multi-character
    "facial_animation",          # expressions, eyes, head
    "lip_sync_plan",             # phoneme / word / sentence timing
    "body_animation",            # locomotion + gesture tracks
    "lighting_cues",             # per-shot lighting instructions
    "transitions",               # transition plan between shots/scenes
    "visual_effects",            # VFX cues
    "particle_effects",          # particle system cues
    "motion_graphics",           # overlay / title / lower-third motion
    "audio_synchronization",     # voice / music / SFX sync points
    "subtitle_timing",           # caption / subtitle cues
    "export_metadata",           # fps, aspect, duration, platforms
    "provider_instructions",     # provider-agnostic render briefs
    "quality_report",            # QC findings + readiness
    "choreography",              # scene blocking / placement
    "animation_diagnostics",     # counts and coverage
    "validation",                # structured validation dict
    "production_readiness",      # {score, status, blockers}
    "generated_at",
)

TIMELINE_FIELDS = (
    "timeline_id",
    "fps",
    "total_duration_sec",
    "total_frames",
    "tracks",                    # list of TIMELINE_TRACK_FIELDS
    "markers",                   # named beat markers
    "publishing_metadata",       # platform / series hints
)

TIMELINE_TRACK_FIELDS = (
    "track_id",
    "track_type",                # scene | shot | animation | audio | music | subtitle | effects | transition
    "clips",                     # list of TIMELINE_CLIP_FIELDS
)

TIMELINE_CLIP_FIELDS = (
    "clip_id",
    "ref_id",                    # scene_id / shot_id / effect_id / ...
    "start_sec",
    "end_sec",
    "start_frame",
    "end_frame",
    "label",
)

SCENE_TIMING_FIELDS = (
    "scene_id",
    "start_sec",
    "end_sec",
    "duration_sec",
    "shot_ids",
    "purpose",
)

CAMERA_SHOT_FIELDS = (
    "shot_id",
    "scene_id",
    "shot_type",                 # CameraShotType
    "movement",                  # CameraMovement
    "start_sec",
    "end_sec",
    "duration_sec",
    "keyframes",                 # list of CAMERA_KEYFRAME_FIELDS
    "motion_curve",              # easing / bezier descriptor
    "path",                      # optional custom path points
    "notes",
)

CAMERA_KEYFRAME_FIELDS = (
    "time_sec",
    "position",                  # {x, y, z}
    "rotation",                  # {pitch, yaw, roll}
    "fov",
    "easing",                    # linear | ease_in | ease_out | ease_in_out | bezier
    "bezier",                    # optional [x1, y1, x2, y2]
)

CHARACTER_MOTION_FIELDS = (
    "motion_id",
    "scene_id",
    "character_id",
    "actions",                   # list of action dicts
    "blocking",                  # placement / path
    "coordination_group",        # multi-character sync group id
)

FACIAL_ANIMATION_FIELDS = (
    "facial_id",
    "scene_id",
    "character_id",
    "expression",                # FacialExpression
    "blend",                     # expression → weight
    "eye_direction",
    "head_movement",
    "start_sec",
    "end_sec",
)

LIP_SYNC_FIELDS = (
    "lip_sync_id",
    "scene_id",
    "character_id",
    "audio_ref",
    "phonemes",                  # list of {phoneme, start_sec, end_sec}
    "words",                     # list of {word, start_sec, end_sec}
    "sentences",
    "pauses",
    "breaths",
)

BODY_ANIMATION_FIELDS = (
    "body_id",
    "scene_id",
    "character_id",
    "locomotion",                # idle | walking | running | ...
    "gestures",
    "hand_tracks",
    "interactions",
    "start_sec",
    "end_sec",
)

LIGHTING_CUE_FIELDS = (
    "cue_id",
    "scene_id",
    "shot_id",
    "start_sec",
    "end_sec",
    "mood",
    "key_light",
    "fill_light",
    "rim_light",
    "color_temperature_k",
    "intensity",
)

TRANSITION_FIELDS = (
    "transition_id",
    "from_ref",                  # scene_id or shot_id
    "to_ref",
    "transition_type",           # TransitionType
    "duration_sec",
    "at_sec",
    "params",
)

EFFECT_FIELDS = (
    "effect_id",
    "scene_id",
    "effect_type",               # EffectType
    "start_sec",
    "end_sec",
    "intensity",
    "params",
    "plugin",                    # future effect plugin id
)

MOTION_GRAPHICS_FIELDS = (
    "gfx_id",
    "scene_id",
    "kind",                      # title | lower_third | overlay | end_card | custom
    "start_sec",
    "end_sec",
    "text",
    "motion",
    "style",
)

AUDIO_SYNC_FIELDS = (
    "sync_id",
    "track",                     # voice | music | sfx
    "ref_id",
    "start_sec",
    "end_sec",
    "offset_sec",
    "notes",
)

SUBTITLE_CUE_FIELDS = (
    "cue_id",
    "start_sec",
    "end_sec",
    "text",
    "speaker",
    "scene_id",
)

CHOREOGRAPHY_FIELDS = (
    "scene_id",
    "placements",                # character_id → {x, y, z, facing}
    "paths",                     # movement paths
    "entrances",
    "exits",
    "interactions",
    "composition",
    "crowd_layout",
)

PROVIDER_INSTRUCTION_FIELDS = (
    "provider_id",               # openai | runway | google_veo | kling | ...
    "capability",                # video | animation | lip_sync | motion
    "brief",                     # free-form instruction payload
    "refs",                      # shot / scene / asset refs
    "priority",
)

EXPORT_METADATA_FIELDS = (
    "fps",
    "aspect_ratio",
    "target_duration_sec",
    "target_platforms",
    "resolution",
    "animation_style",
    "camera_style",
    "motion_intensity",
    "motion_smoothing",
    "quality_tier",
    "series_id",
    "episode_index",
)

QUALITY_REPORT_FIELDS = (
    "status",                    # SUCCESS | WARNING | FAILED
    "warnings",
    "blockers",
    "checks",
)

ANIMATION_SUMMARY_FIELDS = (
    "engine_version",
    "status",                    # planned | no_items
    "items",
    "packages",
    "ready",
    "needs_review",
    "incomplete",
    "total_duration_sec",
    "average_readiness",
    "providers_planned",
    "generated_at",
)


@dataclass
class CameraKeyframe:
    """One camera keyframe on a shot path."""

    time_sec: float = 0.0
    position: dict = field(default_factory=lambda: {"x": 0.0, "y": 1.6, "z": 3.0})
    rotation: dict = field(default_factory=lambda: {"pitch": 0.0, "yaw": 0.0, "roll": 0.0})
    fov: float = 35.0
    easing: str = "ease_in_out"
    bezier: list = field(default_factory=lambda: [0.42, 0.0, 0.58, 1.0])

    def to_dict(self) -> dict:
        return asdict(self)


def readiness_status(score: int, blockers: list) -> str:
    """Map a 0-100 readiness score + blockers onto a ReadinessStatus."""
    if blockers:
        return ReadinessStatus.INCOMPLETE
    if score >= 80:
        return ReadinessStatus.READY
    return ReadinessStatus.NEEDS_REVIEW
