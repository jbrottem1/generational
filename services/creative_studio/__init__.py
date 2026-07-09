"""Creative Studio — Agent 12's visual production design layer.

The creative department of the OS: transforms scripts (ProductionPackages)
into complete visual production blueprints (CreativeProductionPackages)
before rendering. One architecture, unlimited visual styles — production
types, styles, environments, and characters are all runtime registries.

Public surface:
    from services.creative_studio import build_creative_package, design_items
"""

from services.creative_studio.characters import (
    all_characters,
    cast_characters,
    character_prompt_fragment,
    characters_for_role,
    create_character,
    get_character,
    register_character,
)
from services.creative_studio.continuity import track_continuity
from services.creative_studio.director import build_blueprint, interpret_script
from services.creative_studio.environments import (
    all_environments,
    get_environment,
    register_environment,
    select_environments,
)
from services.creative_studio.models import (
    ASSET_REQUIREMENT_FIELDS,
    CHARACTER_FIELDS,
    CONTINUITY_REPORT_FIELDS,
    CREATIVE_BLUEPRINT_FIELDS,
    CREATIVE_ENGINE_VERSION,
    CREATIVE_PACKAGE_FIELDS,
    CREATIVE_PACKAGE_VERSION,
    CREATIVE_SUMMARY_FIELDS,
    ENVIRONMENT_FIELDS,
    PRODUCTION_TYPE_FIELDS,
    SHOT_LIST_ENTRY_FIELDS,
    STORYBOARD_SCENE_FIELDS,
    STYLE_FIELDS,
    CharacterRole,
    ReadinessStatus,
    StoryboardScene,
)
from services.creative_studio.package import build_creative_package, design_items
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

__all__ = [
    "ASSET_REQUIREMENT_FIELDS",
    "CHARACTER_FIELDS",
    "CONTINUITY_REPORT_FIELDS",
    "CREATIVE_BLUEPRINT_FIELDS",
    "CREATIVE_ENGINE_VERSION",
    "CREATIVE_PACKAGE_FIELDS",
    "CREATIVE_PACKAGE_VERSION",
    "CREATIVE_SUMMARY_FIELDS",
    "ENVIRONMENT_FIELDS",
    "PRODUCTION_TYPE_FIELDS",
    "SHOT_LIST_ENTRY_FIELDS",
    "STORYBOARD_SCENE_FIELDS",
    "STYLE_FIELDS",
    "CharacterRole",
    "ReadinessStatus",
    "StoryboardScene",
    "all_characters",
    "all_environments",
    "all_production_types",
    "all_styles",
    "build_asset_requirements",
    "build_blueprint",
    "build_creative_package",
    "build_shot_list",
    "build_storyboard",
    "cast_characters",
    "character_prompt_fragment",
    "characters_for_role",
    "create_character",
    "design_items",
    "get_character",
    "get_environment",
    "get_production_type",
    "get_style",
    "interpret_script",
    "production_readiness",
    "register_character",
    "register_environment",
    "register_production_type",
    "register_style",
    "select_environments",
    "select_production_type",
    "select_style",
    "track_continuity",
    "validate_package",
]
