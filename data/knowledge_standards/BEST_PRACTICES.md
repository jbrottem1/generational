# Best Practices

**Owner:** Agent 27  
**Status:** Validated required practices for future agents  
**Evidence base:** GCIS standards + lessons, Foundation, ES001, Agent 26, Sprint 6h30

These are **must-follow** unless Agent 0 issues an explicit exception.

---

## Production

1. **Paused narration** — Use `communicator_delivery.build_paused_narration` (or equivalent intentional silence) for flagship educator Shorts; do not dump continuous TTS.
2. **`educator_mode=True`** — Academy / Foundation teaching Shorts render through the lip-sync performer educator path.
3. **Foundation white studio** — Educator Shorts under PROJECT FOUNDATION use pure white studio + whiteboard; no MacroCenter/scenery until fundamentals stay premium.
4. **`unique_export` / never overwrite** — Finished MP4s use `unique_path` / `_vN`; preserve A/B history.
5. **`foundation_gate` on ship** — Foundation educator exports must pass fail-closed gate (overall target ≥78; lipsync floor ≥70).
6. **One concept per Short** — Generational Method; one question; no multi-topic cram.
7. **Show before name** — Demo / board reveal precedes the jargon label when introducing terms.
8. **Curiosity Framework opening** — Start with an unanswered curiosity question (0–3s). **Forbidden:** "Welcome back…", "Today we're going to learn…", "In this video…". See `GENERATIONAL_CURIOSITY_FRAMEWORK.md`.
9. **Project Reality** — When a real photo improves understanding, show it in the board evidence panel (`services/reality/`). Curate licenses in `data/reality/catalog.json`; never use unlicensed or watermarked images.
10. **Knowledge Atlas** — Before lessons, run `plan_visual_evidence()` from `services/knowledge_atlas/`; prefer authentic Atlas assets over generated graphics when they teach better; record reuse via `record_lesson_visuals()`.

## Character

11. **Gen attire `none`** — `CHAR-PROFESSOR-001` ships without lab coat; `coat=True` / `attire=lab_coat` only with version bump.
12. **Character Bible first** — No silent redesigns; validate via `services.character_systems` before ship.
13. **No wave spam** — Forbidden professor gestures include `wave` and `react` in Foundation mode.

## Coordination & memory

14. **Echoer ECP** — All multi-agent handoffs use ECP v1 (`ECHOER_PROTOCOL.md` / `services.echoer.protocol`).
15. **AELS before next cycle** — Agent 24 reviews teaching/engagement; apply pause_boost / hook fixes before the next production when flagged.
16. **Wire AELS into the script** — JSON recommendations that never reach the production script are a reject condition (ES001 lesson).
17. **GCIS post-production review** — After every series/sprint batch, write review under `data/gcis/`.
18. **Capture lessons** — Append to `data/gcis/knowledge/lessons_learned.md`; register experiments in Agent 27 registry — do not fork conflicting lesson bodies.

## Architecture

19. **Additive Orchestrator changes** — Do not redesign Orchestrator; expand additively.
20. **No blind 15/16 merges** — Agent 1 merge plan required.

## Voice (series locks)

21. **Match Character Bible** — Gen Foundation: `nova` + `tts-1-hd` unless a documented series lock says otherwise.
