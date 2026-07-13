# Turnaround notes — CHAR-PROFESSOR-001 (Professor Gen)

**Version:** 1.0.0  
**Plate generator:** `services.animation.stick_figure.draw_stick_figure` / `save_turnaround_sheet`

---

## Locked plate

- Front-facing clean black stick, white face.
- Spec: outline black, face white, stroke 7, head_ratio 0.34, **attire=`none`**.
- Studio reference: pure white background when composited for Foundation.
- **Lab coat forbidden** for Gen v1 — `draw_stick_figure(professor=True, coat=False)`.

## Sheets in this folder

| File | Contents |
|------|----------|
| `turnaround_front.png` | Neutral idle front plate (professor motion, no coat) |
| `turnaround_sheet.png` | Simple pose row: idle · think · point · write · present |

## Production use

1. Treat front plate as recognition reference for QC silhouette checks.
2. Pose row documents allowed teaching gestures — not a full 360 turnaround (v1).
3. Side / back views are **planned** for a future version bump; not required for Foundation white-studio front performances.

## Do not

- Recolor the plate.
- Add MacroCenter coats/scenery as the Foundation lock (coat opt-in requires version bump).
- Use wave poses as Gen reference.
