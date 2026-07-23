# Environment Animation

**Owner:** Animation Director (Agent 16) · Worlds: Agent 15 · Assets: Agent 14  
**Rule:** Every world feels alive — backgrounds are not posters.

---

## Always-on life layers (pick ≥2 per scene)

Clouds · Trees · Grass · Water · Smoke · Fire · Dust · Particles · Fog · Animals · Machines · Lights · Weather · Ocean currents · Stars · Planets · Lab instruments · Computer screens · Scientific instruments

---

## Environment FX catalog (seed)

| ID | Effect | Loop | Notes |
|---|---|---|---|
| `ENVFX-clouds-drift` | Clouds | yes | Slow parallax |
| `ENVFX-tree-sway` | Trees | yes | Soft wind |
| `ENVFX-grass-ripple` | Grass | yes | Foreground life |
| `ENVFX-water-caustics` | Water | yes | Ocean / lab tanks |
| `ENVFX-smoke-rise` | Smoke | yes | Soft, non-toxic look |
| `ENVFX-fire-flicker` | Fire | yes | Practical light sync |
| `ENVFX-dust-motes` | Dust | yes | Volume light |
| `ENVFX-particle-field` | Particles | yes | Science sparkle / bio glow |
| `ENVFX-fog-roll` | Fog | yes | Depth planes |
| `ENVFX-animal-idle` | Animals | yes | Silhouette life |
| `ENVFX-machine-hum` | Machines | yes | Lab / factory |
| `ENVFX-light-pulse` | Lights | yes | Screens, LEDs, glow |
| `ENVFX-weather-rain` | Weather | optional | Mood |
| `ENVFX-ocean-current` | Currents | yes | Dash ocean worlds |
| `ENVFX-star-twinkle` | Stars | yes | Space / night |
| `ENVFX-planet-spin` | Planets | slow | Establishing |
| `ENVFX-lab-screens` | Screens | yes | Data flicker |
| `ENVFX-instrument-glow` | Instruments | yes | Practical science light |

Register new FX in `library/registry.json` after first successful use.

---

## Scene minimum

Each storyboard beat must list `environment_fx: []` with at least one living layer unless intentionally abstract void (rare; Animation Director approval).
