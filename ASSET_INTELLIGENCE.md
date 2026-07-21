# Universal Asset Intelligence

Intelligent asset selection for Generational — **not** a new rendering engine.

Feeds the existing production pipeline with the best available media via library index, semantic search, quality ranking, duplicate prevention, cache reuse, niche collections, and validated Asset Packages.

## What this is / is not

| Is | Is not |
|---|---|
| Library intelligence layer | Another rendering engine |
| Optional candidate enricher (`evidence_assets` / `visual_assets`) | A change to production pipeline stages |
| Composer over Reality, local_cache, Asset Generation | A duplicate media generator |

Architecture remains frozen. This layer **selects and scores**; the existing renderer still renders.

## Location

```
services/asset_intelligence/
  models.py      # kinds, collections, metadata/quality fields
  index.py       # LIBRARY_INDEX, usage log, collections, seed
  search.py      # semantic search + quality ranking + duplicate risk
  package.py     # Asset Package builder + validation + attach
  cache.py       # façades over local_cache + fingerprint cache
scripts/asset_intelligence.py
data/asset_intelligence/
```

## Supported asset kinds

Images, video clips, animations, 3D renders, charts, scientific diagrams, maps, background loops, particle effects, sound effects, music, icons, logos, educational graphics, lower thirds, transitions, overlays.

## Metadata (every asset)

Topic, keywords, category, scientific accuracy, visual quality, animation quality, resolution, orientation, duration, license, color palette, motion score, historical performance, reuse count, last usage, creator — plus URI, fingerprint, source system.

## Niche collections

Biology, Astronomy, Physics, History, Finance, Medicine, Technology, Nature, Psychology, Engineering.

## CLI

```bash
# Index existing Reality / cache / Asset Generation registries
python scripts/asset_intelligence.py seed

# Semantic search
python scripts/asset_intelligence.py search "DNA"
python scripts/asset_intelligence.py search "Space" --collection astronomy

# Build a production Asset Package
python scripts/asset_intelligence.py package --topic "Cell division" --keywords "biology,mitosis" --needed 6

# Validate a package file
python scripts/asset_intelligence.py validate data/asset_intelligence/packages/<file>.json

# Collection counts
python scripts/asset_intelligence.py collections
```

## Asset Package contents

- Selected media
- Backup choices
- Licensing information
- Quality scores (visual / educational / retention / motion / thumbnail / overall)
- Reuse analysis
- Visual diversity score
- `renderer_feed` for optional attach (`evidence_assets`, `visual_assets`)

## Validation rejects packages that

- Contain duplicate asset IDs
- Include low-resolution media
- Include poor animation quality (for animated kinds)
- Repeat the same topic excessively
- Fail visual diversity thresholds

## Python API

```python
from services.asset_intelligence import (
    seed_from_existing_sources,
    semantic_search,
    build_asset_intelligence_package,
    attach_package_to_candidate,
    validate_asset_intelligence_package,
)

seed_from_existing_sources()
hits = semantic_search("Psychology", limit=8)
pkg = build_asset_intelligence_package(topic="Confirmation bias", keywords=["psychology"])
candidate = attach_package_to_candidate(candidate, pkg)  # optional — does not edit pipeline ops
```

## Cache

`prefer_cached_media` / `resolve_cached_uri` / `resolve_fingerprint_cache` only **resolve** hits in `services.media_production.local_cache` and `services.asset_generation.cache` — they never regenerate identical media.

## Success criterion

Every new production can pull a smarter, richer, non-duplicative media set from a growing reusable AI media library — without a second render stack.
