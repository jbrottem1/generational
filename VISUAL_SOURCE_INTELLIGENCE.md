# Visual Source Intelligence

**Status:** Production  
**Service:** `services/visual_source_intelligence/`  
**CLI:** `scripts/visual_source_intelligence.py`

Selects the strongest available visual source for every scene **before** media fulfilment and render. Does not create a renderer. Does not redesign the production pipeline.

---

## Pipeline position

```
Scene Builder
      ↓
World placement (soft)
      ↓
Visual Source Intelligence   ← choose source + regenerate asset_requests
      ↓
Media Collection (fulfil)
      ↓
Visual Asset Director (QC)
      ↓
Cinematic Director → Renderer → Export
      ↓
Creative review snapshot (after rendering, no auto-rebuild)
```

Soft ops hooks in `services/production_operations/orchestrator.py`:

1. After `scene_builder` — build + attach VSI package  
2. After `rendering` — creative review answers (weakest scene identified, not rebuilt)

Failures never block production ops.

---

## Per-scene planning

For each scene VSI records:

1. **Viewer understanding** — what the beat must teach  
2. **Ideal visual** — what best communicates that idea  
3. **Selected source** — best available option + fallback reason  

## Fallback ladder

When the ideal asset is missing, choose the next best option:

1. Licensed / library stock video  
2. AI-generated video  
3. Animated diagrams / motion graphics  
4. AI stills with meaningful (non-repeating) motion  
5. Static images only as a last resort  

Higher ladder tiers that are unavailable are skipped with an explicit `fallback_reason`.

## Reject rules

Options can be down-ranked for:

- Slideshow feel  
- Repeated identical camera motion  
- Failing to explain narration  
- Obvious placeholders (`mock://`, cinematic fallback)  
- Lack of cinematic interest  

## Package

Written to `data/visual_source_intelligence/packages/*_VSI.json` (+ `.md` review).

Soft-attach fields on the candidate:

- `visual_source_intelligence` / `VISUAL_SOURCE_INTELLIGENCE`  
- `visual_package.scenes[]` enriched with `vsi_*`, `asset_type`, motion, optional `approved_asset_path`  
- `visual_package.asset_requests[]` rebuilt via existing `services.visual.sources.build_asset_requests`  
- Requests may carry `resolved_path` for the existing `StockFootageFulfiller`  

## Creative review (before export)

Answers:

- Does every scene visually explain the narration?  
- Would a human editor keep this shot?  
- Is the opening visually compelling?  
- Does the visual quality justify publishing?  

If not, identifies the **weakest scene**. Does **not** auto-rebuild.

## CLI

```bash
./venv/bin/python scripts/visual_source_intelligence.py selftest
./venv/bin/python scripts/visual_source_intelligence.py plan --topic "Why Fire Hydrants Are Different Colors"
```

## Compose only

| System | Role |
|--------|------|
| Visual Intelligence | Scene plans + adapter keys |
| Asset Intelligence | Library pool for stock/video hits |
| Evidence Intelligence | Authentic catalog paths |
| World Builder | Reusable world assets |
| Visual Asset Director | QC after fulfilment |
| StockFootageFulfiller | Honors `resolved_path` when VSI attaches a real file |
| Renderer | Unchanged |
