## 2026-07-10 — Communicator delivery

**Source:** Generational_Benchmark_Brain_Energy

### What worked
- Intentional silence between beats > continuous TTS dump
- 'Wait. What?' pause before the 2%/20% punchline
- Show energy particles into brain BEFORE stating the statistic

### Standard
- Use `communicator_delivery.build_paused_narration` for flagship Shorts

---

## 2026-07-10 — Project Excellence

**Source:** Project_Excellence_Stomach_Acid

### What worked
- Show acid dissolving food BEFORE naming mucus
- Quiet MacroCenter (less chrome) improves focus
- Warm voice (nova) + smile-at-rest reads more human
- Sparse choreography > busy teaching

### Standard
- Feature freeze until teaching+motion quality leads

---

## 2026-07-10 — MacroCenter V2 density

**Source:** MacroCenter_V2_Cell_Membrane

### What worked
- Shorter + denser beats longer + thinner
- SHOW allow/block before naming bilayer
- Visual change every few seconds without fidget spam

### Standard
- Density law: every second earns its place

---

# Lessons Learned (GCIS)

Append-only. Newest first. Every entry must name the source sprint/production.

---

## 2026-07-11 — Echoer + AELS sprint infrastructure

**Source:** Sprint 6h30 setup

### Standard
- All agents use ECP v1 (`ECHOER_PROTOCOL.md`) for task handoffs
- Agent 24 AELS reviews every cycle before next production
- Pause boost from AELS recommendations applied cycle-over-cycle

---

## 2026-07-10 — Project MacroCenter launched

**Source:** Flagship `MacroCenter_Biology_001_Cell_Membrane`

### What worked (design intent)
- Dedicated HQ environment (not classroom) creates franchise recognition
- Professor lab-coat mode + hologram interaction beats flat lab backdrop
- Soft hub ambience under VO increases immersion without drowning speech

### Standard
- Academy flagships open inside MacroCenter (`PROJECT_MACROCENTER.md`)

---

## 2026-07-10 — Biology Academy Vol 1 + Generational Method

**Source:** Biology Academy Test Run (5/5) · Educator benchmarks v2 · `GENERATIONAL_METHOD.md`

### What worked
- **Purposeful choreography > more motion.** Idle ~32–45%, walk ~5–7% felt like teaching, not fidgeting.
- **One concept per Short** with hook → demo → explain → real-world → takeaway.
- **Demo overlays synced to beat plans** (`teaching_choreography.py` + `biology_demos.py`) beat generic Ken Burns.
- **Never overwrite exports** (`unique_path`) preserved A/B history (v1 vs v2 educator).
- **Series runners** (`scripts/biology_academy_vol1.py`) encode the whole pattern for reuse.

### What failed / weak
- Educator path still **parallel** to full Orchestrator asset pipeline — two production modes to maintain.
- Biology visuals are strong diagrams but not yet a shared **asset library** of cells/DNA/organs.
- Episodes ~20–24s — strong for retention hooks; may want optional 35–45s depth variants later.
- Live publish still blocked (OAuth) — learning loop cannot close on real audience metrics.

### New standards
- Generational Method is mandatory for educator Shorts.
- QC must include `purposeful_gestures` for educator_mode.
- Post-production review required after every series batch (GCIS).

### Next improvement
- Promote biology/physics demos into a versioned **demo library registry** with reuse counts.
- Wire post-production review checklist into series runners (auto-write draft review JSON).

---

## 2026-07-10 — True Animation + Lip Sync

**Source:** True Animation Benchmark · Animation Benchmark 001 · Physics Academy

### What worked
- Reject Ken Burns-only finishes (Animation QC).
- Lip-sync performer (`services/animation/performer.py`) is the live educator path.
- Stick → grounded educator evolution improved perceived professionalism.

### What failed
- Early educator versions had **constant walking / arm spam** — viewers remembered motion, not concepts.
- Physics Academy v1 used left-anchor non-educator mode; educator_mode is the better teaching standard.

### Standard
- Default educator state = calm idle; move only when the lesson requires it.

---

## 2026-07-11 — Sprint 6h30 Cycle 3 (Hook + Pause Boost)

**Source:** Continuous Improvement Sprint · Muscle Growth Short

### Measured improvement (Cycle 2 → 3)
- AELS engagement: **79.1 → 83.8** (+4.7)
- Hook score: **65 → 77** (+12) via pattern-interrupt hook + `pause_boost=0.05`
- Quality overall: stable at **75.0**

### Validated changes
- Pattern-interrupt hooks (`doesn't`, questions) in `CYCLE_TOPICS` beats 4–7
- `next_config()` applies `pause_boost` when prior hook_score < 72 or pacing < 75
- AELS emits hook recommendations when curiosity gap is weak

### Standard
- First beat must score hook ≥ 72 before shipping; use question or contradiction, not statement-only openers.

---

## Standing anti-patterns (do not repeat)

1. Motion for motion’s sake  
2. Overwriting finished MP4s  
3. Blind-merging Agent 15/16 worktrees without Agent 1 review  
4. Lecturing without demonstration  
5. Shipping without post-production review under GCIS  
