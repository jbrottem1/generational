# CHAR-PROFESSOR-001 — Professor Gen

**Character ID:** `CHAR-PROFESSOR-001`  
**Display name:** Professor Gen  
**Short name:** Gen  
**Version:** 1.0.0  
**Status:** LOCKED for Foundation / Generational educational host use  
**Voice profile:** `nova` + `tts-1-hd`  
**Silhouette test:** Must read as Gen at 1080×1920 from ~1 meter  

**Canonical profile:** `data/character_systems/PROFESSOR_PROFILE.md`  
**Bible:** `data/character_systems/CHARACTER_BIBLE.md`

---

## Concept

Professor Gen is Generational's **flagship digital educator** — a clean black stick figure with a white face who teaches in the Foundation white studio. Calm, curious, lightly warm. Gestures only when teaching.

Not Dash (kinetic explorer). Not MacroCenter scenery host. Gen is the Foundation standard.

---

## Design lock (do not redesign)

| Part | Spec |
|------|------|
| Outline | Clean black `(0, 0, 0, 255)` |
| Face fill | Pure white `(255, 255, 255, 255)` |
| Stroke | `7` at 1024 plate (scale with resolution) |
| Head ratio | `0.34` |
| Head | Perfect circle; white fill |
| Eyes | Simple ovals + pupils |
| Mouth | Smile arc or open ellipse — no teeth detail |
| Torso / limbs | Single-stroke black sticks |
| Attire | `none` — **lab coat forbidden for Gen v1** (future coat needs version bump) |
| Hands | Round mitt endpoints |
| Feet | Small oval plants |
| Forbidden | Color body fills, logos, hair, 3D limb shading, lab coat, wave spam, silent redesign |

Matches `StickFigureSpec` defaults (`services.animation.stick_figure`), including `attire="none"`.

---

## Personality (summary)

Brilliant calm university tutor · curious · lightly warm humor · never sarcastic at the learner · confident without arrogance.

Teaching rhythm: **Welcome → question → board → example → one-line summary → next lesson tease**

---

## Relationships

| Character | Relationship |
|-----------|--------------|
| `CHAR-STICK-001` (Stick) | Predecessor performer plate — proportions inherited; MacroCenter role retired for Foundation |
| `CHAR-DASH` (Dash) | Dash Science mascot — separate brand; do not merge or redesign |

---

## Capability checklist (v1)

Idle · purposeful walk · face audience · think · present · point · write (board) · blink · breathe · lip-sync mouth — **required**.  
Wave in professor mode — **forbidden**.

---

## Assets in this folder

| File | Purpose |
|------|---------|
| `CHARACTER.md` | This identity sheet |
| `design_spec.json` | Locked proportions + palette |
| `expression_sheet.json` | Expression catalog |
| `gesture_sheet.json` | Gesture policy + code map |
| `turnaround_notes.md` | Turnaround guidance |
| `turnaround_front.png` | Front plate |
| `turnaround_sheet.png` | Simple multi-pose sheet |
