# Generational — Creative Studio (Agent 12)

The creative department of the AI Media Operating System. The Creative
Studio is **not** an animation engine and **not** a rendering engine — it
is the design layer that transforms scripts into complete visual
production blueprints *before* rendering. One architecture, unlimited
visual styles.

```python
from services.orchestrator import get_orchestrator

context = {"unified_packages": [...]}          # ProductionPackages in
report = get_orchestrator().run_creative_stage(context)
context["creative_summary"]                    # aggregate design report
context["unified_packages"][0]["creative_package"]  # CreativeProductionPackage out
```

## Creative architecture

```
ProductionPackage (script, scores, topic, keywords)
    ↓
Creative Director        interpret script → select production type →
                         select style → pacing → cinematic language →
                         complexity → storytelling style → techniques
    ↓  creative_blueprint
Storyboard Engine        one professional scene per narration beat
    ↓  storyboard → shot list → asset requirements
Plans                    animation · character · environment · motion · camera
    ↓
Continuity Tracker       characters, lighting, environment, color,
                         camera language, animation style, brand
    ↓
Quality Control          missing assets, broken continuity, scene
                         completeness, timing, provider compatibility
    ↓
CreativeProductionPackage  (production readiness score the Render Engine gates on)
```

File map:

| Module | Responsibility |
|---|---|
| `engines/creative_studio.py` | `CreativeStudioEngine` (key: `creative_studio`) — the orchestrator-facing stage |
| `services/creative_studio/models.py` | All field-tuple contracts + `StoryboardScene` dataclass |
| `services/creative_studio/production_types.py` | Production type registry (25+ media, unlimited expansion) |
| `services/creative_studio/director.py` | The Creative Director — blueprint generation |
| `services/creative_studio/storyboard.py` | Storyboard, shot list, asset requirements |
| `services/creative_studio/styles.py` | Style Library |
| `services/creative_studio/environments.py` | Environment System |
| `services/creative_studio/characters.py` | Character System |
| `services/creative_studio/continuity.py` | Visual continuity tracking |
| `services/creative_studio/quality.py` | Creative quality control + readiness |
| `services/creative_studio/package.py` | CreativeProductionPackage assembly |
| `providers/creative_provider.py` | `CreativeAssetProvider` interface |
| `providers/creative/` | Provider registry + deterministic mock |

Design rules (same as every OS engine): deterministic, JSON-safe dicts,
additive-only contracts, never crashes the pipeline, never mutates another
agent's package slot, never imports another engine (Directive #1).

## Supported production types

`services/creative_studio/production_types.py` ships 24 built-in media —
AI cinematic video, 2D animation, 3D animation, cartoons, anime-inspired,
motion graphics, whiteboard, educational explainers, science
visualization, medical animation, historical reconstruction, infographics,
corporate presentations, commercial ads, luxury branding, product demos,
documentaries, nature videos, children's educational, AI presenter,
reaction, gaming, podcast visualization, comic book style.

Every type is one registered dict (`PRODUCTION_TYPE_FIELDS`): default
style, pacing, complexity, storytelling style, techniques, asset types,
camera language, and selection keywords. `select_production_type()` picks
deterministically: explicit request → keyword match → cinematic default.

**Future formats are one call, never a redesign:**

```python
from services.creative_studio import register_production_type

register_production_type({
    "type_id": "interactive_experience",
    "label": "Interactive Visual Experience",
    "keywords": ["interactive", "choose"],
    "default_style": "cyberpunk",
    "asset_types": ["ai_video", "vector_graphic"],
})
```

## Storyboard specification

One scene per narration beat, every scene carrying the full
`STORYBOARD_SCENE_FIELDS` contract:

`scene_id` · `purpose` (hook/setup/development/escalation/revelation/
payoff) · `emotion` · `narration` · `visual_description` · `camera_angle` ·
`camera_movement` · `lighting` · `color_palette` · `animation_style` ·
`motion_instructions` · `transitions` (in/out) · `background` · `props` ·
`characters` · `overlay_graphics` · `estimated_duration_sec` ·
`asset_requirements` · `production_notes`

Camera work follows a professional coverage cycle (establish → develop →
emphasize) with the hook pinned to a fast push-in close-up and the payoff
to a wide hero pull-back. Durations derive from narration length
(~2.6 words/sec) clamped around the blueprint's pacing target. A flat
`shot_list` (`SHOT_LIST_ENTRY_FIELDS`) and provider-ready
`asset_requirements` (`ASSET_REQUIREMENT_FIELDS`) derive from the board.

## Character architecture

`services/creative_studio/characters.py` — reusable characters
(`CHARACTER_FIELDS`) across roles: original, narrator, mascot, AI avatar,
digital human, cartoon, branded, educational, historical (with
`usage_rights` recording the basis), presenter.

