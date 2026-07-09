# Universal Asset Generation Engine (Agent 14)

The generation department of the Generational AI Media Operating System.
Every image, illustration, animation frame, background, character sheet,
concept art, thumbnail, texture, icon, logo, scene still, video clip, and
future media asset the platform uses originates here.

**Engine key:** `asset_generation`  
**Pipeline stage:** `asset_generation` (distribution — runs after packaging, before render)  
**ContentPackage slot:** `asset_package`  
**Engine version:** `1.1.0` (Phase 2 production hardening)

---

## Mission

Transform structured creative requests into production-ready assets using
the best available AI providers. The engine does **not** plan content,
write scripts, or apply psychology — it consumes upstream outputs and
generates assets.

---

## Phase 2 — Production Hardening

Phase 2 extends Phase 1 without redesigning the engine:

| Capability | Module | Notes |
|---|---|---|
| Provider catalog | `providers/asset_generation/` | `provider_catalog()`, `providers_for_class()`, `providers_by_capability()` |
| Latency-aware selection | `selection.py` | `latency_ms` in profiles; new `latency` strategy |
| Retry + fallback | `generator.py` | Per-provider retries; ordered fallback ending in mock |
| Asset caching | `cache.py` | Content-address fingerprints (unchanged, hardened) |
| Job queue | `queue.py` | `asset_generate` / `asset_batch` / `asset_package` on `core.jobs` |
| Batch generation | `batch.py` | `batch_generate()` with optional concurrency |
| Usage tracking | `usage.py` | Append-only `data/asset_generation/usage.json` |
| Asset metadata | `metadata.py` | `ASSET_METADATA_FIELDS` on every asset |
| Extended media | catalog + adapters | `animation`, `audio`, `motion_graphics` prepared |

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
                                   audio_assets / animation_assets
```

| Layer | Location | Role |
|---|---|---|
| Engine | `engines/asset_generation.py` | Thin pipeline adapter (`run(context) → dict`) |
| Service | `services/asset_generation/` | Prompt compilation, selection, generation, QC, registry, batch, queue, usage |
| Providers | `providers/generation_provider.py` + `providers/asset_generation/` | Swappable AI backends |

---

## Provider Architecture

Every backend implements `GenerationProvider` (`providers/generation_provider.py`):

- `supports(asset_class, asset_type)` — coverage declaration
- `generate(prompt_spec, request)` — returns `{uri, provider, format, width, height, ...}` or `{error}`
- `profile` — quality, cost_per_asset, speed, consistency, **latency_ms**
- `describe()` — uniform self-description for the registry catalog
- `prompt_style` — dialect hints for the Prompt Compiler
- `offline` / `local` — routing for offline and local-model support
- `capabilities` — discovery tags (image-gen, video-gen, sfx, …)

**Media classes** (additive): `image` · `video` · `three_d` · `animation` · `audio` · `motion_graphics`

**Shipped adapters** (stubs until API keys are configured — no live calls):

| Adapter | Classes | Notes |
|---|---|---|
| `openai_images` | image | OpenAI gpt-image |
| `google_imagen` | image | Google Imagen |
| `flux` | image | Black Forest Labs |
| `stable_diffusion` | image | Stability API |
| `midjourney` | image | **Placeholder** — no public API |
| `adobe_firefly` | image | Adobe Firefly |
| `google_veo` | video, animation | Google Veo |
| `runway` | video, animation, motion_graphics | Runway |
| `kling` | video, animation | Kling |
| `luma` | video, three_d, animation | Luma Dream Machine |
| `pika` | video, animation, motion_graphics | Pika |
| `elevenlabs_audio` | audio | Prepared for SFX / music / voice |
| `motion_graphics_stub` | motion_graphics | Prepared kinetic-typography backend |
| `local_diffusion` | image | Offline / local endpoint |
| `mock_generation` | all | Deterministic Demo Mode fallback |

```python
from providers.asset_generation import register_generation_provider, provider_catalog
register_generation_provider(MyCustomProvider())
provider_catalog()   # [{name, available, profile, latency_ms, ...}, ...]
```

No engine code changes when a backend swaps in.

---

## Provider Selection Engine

`services/asset_generation/selection.py` scores candidates deterministically
on **asset type/class**, **quality**, **cost**, **speed**, **consistency**,
**latency**, and **availability**:

| Strategy | Optimizes for |
|---|---|
| `balanced` | Quality + cost + speed + consistency + latency (default) |
| `quality` | Highest output quality |
| `cost` | Lowest cost per asset |
| `speed` | Fastest generation |
| `consistency` | Character/style reproducibility |
| `latency` | Lowest end-to-end latency |

Output: `{primary, fallbacks, strategy, candidates}` — the fallback chain
always ends in the offline mock so generation never dead-ends.

```python
from services.asset_generation import configure
configure(selection_strategy="latency", max_cost_per_package=10.0, batch_concurrency=4)
```

---

## Prompt Compiler

Two-pass, deterministic compilation (`services/asset_generation/prompts.py`):

1. **`compile_prompt(request, item)`** — canonical, provider-agnostic
   `PROMPT_SPEC_FIELDS` dict.
2. **`optimize_for_provider(spec, provider)`** — rewrites for the target
   backend's dialect. Provider dialects come from adapters only.

---

## Asset Lifecycle

```
Request collection → Safety gate → Cache lookup → Provider selection
  → Prompt compilation → Generation (retries + fallback chain)
  → Quality analysis → Metadata → Registry write → Usage event
  → AssetPackage assembly
