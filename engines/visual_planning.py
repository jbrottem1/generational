"""Visual Planning engine — detailed visual prompts per scene."""

from __future__ import annotations

from core.log import get_logger, log_event
from core.production_models import VisualPrompt
from engines.base import Engine

logger = get_logger(__name__)

NICHE_PALETTES = {
    "Science": "deep blue, cyan highlights, high contrast",
    "Psychology": "warm amber, soft shadows, intimate",
    "Finance": "navy, gold accents, clean corporate",
    "Space": "black, starfield, nebula purple",
    "Dark History": "desaturated, grain, candlelight",
    "Health": "green, white, bright natural light",
    "AI & Future Tech": "neon cyan, dark grid, holographic",
}


class VisualPlanningEngine(Engine):
    key = "visual_planning"
    label = "Visual Planning"
    icon = "🎨"
    description = "Generate detailed visual prompts for image/video providers."

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        packages = context.get("production_packages") or []
        niche = context.get("niche", "General Content")
        palette = NICHE_PALETTES.get(niche, "cinematic, balanced contrast")

        for pkg in packages:
            prompts = []
            for scene in pkg.get("scenes", []):
                subject = scene.get("on_screen_text") or scene.get("title", "")
                vp = VisualPrompt(
                    scene_id=scene["scene_id"],
                    subject=subject[:80],
                    environment=f"{niche} themed backdrop supporting the narrative",
                    mood=scene.get("emotion", "curious"),
                    lighting="three-point with rim light" if scene.get("emotion") == "dramatic" else "soft natural",
                    camera_angle="medium close-up" if "close" in scene.get("camera_movement", "") else "wide shot",
                    camera_movement=scene.get("camera_movement", "slow push-in"),
                    animation_style="kinetic typography + b-roll montage",
                    color_palette=palette,
                    cinematic_direction=(
                        f"Faceless {niche.lower()} short — {scene.get('emotion', '')} tone, "
                        f"{scene.get('transition', 'cut')} to next beat."
                    ),
                    prompt_text=(
                        f"{subject}. {scene.get('visual_description', '')} "
                        f"Mood: {scene.get('emotion')}. Palette: {palette}."
                    ),
                )
                prompts.append(vp.to_dict())
            pkg["visual_prompts"] = prompts

        log_event(logger, "visual_planning.completed", packages=len(packages))
        return {"production_packages": packages}
