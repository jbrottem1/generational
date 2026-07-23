# Generational Version 2 — Creative Quality Initiative

Architecture is **frozen**. No new engines. No pipeline redesign. No duplicate systems.

The production pipeline exists. V2 raises the creative quality of every exported video so viewers **want** to watch — not merely can play a file.

## What V2 measures (every production)

| Craft score | Purpose |
|---|---|
| Visual quality | Depth, fidelity, world richness |
| Motion quality | Motivated camera + layered motion |
| Storytelling | Hook → complication → payoff |
| Educational clarity | One claim per beat, readable |
| Hook | 0–3s scroll-stop |
| Viewer retention | Finish probability |
| Audio quality | Human narration + mix |
| Overall professionalism | Documentary polish |

Plus existing Creative Excellence dimensions (curiosity, emotional impact, shareability…).

**Rule:** after every production, identify **exactly ONE** highest-impact improvement.  
**Do not automatically rebuild.**

## Visual standard

Aim for **educational documentary**, not automated slideshow:

- Layered FG/BG motion  
- Cinematic depth + motivated lighting  
- Persistent worlds (World Builder)  
- Motivated camera (Cinematic Director)  
- Environmental ambience + effects language  

## Where quality is improved (existing systems only)

| Lever | Existing system |
|---|---|
| Lighting bias toward documentary/scientific depth | `services/cinematic_director/intensity.py` |
| Stronger Ken Burns / pan drift (no still locks) | `services/media_production/ffmpeg_assembler.py` |
| Layered environment + ambient activity in scene backgrounds | `services/world_builder/package.py` |
| V2 craft scorecard + single recommendation | `services/creative_excellence/` |

## Commands

```bash
# Review any finished production report
python scripts/run_creative_excellence_review.py \
  --report data/productions/_ops/<id>/PRODUCTION_REPORT.json \
  --topic "Why Octopuses Have Three Hearts"

# Flagship / gold-standard baseline
python scripts/run_creative_excellence_review.py --gold-standard
```

Wired softly at the end of `run_studio_ops` (already present).

## API

```python
from services.creative_excellence import review_production_creative_excellence

result = review_production_creative_excellence(candidate, production_report=report, production_id="…")
print(result["scorecard"]["v2_quality"]["scores"])
print(result["single_recommendation"])  # exactly one
```

## Success

Measured by **rising V2 craft / Creative Excellence scores** on completed exports — not by adding systems.
