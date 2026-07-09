# Generational — Creative Studio (Agent 12)

The creative department of the AI Media Operating System. The Creative
Studio is **not** an animation engine and **not** a rendering engine — it
is the design layer that transforms scripts into complete visual
production blueprints *before* rendering. One architecture, unlimited
visual styles.

**v1.1 — Creative Intelligence & Storytelling** adds: the World Engine
(persistent worlds), the Camera Director (lens-level shot direction),
Color & Lighting design, full Animation Planning (facial, lip-sync,
physics), expanded Asset Planning (vehicles, icons, logos, textures, VFX,
particles), Platform Adaptation, persistent Creative Memory, the Learning
Loop, and extended quality validation. All additive — every v1.0 field
and behavior is preserved.

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
Learning Loop            analytics / trend / optimization / behavioral
                         recommendations → creative guidance
    ↓
Creative Director        interpret script → select production type →
                         select style → select world → pacing →
                         cinematic language → complexity →
                         storytelling style → techniques
    ↓  creative_blueprint
Storyboard Engine        one professional scene per narration beat
                         (+ psychology, music, SFX, retention)
    ↓  storyboard → shot list
Camera Director          lens, movement, zoom, tracking, DOF, focus
                         pulls, motion pacing, composition per shot
Color & Lighting         palette, per-scene lighting, contrast strategy,
                         hierarchy, brand colors, accessibility,
                         emotional color map
Animation Planning       character movement, facial, camera animation,
                         motion graphics, timing, lip-sync, physics
Asset Planning           categorized structured requests — characters,
                         backgrounds, objects, vehicles, icons, logos,
                         textures, VFX, particle systems
Platform Adaptation      per-platform aspect ratio, safe zones, pacing,
                         opening seconds, CTA placement
    ↓
Continuity Tracker       characters, lighting, environment, color,
                         camera language, animation style, brand
    ↓
Quality Control          missing assets, continuity, completeness,
                         timing, providers, duplicate characters,
                         story flow, brand violations, accessibility
    ↓
CreativeProductionPackage  (production readiness score the Render Engine gates on)
    ↓
Creative Memory          characters, worlds, styles, motifs, structures,
                         transitions, themes remembered for future productions
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
| `services/creative_studio/worlds.py` | World Engine — persistent worlds *(v1.1)* |
| `services/creative_studio/camera.py` | Camera Director — lens-level shot direction *(v1.1)* |
| `services/creative_studio/color_lighting.py` | Color & Lighting design *(v1.1)* |
| `services/creative_studio/animation.py` | Animation Planning *(v1.1)* |
| `services/creative_studio/assets.py` | Expanded Asset Planning *(v1.1)* |
| `services/creative_studio/platforms.py` | Platform Adaptation *(v1.1)* |
| `services/creative_studio/memory.py` | Persistent Creative Memory *(v1.1)* |
| `services/creative_studio/guidance.py` | Learning Loop — upstream intelligence → guidance *(v1.1)* |
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
`asset_requirements` · `production_notes` — plus (v1.1)
`psychological_objective` · `narration_alignment` · `music_mood` ·
`sound_effects` · `visual_emphasis` · `expected_retention` (a
deterministic 0-100 prediction modeling the short-form retention curve:
steep early drop, mid-video sag, strong beats holding viewers, over-long
scenes bleeding them).

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

**v1.1 identity fields** (additive): `kind` (`CharacterKind`: human,
animal, mascot, cartoon, anime, 3d, brand_mascot, historical, fantasy,
custom), `expressions` (named facial expressions), `movement_style`,
`emotion_profile` (emotion → performance note), `outfits`, `accessories`,
and `memory_hooks` — the stable keys future productions use to recall the
character from Creative Memory.

## World Engine *(v1.1)*

`services/creative_studio/worlds.py` — persistent worlds
(`WORLD_FIELDS`) that productions live inside, so a channel's videos feel
like chapters of one place. Each world carries lighting, architecture,
textures, mood, weather, camera language, environmental storytelling, and
the environment ids it stages scenes in. Nine built-ins: The Studio
(neutral), Metropolis (city), Everwood (nature), Meridian Station
(sci-fi), The Old Dominion (historical), Clearline (minimalist abstract),
The Atrium (corporate), Wonderrealm (fantasy), The Academy (educational).
`select_world()` casts deterministically from content signals;
`register_world()` adds custom worlds at runtime. The blueprint records
the chosen `world_id` and the package carries a full `world_plan` with
per-scene staging.

## Camera Director *(v1.1)*

`services/creative_studio/camera.py` — extends every board scene into one
directed shot (`CAMERA_SHOT_FIELDS`): angle, professional lens selection
(24mm scale → 100mm macro grammar), movement, zoom, tracking, depth of
field, focus pulls, motion pacing, duration, and composition per purpose
(hooks get centered negative-space frames, revelations break symmetry).
The package's `camera_plan` also carries the production's `lens_kit`.

## Color & Lighting *(v1.1)*

`services/creative_studio/color_lighting.py` — one plan
(`COLOR_LIGHTING_FIELDS`) per production: the master palette, per-scene
lighting setups keyed to purpose, a contrast strategy across the arc,
visual hierarchy rules, brand colors, **accessibility guidance** (caption
contrast ≥ 4.5:1, safe zones, flash safety, color independence, mobile
text sizing), and an `emotional_color_map` translating each scene's
emotion into a color treatment.

