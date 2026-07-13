# CHARACTER QC CHECKLIST — Production Verification

**Owner:** Agent 26  
**Gate:** Run before Foundation / educator production ship  
**Code gate:** `services.character_systems.validate_production_character`

---

## A. Identity

- [ ] `character_id` is `CHAR-PROFESSOR-001` for Foundation Gen performances
- [ ] Display name / short name match bible (Professor Gen / Gen)
- [ ] Spec version matches locked design_spec (`1.0.0` unless bumped)
- [ ] Universe registry lists character as `locked`
- [ ] Dash and Stick remain locked and unchanged

## B. Visual consistency

- [ ] Outline is black `(0, 0, 0, 255)` / `#000000`
- [ ] Face fill is white `(255, 255, 255, 255)` / `#FFFFFF`
- [ ] Stroke is `7` (±0 tolerance for Gen)
- [ ] Head ratio is `0.34` (±0.01)
- [ ] No color body fills, logos, hair, or clothing redesigns on the Foundation plate
- [ ] Attire is `none` — no lab coat / teal accents on Gen Foundation renders
- [ ] Silhouette still reads as Gen at phone size (1080×1920)

## C. Studio (Foundation)

- [ ] Background is pure white `(255, 255, 255)`
- [ ] Hairline floor only — no MacroCenter / lab scenery
- [ ] Whiteboard is the primary teaching tool
- [ ] No decorative effects competing with teaching

## D. Motion / gesture

- [ ] `educator_mode=True` for Gen teaching videos
- [ ] Gestures only on teaching beats
- [ ] No `wave` in professor mode (wave spam rejected)
- [ ] `write` used during board stroke-reveal windows
- [ ] Feet planted / purposeful walks only
- [ ] Blink + breath present; no fidget
- [ ] Gesture transitions blended (no snaps)

## E. Teaching rhythm

- [ ] Welcome → question → board → example → one-line summary → next tease
- [ ] One question per Short
- [ ] Humor never sarcastic at the learner

## F. Voice

- [ ] Voice profile preference `nova` + `tts-1-hd` documented / requested
- [ ] No filler voice lines

## G. Automated validation

```bash
./venv/bin/python -c "from services.character_systems import validate_production_character, load_character; print(validate_production_character(load_character('CHAR-PROFESSOR-001')))"
./venv/bin/pytest tests/test_character_systems.py -q
```

- [ ] `validate_production_character` returns `ok: true`
- [ ] `tests/test_character_systems.py` passes

## H. Ship decision

| Result | Action |
|--------|--------|
| All checks pass | ACCEPT for character continuity |
| Any fail | REVISIONS — do not ship redesigned plate |
