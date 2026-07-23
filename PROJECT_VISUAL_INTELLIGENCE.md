# PROJECT VISUAL INTELLIGENCE — Generational Knowledge Atlas

**Status:** LOCKED — permanent Visual Intelligence System  
**Established:** 2026-07-12  
**Executive Sponsor:** Agent 0  
**Companions:** `PROJECT_REALITY.md` · `PROJECT_FOUNDATION.md` · `GENERATIONAL_METHOD.md`

---

## Mission

Build the **Generational Knowledge Atlas** — the company's permanent visual knowledge library.

For every topic, ask: *"What visual evidence would teach this concept best?"*

Prefer **authentic visual evidence** over generated graphics when it improves understanding.

---

## Visual types (intelligent selection)

The Atlas chooses the best format per concept:

| Type | Examples |
|------|----------|
| Photographs | Wildlife, specimens, field evidence |
| Microscopy / histology | Cells, tissues, slides |
| Medical imaging | X-ray, CT, MRI (when appropriate) |
| Remote sensing | Satellite, aerial |
| Astronomical | NASA/NOAA observations |
| Specimens & fossils | Museum collections |
| Diagrams & maps | Scientific illustrations, cross-sections |
| Data visuals | Graphs, charts |
| Documents | Historical primary sources (public domain) |
| Comparisons | Side-by-side, before/after, time-lapse |

---

## Source hierarchy

Prefer trusted educational sources: NASA, NOAA, USGS, NIH, CDC, Smithsonian, NPS, universities, museums, government agencies, peer-reviewed publications, public-domain archives, properly licensed collections.

**Never** include assets that cannot legally be reused.

---

## Package layout

| Path | Role |
|------|------|
| `data/knowledge_atlas/catalog.json` | Indexed asset library |
| `data/knowledge_atlas/collections.json` | Domain collections (Biology, Astronomy, …) |
| `data/knowledge_atlas/INDEX.md` | Human-readable atlas index |
| `services/knowledge_atlas/` | Search, planner, ingest, QC, feedback |
| `scripts/sync_atlas_from_reality.py` | Import Project Reality assets into Atlas |

---

## Pre-lesson workflow

```
Script → concept beats → plan_visual_evidence()
  → search Atlas (keywords, concepts, domain)
  → evaluate (resolution, license, accuracy, clarity)
  → recommend layout (split_compare, zoom, evidence_tray)
  → professor teaches WITH evidence
  → post-lesson feedback strengthens library
```

---

## QC (reject)

- Low resolution (<400 px shortest side)
- Watermarked or unlicensed material
- Visually confusing or irrelevant imagery
- Duplicate assets (fingerprint dedup)
- Poor educational value

---

## Self-improvement

After every lesson:

- Was the visual effective?
- Could another asset explain better?
- Should this asset join the permanent library?
- Should a better version replace it?

Record via `services/knowledge_atlas/feedback.py`.

---

## Success condition

Viewers feel every lesson is supported by **authentic visual evidence**. Professor guides; visuals prove. The library grows stronger with every production.
