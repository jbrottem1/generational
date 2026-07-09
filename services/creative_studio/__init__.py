"""Creative Studio — Agent 12's visual production design layer.

The creative department of the OS: transforms scripts (ProductionPackages)
into complete visual production blueprints (CreativeProductionPackages)
before rendering. One architecture, unlimited visual styles — production
types, styles, environments, and characters are all runtime registries.

Public surface:
    from services.creative_studio import build_creative_package, design_items
"""

from services.creative_studio.animation import build_animation_plan
from services.creative_studio.assets import build_asset_plan
from services.creative_studio.camera import build_camera_plan
from services.creative_studio.characters import (
    all_characters,
    cast_characters,
    character_prompt_fragment,
    characters_for_role,
    create_character,
    get_character,
    register_character,
)
from services.creative_studio.color_lighting import build_color_lighting_plan
from services.creative_studio.continuity import track_continuity
from services.creative_studio.director import build_blueprint, interpret_script
from services.creative_studio.environments import (
    all_environments,
    get_environment,
    register_environment,
    select_environments,
)
from services.creative_studio.guidance import (
    apply_guidance_to_item,
    derive_creative_guidance,
)
from services.creative_studio.memory import (
    CreativeMemory,
    MemoryKind,
    get_creative_memory,
    record_production,
)
from services.creative_studio.models import (
    ASSET_REQUIREMENT_FIELDS,
    CAMERA_SHOT_FIELDS,
    CHARACTER_FIELDS,
    COLOR_LIGHTING_FIELDS,
    CONTINUITY_REPORT_FIELDS,
    CREATIVE_BLUEPRINT_FIELDS,
    CREATIVE_ENGINE_VERSION,
    CREATIVE_GUIDANCE_FIELDS,
    CREATIVE_PACKAGE_FIELDS,
    CREATIVE_PACKAGE_VERSION,
    CREATIVE_SUMMARY_FIELDS,
    ENVIRONMENT_FIELDS,
    MEMORY_ENTRY_FIELDS,
    PLATFORM_ADAPTATION_FIELDS,
    PRODUCTION_TYPE_FIELDS,
    SHOT_LIST_ENTRY_FIELDS,
    STORYBOARD_SCENE_FIELDS,
    STYLE_FIELDS,
    WORLD_FIELDS,
    CharacterKind,
    CharacterRole,
    ReadinessStatus,
    StoryboardScene,
)
from services.creative_studio.package import build_creative_package, design_items
from services.creative_studio.platforms import (
    build_platform_adaptations,
    get_platform_profile,
    platform_ids,
    register_platform_profile,
)
from services.creative_studio.production_types import (
    all_production_types,
    get_production_type,
    register_production_type,
    select_production_type,
)
from services.creative_studio.quality import production_readiness, validate_package
from services.creative_studio.storyboard import (
    build_asset_requirements,
    build_shot_list,
    build_storyboard,
)
from services.creative_studio.styles import (
    all_styles,
    get_style,
    register_style,
    select_style,
)
from services.creative_studio.worlds import (
    all_worlds,
    get_world,
    register_world,
    select_world,
    world_ids,
)

__all__ = [
    "ASSET_REQUIREMENT_FIELDS",
    "CAMERA_SHOT_FIELDS",
    "CHARACTER_FIELDS",
    "COLOR_LIGHTING_FIELDS",
    "CONTINUITY_REPORT_FIELDS",
    "CREATIVE_BLUEPRINT_FIELDS",
    "CREATIVE_ENGINE_VERSION",
    "CREATIVE_GUIDANCE_FIELDS",
    "CREATIVE_PACKAGE_FIELDS",
    "CREATIVE_PACKAGE_VERSION",
    "CREATIVE_SUMMARY_FIELDS",
    "ENVIRONMENT_FIELDS",
    "MEMORY_ENTRY_FIELDS",
    "PLATFORM_ADAPTATION_FIELDS",
    "PRODUCTION_TYPE_FIELDS",
    "SHOT_LIST_ENTRY_FIELDS",
    "STORYBOARD_SCENE_FIELDS",
    "STYLE_FIELDS",
    "WORLD_FIELDS",
    "CharacterKind",
    "CharacterRole",
    "CreativeMemory",
    "MemoryKind",
    "ReadinessStatus",
    "StoryboardScene",
    "all_characters",
    "all_environments",
    "all_production_types",
    "all_styles",
    "all_worlds",
    "apply_guidance_to_item",
    "build_animation_plan",
    "build_asset_plan",
    "build_asset_requirements",
    "build_blueprint",
    "build_camera_plan",
    "build_color_lighting_plan",
    "build_creative_package",
    "build_platform_adaptations",
    "build_shot_list",
    "build_storyboard",
    "cast_characters",
    "character_prompt_fragment",
    "characters_for_role",
    "create_character",
    "derive_creative_guidance",
    "design_items",
    "get_character",
    "get_creative_memory",
    "get_environment",
    "get_platform_profile",
    "get_production_type",
    "get_style",
    "get_world",
    "interpret_script",
    "platform_ids",
    "production_readiness",
    "record_production",
    "register_character",
    "register_environment",
    "register_platform_profile",
    "register_production_type",
    "register_style",
    "register_world",
    "select_environments",
    "select_production_type",
    "select_style",
    "select_world",
    "track_continuity",
    "validate_package",
]