**Consistency mechanism:** every character carries a stable
`visual_signature` (one canonical appearance sentence) and a
`color_anchor`. `character_prompt_fragment()` renders the exact text
embedded verbatim into every generation prompt featuring the character —
the same description in every scene of every production is what keeps the
design identical. On-screen characters additionally get one *reusable*
reference-sheet asset requirement generated before scene assets.

House cast shipped: The Narrator (voice-only), Nova (AI presenter avatar),
Gen (mascot), Professor Atlas (educational). `create_character()` adds
unlimited new cast members at runtime.

## Style system

`services/creative_studio/styles.py` — 16 built-in styles (minimal,
luxury, corporate, scientific, medical, space, cyberpunk, finance,
history, nature, kids, anime-inspired, comic, psychology, motivational,
documentary), each one dict (`STYLE_FIELDS`): palette, lighting,
typography, camera language, motion language, texture, mood, suited
production types. `register_style()` expands the library without limit;
`select_style()` resolves explicit request → keyword match → the
production type's default.

## Environment system

`services/creative_studio/environments.py` — 12 built-in reusable
environments (studio, office, laboratory, hospital, nature, space, city,
classroom, factory, historical, fantasy), each one dict
(`ENVIRONMENT_FIELDS`): lighting, palette, props, mood, camera notes,
selection keywords. `select_environments()` casts locations from content
signals and always returns at least the neutral studio.
`register_environment()` adds future environments at runtime.

## Provider interfaces

Nothing is hardcoded. Asset sourcing is typed
(`CREATIVE_ASSET_TYPES`): `ai_image`, `ai_video`, `animation`,
`asset_3d`, `vector_graphic`, `stock_footage`, `user_asset`,
`brand_asset` — additive-only.

`CreativeAssetProvider` (`providers/creative_provider.py`) declares
`supports(asset_type)` and `fulfill(requirement)`. The registry
(`providers/creative/`) resolves providers per asset type; the
deterministic `MockCreativeProvider` serves everything until real backends
land:

```python
from providers.creative import register_creative_provider

register_creative_provider("ai_video", MyVideoModelProvider())
# nothing in the studio changes
```

Each CreativeProductionPackage carries a `provider_plan` (asset type →
provider name) so downstream stages know exactly how assets will be
sourced, and QC flags asset types no provider supports.

## The CreativeProductionPackage

Written to the ContentPackage `creative_package` slot
(`CREATIVE_PACKAGE_FIELDS`, v1.0): production type, creative blueprint,
storyboard, shot list, animation plan, character plan, environment plan,
motion plan, camera plan, asset requirements, thumbnail concepts,
continuity report, creative diagnostics, provider plan, validation, and
`production_readiness` — a 0-100 score with status
`ready | needs_review | incomplete` the Render Engine can gate on.

Continuity (`CONTINUITY_REPORT_FIELDS`) tracks characters, lighting,
environment, color, camera language, animation style, and brand
consistency scene-to-scene; breaks surface as warnings and lower the
continuity score — never an exception.

## Pipeline integration

- Input: `unified_packages` (canonical ContentPackage dicts), falling back
  to `ideas` / `selected_ideas` — the same collection order as SEO,
  Publishing, and Analytics.
- Output: `creative_summary` + `creative_packages` context keys, plus each
  item's `creative_package` slot (Agent 12's only write zone).
- Stage: `creative` (`services/orchestrator/stages.py`), runnable on
  demand via `get_orchestrator().run_creative_stage(context)`. Scheduling
  it automatically inside `run_full_pipeline()` (between packaging and
  render) is an Agent 1 decision via `register_stage()`.
- Orchestrator-only communication: the studio never invokes another
  engine; it reads upstream slots (`script_package`, `visual_package`,
  `scene_breakdown`) and writes only its own.

## Future expansion guide

Everything expands through registries — never through redesign:

| To add | Do this |
|---|---|
| A new visual medium (e.g. interactive experiences) | `register_production_type({...})` |
| A new visual style (e.g. a brand's house look) | `register_style({...})` |
| A new environment | `register_environment({...})` |
| A new character / AI avatar / digital human | `create_character({...})` |
| A real generation backend | implement `CreativeAssetProvider`, `register_creative_provider(asset_type, provider)` |
| A new asset type | append to `CREATIVE_ASSET_TYPES` (additive, Agent 1 review) |
| New package fields | append to `CREATIVE_PACKAGE_FIELDS` (additive-only) |

This is how the studio eventually powers Shorts, TikTok, Reels, animated
series, courses, documentaries, commercials, brand campaigns, training
videos, AI presenters, reaction channels, original animated franchises,
and interactive experiences — one architecture, unlimited styles.

## Testing

`tests/test_creative_studio.py` (service layer: director, storyboard,
characters, styles, environments, continuity, QC) and
`tests/test_creative_studio_engine.py` (engine contract, package output,
slot ownership, providers, ContentPackage round-trip, orchestrator stage).
Run with `python -m pytest tests/test_creative_studio*.py`.
