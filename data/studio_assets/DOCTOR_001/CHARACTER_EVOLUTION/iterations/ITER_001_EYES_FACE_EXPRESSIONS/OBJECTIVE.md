# Iteration 001 — Eyes / Face / Expressions

## Artistic objective

Create immediate audience trust. Improve eye proportions, iris/pupil hierarchy, eyelids, blink timing, resting expression, smile readability, cheek shape, mouth aperture, eyebrow movement, micro-asymmetry, gaze, and head orientation during speech.

**Out of scope:** coat, limbs, silhouette body, color palette of wardrobe, lab environment, walk/grasp timing.

## Implementation summary

1. Quieted iris emission (1.2 → 0.18); darker larger pupil; thicker lids.
2. Smaller cheeks; softer jaw; readable lip + mouth cavity cue; split brows.
3. Stronger shape-key deltas (smile, blink, brow, visemes).
4. Resting warmth: smile 0.32 + eye_squint 0.14 + cheek_raise 0.12.
5. Golden Motion facial channels only: smile/blink/gaze/head-during-speak; walk/grasp/cameras/lighting unchanged in intent.

## Pass conditions

- Eyes score ↑ · Face score ↑ · Overall appeal ↑ · No regression elsewhere.