## Animation Planning *(v1.1)*

`services/creative_studio/animation.py` — plans, never renders: character
movement per cast member, facial animation per scene (expression lands one
beat before the motivating line), camera animation easing, motion-graphics
timing, scene transitions, lip-sync word windows derived from narration
(~2.6 words/sec; phoneme timing comes from the Voice engine at render
time), and physics notes. v1.0 keys (`animation_style`, `techniques`,
`complexity`, `scenes`) are preserved for downstream consumers.

## Platform Adaptation *(v1.1)*

`services/creative_studio/platforms.py` — per-platform creative
variations (`PLATFORM_ADAPTATION_FIELDS`): aspect ratio, resolution, safe
zones, visual pacing, opening-seconds treatment, CTA placement, and
duration ceilings for YouTube/Shorts, TikTok, Instagram/Reels, Facebook,
X, and LinkedIn. Publishing (Agent 7) owns metadata and scheduling; this
module owns only the creative variation. Future platforms are one
`register_platform_profile()` call.

## Creative Memory *(v1.1)*

`services/creative_studio/memory.py` — append-only persistent store
(`data/creative_studio/memory.json`, `MEMORY_ENTRY_FIELDS`) remembering
characters, worlds, brands, styles, motifs, scene structures, transitions,
themes, and assets across productions. The engine records every designed
production; entries are recallable by kind + key (`memory.latest()`).
Analytics and the Optimization Laboratory read these JSON entries through
the orchestrator — never through engine calls. A broken store degrades to
a logged warning, never a crash.

## Learning Loop *(v1.1)*

`services/creative_studio/guidance.py` — reads what upstream intelligence
already put on the shared context (`learning_recommendations` from Agent
9, `opportunity_recommendations` from trend intelligence,
`optimization_report` from Agent 13, `psychology_report` /
`attention_report` from Agent 2) and derives creative guidance
(`CREATIVE_GUIDANCE_FIELDS`): pacing hints, style hints, hook emphasis,
retention focus. Guidance only fills preferences the item does not
explicitly state — explicit requests always win — and the applied guidance
is recorded in the package's `learning_adaptations` for auditability.

## Style system

`services/creative_studio/styles.py` — 24 built-in styles (minimal,
luxury, corporate, scientific, medical, space, cyberpunk, finance,
history, nature, kids, anime-inspired, comic, psychology, motivational,
documentary, and — v1.1 — pixar-inspired, photorealistic, watercolor,
oil painting, paper animation, motion design, infographic, educational),
each one dict (`STYLE_FIELDS`): palette, lighting,
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
`brand_asset` — plus (v1.1) `character`, `background`, `object`,
`vehicle`, `icon`, `logo`, `texture`, `vfx`, `particle_system` —
additive-only. Asset Planning (`assets.py`) emits categorized structured
*requests* only; providers fulfil them later.

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
(`CREATIVE_PACKAGE_FIELDS`, v1.1): production type, creative blueprint,
storyboard, shot list, animation plan, character plan, environment plan,
motion plan, camera plan, asset requirements, thumbnail concepts,
continuity report, creative diagnostics, provider plan, validation, and
`production_readiness` — a 0-100 score with status
`ready | needs_review | incomplete` the Render Engine can gate on — plus
(v1.1, additive) `world_plan`, `color_lighting_plan`,
`platform_adaptations`, `creative_memory` (the entries recorded for this
production), and `learning_adaptations` (the guidance that shaped it).

Continuity (`CONTINUITY_REPORT_FIELDS`) tracks characters, lighting,
environment, color, camera language, animation style, and brand
consistency scene-to-scene; breaks surface as warnings and lower the
continuity score — never an exception.

Quality control (v1.1) additionally validates duplicate characters (same
id or same visual signature cast twice), broken story flow (arc must open
on a hook, close on a payoff, never regress), brand violations (branded
characters in the wrong brand's production), and accessibility (guidance
must be present in the color & lighting plan). All findings degrade
gracefully as warnings.

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
| A new persistent world | `register_world({...})` |
| A new character / AI avatar / digital human | `create_character({...})` |
| A new platform's creative profile | `register_platform_profile({...})` |
| A real generation backend | implement `CreativeAssetProvider`, `register_creative_provider(asset_type, provider)` |
| A new asset type | append to `CREATIVE_ASSET_TYPES` (additive, Agent 1 review) |
| New package fields | append to `CREATIVE_PACKAGE_FIELDS` (additive-only) |

This is how the studio eventually powers Shorts, TikTok, Reels, animated
series, courses, documentaries, commercials, brand campaigns, training
videos, AI presenters, reaction channels, original animated franchises,
and interactive experiences — one architecture, unlimited styles.

## Testing

`tests/test_creative_studio.py` (service layer: director, storyboard,
characters, styles, environments, continuity, QC),
`tests/test_creative_studio_engine.py` (engine contract, package output,
slot ownership, providers, ContentPackage round-trip, orchestrator stage),
and `tests/test_creative_intelligence.py` (v1.1: worlds, camera director,
color & lighting, animation planning, asset planning, platform
adaptation, creative memory, learning loop, extended QC, failure
handling). Run with `python -m pytest tests/test_creative*.py`.
