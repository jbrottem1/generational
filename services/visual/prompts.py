"""AI prompt builders — model-ready image and video prompts per scene.

Every storyboard scene becomes one prompt set for each supported image model
(Midjourney, Flux, Stable Diffusion, DALL-E, OpenAI Images) and each
supported video model (Runway, Veo, Pika, Luma, Kling, Sora). One shared
spec (lighting, composition, lens, mood, art style, palette, quality,
aspect ratio / camera movement, character action, physics, duration) is
formatted into each model's preferred prompt dialect, so adding a model is
one new formatter — never a new planning pass.
"""

from __future__ import annotations

IMAGE_MODELS = ["midjourney", "flux", "stable_diffusion", "dalle", "openai_images"]

# Sora is included now so downstream renderers can adopt it the day it is
# available — the formatter contract is identical to the live models.
VIDEO_MODELS = ["runway", "veo", "pika", "luma", "kling", "sora"]

# Lens fallback when a scene carries no shot-driven lens recommendation
# (the shot table in services/visual/shots.py is the primary source).
ANGLE_LENSES = {
    "extreme close-up": "100mm macro, f/2.8",
    "slow-motion close-up": "85mm prime, f/1.4",
    "direct-address medium close-up": "50mm prime, f/2.0",
    "medium shot": "35mm prime, f/2.8",
    "dutch angle medium shot": "24mm wide, f/4",
    "over-the-shoulder reveal": "35mm anamorphic, f/2.8",
}
DEFAULT_LENS = "35mm prime, f/2.8"

# Art style per niche keeps the whole package visually coherent.
NICHE_ART_STYLES = {
    "Science": "photorealistic scientific visualization, volumetric detail",
    "Psychology": "moody editorial photography, intimate realism",
    "Finance": "clean premium editorial, glass and metal textures",
    "Space": "NASA-grade astrophotography realism",
    "Dark History": "archival documentary photography, period-accurate grain",
    "Health": "bright lifestyle photography, natural realism",
    "AI & Future Tech": "sleek concept art, holographic sci-fi realism",
}
DEFAULT_ART_STYLE = "cinematic photorealism, filmic color grade"

QUALITY_TAGS = "ultra-detailed, sharp focus, professional color grade, 8k"


def _physics_for(motion_intensity: int) -> str:
    if motion_intensity >= 70:
        return "fast dynamic physics — debris, hair, and fabric react to rapid movement"
    if motion_intensity >= 45:
        return "natural weighted physics — believable momentum and settle"
    return "calm, near-still physics — subtle drift, breathing-level movement only"


def _character_action(scene: dict) -> str:
    purpose = scene.get("purpose", "story_beat")
    return {
        "hook": "subject snaps toward camera mid-realization",
        "pattern_interrupt": "subject freezes, breaking the established rhythm",
        "curiosity_loop": "subject leans toward something just out of frame",
        "story_beat": "subject demonstrates the narration's key action naturally",
        "payoff": "subject reacts with visible relief and recognition",
        "cta": "subject addresses the lens directly with an inviting gesture",
    }.get(purpose, "subject moves naturally with the scene's emotion")


def build_prompt_spec(scene: dict, *, art_style: str, aspect_ratio: str) -> dict:
    """The shared, model-agnostic visual spec for one scene."""
    return {
        "subject": scene.get("visual_description", ""),
        "lighting": scene.get("lighting", ""),
        "composition": scene.get("shot_composition", ""),
        "lens": scene.get("lens_recommendation") or ANGLE_LENSES.get(scene.get("camera_angle", ""), DEFAULT_LENS),
        "mood": scene.get("emotion", ""),
        "art_style": art_style,
        "color_palette": scene.get("color_palette", ""),
        "quality": QUALITY_TAGS,
        "aspect_ratio": aspect_ratio,
        "camera_movement": scene.get("camera_motion", ""),
        "character_action": _character_action(scene),
        "physics": _physics_for(int(scene.get("motion_intensity", 50) or 50)),
        "duration_sec": scene.get("length_sec", 0),
    }


def _base_description(spec: dict) -> str:
    return (
        f"{spec['subject']} Mood: {spec['mood']}. Lighting: {spec['lighting']}. "
        f"Composition: {spec['composition']}. Lens: {spec['lens']}. "
        f"Style: {spec['art_style']}. Palette: {spec['color_palette']}."
    )


# --- Image model formatters -------------------------------------------------

