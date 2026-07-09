# Generational — Capability Matrix (v9.6)

Maps **what the OS can do** (capability tags) to **who does it** (engine
keys) and **which department** owns it. The live index is
`engines.registry.capability_index()`; full tag list in
`ENGINE_CAPABILITY_INDEX.md`. Agent roster: `AGENT_REGISTRY.md`.

Capability tags are declared on `ContractEngine` subclasses via the
`capabilities` list — discovery is automatic at registration time.

---

## Matrix by department

| Department | Capability domain | Example tags | Engine keys |
|---|---|---|---|
| **Foundation** | Trend & opportunity discovery | `trend`, `forecasting`, `opportunity-scoring` | `trend_discovery`, `opportunity_ranking`, `trend_forecasting` |
| **Foundation** | Market strategy | `market-intelligence`, `roi`, `roadmap` | `market_intelligence` |
| **Foundation** | Psychology & attention | `psychology`, `virality`, `attention` | `psychology`, `attention_graph`, `threat_detection` |
| **Foundation** | Script & story | `script`, `storytelling`, `critique` | `script_generation`, `script`, `critic`, `revision` |
| **Foundation** | Visual & audio planning | `visual`, `cinematic`, `audio`, `voice` | `visual_intelligence`, `voice_audio` |
| **Production** | Media assembly | `scene-planning`, `timeline`, `subtitles` | `scene_planning` … `render_package` |
| **Production** | Render & video | `render`, `timeline`, `captions`, `mock-render` | `render`, `image`, `video` |
| **Production** | SEO & localization | `seo`, `multi-language`, `localization` | `seo_optimization` |
| **Production** | Publishing | `publishing`, `scheduling`, `multi-platform` | `scheduler`, `publishing` |
| **Intelligence** | Analytics & learning | `analytics`, `learning`, `attribution` | `analytics`, `learning` |
| **Intelligence** | Creative design | `creative`, `storyboard`, `style` | `creative_studio` **LIVE** |
| **Intelligence** | Optimization lab | `experimentation`, `ab-testing` | `optimization_lab` *(stub — Agent 13)* |
| **Media Gen** | Asset generation | `asset-generation`, `image-gen`, `video-gen` | `asset_generation` **LIVE** |
| **Media Gen** | IP & universes | `characters`, `universes`, `continuity` | `character_universe` *(stub — Agent 15)* |
| **Media Gen** | Animation | `animation-planning`, `cinematics`, `lip-sync` | `animation` *(stub — Agent 16)* |
| **Media Gen** | Post-production | `editing`, `color`, `captions`, `exports` | `post_production` **LIVE** |

---

## Cross-cutting capabilities

| Tag | Engines | Purpose |
|---|---|---|
| `quality-gate` | `quality`, `citation`, `threat_detection` | Safety boundary before distribution |
| `research` | `research`, `citation` | Source-backed content |
| `multi-platform` | `seo_optimization`, `publishing` | Per-platform formatting |
| `mock-render` / demo modes | `render`, `publishing`, `analytics` | Provider-swappable stubs until live APIs land |

---

## Adding a capability

1. Append the tag to your engine's `capabilities` list (no central file edit).
2. Run `python3 -m pytest tests/test_architecture.py` — the index test
   verifies every listed engine key is registered.
3. Regenerate `ENGINE_CAPABILITY_INDEX.md` (or let Agent 1 refresh on the
   next architecture review).
