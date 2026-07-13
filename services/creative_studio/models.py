"""Data contracts for the Creative Studio (Agent 12).

Field tuples are the testable contract (same convention as the Render,
Optimization, Publishing, and Analytics engines). Everything the studio
emits is a plain JSON-safe dict so the workflow context, ContentPackage
slots, and the UI can carry it without conversion.

Contract rules (DATA_CONTRACTS.md): additive-only from 1.0 on — append
fields freely, never remove, rename, or repurpose existing ones.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

CREATIVE_ENGINE_VERSION = "1.0.0"

# Version of the CreativeProductionPackage written into each
# ContentPackage `creative_package` slot.
CREATIVE_PACKAGE_VERSION = "1.0"


class ReadinessStatus:
    """Lifecycle of one creative production package."""

    READY = "ready"                  # blueprint complete, renderable as designed
    NEEDS_REVIEW = "needs_review"    # complete but with warnings a human should see
    INCOMPLETE = "incomplete"        # missing scenes/assets — not renderable yet

    ALL = (READY, NEEDS_REVIEW, INCOMPLETE)


# The CreativeProductionPackage — the complete visual production blueprint
# the Creative Studio hands to the Render Engine (via the orchestrator).
CREATIVE_PACKAGE_FIELDS = (
    "creative_package_version",
    "engine_version",
    "project_id",
    "production_type",           # PRODUCTION_TYPE_FIELDS dict
    "creative_blueprint",        # CREATIVE_BLUEPRINT_FIELDS dict
    "storyboard",                # list of STORYBOARD_SCENE_FIELDS dicts
    "shot_list",                 # list of SHOT_LIST_ENTRY_FIELDS dicts
    "animation_plan",            # animation style, techniques, per-scene notes
    "character_plan",            # cast list + consistency rules
    "environment_plan",          # environments used + continuity rules
    "motion_plan",               # per-scene motion instructions
    "camera_plan",               # cinematic language + per-scene camera work
    "asset_requirements",        # list of ASSET_REQUIREMENT_FIELDS dicts
    "thumbnail_concepts",        # creative thumbnail directions
    "continuity_report",         # CONTINUITY_REPORT_FIELDS dict
    "creative_diagnostics",      # counts, coverage, style/environment usage
    "production_readiness",      # {score, status, blockers}
    "validation",                # quality-control findings (warnings, never raises)
    "provider_plan",             # asset type → provider routing
    "generated_at",
)

# The Creative Director's production blueprint — every creative decision
# made before a single scene is boarded.
CREATIVE_BLUEPRINT_FIELDS = (
    "production_type",           # production type id (production_types.py)
    "visual_style",              # style id (styles.py)
    "pacing",                    # {"tempo", "scene_target_sec", "cuts_per_minute"}
    "cinematic_language",        # {"camera_grammar", "shot_progression", "transition_grammar"}
    "production_complexity",     # simple | standard | advanced | flagship
    "storytelling_style",        # narrative structure key
    "recommended_techniques",    # ordered technique list
    "aspect_ratio",
    "target_duration_sec",
    "tone",
    "audience",
    "script_interpretation",     # {"premise", "arc", "key_moments", "emotional_curve"}
)

# One storyboard scene — the atom of the visual production blueprint.
STORYBOARD_SCENE_FIELDS = (
    "scene_id",
    "purpose",
    "emotion",
    "narration",
    "visual_description",
    "camera_angle",
    "camera_movement",
    "lighting",
    "color_palette",
    "animation_style",
    "motion_instructions",
    "transitions",               # {"in", "out"}
    "background",
    "props",
    "characters",                # character_ids present in the scene
    "overlay_graphics",
    "estimated_duration_sec",
    "asset_requirements",        # asset_ids this scene needs
    "production_notes",
)

# One entry of the flat shot list derived from the storyboard.
SHOT_LIST_ENTRY_FIELDS = (
    "shot_id",
    "scene_id",
    "shot_number",
    "shot_type",
    "camera_angle",
    "camera_movement",
    "subject",
    "duration_sec",
    "notes",
)

# One creative asset requirement — what a provider must fulfil.
ASSET_REQUIREMENT_FIELDS = (
    "asset_id",
    "scene_id",
    "asset_type",                # providers/creative_provider.py CREATIVE_ASSET_TYPES
    "description",
    "prompt",
    "style",                     # style id the asset must respect
    "priority",                  # required | recommended | optional
    "reusable",                  # True → shareable across scenes/productions
    "status",                    # planned | fulfilled | missing
)

# One reusable character — visual consistency across productions comes from
# the stable `visual_signature` every generation prompt must embed.
CHARACTER_FIELDS = (
    "character_id",
    "name",
    "role",                      # CharacterRole value
    "archetype",
    "description",
    "visual_signature",          # canonical appearance sentence — identical in every scene
    "design_notes",
    "wardrobe",
    "color_anchor",              # signature color kept identical everywhere
    "voice_profile",
    "personality",
    "usage_rights",              # original | licensed | historical_public_domain
    "brand_id",
)


class CharacterRole:
    """Supported reusable character roles."""

    ORIGINAL = "original"
    NARRATOR = "narrator"
    MASCOT = "mascot"
    AI_AVATAR = "ai_avatar"
    DIGITAL_HUMAN = "digital_human"
    CARTOON = "cartoon"
    BRANDED = "branded"
    EDUCATIONAL = "educational"
    HISTORICAL = "historical"
    PRESENTER = "presenter"

    ALL = (
        ORIGINAL, NARRATOR, MASCOT, AI_AVATAR, DIGITAL_HUMAN,
        CARTOON, BRANDED, EDUCATIONAL, HISTORICAL, PRESENTER,
    )


# One visual style preset (styles.py). Unlimited expansion via register_style().
STYLE_FIELDS = (
    "style_id",
    "label",
    "description",
    "color_palette",
    "lighting",
    "typography",
    "camera_language",
    "motion_language",
    "texture",
    "mood",
    "suited_production_types",
)

# One reusable environment preset (environments.py).
ENVIRONMENT_FIELDS = (
    "environment_id",
    "label",
    "description",
    "lighting",
    "color_palette",
    "props",
    "mood",
    "camera_notes",
    "keywords",
)

# One production type (production_types.py). Every future visual medium is
# one more registered entry — never an architectural change.
PRODUCTION_TYPE_FIELDS = (
    "type_id",
    "label",
    "description",
    "default_style",
    "default_pacing",            # slow | measured | dynamic | rapid
    "complexity",                # simple | standard | advanced | flagship
    "storytelling_style",
    "techniques",
    "asset_types",               # creative asset types this medium consumes
    "camera_language",
    "keywords",                  # selection signals matched against topic/script
)

# The continuity report — what the studio tracked between scenes.
CONTINUITY_REPORT_FIELDS = (
    "characters",                # per-character scene presence
    "lighting",
    "environment",
    "color",
    "camera_language",
    "animation_style",
    "brand_consistency",
    "breaks",                    # detected continuity breaks (warnings)
    "continuity_score",          # 0-100
)

# The aggregate summary returned to the orchestrator on the
# `creative_summary` context key.
CREATIVE_SUMMARY_FIELDS = (
    "engine_version",
    "status",                    # designed | no_items
    "items",
    "packages",
    "ready",
    "needs_review",
    "incomplete",
    "production_types",
    "styles",
    "average_readiness",
    "generated_at",
)


@dataclass
class StoryboardScene:
    """One scene of the professional storyboard."""

    scene_id: str
    purpose: str
    emotion: str = ""
    narration: str = ""
    visual_description: str = ""
    camera_angle: str = ""
    camera_movement: str = ""
    lighting: str = ""
    color_palette: str = ""
    animation_style: str = ""
    motion_instructions: str = ""
    transitions: dict = field(default_factory=dict)   # {"in", "out"}
    background: str = ""
    props: list = field(default_factory=list)
    characters: list = field(default_factory=list)
    overlay_graphics: list = field(default_factory=list)
    estimated_duration_sec: float = 0.0
    asset_requirements: list = field(default_factory=list)
    production_notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "StoryboardScene":
        known = {key: value for key, value in data.items() if key in cls.__dataclass_fields__}
        return cls(**known)


def readiness_status(score: int, blockers: list) -> str:
    """Map a 0-100 readiness score + blockers onto a ReadinessStatus."""
    if blockers:
        return ReadinessStatus.INCOMPLETE
    if score >= 80:
        return ReadinessStatus.READY
    return ReadinessStatus.NEEDS_REVIEW
