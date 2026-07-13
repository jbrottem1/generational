# Prompt Library

**Owner:** Agent 27  
**Versioning:** Patterns below are **v1** approved unless marked retired.  
**Canonical GCIS archives (do not fork):**

- Successful: [`data/gcis/knowledge/prompts/successful.md`](../gcis/knowledge/prompts/successful.md)
- Failed / avoid: [`data/gcis/knowledge/prompts/failed.md`](../gcis/knowledge/prompts/failed.md)

---

## Categories

| Category | Use for | Primary sources |
|----------|---------|-----------------|
| `animation` | Choreography, gesture beats, Fluid Motion | `teaching_choreography.py`, Fluid Motion |
| `education` | Generational Method teaching beats | `GENERATIONAL_METHOD.md`, AELS |
| `seo` | Titles, hooks, packaging | Agent 8 / `services/seo` |
| `research` | Fact-safe simplification | STD-SCI-001 |
| `script` | Short structure, VO lines | Agent 3, Foundation lesson map |
| `render` | Export / gate language | `foundation_gate`, unique export |
| `publish` | Scheduler / platform copy | Agent 7 (OAuth blocked) |
| `executive` | Sprint / Echoer envelopes | ECP v1, Agent 0 |

---

## Approved v1 prompt patterns

Drawn from PROJECT_FOUNDATION + Generational Method + GCIS successful prompts.

### PL-v1-001 — Welcome back opening
- **Category:** `script` / `education`
- **Pattern:** Open with exactly: `Welcome back to Generational.` (2–3s), then today’s question.
- **Evidence:** PROJECT_FOUNDATION lesson structure; Foundation Newton series.
- **Status:** approved v1

### PL-v1-002 — Watch the board / demo cue
- **Category:** `script` / `animation`
- **Pattern:** Use an imperative demo cue in the first teaching beats: `Watch…` / `Look…` / board write reveal — show before naming.
- **Evidence:** GCIS successful Method Short; AELS ES001 hook (Watch in first 3 beats, hook 97).
- **Status:** approved v1

### PL-v1-003 — In the next lesson closer
- **Category:** `script` / `education`
- **Pattern:** Close with curiosity bridge: `In the next lesson…` (one concrete tease, no filler).
- **Evidence:** PROJECT_FOUNDATION closing beat; Method curiosity bridge.
- **Status:** approved v1

### PL-v1-004 — Generational Method Short skeleton
- **Category:** `script` / `education`
- **Pattern:**
  ```
  [HOOK 1 sentence, curiosity or paradox]
  [DEMO cue — "Watch…" / "Look…"]
  [MECHANISM in plain language, 2–3 sentences]
  [REAL-WORLD analogy, 1 sentence]
  [TAKEAWAY — one memorable line]
  ```
- **Evidence:** `prompts/successful.md`; STD-TEACH-001.
- **Status:** approved v1

### PL-v1-005 — Pattern-interrupt hook
- **Category:** `education` / `seo`
- **Pattern:** First beat uses question or contradiction (`doesn't`, curiosity gap) — not statement-only openers. Target hook ≥72 before ship when AELS reviews.
- **Evidence:** Sprint 6h30 Cycle 3 (hook 65→77); lessons_learned 2026-07-11.
- **Status:** approved v1

### PL-v1-006 — Paused narration (voice)
- **Category:** `script` / `render`
- **Pattern:** Build VO with intentional silence between beats via `communicator_delivery.build_paused_narration`; pause before punchlines.
- **Evidence:** Communicator delivery lesson; Foundation nova + pauses.
- **Status:** approved v1

---

## Index — GCIS successful.md

See full notes in GCIS for:

- Method Short skeleton (~20–30s)
- Voice settings that worked (`onyx` / `tts-1` platform default; Gen locks `nova` / `tts-1-hd`)
- `demo_id` naming (`bio_*`, foundation physics ids)
- Series runner pattern (`biology_academy_vol1.py`)

---

## Retired / avoid

**Do not reuse without explicit redesign.** Full table:

→ [`data/gcis/knowledge/prompts/failed.md`](../gcis/knowledge/prompts/failed.md)

Highlights:

- Constant walk + arm sway  
- Ken Burns-only slideshow  
- Multi-topic cram  
- Rambling filler  
- Overwrite master MP4  
- Wave gesture loops  
- Lecture without on-screen demo  
- Blind 15/16 worktree merge  
