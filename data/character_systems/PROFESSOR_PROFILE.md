# PROFESSOR PROFILE — Professor Gen

**Character ID:** `CHAR-PROFESSOR-001`  
**Display name:** Professor Gen  
**Short name:** Gen  
**Version:** 1.0.0  
**Status:** LOCKED  
**Voice profile:** `nova` + `tts-1-hd`

---

## One-line identity

A brilliant, calm university tutor who makes one idea clear per lesson — curious, lightly warm, never sarcastic at the learner.

---

## Personality

| Trait | Spec |
|-------|------|
| Intelligence | High — explains with precision, not jargon dumps |
| Calm | Steady presence; no panic comedy |
| Curiosity | Genuine interest in the learner's question |
| Warmth | Light, friendly humor; never mean |
| Confidence | Sure without arrogance |
| Patience | Comfortable with silence and thinking beats |

**Never:** sarcastic at the learner · condescending · frantic · fidgety · decorative gesturing · slapstick panic (that is Dash territory)

---

## Teaching philosophy

1. **One question per Short** — protect focus.
2. **Show, then say** — board writing and pointing carry the proof.
3. **Real world once** — one concrete example, not a list.
4. **One-line summary** — leave a memorable sentence.
5. **Tease next** — invite continuity without cliffhanger gimmicks.

Aligned with `PROJECT_FOUNDATION.md` and Generational Method educator mode.

---

## Teaching rhythm (locked)

| Beat | Purpose | Typical gesture |
|------|---------|-----------------|
| Welcome | Orient viewer | `idle` / planned `greeting` |
| Question | Frame curiosity | `think` or `present` |
| Board | Write / circle / underline | `write`, then `point` |
| Example | Ground the idea | `point` or `present` |
| One-line summary | Lock takeaway | `present` |
| Next lesson tease | Continuity | `idle` (calm close) |

Opening line pattern: *"Welcome back to Generational."*  
Closing pattern: *"In the next lesson…"*

---

## Voice & speech

| Field | Lock |
|-------|------|
| Provider preference | OpenAI TTS |
| Voice | `nova` |
| Model | `tts-1-hd` |
| Tone | Clear tutor; measured pace |
| Humor | Dry-warm asides, rare; never mock the student |
| Filler | Forbidden |

Agent 26 owns the **preference lock**. Agent 5 / 19 own connector wiring. Do not change provider code unless wiring this default into a character spec consumer.

---

## Humor rules

- Allowed: soft wonder, gentle surprise at a clever result, understated delight.
- Forbidden: sarcasm aimed at the learner, roast comedy, panic bits, meme voice.
- Timing: humor after clarity, never instead of it.

---

## Signature behaviors

1. **Faces the audience** when speaking the question and the summary.
2. **Turns to the board** only to write or point at what was written.
3. **Walks with purpose** — short reposition, then plant; no pacing loops.
4. **Blinks and breathes** naturally (`fluid_life` professor amp).
5. **Gestures only when teaching** — idle between beats.
6. **Write gesture** — right hand to board during stroke-reveal beats.
7. **Never wave spam** — `wave` is forbidden in professor / Foundation mode.
8. **No lab coat** — attire locked to `none` for Gen v1; MacroCenter coat is a future opt-in (`coat=True` / `attire=lab_coat`) requiring a version bump.

---

## Emotional range (v1)

| Expression | Use |
|------------|-----|
| `neutral` | Default teach |
| `curious` | Framing today's question |
| `thinking` | Processing / setup |
| `clarity` | After board proof lands |
| `warm_close` | Summary + next tease |

High-energy `panic` / `shock` are **out of range** for Gen (reserved for Dash / other performers).

---

## Visual lock reminder

Clean black stick · white face · stroke 7 · head_ratio 0.34 · simple eyes/mouth.  
See `data/universe/characters/CHAR-PROFESSOR-001/design_spec.json`.

---

## Relationship notes

- **Stick (`CHAR-STICK-001`)** — predecessor performer plate; Gen is the named Foundation host.
- **Dash (`CHAR-DASH`)** — separate Dash Science mascot; kinetic explorer personality. Do not blend.
