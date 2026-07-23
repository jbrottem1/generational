# Evidence & Visual Intelligence Engine

**Status:** Production  
**Engine key:** `evidence_intelligence`  
**Service:** `services/evidence_intelligence/`

Every educational video gathers accurate, high-quality visual evidence **before** Visual Intelligence / Scene Builder.

Real photographs, scientific diagrams, satellite imagery, museum artifacts, and open-license collections are preferred over AI-generated artwork.

---

## Pipeline position

```
script_generation → attention_graph → evidence_intelligence → visual_intelligence → …
```

Does **not** replace Visual Intelligence, Scene Planning, or Reality/Atlas — it enriches them.

---

## Trusted sources (priority)

NASA · NOAA · USGS · NIH · CDC · WHO · PubMed · Google Scholar · Wikimedia Commons · Library of Congress · Smithsonian · National Park Service · ESA · Government agencies · University repositories · Official media kits · Open-license collections · Reality Catalog · Knowledge Atlas

Live gather currently searches the **Reality Catalog** + **Knowledge Atlas** first (local authentic corpus), ranked by `services/quality/visual_priority.py`.

---

## Per-scene decisions

| Question | Field |
|----------|-------|
| Real image available? | `modality.real_image_available` |
| Video footage available? | `modality.video_footage_available` |
| Diagram more effective? | `modality.diagram_preferred` |
| Animation required? | `modality.animation_required` |
| 3D visualization required? | `modality.visualization_3d_required` |
| AI only as fallback? | `modality.ai_generation_fallback_only` |

---

## Per-scene output

- Evidence Confidence  
- Image Source  
- License Status  
- Visual Type  
- Recommended Camera Motion  
- Suggested Zooms  
- Highlight Regions  
- Callout Targets  
- Annotation Locations  

### Annotations (V2 rules)

Every annotation requires:

1. Semantic `target` (`keyword:…` / `panel:…`)  
2. `narration_cue` matching spoken teaching content  
3. Timed window with fade in/out  

Kinds: label · arrow · circle · bracket · measurement · timeline · comparison overlay · highlight  

Max 4 per scene. Annotations disappear after their teaching window (`end_sec`).

**Never** random decorative arrows/circles.

---

## Scene Builder handoff

```json
{
  "image": { "...EvidenceHit..." },
  "motion_plan": { "camera_motion": "ken_burns_in", "suggested_zooms": [] },
  "annotation_plan": [],
  "narration_timing": { "start_sec": 0, "end_sec": 5 },
  "transition_type": "crossfade",
  "expected_attention_score": 72
}
```

Attached on each candidate as:

- `evidence_package`  
- `scene_builder_plans`  
- `atlas_asset_ids` / `reality_image_ids`  

Visual Intelligence binds these onto `visual_package.scenes` (`asset_type=atlas_image` when authentic).

---

## Usage

```python
from services.evidence_intelligence import build_evidence_package, scene_builder_payload

pkg = build_evidence_package(candidate, topic="How cameras are made", domain="science")
for scene in pkg.scenes:
    print(scene_builder_payload(scene))
```

```bash
./venv/bin/python -m pytest tests/test_evidence_intelligence.py -q
./venv/bin/python scripts/verify_evidence_intelligence.py
```

---

## Files

| Path | Role |
|------|------|
| `services/evidence_intelligence/models.py` | Contracts |
| `services/evidence_intelligence/gather.py` | Search + modality + annotations + motion |
| `services/evidence_intelligence/bind.py` | VI / Scene Builder binding |
| `engines/evidence_intelligence.py` | Pipeline adapter |
