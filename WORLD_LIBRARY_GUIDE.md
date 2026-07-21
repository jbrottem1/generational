# World Library Guide

## Storage

```
data/world_builder/library/
  LIBRARY_INDEX.json
  USAGE_HISTORY.json
  WORLD-*.json
```

Templates seed from `services/world_builder/catalog.py` via `seed` / first package build.

## Operations

| Action | API / CLI |
|---|---|
| Seed templates | `seed_library_from_catalog()` / `world_builder.py seed` |
| Search | `search_worlds(query)` / `search "..."` |
| Select best | `select_best_world(...)` / `select --topic` |
| Inspect | `get_library_world(id)` / `inspect` |
| Save custom | `save_world(world)` |
| Variation | `create_world_variation(base_id, ...)` |
| Extend zone | `extend_world(id, zone=...)` / `extend` |
| Usage history | `usage` CLI |

## Selection signals

Semantic topic overlap, location type, time period, scientific/historical accuracy, audience, channel identity, reuse frequency (light penalty for overuse), continuity via `existing_world_id`.

Returns: best world, alternatives, reasoning, reuse score, continuity compatibility, required adaptations.

## Avoid rebuilds

If a production continues a location, pass `existing_world_id`. Prefer library hits over inventing a new set.
