# Production Standards

**Owner:** Agent 27 · elevates GCIS `standards.md` + Foundation / Character locks  
**Sources of truth cited:** [PROJECT_FOUNDATION.md](../../PROJECT_FOUNDATION.md), `services/animation/foundation_gate.py`, [Character Bible](../character_systems/CHARACTER_BIBLE.md), [GCIS standards](../gcis/knowledge/standards.md)

Markers:

- **LOCKED** — company default until Agent 0 revises  
- **ASPIRATIONAL** — validated direction; not yet hard-gated everywhere  

Do not invent conflicting rules. When GCIS and this doc differ, open a revision — do not silently fork.

---

## Animation

| Status | Standard |
|--------|----------|
| LOCKED | Purposeful gestures only; calm idle default (STD-ANIM-001) |
| LOCKED | Ken Burns-only / slideshow finishes rejected (STD-ANIM-002) |
| LOCKED | `educator_mode=True` for Academy / Foundation teaching Shorts (STD-ANIM-003) |
| LOCKED | Fluid Motion law: better movement, not more (`PROJECT_FLUID_MOTION.md`) |
| LOCKED | Foundation white studio `(255,255,255)` + hairline floor + whiteboard primary tool |
| ASPIRATIONAL | Phoneme/viseme lip-sync (stub today; deferred until Foundation ≥80 stable) |
| ASPIRATIONAL | MacroCenter / rich environments return only after fundamentals stay premium |

## Teaching

| Status | Standard |
|--------|----------|
| LOCKED | Generational Method structure: curiosity → demo → explain → real-world → takeaway → bridge (STD-TEACH-001) |
| LOCKED | One core concept / one question per Short (STD-TEACH-002) |
| LOCKED | **Curiosity Framework** (`GENERATIONAL_CURIOSITY_FRAMEWORK.md`): open with unanswered question; forbid "Welcome back / Today we'll learn / In this video" |
| LOCKED | Show before name; demo overlays synced to choreography beats |
| LOCKED | **Project Reality** (`PROJECT_REALITY.md`): licensed real scientific images in evidence panels; professor points and annotates |
| LOCKED | **Knowledge Atlas** (`PROJECT_VISUAL_INTELLIGENCE.md`): permanent visual evidence library; search + plan before lessons; grow library after every production |
| LOCKED | Educational simplification OK; never invent false mechanisms (STD-SCI-001) |
| LOCKED | State evolving science clearly (e.g. monarch–viceroy complexity) — never oversell tentative ideas |

## Voice

| Status | Standard |
|--------|----------|
| LOCKED | Intentional pauses via `communicator_delivery.build_paused_narration` for flagship Shorts |
| LOCKED | Foundation path: OpenAI TTS `nova` + `tts-1-hd` (Character Bible / Gen profile) |
| LOCKED | GCIS educator default note: `onyx` / `tts-1` until series upgrades (STD-VOICE-001) — series may lock voice in Character Bible |
| ASPIRATIONAL | ElevenLabs / premium voice upgrade (EX-004 backlog) |

## Lip-sync

| Status | Standard |
|--------|----------|
| LOCKED | Live educator path uses `services/animation/performer.py` lip-sync performance |
| LOCKED | Foundation lipsync floor ≥70 in content score; gate enforces |
| ASPIRATIONAL | Phoneme-accurate mouth shapes |

## Script structure

| Status | Standard |
|--------|----------|
| LOCKED | No filler; every sentence teaches |
| LOCKED | Pattern-interrupt / curiosity hooks; first beat hook ≥72 when AELS reviews |
| LOCKED | Curiosity bridge closer (“In the next lesson…”) |

## Pacing

| Status | Standard |
|--------|----------|
| LOCKED | Density law: every second earns its place |
| LOCKED | Target educator Short ~20–35s unless series specifies otherwise |
| LOCKED | Pause boost applied cycle-over-cycle when AELS flags weak hook/pacing |

## Rendering

| Status | Standard |
|--------|----------|
| LOCKED | **Generational OS V2.5** (`GENERATIONAL_OS_V2_5.md`): four-layer pipeline, manifest, classified export |
| LOCKED | **Local-first execution** (`EXECUTION_MODE.md`): cloud prepares `RENDER_PACKAGE.json`; local Mac renders |
| LOCKED | **Permanent Media Library** (`MEDIA_LIBRARY.md`): `~/Desktop/AI Start-Up/Videos/{Category}/` |
| LOCKED | File naming: `<Category>_<Series>_<Episode>_<Topic>.mp4` + companion folder per export |
| LOCKED | Library index: `VIDEO_LIBRARY.json` with search, dedup via SHA-256 hash |
| LOCKED | Cloud agents never report `"Video exported."` — use `"Production package prepared. Awaiting local render."` |
| LOCKED | SUCCESS only after verified MP4 + manifest + production DB update |
| LOCKED | Foundation exports pass `foundation_gate` (idle/walk/wave/mouth/lipsync floors; overall target ≥78) |
| LOCKED | `unique_path` / `_vN` — never overwrite finished exports (STD-EXPORT-001) |
| LOCKED | Educator QC includes `purposeful_gestures` + interactive teaching (STD-QC-001) |

## Publishing

| Status | Standard |
|--------|----------|
| LOCKED | Code path ready; live YouTube blocked until OAuth (EX-001) |
| ASPIRATIONAL | Live publish smoke EX-002 → analytics → AELS calibration loop |

## Brand

| Status | Standard |
|--------|----------|
| LOCKED | Franchise recognition via consistent host (Gen) + Method teaching voice |
| ASPIRATIONAL | MacroCenter HQ as Academy flagship environment (deferred under Foundation freeze) |

## Character consistency

| Status | Standard |
|--------|----------|
| LOCKED | Professor Gen `CHAR-PROFESSOR-001` via Character Bible / Agent 26 |
| LOCKED | Gen attire `none` — lab coat forbidden without version bump |
| LOCKED | Forbidden Foundation gestures: `wave`, `react` |
| LOCKED | Pre-ship character QC via `services/character_systems` |

## Docs

| Status | Standard |
|--------|----------|
| LOCKED | Post-production GCIS review after every series batch (STD-GCIS-001) |
| LOCKED | Sprint executive report after every major sprint (STD-GCIS-002) |
| LOCKED | Echoer ECP v1 for agent task handoffs |
| LOCKED | Knowledge capture via Agent 27 — index GCIS; do not duplicate full lesson bodies |

## Testing

| Status | Standard |
|--------|----------|
| LOCKED | Foundation / gate / lip-sync / character / knowledge packages covered by pytest before ACCEPT |
| LOCKED | Do not redesign Orchestrator; expand additively (STD-ARCH-001) |
| LOCKED | No blind merge of Agent 15/16 worktrees (STD-MERGE-001) |

---

## Related

- GCIS operational table: `data/gcis/knowledge/standards.md`  
- Best practices (required workflows): [BEST_PRACTICES.md](BEST_PRACTICES.md)  
- Style index: [STYLE_GUIDES.md](STYLE_GUIDES.md)  
