# Visual Asset Director

**Status:** Production  
**Service:** `services/visual_asset_director/`  
**CLI:** `scripts/visual_asset_director.py`

Quality-control layer that evaluates, selects, rejects, and prepares visual assets **before** they reach the AI Cinematic Director and existing renderer.

Does **not** build a renderer. Does **not** duplicate Scene Builder. Does **not** replace the Cinematic Director.

---

## Pipeline position

```
Scene Builder
      ↓
Visual Asset Director   ← approve / reject / continuity / style
      ↓
AI Cinematic Director
      ↓
Renderer
```

Soft ops hook: after `media_collection`, before `animation` (cinematography). Failure never blocks production ops.

---

## Responsibilities

- Evaluate every image/video candidate (resolution, blur, contrast, aspect, framing, clutter, watermarks, stock/AI heuristics)
- Select the strongest candidate per scene
- Reject poor-quality assets (with reason codes)
- Maintain continuity (palette, environment, character refs, style)
- Prepare approved assets for cinematic rendering (`approved_asset_path`, scorecards, `cinematic_ready`)

---

## Style library

`documentary` · `pixar_inspired_3d` · `scientific_illustration` · `photorealistic` · `cinematic_film` · `animated_educational` · `museum_display` · `historical_recreation` · `futuristic` · `medical_visualization`

```bash
python scripts/visual_asset_director.py styles
```

---

## VISUAL_PACKAGE.json

Includes: approved assets · rejected assets · rejection reasons · visual scorecards · continuity report · style profile · thumbnail candidate · character/environment references · asset manifest.

Written to `data/visual_asset_director/packages/` (and optionally project `Assets/VISUAL_PACKAGE.json`).

---

## Visual scorecard (per scene)

Resolution · Lighting · Composition · Continuity · Character Consistency · Environment Consistency · Educational Clarity · Motion Potential · Thumbnail Appeal · Overall Professional Quality

Composition sub-scores: Rule of Thirds · Subject clarity · Eye direction · Leading lines · Depth · Layering · Background separation · Visual hierarchy · Negative space · Educational clarity

---

## Integration (compose only)

| System | Role |
|--------|------|
| Scene Builder | Scene purpose / subjects / beats |
| World Builder | Environment + world continuity refs |
| Asset Intelligence | Library search / pool (not reimplemented) |
| AI Cinematic Director | Camera / lighting / motion after assets approved |
| Audience Intelligence / CPL | Soft style & lesson context when present |
| Renderer | Unchanged — consumes approved paths when attached |

Soft attach: `attach_visual_package_to_candidate()` — never overwrites cinematic camera/lighting or world placement ownership fields.

---

## CLI

```bash
python scripts/visual_asset_director.py evaluate path/to/frame.png --style documentary
python scripts/visual_asset_director.py direct \
  --topic "Why Octopuses Have Three Hearts" \
  --niche biology \
  --style documentary \
  --scenes-dir "~/Desktop/AI Start-UP/Videos/Shorts/Science/Biology/Why Octopuses Have Three Hearts/Assets/scenes" \
  --world-json ".../Assets/WORLD_PACKAGE.json" \
  --out ".../Assets/VISUAL_PACKAGE.json"
python scripts/visual_asset_director.py compare --scenes-dir ".../Assets/scenes" --topic "Why Octopuses Have Three Hearts"
python scripts/visual_asset_director.py validate path/to/VISUAL_PACKAGE.json
```

---

## Files

| Path | Role |
|------|------|
| `models.py` | Styles, reject codes, thresholds |
| `inspect.py` | PIL heuristics (blur, contrast, aspect, watermark risk) |
| `composition.py` | Composition scoring |
| `continuity.py` | Cross-scene continuity report |
| `scorecard.py` | Per-scene scorecard |
| `styles.py` | Style profile resolution |
| `director.py` | Select / reject / direct |
| `package.py` | Persist + attach VISUAL_PACKAGE |

```bash
./venv/bin/python -m pytest tests/test_visual_asset_director.py -q
```
