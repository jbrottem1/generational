# World Continuity Guide

## Goal

The same location must remain recognizable across scenes when viewed from different zones or later framed by the Cinematic Director.

## What stays stable

- `world_id` and world version
- Architecture / spatial map
- Persistent prop ids and default positions
- Scale, era, scientific/historical constraints
- Environmental identity (e.g. aquarium viewport remains the aquarium viewport)

## What may change (via state events)

| Event | Effect |
|---|---|
| `door_toggled` | Door open/closed |
| `object_moved` | Position + required `reason` |
| `display_activated` | Screen/holo content |
| `equipment_introduced` | New object enters state |
| `weather_changed` / `time_advanced` | Environment clock |
| `character_entered` / `exited` | Presence + visited zones |
| `experiment_progressed` | Lab progress flags |
| `reset` | Clear production state |

Later scenes **inherit** state unless the script resets it.

## Example — AI Laboratory

1. Scene 1: talent beside `obj_neural_holo` in `holo_stage`
2. Scene 2: talent at `workstation`; holo remains at prior coordinates
3. Scene 3: view from `server_aisle`; landmarks stay spatially believable

## Example — Ocean Research Observatory

Zones cycle:

`observation_chamber` → `underwater_viewing` → `scientific_display`

Aquarium viewport and heart display keep stable object ids across the cut list.

## Validation

Hard failures include: unexplained object moves, lost world identity, floating props, impossible zone ids, inconsistent scale, cinematic prescriptions leaking into Environment Packages.

Same-zone multi-scene reuse is **allowed** (continuity). Empty/meaningless backgrounds are not.
