# AI Cinematic Director

Intelligent directing layer between **script** and **renderer**.

Does **not** create a new rendering engine. Does **not** duplicate animation systems.

Reuses:

- `services.cinematography`
- `services.visual`
- `services.ai_director` (when present on candidate)
- Existing `engines.cinematography` pipeline stage
- Renderer fields: `camera_motion`, `zoom`, `motion_intensity`, `lighting`, `transition`, `shot_composition`

## Package contents

`cinematic_direction_package` includes:

- Shot list  
- Camera plan  
- Timing  
- Motion plan (+ movement scores)  
- Lighting  
- Color palette (science / biology / history / psychology / finance / nature / technology)  
- Transition plan  
- Emotional pacing (retention-heuristic intensities — labeled as predictions)  
- Director notes  
- Validation gate  

## Commands

```bash
python scripts/cinematic_director.py palettes

python scripts/cinematic_director.py direct \
  --topic "Why Octopuses Have Three Hearts" \
  --niche biology \
  --script "Stop. An octopus has three hearts..."

python scripts/cinematic_director.py validate path/to/CINEMATIC_DIRECTION_PACKAGE.json
```

## How it reaches the renderer

1. `build_cinematic_direction_package` / `direct_candidate`
2. Scenes written into `visual_package.scenes` with renderer-known keys
3. Existing cinematography plan / animation handoff still attached
4. `engines.render` / studio render consume those fields — no second compositor

## Validation rejects

- Static shots longer than ~4.5s  
- Identical camera moves in a row  
- Flat emotional pacing  
- Weak opening (first 3 seconds)  
- Overall low movement score  

Auto-fix runs once when validation fails.