def _midjourney(spec: dict) -> str:
    return (
        f"{spec['subject']} {spec['lighting']}, {spec['composition']}, shot on {spec['lens']}, "
        f"{spec['mood']} mood, {spec['art_style']}, {spec['color_palette']}, {spec['quality']} "
        f"--ar {spec['aspect_ratio'].replace(':', ':')} --style raw --v 6"
    )


def _flux(spec: dict) -> str:
    return (
        f"{_base_description(spec)} {spec['quality']}. "
        f"Aspect ratio {spec['aspect_ratio']}. Rendered with precise prompt adherence."
    )


def _stable_diffusion(spec: dict) -> str:
    positive = (
        f"{spec['subject']} ({spec['lighting']}), ({spec['composition']}), {spec['lens']}, "
        f"{spec['mood']} atmosphere, {spec['art_style']}, {spec['color_palette']}, {spec['quality']}"
    )
    return f"{positive} | Negative prompt: blurry, watermark, text artifacts, extra limbs, low quality"


def _dalle(spec: dict) -> str:
    return (
        f"A {spec['aspect_ratio']} frame: {_base_description(spec)} "
        f"Render at the highest possible fidelity."
    )


def _openai_images(spec: dict) -> str:
    return (
        f"{_base_description(spec)} High fidelity, {spec['quality']}. "
        f"Frame for {spec['aspect_ratio']} vertical video."
        if spec["aspect_ratio"] == "9:16"
        else f"{_base_description(spec)} High fidelity, {spec['quality']}. Frame for {spec['aspect_ratio']} video."
    )


IMAGE_FORMATTERS = {
    "midjourney": _midjourney,
    "flux": _flux,
    "stable_diffusion": _stable_diffusion,
    "dalle": _dalle,
    "openai_images": _openai_images,
}


# --- Video model formatters -------------------------------------------------

def _video_body(spec: dict) -> str:
    return (
        f"Scene: {spec['subject']} Camera: {spec['camera_movement']}, {spec['lens']}. "
        f"Action: {spec['character_action']}. Lighting: {spec['lighting']}. "
        f"Physics: {spec['physics']}. Mood: {spec['mood']}. "
        f"Palette: {spec['color_palette']}. Duration: {spec['duration_sec']}s, {spec['aspect_ratio']}."
    )


def _runway(spec: dict) -> str:
    return f"{_video_body(spec)} Cinematic motion, consistent subject, no morphing artifacts."


def _veo(spec: dict) -> str:
    return f"{_video_body(spec)} Photorealistic detail, natural motion blur, stable temporal coherence."


def _pika(spec: dict) -> str:
    return f"{_video_body(spec)} Smooth camera path, strong subject lock, stylized polish."


def _luma(spec: dict) -> str:
    return f"{_video_body(spec)} Dream-machine realism, fluid parallax, physically plausible light."


def _kling(spec: dict) -> str:
    return f"{_video_body(spec)} High-fidelity human motion, accurate physics simulation."


def _sora(spec: dict) -> str:
    return f"{_video_body(spec)} World-consistent simulation, persistent objects, film-grade rendering."


VIDEO_FORMATTERS = {
    "runway": _runway,
    "veo": _veo,
    "pika": _pika,
    "luma": _luma,
    "kling": _kling,
    "sora": _sora,
}


# --- Public API ---------------------------------------------------------------

def build_image_prompts(scenes: list, *, niche: str = "", aspect_ratio: str = "9:16", art_style: str = "") -> list:
    """One prompt set per scene — every image model gets a dialect-correct prompt."""
    art_style = art_style or NICHE_ART_STYLES.get(niche, DEFAULT_ART_STYLE)
    prompt_sets = []
    for scene in scenes:
        spec = build_prompt_spec(scene, art_style=art_style, aspect_ratio=aspect_ratio)
        prompt_sets.append(
            {
                "scene_number": scene.get("scene_number", 0),
                "spec": spec,
                "prompts": {model: IMAGE_FORMATTERS[model](spec) for model in IMAGE_MODELS},
            }
        )
    return prompt_sets


def build_video_prompts(scenes: list, *, niche: str = "", aspect_ratio: str = "9:16", art_style: str = "") -> list:
    """One prompt set per scene — every video model gets a dialect-correct prompt."""
    art_style = art_style or NICHE_ART_STYLES.get(niche, DEFAULT_ART_STYLE)
    prompt_sets = []
    for scene in scenes:
        spec = build_prompt_spec(scene, art_style=art_style, aspect_ratio=aspect_ratio)
        prompt_sets.append(
            {
                "scene_number": scene.get("scene_number", 0),
                "spec": spec,
                "prompts": {model: VIDEO_FORMATTERS[model](spec) for model in VIDEO_MODELS},
            }
        )
    return prompt_sets
