"""Render & Video Production Engine (Agent 6).

Converts a complete ProductionPackage into a render-ready 9:16 vertical
short-form video package: master timeline, per-scene render plans, caption
render plan, audio mix plan, transition/motion instructions, resolved
(mock) assets, validation with a production readiness score, and a
simulated render result. Real rendering backends swap in behind
`providers/` and `engines.render.assets.register_fulfiller()` — nothing
in the plan format changes when they arrive.
"""

from engines.render.assets import (
    AssetFulfiller,
    AssetResolver,
    ensure_renderable_still,
    fulfiller_keys,
    get_fulfiller,
    register_fulfiller,
)
from engines.render.audio_mix import DUCKING, LOUDNESS_TARGET, TRACK_LEVELS_DB, AudioMixer
from engines.render.captions import (
    CAPTION_MODES,
    CAPTION_STYLE_PRESETS,
    PLATFORM_LAYOUTS,
    SAFE_AREA,
    CaptionRenderer,
)
from engines.render.engine import (
    RenderEngine,
    build_render_output,
    normalize_scenes,
    render_ideas,
    resolve_idea_assets,
    safe_mock_render_package,
)
from engines.render.models import (
    MAX_RUNTIME_SEC,
    MIN_RUNTIME_SEC,
    OUTPUT_FORMAT,
    RENDER_ENGINE_VERSION,
    RENDER_PACKAGE_VERSION,
    SCENE_RENDER_PLAN_FIELDS,
    SUPPORTED_PLATFORMS,
    TIMELINE_SEGMENT_FIELDS,
    RenderJob,
    RenderJobStatus,
    RenderStatus,
    TimelineSegment,
)
from engines.render.motion import MOTION_EFFECTS, MotionPlanner
from engines.render.packaging import OutputPackager
from engines.render.renderer import MockRenderer, estimate_render_duration
from engines.render.scene_plans import SceneRenderer
from engines.render.timeline import TimelineBuilder
from engines.render.transitions import (
    SUPPORTED_TRANSITIONS,
    TRANSITION_DURATIONS,
    TRANSITION_SOUNDS,
    TransitionPlanner,
    normalize_transition,
)
from engines.render.validator import CHECK_WEIGHTS, RenderValidator

__all__ = [
    "AssetFulfiller",
    "AssetResolver",
    "ensure_renderable_still",
    "AudioMixer",
    "CAPTION_MODES",
    "CAPTION_STYLE_PRESETS",
    "CHECK_WEIGHTS",
    "CaptionRenderer",
    "DUCKING",
    "LOUDNESS_TARGET",
    "MAX_RUNTIME_SEC",
    "MIN_RUNTIME_SEC",
    "MOTION_EFFECTS",
    "MockRenderer",
    "MotionPlanner",
    "OUTPUT_FORMAT",
    "OutputPackager",
    "PLATFORM_LAYOUTS",
    "RENDER_ENGINE_VERSION",
    "RENDER_PACKAGE_VERSION",
    "RenderEngine",
    "RenderJob",
    "RenderJobStatus",
    "RenderStatus",
    "RenderValidator",
    "SAFE_AREA",
    "SCENE_RENDER_PLAN_FIELDS",
    "SUPPORTED_PLATFORMS",
    "SUPPORTED_TRANSITIONS",
    "SceneRenderer",
    "TIMELINE_SEGMENT_FIELDS",
    "TRACK_LEVELS_DB",
    "TRANSITION_DURATIONS",
    "TRANSITION_SOUNDS",
    "TimelineBuilder",
    "TimelineSegment",
    "TransitionPlanner",
    "build_render_output",
    "estimate_render_duration",
    "fulfiller_keys",
    "get_fulfiller",
    "normalize_scenes",
    "normalize_transition",
    "register_fulfiller",
    "render_ideas",
    "resolve_idea_assets",
    "safe_mock_render_package",
]
