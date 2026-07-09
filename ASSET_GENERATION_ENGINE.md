# Universal Asset Generation Engine (Agent 14)

The generation department of the Generational AI Media Operating System.
Every image, illustration, animation frame, background, character sheet,
concept art, thumbnail, texture, icon, logo, scene still, video clip, and
future media asset the platform uses originates here.

**Engine key:** `asset_generation`  
**Pipeline stage:** `asset_generation` (distribution — runs after packaging, before render)  
**ContentPackage slot:** `asset_package`

---

## Mission

Transform structured creative requests into production-ready assets using
the best available AI providers. The engine does **not** plan content,
write scripts, or apply psychology — it consumes upstream outputs and
generates assets.

---

## Architecture

```
Creative Studio (plans)          Asset Generation (generates)       Render (assembles)
─────────────────────────        ────────────────────────────       ──────────────────
creative_package                 asset_package                      render_package
  asset_requirements      →        assets[]                    →      timeline
  storyboard                       scene_assets                       scene renders
  character_plan                   character_assets
  thumbnail_concepts               thumbnail_assets
                                   video_assets
```

| Layer | Location | Role |
|---|---|---|
| Engine | `engines/asset_generation.py` | Thin pipeline adapter (`run(context) → dict`) |
| Service | `services/asset_generation/` | Prompt compilation, selection, generation, QC, registry |
| Providers | `providers/generation_provider.py` + `providers/asset_generation/` | Swappable AI backends |

---

## Provider Architecture

Every backend implements `GenerationProvider` (`providers/generation_provider.py`):

- `supports(asset_class, asset_type)` — coverage declaration
- `generate(prompt_spec, request)` — returns `{uri, provider, format, width, height, ...}` or `{error}`
- `profile` — selection signals: quality, cost_per_asset, speed, consistency
- `prompt_style` — dialect hints for the Prompt Compiler
- `offline` / `local` — routing for offline and local-model support

**Shipped adapters** (stubs until API keys are configured):

OpenAI Images · Google Imagen · Google Veo · Runway · Kling · Luma · Pika ·
Flux · Stable Diffusion · Midjourney · Adobe Firefly · Local Diffusion

**Demo Mode:** `MockGenerationProvider` serves every asset class deterministically
with zero network access — the guaranteed fallback of last resort.

Register or replace backends:

```python
from providers.asset_generation import register_generation_provider
register_generation_provider(MyCustomProvider())
```

No engine code changes when a backend swaps in.

---

## Provider Selection Engine

`services/asset_generation/selection.py` scores candidates deterministically:

| Strategy | Optimizes for |
|---|---|
| `balanced` | Quality + cost + speed + consistency (default) |
| `quality` | Highest output quality |
| `cost` | Lowest cost per asset |
| `speed` | Fastest generation |
| `consistency` | Character/style reproducibility |

Output: `{primary, fallbacks, strategy, candidates}` — the fallback chain
always ends in the offline mock so generation never dead-ends.

Configure via `data/asset_generation/config.json` or runtime:

```python
from services.asset_generation import configure
configure(selection_strategy="quality", max_cost_per_package=10.0)
```

---

## Prompt Compiler

Two-pass, deterministic compilation (`services/asset_generation/prompts.py`):

1. **`compile_prompt(request, item)`** — canonical, provider-agnostic
   `PROMPT_SPEC_FIELDS` dict: subject, style pack, lighting, camera, mood,
   emotion, palette, aspect ratio, resolution, character references (verbatim
   from Creative Studio cast), environment references, brand style, negative prompt.

2. **`optimize_for_provider(spec, provider)`** — rewrites for the target
   backend's dialect (natural language, tagged, cinematic ordering,
   parameter suffixes). Provider dialects come from adapters only — never
   from engine code.

---

## Asset Lifecycle

```
Request collection → Safety gate → Cache lookup → Provider selection
  → Prompt compilation → Generation (retries + fallback chain)
  → Quality analysis → Registry write → AssetPackage assembly
```

### Request sources

1. **Creative Studio** — `creative_package.asset_requirements` + thumbnail concepts
2. **Fallback** — `scene_breakdown` + title/hook when no creative package exists

### Asset Registry

`services/asset_generation/registry.py` — JSON store at `data/asset_generation/`:

- **Assets** — one entry per `asset_id` with append-only version history
- **Generation jobs** — auditable record of every attempt
- **Collections** — named groups (brand libraries, character packs)
- **Fingerprint index** — content-address → asset_id for cache and duplicate detection

### Cache

`services/asset_generation/cache.py` — provider-agnostic content addressing.
Identical requests never generate twice; cache hits return `AssetStatus.CACHED`
with zero generation cost.

---

## Supported Asset Types

40+ catalog types in `services/asset_generation/catalog.py`:

