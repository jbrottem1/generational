"""Visual Intelligence service — the Cinematic AI Director of the pipeline.

Public API for turning any scripted idea into a complete Visual Production
Package: directed storyboard, professional shot list, style-preset art
direction, per-model AI image/video prompts, provider-agnostic asset
requests, scored thumbnail concepts, hook sequence, caption plan, pacing /
camera / motion reports, a predicted retention curve, and a machine-ready
Render Package. The `visual_intelligence` pipeline engine is a thin wrapper
around this module; it is equally usable standalone (e.g. re-directing an
approved idea for a different platform or style):

    from services.visual import build_visual_package

    package = build_visual_package(idea, niche="Science", style_key="cyberpunk",
                                   subject="black holes", aspect_ratio="9:16")
    best_thumbnail = package["thumbnails"][0]
    render_plan = package["render_package"]

Extension points that never require touching the engine:

- `register_style()` — new visual style presets
- `register_source()` — new asset source adapters (providers)
- one formatter in `prompts.py` — new AI image/video models
"""

from __future__ import annotations

from services.visual.hooks import HOOK_FRAME_COUNT, HOOK_WINDOW_SEC, build_hook_sequence
from services.visual.models import (
    REQUIRED_SCENE_COMPONENTS,
    THUMBNAIL_SCORE_KEYS,
    ScenePlan,
    ThumbnailConcept,
)
from services.visual.package import (
    PACKAGE_SCORE_WEIGHTS,
    build_camera_plan,
    build_caption_plan,
    build_motion_report,
    build_pacing_report,
    build_retention_curve,
    build_storyboard,
    build_transitions,
    build_visual_package,
    overall_visual_score,
)
from services.visual.prompts import (
    IMAGE_MODELS,
    VIDEO_MODELS,
    build_image_prompts,
    build_video_prompts,
)
from services.visual.psychology import (
    VISUAL_DIMENSION_KEYS,
    VISUAL_DIMENSION_LABELS,
    VISUAL_SCORE_WEIGHTS,
    attention_level_for,
    predict_scene_retention,
    scene_visual_score,
    score_scene_visuals,
)
from services.visual.render_prep import RENDER_PACKAGE_VERSION, build_render_package
from services.visual.scenes import NICHE_VISUAL_PALETTES, palette_for, plan_scenes
from services.visual.shots import SHOT_TYPES, build_shot_list, shot_for
from services.visual.sources import (
    AssetSourceAdapter,
    build_asset_requests,
    get_source,
    register_source,
    source_keys,
)
from services.visual.styles import (
    DEFAULT_STYLE,
    get_style,
    register_style,
    resolve_style,
    style_keys,
)
from services.visual.thumbnails import (
    THUMBNAIL_ARCHETYPES,
    THUMBNAIL_SCORE_WEIGHTS,
    build_thumbnail_concepts,
    click_probability_pct,
    expected_ctr_pct,
)

__all__ = [
    "AssetSourceAdapter",
    "DEFAULT_STYLE",
    "HOOK_FRAME_COUNT",
    "HOOK_WINDOW_SEC",
    "IMAGE_MODELS",
    "NICHE_VISUAL_PALETTES",
    "PACKAGE_SCORE_WEIGHTS",
    "RENDER_PACKAGE_VERSION",
    "REQUIRED_SCENE_COMPONENTS",
    "SHOT_TYPES",
    "ScenePlan",
    "THUMBNAIL_ARCHETYPES",
    "THUMBNAIL_SCORE_KEYS",
    "THUMBNAIL_SCORE_WEIGHTS",
    "ThumbnailConcept",
    "VIDEO_MODELS",
    "VISUAL_DIMENSION_KEYS",
    "VISUAL_DIMENSION_LABELS",
    "VISUAL_SCORE_WEIGHTS",
    "attention_level_for",
    "build_asset_requests",
    "build_camera_plan",
    "build_caption_plan",
    "build_hook_sequence",
    "build_image_prompts",
    "build_motion_report",
    "build_pacing_report",
    "build_render_package",
    "build_retention_curve",
    "build_shot_list",
    "build_storyboard",
    "build_thumbnail_concepts",
    "build_transitions",
    "build_video_prompts",
    "build_visual_package",
    "click_probability_pct",
    "expected_ctr_pct",
    "get_source",
    "get_style",
    "overall_visual_score",
    "palette_for",
    "plan_scenes",
    "predict_scene_retention",
    "register_source",
    "register_style",
    "resolve_style",
    "scene_visual_score",
    "score_scene_visuals",
    "shot_for",
    "source_keys",
    "style_keys",
]
