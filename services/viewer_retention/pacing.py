"""Module 2 — Visual Pacing Engine: optimal cut duration per scene."""

from __future__ import annotations

from core.heuristics import clamp
from services.viewer_retention.models import ScenePacing

_PACING_LABELS = (
    "cut_2s",
    "cut_3s",
    "dramatic_pause",
    "montage",
    "zoom_rhythm",
    "motion_rhythm",
)


def _scenes(candidate: dict) -> list[dict]:
    vp = candidate.get("visual_package") or {}
    scenes = list(vp.get("scenes") or [])
    if scenes:
        return scenes
    ep = candidate.get("evidence_package") or {}
    return list(ep.get("scenes") or [])


def _density(narration: str) -> int:
    words = len(str(narration or "").split())
    # Higher word count → higher information density
    return clamp(30 + words * 4, 20, 100)


def _importance(idx: int, total: int, narration: str) -> int:
    text = (narration or "").lower()
    score = 55
    if idx == 0:
        score += 25  # hook scene
    if idx == total - 1:
        score += 10  # payoff
    if any(w in text for w in ("notice", "look", "key", "secret", "surprising", "because")):
        score += 12
    return clamp(score, 20, 100)


def choose_pacing(
    *,
    attention: int,
    density: int,
    movement: int,
    importance: int,
    index: int,
) -> tuple[float, str, str]:
    """Return (duration_sec, label, reason). Visual change every few seconds."""
    # Hook always fast — first-3s survival
    if index == 0:
        return 2.0, "cut_2s", "Hook window — rapid visual payoff"
    if importance >= 85 and attention >= 70:
        return 2.2, "cut_2s", "High-importance beat — keep energy high"
    if density >= 75:
        return 2.3, "montage", "High information density → faster cuts"
    if attention < 60:
        return 1.9, "cut_2s", "Low attention risk → accelerate before drop-off"
    # Mid-video pattern interrupt: every 3rd beat shift rhythm
    if index % 3 == 2:
        return 2.2, "zoom_rhythm", "Forced visual variety every few seconds"
    if importance >= 80 and density < 50 and index > 2:
        return 3.6, "dramatic_pause", "Payoff breathe — only after setup"
    if movement >= 70:
        return 2.8, "motion_rhythm", "Strong motion carries slightly longer hold"
    if importance >= 70:
        return 2.6, "cut_3s", "Balanced educational beat"
    return 2.4, "cut_3s", "Default energetic short-form pacing"


def build_pacing_plan(candidate: dict) -> list[ScenePacing]:
    scenes = _scenes(candidate)
    if not scenes:
        # Synthetic single-beat plan from script length estimate
        return [
            ScenePacing(
                scene_id="hook",
                duration_sec=2.5,
                pacing_label="cut_2s",
                attention_score=80,
                information_density=60,
                movement_intensity=70,
                importance=90,
                reason="No scenes yet — seed hook pacing",
            )
        ]

    plan: list[ScenePacing] = []
    total = len(scenes)
    for i, scene in enumerate(scenes):
        sid = str(scene.get("scene_id") or scene.get("id") or f"s{i+1}")
        narration = str(scene.get("narration") or scene.get("voiceover") or "")
        attention = int(scene.get("expected_attention_score") or scene.get("attention_score") or 65)
        movement = int(
            (scene.get("motion_plan") or {}).get("intensity")
            or scene.get("movement_intensity")
            or 55
        )
        density = _density(narration)
        importance = _importance(i, total, narration)
        duration, label, reason = choose_pacing(
            attention=attention,
            density=density,
            movement=movement,
            importance=importance,
            index=i,
        )
        # Cap static holds — educational shorts need a visual change every few seconds
        if label not in ("dramatic_pause",) and duration > 3.2:
            duration = 3.2
            reason += " (capped for retention)"
        elif label == "dramatic_pause" and duration > 4.0:
            duration = 4.0
            reason += " (payoff pause capped)"
        plan.append(
            ScenePacing(
                scene_id=sid,
                duration_sec=round(duration, 2),
                pacing_label=label if label in _PACING_LABELS else "cut_3s",
                attention_score=attention,
                information_density=density,
                movement_intensity=movement,
                importance=importance,
                reason=reason,
            )
        )
    return plan


def pacing_variety_score(plan: list[ScenePacing]) -> int:
    if not plan:
        return 40
    labels = {p.pacing_label for p in plan}
    durations = [p.duration_sec for p in plan]
    spread = max(durations) - min(durations) if durations else 0
    score = 50 + min(30, len(labels) * 8) + min(20, int(spread * 8))
    if any(d > 6 for d in durations):
        score -= 15
    return clamp(score, 0, 100)