```

### Cache

Content-address fingerprints — identical requests never generate twice.

### Metadata

Every asset carries `ASSET_METADATA_FIELDS`: title, description, tags,
brand_id, style, character_ids, source, license, mime_type, file_size_bytes, extra.

### Usage tracking

Append-only events in `data/asset_generation/usage.json`. Packages include
a `usage_report` summary.

---

## Batch Generation & Job Queue

```python
from services.asset_generation import batch_generate, submit_generate, run_generate

batch_generate([req_a, req_b, req_c])
run_generate(request)          # submit + sync execute
submit_generate(request)       # enqueue only
submit_batch(requests)
submit_package(item)
```

Job types: `asset_generate` · `asset_batch` · `asset_package`.

---

## Supported Asset Types

40+ catalog types plus Phase 2: character animation, motion graphic, title
card, sound effect, music bed, voice clip. Expand via `register_asset_type()`.

---

## Configuration

| Key | Default | Purpose |
|---|---|---|
| `selection_strategy` | `balanced` | Provider scoring strategy |
| `provider_priority` | `{}` | Per-class provider ordering override |
| `max_cost_per_asset` | `2.0` | USD limit per asset |
| `max_cost_per_package` | `25.0` | USD limit per ContentPackage |
| `max_retries` | `2` | Attempts per provider |
| `cache_enabled` | `true` | Content-address cache |
| `batch_concurrency` | `4` | Parallel workers for batch_generate |
| `usage_tracking_enabled` | `true` | Persist usage events |

---

## Extension Guide

1. Subclass `GenerationProvider` / `_StubAdapter` in adapters.
2. Declare `asset_classes`, `profile` (include `latency_ms`), `prompt_style`.
3. Implement `generate()` — return errors in the dict, never raise.
4. Append to `ADAPTER_CLASSES` or call `register_generation_provider()`.

---

## Tests

`tests/test_asset_generation.py` — 30+ tests. Run:

```bash
python3 -m pytest tests/test_asset_generation.py -v
```

---

## Remaining Roadmap

1. Wire real API calls in adapter stubs (OpenAI, Runway, Flux, etc.)
2. Schedule Creative Studio before asset generation in the full pipeline
3. Teach Render to prefer `asset_package.assets` URIs
4. Background workers draining `core.jobs` asynchronously
5. Asset collections UI
6. Temporal video consistency
7. 3D export / material / rig validation
8. Live audio provider implementations
9. Autonomous campaign generation from one brief