**Images:** illustration, photorealistic, concept art, character sheets,
expressions, poses, environment art, props, vehicles, architecture, icons,
logos, infographics, charts, maps, backgrounds, textures, thumbnails,
storyboard frames, scene images, marketing graphics, branding assets.

**Video:** clips, cinematic shots, animation, looping clips, camera moves,
transitions, motion backgrounds, green screen, B-roll.

**3D preparation:** objects, meshes, materials, rigs, character models.

Expand at runtime: `register_asset_type({...})`.

---

## Style System

15 built-in style packs in `services/asset_generation/styles.py` aligned
with Creative Studio style ids: Pixar, Anime, Comic, Disney, Ghibli,
Cyberpunk, Photorealistic, Oil Painting, Watercolor, Pencil, Minimal,
Corporate, Educational, Luxury, Cinematic.

---

## Character Consistency

`services/asset_generation/characters.py` embeds Creative Studio
`visual_signature`, wardrobe, and color anchors verbatim into every
prompt featuring a persistent character — consistency from data, not
model memory.

---

## Quality Analysis

Every asset validated (`services/asset_generation/quality.py`):

- Resolution vs quality tier
- Aspect ratio match
- Brand/style compliance
- Prompt completeness
- Provider errors
- Safety flags
- Duplicate detection
- Generation confidence (0-100)

Package readiness `{score, status, blockers}` gates downstream render.

---

## Configuration

`data/asset_generation/config.json` (optional):

| Key | Default | Purpose |
|---|---|---|
| `selection_strategy` | `balanced` | Provider scoring strategy |
| `provider_priority` | `{}` | Per-class provider ordering override |
| `max_cost_per_asset` | `2.0` | USD limit per asset |
| `max_cost_per_package` | `25.0` | USD limit per ContentPackage |
| `quality_tier` | `standard` | Minimum resolution tier |
| `max_retries` | `2` | Attempts per provider |
| `cache_enabled` | `true` | Content-address cache |
| `allow_placeholders` | `true` | Demo Mode mock output |
| `safety_rules` | `[...]` | Blocked content terms |
| `max_assets_per_item` | `80` | Generation cap per item |

---

## Integration Points

### Consumes

| Source | Fields |
|---|---|
| `creative_package` | `asset_requirements`, `storyboard`, `character_plan`, `thumbnail_concepts`, `creative_blueprint` |
| Fallback | `scene_breakdown`, `title`, `hook`, `visual_style` |

### Produces

| Output | Location |
|---|---|
| `asset_package` | ContentPackage slot (Agent 14 write zone) |
| `asset_generation_summary` | Context key — aggregate run summary |
| `asset_packages` | Context key — list of AssetPackage dicts |

### Downstream

Render Engine (Agent 6) consumes `asset_package.assets` for timeline assembly.

---

## Extension Guide

### Add a new provider

1. Subclass `GenerationProvider` in `providers/asset_generation/adapters.py`
   (or a new module).
2. Declare `asset_classes`, `profile`, `prompt_style`, `api_key_env`.
3. Implement `generate()` — return errors in the dict, never raise.
4. Register via `register_generation_provider()` or append to `ADAPTER_CLASSES`.

### Add a new asset type

```python
from services.asset_generation import register_asset_type
register_asset_type({
    "type_id": "spatial_scene",
    "label": "Spatial Scene",
    "asset_class": "three_d",
    "default_aspect_ratio": "1:1",
    "default_resolution": "2048x2048",
})
```

### Add a new style pack

```python
from services.asset_generation import register_style_pack
register_style_pack({
    "style_id": "retro_futurism",
    "prompt_fragment": "retro-futurist, chrome surfaces, warm tungsten glow",
    "negative_fragment": "modern flat design",
})
```

---

## Tests

`tests/test_asset_generation.py` — 20+ tests covering:

- Engine contract and registration
- Asset type catalog
- Prompt compilation and provider dialect optimization
- Provider selection strategies
- Full AssetPackage generation
- Cache reuse and fingerprint determinism
- Safety blocking
- Provider fallback chain
- Slot ownership (no mutation of other agents' fields)
- Orchestrator stage integration
- Asset registry versioning

Run: `python3 -m pytest tests/test_asset_generation.py -v`

---

## Remaining Roadmap

1. **Real provider implementations** — wire API calls in adapter stubs (OpenAI, Runway, Flux, etc.)
2. **Creative Studio stage integration** — schedule `creative` before `asset_generation` in full pipeline
3. **Render Engine handoff** — teach Render to prefer `asset_package.assets` over placeholder resolution
4. **Batch generation** — parallel job queue for large campaigns
5. **Asset collections UI** — browse brand libraries and reusable assets
6. **Video frame consistency** — temporal consistency across clip sequences
7. **3D pipeline** — mesh export, material baking, rig validation
8. **Autonomous campaigns** — generate entire marketing libraries from one brief
