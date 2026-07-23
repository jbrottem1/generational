# Generational Version 1 — Release Plan

**Status:** **NOT_READY** (as of 2026-07-14 operational review)  
**Principle:** Improve only with production evidence. No architecture expansion without measured justification.

---

## Current baseline (locked evidence)

| Gate | Required | Measured |
|------|----------|----------|
| Environment health | No blockers | **21/21 pass** |
| Pilot sample | ≥20 runs | **25/25** |
| Deliverable MP4 rate | ≥90% (V1) / ≥80% (minor) | **0%** |
| Ops success rate | ≥90% | **0%** |
| Avg quality score | ≥80 | **85.7** ✓ |
| Publishing | Manual only until V1 | Disabled ✓ |

Creative/upstream path is ready. **Export path is not.**

---

## Release gates (must all pass)

### Gate A — Deliverable factory
- Fresh **20–25** production sample  
- `video_exists=true` on **≥90%**  
- Verified file size + streams (existing ffprobe helpers)  
- Ops `success` aligned with deliverable  

### Gate B — Honesty under degradation
- When animation unavailable: motion/cinematic dims **capped** (measured in reports)  
- No APPROVE/publish recommendation without MP4  

### Gate C — Recovery
- Interrupted job resumes without re-running succeeded stages  
- Proven on ≥3 intentional mid-pipeline interruptions  

### Gate D — Batch ops
- Provider health check before GenOS/queue drain  
- Production queue write locking (prevent lost jobs)  

### Gate E — Re-prove business path
- Re-run V1 Launch pilot (`scripts/v1_launch.py run-program --limit 25`)  
- Decision must become `READY_FOR_LAUNCH` or `READY_WITH_MINOR_FIXES` under existing thresholds  

**Only after A–E:** enable **manual** first publishes (still no auto-publish).

---

## Workstream (existing systems only)

| Order | Work | Success metric | Est. |
|------:|------|----------------|------|
| 1 | Production-mode MP4 materialization via current export/studio_render/ffmpeg | MP4 rate ≥90% on 20-run sample | 2–4 days |
| 2 | Cap scores when animation unavailable | Cap visible on 100% of skip runs | 0.5 day |
| 3 | Ops stage-skip resume | 3/3 recovery drills pass | 1–2 days |
| 4 | Queue file lock + provider preflight | No lost jobs; failed preflight blocks batch | 1 day |
| 5 | Re-run Launch Program 25 | Decision ≠ NOT_READY | 0.5 day ops |

**Calendar estimate to V1 candidate:** **≈ 5–8 engineering days** after Gate A starts — not weeks of architecture.

---

## Decision matrix (use after next pilot)

| Outcome | Decision |
|---------|----------|
| MP4 ≥90% · success ≥90% · score ≥80 · resume proven | **READY_FOR_V1** |
| MP4 ≥80% · success ≥75% · score ≥75 · resume optional remaining | **READY_AFTER_MINOR_FIXES** |
| MP4 <80% or success <75% | **NOT_READY** |

---

## Explicit non-goals until Gate A passes

- New production engines  
- New architectural layers  
- Speculative creative features  
- Automatic multi-platform publishing  
- Refactors not required to raise MP4 rate or resume correctness  

---

## Operating cadence (COO)

1. **Daily / batch:** `python scripts/v1_launch.py health`  
2. **After export fix:** `python scripts/v1_launch.py pilot --limit 25`  
3. **Decide:** `python scripts/v1_launch.py recommend`  
4. **Ship:** only when recommendation leaves `NOT_READY`  

---

## Sign-off line

**As of this review: NOT_READY for Version 1 public launch.**  
Proceed via Gate A (export materialization) with evidence-based, freeze-respecting fixes only.
