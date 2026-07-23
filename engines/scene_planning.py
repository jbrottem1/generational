"""Scene Planning engine — decomposes each approved script into structured scenes."""

from __future__ import annotations

import re
import uuid

from core.log import get_logger, log_event
from core.production_models import ProductionPackage, Scene, build_production_package
from engines.base import Engine
from services.editorial import REQUIRED_STORY_BEATS, STORY_BEAT_LABELS

logger = get_logger(__name__)

EMOTIONS = ["curious", "urgent", "revelatory", "calm", "dramatic"]
CAMERAS = ["slow push-in", "static close-up", "handheld drift", "wide establishing", "rack focus"]
TRANSITIONS = ["cut", "crossfade", "whip pan", "match cut"]

# Beat-aware emotion / camera language for motivational arcs.
BEAT_DIRECTION = {
    "hook": ("curious", "slow push-in", "Cinematic establishing landscape with subtle camera drift"),
    "struggle": ("urgent", "handheld drift", "Storm, weight, or solitary path — viewer recognition"),
    "real_life_example": ("revelatory", "wide establishing", "Documentary archival / craftsman / athlete at work"),
    "lesson": ("calm", "slow push-in", "Quiet reflective landscape or laboratory / study space"),
    "application": ("dramatic", "rack focus", "Hands at work, first step, concrete action imagery"),
    "memorable_ending": ("calm", "slow push-in", "Horizon clearing — resolve without text stickers"),
}


def script_to_scenes(script: str, title: str) -> list:
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", script) if s.strip()]
    if not sentences:
        sentences = [script]

    per_scene = max(1, len(sentences) // min(3, len(sentences)))
    chunks = []
    for i in range(0, len(sentences), per_scene):
        chunks.append(" ".join(sentences[i : i + per_scene]))
    if len(chunks) == 1 and len(sentences) > 1:
        mid = len(sentences) // 2
        chunks = [" ".join(sentences[:mid]), " ".join(sentences[mid:])]

    scenes = []
    elapsed = 0.0
    for index, narration in enumerate(chunks, start=1):
        words = len(narration.split())
        duration = max(3.0, min(12.0, words / 2.5))
        scene = Scene(
            scene_id=f"sc_{uuid.uuid4().hex[:8]}",
            title=f"{title} — Part {index}",
            duration_sec=round(duration, 1),
            narration=narration,
            visual_description=f"Visual supporting: {narration[:120]}...",
            emotion=EMOTIONS[index % len(EMOTIONS)],
            camera_movement=CAMERAS[index % len(CAMERAS)],
            transition=TRANSITIONS[min(index - 1, len(TRANSITIONS) - 1)],
            on_screen_text=narration.split(".")[0][:60] if narration else "",
            keywords=[w.lower() for w in re.findall(r"[A-Za-z']{4,}", narration)][:5],
            timing_start=elapsed,
            timing_end=elapsed + duration,
        )
        elapsed += duration
        scenes.append(scene.to_dict())
    return scenes


def beats_to_scenes(story_beats: dict, title: str) -> list:
    """One scene (or clip group) per motivational story beat when beats are present."""
    scenes = []
    elapsed = 0.0
    for index, beat_key in enumerate(REQUIRED_STORY_BEATS, start=1):
        narration = str(story_beats.get(beat_key, "")).strip()
        if not narration:
            continue
        emotion, camera, visual = BEAT_DIRECTION.get(
            beat_key, ("curious", "slow push-in", f"Visual for {beat_key}")
        )
        words = len(narration.split())
        duration = max(3.0, min(14.0, words / 2.5))
        scene = Scene(
            scene_id=f"sc_{uuid.uuid4().hex[:8]}",
            title=f"{title} — {STORY_BEAT_LABELS.get(beat_key, beat_key)}",
            duration_sec=round(duration, 1),
            narration=narration,
            visual_description=f"{visual}. Supporting narration: {narration[:100]}",
            emotion=emotion,
            camera_movement=camera,
            transition=TRANSITIONS[min(index - 1, len(TRANSITIONS) - 1)],
            on_screen_text=narration.split(".")[0][:60],
            keywords=[w.lower() for w in re.findall(r"[A-Za-z']{4,}", narration)][:5],
            timing_start=elapsed,
            timing_end=elapsed + duration,
        )
        elapsed += duration
        scenes.append(scene.to_dict())
    return scenes


class ScenePlanningEngine(Engine):
    key = "scene_planning"
    label = "Scene Planning"
    icon = "🎬"
    description = "Decompose approved scripts into structured scenes."

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        approved = context.get("approved_content") or []
        niche = context.get("niche", "General Content")
        packages = []

        for idea in approved:
            pkg = build_production_package(idea, niche)
            d = pkg.to_dict()
            d["thumbnail_concept"] = idea.get("thumbnail_concept", "")
            d["story_beats"] = idea.get("story_beats") or {}
            d["publishable"] = bool(idea.get("publishable", True))
            d["content_pillar"] = idea.get("content_pillar", "")
            beats = d["story_beats"]
            if beats and sum(1 for v in beats.values() if str(v).strip()) >= 4:
                d["scenes"] = beats_to_scenes(beats, idea.get("title", "Scene"))
            else:
                d["scenes"] = script_to_scenes(idea.get("script", ""), idea.get("title", "Scene"))
            packages.append(d)

        log_event(logger, "scene_planning.completed", packages=len(packages))
        return {"production_packages": packages}
