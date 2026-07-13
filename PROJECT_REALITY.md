# PROJECT REALITY — Real Image Integration System

**Status:** LOCKED — company standard for Foundation educational Shorts  
**Established:** 2026-07-12  
**Executive Sponsor:** Agent 0  
**Companion:** `PROJECT_FOUNDATION.md` · `GENERATIONAL_CURIOSITY_FRAMEWORK.md`

---

## Doctrine

The professor remains **animated**. The science becomes **real**.

Whenever a real photograph, microscope image, or scientific illustration improves understanding, display it alongside Professor Gen. The professor is the guide; reality is the evidence.

---

## Non-negotiables

| Rule | Detail |
|------|--------|
| License-first | Only public domain, CC0, CC-BY, or CC-BY-SA assets in `data/reality/catalog.json` |
| No runtime scrape | Curate locally; download once with attribution |
| Foundation preserved | White studio `(255,255,255)`; professor visible left; evidence panel in board region |
| Professor interacts | Point, present, and annotate — never ignore the image |
| Scientific accuracy | High resolution, relevant, verified organism labels |
| No clutter | Side panel, split compare, or evidence tray — one clear focal layout per beat |

---

## Educational flow

```
Curiosity question
  → Real image appears
  → Professor points
  → Key feature highlighted
  → Scientific explanation
  → Comparison (when applicable)
  → Takeaway + bridge
```

---

## Package layout

| Path | Role |
|------|------|
| `data/reality/catalog.json` | Licensed image registry |
| `data/reality/images/` | Local image files |
| `data/reality/ATTRIBUTION.md` | Credits and source URLs |
| `services/reality/` | Catalog, panel renderer, annotations, planner, QC |
| `scripts/fetch_reality_images.py` | One-time / refresh download helper |

---

## QC (Reality gate)

Before export verify:

- Image file exists and meets minimum resolution (≥400 px shortest side)
- License in allowlist
- Panel readable at 1080×1920
- Images synchronized to narration beats
- Foundation gate still passes (idle, walk, lipsync)

---

## Success condition

Viewers finish thinking: *"I've never looked at that before… now I understand exactly what I'm seeing."*

Animation makes the lesson engaging. Real images make it credible.
