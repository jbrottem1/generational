# Phase V — Character Review Board: DOCTOR_001

**Role:** Creative Director · Character Art Director · Animation Supervisor · Review Board  
**Architecture:** Frozen (no new engines)  
**Evidence:** `CHARACTER_PRODUCTION/VALIDATION_RENDERS/` · Golden Motion `GOLDEN_MOTION_20260718T164914Z`  
**Interactive board:** open the Cursor canvas beside chat  

---

## Board decision

### NOT READY

Technically successful skeletal actor. Creatively fails the permanent-face-of-Generational test.  
After one episode, audiences remember “a robot,” not the Doctor.

**Overall appeal: 3.8 / 10** (mean of 12 categories)

| Category | Score |
|----------|------:|
| 1 Silhouette | 4 |
| 2 Facial appeal | 3 |
| 3 Readability | 4 |
| 4 Eyes | 3 |
| 5 Expressions | 3 |
| 6 Gesture quality | 4 |
| 7 Costume design | 2 |
| 8 Color harmony | 6 |
| 9 Educational trust | 4 |
| 10 Memorability | 3 |
| 11 Animation quality | 5 |
| 12 Environment relationship | 4 |

---

## Silhouette test

**FAIL.** Blackout reads round torso + ball joints + dark skullcap — not a medical coat host. Missing hem flare, lapels, soft shoulder, signature pin stance.

---

## Category summaries (brutal)

### 1. Silhouette — 4
- **Strength:** Humanoid; navy cranial cue; height plausible.
- **Weakness:** Egg + floating capsules = toy mannequin; coat invisible in outline.
- **Revision:** Continuous soft coat silhouette; connected limbs; readable hands/feet.

### 2. Facial appeal — 3
- **Strength:** Warm sand + navy panel intent; features exist (not blank ball).
- **Weakness:** Primitive kitbash; balloon cheeks; cone chin; floating neck.
- **Revision:** Continuous head sculpt; mouth plane; integrate cranial panel.

### 3. Readability — 4
- **Strength:** Cap readable mid/wide.
- **Weakness:** Extreme CU fails; some GM speak frames hit back of cranial panel.
- **Revision:** Hero topology; lock face-to-camera on dialogue; coat for wide.

### 4. Eyes — 3
- **Strength:** Separate eye stack + gaze bones; on-brand teal.
- **Weakness:** Vacant glow; weak pupil; thin lids; doll specular.
- **Revision:** Darker pupil hierarchy; soft lids; quieter emission; resting squint.

### 5. Expressions — 3
- **Strength:** Broad shape-key library in pipeline.
- **Weakness:** Smile ≈ neutral on screen; emotion needs audio.
- **Revision:** Mouth aperture redesign; larger expression deltas; child-nameable sheet.

### 6. Gesture — 4
- **Strength:** Real walk/reach/grasp skeletal path.
- **Weakness:** Ball hands; chrome elbows; mechanical follow-through.
- **Revision:** Finger-readable hands; soft joint fairings; coat lag on turn.

### 7. Costume — 2 (lowest)
- **Strength:** Intent of white coat + teal + insignia.
- **Weakness:** Renders as ribbed egg + floating cyan slabs — not a coat.
- **Revision:** Collar, lapels, hem, cuffs, chest pin; kill floating trim; clip-free bind.

### 8. Color — 6 (highest)
- **Strength:** Dawn-white / navy / teal fits Generational.
- **Weakness:** Chrome elbows; noisy ribbing; body blends into grey lab.
- **Revision:** Soft navy joints; quieter face noise; coat value vs walls.

### 9. Educational trust — 4
- **Strength:** Calm palette; non-villainous context.
- **Weakness:** Toy construction undercuts professional kindness.
- **Revision:** Soft continuous surfaces; trustworthy eyes; coat professionalism.

### 10. Memorability — 3
- **Strength:** Cranial navy is a seed icon.
- **Weakness:** Category (“robot”) beats character (“Doctor”).
- **Revision:** Lock cranial crescent + resting smile + Generational pin; ban clutter.

### 11. Animation — 5
- **Strength:** Alive pipeline — walk, grasp, visemes, blinks, cameras (not Ken Burns).
- **Weakness:** Thin personality; weak breath/idle; face-missed dialogue shots.
- **Revision:** Preserve GM beats; face cameras; breath; coat follow-through.

### 12. Environment — 4
- **Strength:** Persistent 3D lab; action props real.
- **Weakness:** Greybox set shares placeholder DNA with character.
- **Revision:** Value contrast, practicals, denser dress via existing Stage tools.

---

## Top 10 weaknesses (impact order)

1. No medical-coat silhouette  
2. Eyes do not create trust  
3. Face is primitive ball kitbash  
4. Expressions don’t read without audio  
5. Hands are spheres  
6. Dialogue cameras catch back of head  
7. Exposed metallic joint balls  
8. Coat/torso clipping in motion  
9. Lab set shares greybox DNA  
10. No single iconic signature locked  

Each: favor high-impact, low runtime-risk changes; keep bone names, shape-key names, BlenderRuntime, Golden Motion.

---

## Action plan

### Phase 1 — Quick wins (re-render GM after each)
- Quiet eye emission; darker pupils; resting squint  
- Soft joint caps; remove chrome elbows  
- Face dialogue cameras to −Y face plane (keep beats)  
- Shrink cheek balloons; stronger resting smile  
- Coat ribbing down; pin visibility  

### Phase 2 — Medium
- Readable coat (collar/lapels/hem/cuffs)  
- Mouth topology + expression pass  
- Finger-readable hands on existing bones  
- Coat weights / clip fix  
- Lab contrast + set dress (frozen Stage)  

### Phase 3 — Long-term
- Authored hero mesh per `EXTERNAL_ASSET_BRIEF.md`  
- Textures, LODs, correctives  
- Stable cloth hybrid with coat-bone fallback  
- Board re-review toward APPROVED WITH REVISIONS → APPROVED  

---

## Golden Scene rule

Do **not** change Walk → Grasp → Smile → Speak intent.  
Improve art one category at a time; re-render the same Golden Motion for before/after.

---

## Frozen compatibility

Character Rig Studio · Animation Runtime · BlenderRuntime · Golden Motion · Character Performance Engine · Production Asset Studio · Creative Direction Guide.
