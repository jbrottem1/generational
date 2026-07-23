# Automation Hooks — Dash Science

Goal: produce thousands of recognizable Shorts without reinventing style.

## Pipeline mapping (no Orchestrator redesign)

| Stage | Existing system | Dash extension |
|---|---|---|
| Idea / Script | Script engine / asset production | Topic → `episode_package` using SERIES_BIBLE voice |
| Visual plan | Visual Story Plan | Force `character_id=CHAR-DASH` + ANIM component IDs per scene |
| Image gen | Asset generation | Append `prompt_lock.json` positive/negative locks |
| Motion | FFmpeg multi-scene + MotionPlanner | Prefer component tags as effect hints (`walk`, `punch_in`, etc.) |
| Voice / captions / music | Existing media stages | Voice direction from package |
| QC | Production QC | Add Dash gates from `production_schema.json` |
| Export | final_export | Unchanged |

## Episode factory loop

1. Pick topic + scientific sources  
2. Instantiate `episode_template`  
3. Write script (hook ≤2.5s)  
4. Break into scenes ≤4s each  
5. Assign `dash_animation` from `ANIM-DASH-V1` only  
6. Generate frames with prompt lock  
7. Assemble + QC gates  
8. Register reusable props/FX back into `registry.json`  

## Consistency gates (fail = reject)

- Dash proportions match `design_spec.json`  
- No clothing/hair/color fill on Dash  
- Static frame ≤3s  
- Beat change every 2–4s  
- Background not flat solid full-frame  
