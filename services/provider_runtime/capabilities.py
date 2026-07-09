"""Provider capability declarations — additive-only vocabulary for selection.

Each provider advertises one or more capabilities; the Provider Selection
Engine routes operations to the best available backend automatically.
"""

from __future__ import annotations

# Canonical capability tags (additive-only — append, never rename/remove).
IMAGE_GENERATION = "image_generation"
VIDEO_GENERATION = "video_generation"
ANIMATION = "animation"
SPEECH = "speech"
VOICE_CLONING = "voice_cloning"
MUSIC = "music"
SOUND_EFFECTS = "sound_effects"
LLM = "llm"
REASONING = "reasoning"
IMAGE_EDITING = "image_editing"
UPSCALING = "upscaling"
LIP_SYNC = "lip_sync"
MOTION = "motion"
CHARACTER_CONSISTENCY = "character_consistency"
THREE_D_GENERATION = "3d_generation"
RENDERING = "rendering"
CAPTION = "caption"
SUBTITLE = "subtitle"
METADATA = "metadata"
THUMBNAIL = "thumbnail"
SCRIPT = "script"

ALL_CAPABILITIES = (
    IMAGE_GENERATION,
    VIDEO_GENERATION,
    ANIMATION,
    SPEECH,
    VOICE_CLONING,
    MUSIC,
    SOUND_EFFECTS,
    LLM,
    REASONING,
    IMAGE_EDITING,
    UPSCALING,
    LIP_SYNC,
    MOTION,
    CHARACTER_CONSISTENCY,
    THREE_D_GENERATION,
    RENDERING,
    CAPTION,
    SUBTITLE,
    METADATA,
    THUMBNAIL,
    SCRIPT,
)

# Maps high-level runtime operations to required capabilities.
OPERATION_CAPABILITIES = {
    "generate_script": (SCRIPT, LLM),
    "generate_image": (IMAGE_GENERATION,),
    "generate_video": (VIDEO_GENERATION,),
    "generate_animation": (ANIMATION,),
    "generate_voice": (SPEECH,),
    "generate_music": (MUSIC,),
    "generate_sound_effects": (SOUND_EFFECTS,),
    "generate_thumbnail": (THUMBNAIL, IMAGE_GENERATION),
    "generate_caption": (CAPTION, LLM),
    "generate_subtitles": (SUBTITLE, LLM),
    "generate_metadata": (METADATA, LLM),
}
