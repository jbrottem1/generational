# Generational Creative Direction Guide

**Phase:** III — Creative Direction & Visual Identity  
**Status:** Permanent constitution for all future assets  
**Architecture:** Frozen — no new engines, no runtime redesign  
**Applies to:** Characters · Environments · Props · Lighting · Materials · Motion · Interfaces  

Related: [Production Asset Studio](PRODUCTION_ASSET_STUDIO.md) · [Facial Performance & Environment Standard](FACIAL_PERFORMANCE_AND_ENVIRONMENT_STANDARD.md)

---

## North star

Generational is not photorealism.

Generational is **iconic, warm, educational cinema**.

Someone pausing any frame should instantly recognize the Generational Universe — the way a studio’s worlds are recognizable by silhouette, light, and color alone.

The audience should remember **the Doctor** because of character, not technology.

---

## Creative principles

1. **One studio, one world** — every asset feels designed by the same creative team.
2. **Appeal before speech** — the Doctor must be likable in silence.
3. **Emotion over detail** — clarity of feeling beats polygon count.
4. **Warm intelligence** — science feels hopeful, never cold or threatening.
5. **Lived-in spaces** — locations tell stories; nothing feels empty.
6. **Runtime respect** — identity upgrades must never break skeletal compatibility.

---

## Shape language

| Intent | Form |
|--------|------|
| Trust / warmth | Soft rounds, gentle ovals |
| Intelligence | Clean verticals, calm rectangles |
| Discovery | Soft arcs, open curves |
| Technology | Rounded rectangles, never harsh spikes |
| Avoid | Aggressive spikes, perfect spheres-as-toys, uncanny hyper-detail |

**Doctor silhouette:** tall, approachable, slightly oversized head for appeal, soft shoulder line, readable coat flare, clear head–shoulders–hips hierarchy.

**Lab architecture:** horizontal calm + tall window light; rounded furniture corners; tech panels as soft rectangles with cyan glow — never sci-fi menace.

---

## Color palette (constitution)

| Role | Name | Hex | Use |
|------|------|-----|-----|
| Primary | Dawn White | `#F7F4EF` | Walls, coat, soft surfaces |
| Secondary | Warm Sand | `#E8DFD2` | Wood accents, furniture |
| Trust | Generational Teal | `#2F9EBC` | Brand, UI, accents, iris rim |
| Depth | Midnight Navy | `#1B2A4A` | Contrast, underlayers |
| Life | Leaf Green | `#4F8F5B` | Plants, hope |
| Light | Window Gold | `#F2D4A5` | Natural key warmth |
| Clarity | Soft Sky | `#A9D4E8` | Holograms, screens |
| Alert | Ember Coral | `#E07A5F` | Urgency only |

**Forbid:** random palette drift, neon cyberpunk pinks, sterile pure greys as the dominant lab mood, horror desaturation.

---

## Color script (emotion)

| Emotion | Dominant | Support |
|---------|----------|---------|
| Curiosity | Soft Sky + Teal | Warm Sand |
| Discovery | Teal + Window Gold | Dawn White |
| Hope | Window Gold + Leaf Green | Dawn White |
| Reflection | Midnight Navy soft + Warm Sand | muted Teal |
| Celebration | Window Gold + Teal | Leaf Green |
| Urgency | Ember Coral | Navy (controlled) |
| Comfort | Warm Sand + Dawn White | gentle Teal |
| Scientific precision | Teal + Dawn White | clean Navy lines |

---

## The Doctor — character bible

### Communicates
intelligence · warmth · kindness · curiosity · confidence · professionalism · optimism

### Never appears
threatening · emotionless · generic · overly mechanical · toy-like · uncanny

### Appeal checklist
- **Silhouette** readable at thumbnail size  
- **Eyes** large, warm, clear focus — audience likes him before he speaks  
- **Mouth** soft smile resting baseline; never grim  
- **Posture** open chest, slight forward curiosity lean when teaching  
- **Coat** medical white with teal identity trim — not grey armor  
- **Walk** easy weight transfer, gentle arm swing, breathing always on  

### Facial performance
Blend — never snap. Prefer:

micro-asymmetry · soft blinks (not metronome) · eye-leads-head · brow for thought · cheek raise on genuine smile · speech visemes that support emotion

---

## Generational Medical Lab

**Feeling:** inspirational teaching sanctuary — not cold clinic.

Must include:
- warm natural window light  
- polished but inviting floor  
- wood + fabric soft furniture  
- living plants  
- books / ongoing research  
- soft holographic teaching displays  
- organized medical tech without visual clutter  
- subtle Generational teal brand marks  

**Avoid:** empty grey rooms, harsh fluorescent-only light, hospital horror mood.

---

## Lighting philosophy

Signature Generational light should be recognizable alone:

- warm key (window gold bias)  
- soft fill (never flat)  
- gentle teal-cool rim for intellect  
- controlled reflections on floor/glass  
- atmospheric depth (soft haze, never fog soup)  
- emotion drives exposure — hope brighter, reflection softer  

Presets remain Lighting Studio IDs; **Morning Discovery** is the Golden Motion default.

---

## Camera philosophy

- Vertical educational cinema (1080×1920) as primary  
- Eye-level empathy for teaching beats  
- Never hide missing performance with frantic cuts  
- Hands and face readable in interaction inserts  
- Depth: foreground interest · midground actor · background story  

---

## Motion style

Personality through movement:

anticipation · follow-through · ease-in/out · breathing · head micro-motion · eye darts · weight · balance · coat secondary motion  

Avoid robotic holds and instant pose snaps.

---

## Environment storytelling

| Location | Must show |
|----------|-----------|
| Lab | Ongoing research, teaching readiness |
| Library | History, quiet discovery |
| Classroom | Evidence of learning |
| Museum | Achievements, wonder |

Nothing empty. Always midground life cues (screens, books, plants, soft motion).

---

## Typography & interface

- Clean humanist sans for UI overlays (when used)  
- Teal accent bars, Dawn White panels, Navy text  
- Rounded corners, generous padding  
- Educational clarity over ornament  

---

## Quality review (reject if…)

Evaluate every asset against:

1. Visual Appeal  
2. Emotional Connection  
3. Recognizability  
4. Animation Quality  
5. Educational Clarity  
6. Brand Consistency  
7. Runtime Compatibility  

**Reject** assets that improve tech metrics but weaken identity, break the rig/runtime, or replace skeletal performance with image animation.

---

## Machine-readable constitution

`data/creative_direction/STYLE_CONSTITUTION.json`  
CLI: `python scripts/creative_direction.py`

---

## Success for the next Golden Motion

No new engines.

Same pipeline — unmistakably Generational world:

memorable Doctor · beautiful lab · expressive face · cinematic light · cohesive design · emotional educational storytelling
