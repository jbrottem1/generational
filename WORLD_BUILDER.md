# World Builder — Persistent World & Environment System

Reusable environments for Generational. **Not** a renderer, Scene Builder, or Cinematic Director.

## Ownership boundaries

| System | Owns |
|---|---|
| **Scene Builder** | What happens, subjects, actions, information, approximate duration |
| **World Builder** | Where scenes happen, persistent environments, objects, spatial continuity, location connections |
| **Asset Intelligence** | Media search, cache, scoring (World only *requests/references*) |
| **AI Cinematic Director** | Camera, framing, lighting *treatment*, motion, emotional pacing, edit transitions |
| **Sound design** | Final mix (World supplies ambience *labels* only) |
| **Renderer** | Technical render of approved Environment + Cinematic packages |

World Builder must **not** prescribe final camera movement, framing, lighting treatment, or editing transitions.

## Pipeline placement

```
Research → Psychology → Studio → Script → Scene Builder
  → World Builder → Media/Asset Resolution → Narration
  → AI Cinematic Director → Rendering → QA → CPL → Publishing
```

World **enriches** the scene package. Renderer receives **both**:

- `environment_package` / `environment_packages` (this system)
- `cinematic_direction_package` (separate, untouched)

## Location

```
services/world_builder/
  models.py catalog.py library.py state.py
  environment.py package.py assets.py validate.py
scripts/world_builder.py
data/world_builder/library/ packages/ state/
```

See also: `WORLD_PACKAGE_SCHEMA.md`, `WORLD_CONTINUITY_GUIDE.md`, `WORLD_LIBRARY_GUIDE.md`, `WORLD_BUILDER_TROUBLESHOOTING.md`.

## CLI

```bash
python scripts/world_builder.py seed
python scripts/world_builder.py list
python scripts/world_builder.py search "octopus ocean"
python scripts/world_builder.py inspect "Ocean Research Observatory"
python scripts/world_builder.py preview WORLD-AI_LABORATORY
python scripts/world_builder.py select --topic "Why Octopuses Have Three Hearts"
python scripts/world_builder.py package --topic "Why Octopuses Have Three Hearts" \
  --world-type "Ocean Research Observatory" --scenes 3 --platform youtube_shorts
python scripts/world_builder.py validate data/world_builder/packages/<file>.json
python scripts/world_builder.py validate-continuity <package.json>
python scripts/world_builder.py state --world-id WORLD-AI_LABORATORY --production-id demo
python scripts/world_builder.py reset-state --world-id WORLD-AI_LABORATORY --production-id demo
python scripts/world_builder.py extend --world-id WORLD-AI_LABORATORY --zone-id annex
python scripts/world_builder.py usage
```

## Python

```python
from services.world_builder import (
    fulfill_world_request,
    place_candidate_in_world,
    empty_world_request,
)

req = empty_world_request(
    topic="Why Octopuses Have Three Hearts",
    location_type="Ocean Research Observatory",
    platform="youtube_shorts",
    audience="general_public",
)
pkg = fulfill_world_request(req, scene_count=3, production_id="octopus_three_hearts")
candidate = place_candidate_in_world(candidate, world_type="AI Laboratory")
```

## Mission success criteria

- Reusable persistent environments
- Spatial/object continuity across scenes
- World reuse across productions
- Structured Environment Packages for the existing pipeline
- Strict separation from Scene Builder and Cinematic Director
- Reject inconsistent/inaccurate states
- Coherent environments — not disconnected backgrounds
