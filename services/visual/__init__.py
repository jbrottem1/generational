"""Visual Intelligence service — the visual brain of the pipeline.

Public API for turning any scripted idea into a complete Visual Production
Package: storyboard, art-directed scenes, per-model AI image/video prompts,
scored thumbnail concepts, hook sequence, caption plan, and pacing / camera /
motion reports. The `visual_intelligence` pipeline engine is a thin wrapper
around this module; it is equally usable standalone (e.g. re-planning the
visuals of an approved idea for a different platform):

    from services.visual import build_visual_package

    package = build_visual_package(idea, niche="Science",
                                   subject="black holes", aspect_ratio="9:16")
    best_thumbnail = package["thumbnails"][0]

Every downstream renderer (image, video, thumbnail, caption) consumes this
package — new AI models plug in as one formatter in `prompts.py`.
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
    scene_visual_score,
    score_scene_visuals,
)
from services.visual.scenes import NICHE_VISUAL_PALETTES, palette_for, plan_scenes
from services.visual.thumbnails import (
    THUMBNAIL_ARCHETYPES,
    THUMBNAIL_SCORE_WEIGHTS,
    build_thumbnail_concepts,
    expected_ctr_pct,
)

__all__ = [
    "HOOK_FRAME_COUNT",
    "HOOK_WINDOW_SEC",
    "IMAGE_MODELS",
    "NICHE_VISUAL_PALETTES",
    "PACKAGE_SCORE_WEIGHTS",
    "REQUIRED_SCENE_COMPONENTS",
    "ScenePlan",
    "THUMBNAIL_ARCHETYPES",
    "THUMBNAIL_SCORE_KEYS",
    "THUMBNAIL_SCORE_WEIGHTS",
    "ThumbnailConcept",
    "VIDEO_MODELS",
    "VISUAL_DIMENSION_KEYS",
    "VISUAL_DIMENSION_LABELS",
    "VISUAL_SCORE_WEIGHTS",
    "build_camera_plan",
    "build_caption_plan",
    "build_hook_sequence",
    "build_image_prompts",
    "build_motion_report",
    "build_pacing_report",
    "build_storyboard",
    "build_thumbnail_concepts",
    "build_transitions",
    "build_video_prompts",
    "build_visual_package",
    "expected_ctr_pct",
    "overall_visual_score",
    "palette_for",
    "plan_scenes",
    "scene_visual_score",
    "score_scene_visuals",
]
