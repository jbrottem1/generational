# Environment Package Schema

Version: `2.0.0` (`package_type: environment`)

Produced by World Builder for **each scene**. Does **not** include cinematic prescriptions.

## Top-level fields

| Field | Description |
|---|---|
| `world_id` | Persistent world identity |
| `world_version` | Schema/version string |
| `environment_name` | Human name |
| `selected_zone` | Room/zone id for this scene |
| `spatial_layout` | Zone description, landmarks, entrances/exits, connections, scale |
| `required_persistent_objects` | Props with positions inherited from world state |
| `required_temporary_objects` | Scene-only props from the request |
| `background_activity` | Ambient motion labels |
| `environmental_ambience` | Labels handed to sound design (`handoff_to: sound_design`) |
| `scale` | Environmental scale model |
| `continuity_state` | Snapshot of doors, object positions, visited zones, displays |
| `scientific_constraints` / `historical_constraints` | Accuracy rails |
| `allowed_subject_positions` | Where talent/subjects may stand |
| `restricted_areas` | Forbidden volumes |
| `recommended_transition_destination` | Next zone id (spatial hint only — not an edit transition) |
| `asset_requirements` | Resolved/missing refs for Asset Intelligence |
| `aesthetic_context` | Palette/materials/era — **context**, not final grade |
| `cinematic_prescriptions` | Always `null` |
| `ownership` | Explicit system boundaries |
| `world_validation` | Hard failures / warnings for this package |

## Production package (`package_type: world_production`)

Wraps:

- `world` definition
- `environment_packages[]` (one per scene)
- `continuity` + `continuity_validation`
- `selection` (best/alternatives/reasoning)
- `renderer_feed` (environment only)
- `contracts` separating cinematic vs environment

## Request contract (Scene Builder → World)

`topic`, `scene_purpose`, `time_period`, `location_type`, `required_subjects`, `required_objects`, `required_actions`, scientific/historical constraints, `continuity_requirements`, `existing_world_id`, `platform`, `audience`, `channel`, `scene_id`.
