"""DOCTOR_001 — biography, personality, voice, teaching style (locked IP)."""

from __future__ import annotations

from typing import Any

from services.studio_assets.doctor_001.catalog import (
    ASSET_VERSION,
    CHARACTER_ID,
    DISPLAY_NAME,
    LEGACY_ALIAS,
)


COLOR_PALETTE: dict[str, Any] = {
    "primary": {"name": "Medical White", "hex": "#F4F7FA", "rgb": [244, 247, 250]},
    "secondary": {"name": "Premium Titanium", "hex": "#8A939E", "rgb": [138, 147, 158]},
    "navy_underlayer": {"name": "Deep Navy", "hex": "#1B2A4A", "rgb": [27, 42, 74]},
    "accent": {"name": "Warm Trust Cyan", "hex": "#3BA7E0", "rgb": [59, 167, 224]},
    "deep_accent": {"name": "Deep Clinical Blue", "hex": "#1A5F8A", "rgb": [26, 95, 138]},
    "chassis_shadow": {"name": "Chassis Shadow", "hex": "#2C343D", "rgb": [44, 52, 61]},
    "eye_core": {"name": "Intelligent Eye Core", "hex": "#7FD4FF", "rgb": [127, 212, 255]},
    "interface_ok": {"name": "Vitals OK", "hex": "#3DDC97", "rgb": [61, 220, 151]},
    "interface_warn": {"name": "Caution", "hex": "#F0C040", "rgb": [240, 192, 64]},
    "emergency": {"name": "Alert", "hex": "#E85D4C", "rgb": [232, 93, 76]},
    "forbid_random_palette_drift": True,
    "master_concept_art": "data/studio_assets/DOCTOR_001/MASTER_CONCEPT_ART/",
}


def identity_core() -> dict[str, Any]:
    return {
        "character_id": CHARACTER_ID,
        "legacy_alias": LEGACY_ALIAS,
        "name": DISPLAY_NAME,
        "version": ASSET_VERSION,
        "status": "permanent",
        "role": "Canonical Medical Educator — Generational Universe",
        "universe": "Generational",
        "style_mode": "cinematic_realism",
        "archetype": "humanoid_cyborg_physician_educator",
        "home_world_id": "LOC-GMRI",
        "home_world_name": "The Generational Medical Research Institute",
        "continuity_law": "Visually identical across every future video. Never regenerate from scratch.",
        "human_realism_framework": "HUMAN_REALISM_FRAMEWORK_V1",
        "is_gold_standard": True,
        "proportions": {
            "height_cm": 185,
            "head_height_ratio": 0.125,
            "shoulder_width_ratio": 0.26,
            "arm_span_to_height": 1.0,
            "leg_length_ratio": 0.48,
            "build": "athletic_approachable_humanoid",
        },
        "silhouette_keys": [
            "white_medical_chassis",
            "warm_blue_chest_interface",
            "intelligent_eye_cores",
            "rounded_friendly_cranial_form",
            "professional_open_posture",
        ],
        "forbid": [
            "generic_robot",
            "uncanny_horror",
            "stick_figure",
            "palette_drift",
            "regenerate_per_episode",
            "episode_only_redesign",
        ],
    }


def biography_md() -> str:
    return f"""# {DISPLAY_NAME} — Permanent Biography

**Character ID:** `{CHARACTER_ID}`  
**Legacy alias:** `{LEGACY_ALIAS}`  
**Version:** `{ASSET_VERSION}`  
**Status:** Permanent Generational Studio Character

## Origin

The Doctor is the first permanent Generational Studio Character — not an episode prop,
not a one-off generation. Commissioned as company intellectual property: a humanoid
cyborg physician-educator who unites clinical precision with warm, approachable teaching.

## Purpose

Serve as the canonical medical educator for the entire Generational Universe across
science, biology, medicine, anatomy, health, chemistry, and related educational series.

## Mission

Help every learner understand the human body and medical science with clarity,
compassion, and curiosity. Never intimidate. Never condescend. Always show the evidence.

## Education & knowledge domains

Medicine · molecular biology · anatomy · physiology · immunology · medical imaging ·
public health · chemistry fundamentals · physics of everyday medical tools ·
trustworthy clinical AI literacy.

## Personality essence

Highly intelligent · patient · curious · optimistic · encouraging · evidence-driven ·
never arrogant · never cold industrial.

## Relationships

Works with Generational hosts (Atlas, Nova, Orion, Piper, Luna) as peer educator.
Never redesigns locked Dash / Professor Gen stick IPs; optional careful cameos only.

## Continuity

Every future production must cast `{CHARACTER_ID}` from this Studio Asset package.
Visual identity remains identical across every video.
"""


def personality_profile() -> dict[str, Any]:
    return {
        "character_id": CHARACTER_ID,
        "core_traits": [
            "highly_intelligent",
            "patient",
            "curious",
            "optimistic",
            "encouraging",
            "evidence_driven",
            "compassionate",
            "calm_under_pressure",
        ],
        "social_style": "warm_authority",
        "humor": "gentle_precise_never_mocking",
        "conflict_style": "clarify_then_reassure",
        "learner_stance": "never_condescending",
        "default_energy": 0.55,
        "teaching_energy": 0.65,
        "emergency_energy": 0.75,
    }


def emotional_profile() -> dict[str, Any]:
    return {
        "character_id": CHARACTER_ID,
        "baseline": "calm_compassionate_focus",
        "easy_access": ["curiosity", "compassion", "confidence", "concern", "delight"],
        "rare": ["anger", "panic"],
        "forbidden_performance": ["cruelty", "mockery", "horror_uncanny"],
        "transition_model": ["anticipation", "peak", "recovery", "emotional_residue"],
        "full_body_rule": True,
        "emotion_to_body": {
            "compassion": {"gaze": "soft", "posture": "open", "gesture": "open_palm_reassurance"},
            "curiosity": {"gaze": "forward", "posture": "slight_lean", "gesture": "chin_think"},
            "concern": {"gaze": "topic_then_audience", "posture": "attentive", "gesture": "restrained"},
            "confidence": {"gaze": "direct", "posture": "upright", "gesture": "open_palm_teach"},
            "determination": {"gaze": "locked", "posture": "stable", "gesture": "precise_point"},
            "delight": {"gaze": "bright", "posture": "open", "gesture": "heart_hand"},
        },
    }


def strengths_flaws() -> dict[str, Any]:
    return {
        "character_id": CHARACTER_ID,
        "strengths": [
            "Explains complex medicine in clear steps",
            "Reads learner confusion and adapts pacing",
            "Maintains calm during alarming topics",
            "Pairs evidence with emotional safety",
            "Consistent visual and vocal identity builds trust",
            "Demonstrates before declaring",
        ],
        "flaws": [
            "Can over-detail when fascinated by a mechanism",
            "Sometimes pauses too long while selecting the perfect analogy",
            "Reluctant to speculate beyond evidence (may frustrate sensational framing)",
            "Protective of clinical accuracy — may correct hosts mid-scene",
            "Under-uses humor unless it serves understanding",
        ],
        "growth_edges": [
            "Invite wonder without sacrificing rigor",
            "Share the mic with co-hosts more often",
        ],
    }


def teaching_style_md() -> str:
    return f"""# {DISPLAY_NAME} — Teaching Style

## Principles

1. **Demonstrate before declare** — show the structure, then name it.  
2. **Safety first** — alarming topics arrive with reassurance and next steps.  
3. **One clear idea per beat** — then scaffold complexity.  
4. **Faces teach** — mute storytelling must still communicate.  
5. **Evidence on screen** — diagrams, scans, and models earn claims.  
6. **Never talk down** — respect every learner's intelligence.

## Cadence

- Hook with a human moment  
- Reveal the mechanism  
- Check understanding with a simple reframe  
- Close with agency (what the viewer can do or remember)

## Gesture language

Open palm teach · hologram pinch · clipboard point · scanner sweep · heart-hand greeting.

## Forbidden

Scare tactics · gore for shock · condescension · “miracle cure” hype · redesigning the character mid-series.
"""


def voice_identity() -> dict[str, Any]:
    return {
        "character_id": CHARACTER_ID,
        "voice_profile_id": "VOICE-THE-DOCTOR-001",
        "traits": [
            "professional",
            "calm",
            "confident",
            "friendly",
            "curious",
            "educational",
            "encouraging",
            "warm",
        ],
        "pacing": "natural_educational",
        "tts_hint": {
            "voice": "onyx",
            "model": "tts-1-hd",
            "style": "warm_clinical_educator",
        },
        "prosody": {
            "pitch": "mid_warm",
            "emphasis": "key_medical_terms",
            "pauses": "after_definitions",
        },
        "sync": "designed_for_high_quality_ai_narration_synchronization",
        "failover": "pause_production_do_not_silent_demo_when_configured",
    }


def catch_phrases() -> dict[str, Any]:
    return {
        "character_id": CHARACTER_ID,
        "phrases": [
            "Let's look carefully — clarity is part of the care.",
            "Your body is not a mystery when we examine the evidence.",
            "Fear fades when understanding arrives.",
            "Watch the mechanism — then the name will stick.",
            "Science is not cold. Precision can be kind.",
            "One clear step at a time.",
            "That question is excellent — let's answer it with evidence.",
            "Healthy curiosity is a clinical tool.",
            "I'm here to make the complex human-sized.",
            "Remember: understanding is a form of protection.",
        ],
        "signature_greeting_gesture": "heart_height_open",
        "signature_close": "One clear step at a time.",
    }


def continuity_rules_md() -> str:
    return f"""# Continuity Rules — {DISPLAY_NAME} (`{CHARACTER_ID}`)

1. **Canonical ID is `{CHARACTER_ID}`.** Legacy alias `{LEGACY_ALIAS}` may appear in older pipelines — same character.  
2. **Never regenerate from scratch** for an episode. Always load this Studio Asset.  
3. **Visual identity is locked** — palette, silhouette, proportions, materials.  
4. **Expressions / hands / animations** come only from this package libraries.  
5. **PerformancePlans** required on every scene featuring `{CHARACTER_ID}`.  
6. **Style mode:** feature-film cinematic realism — not uncanny photoreal, not stick art.  
7. **Recognition test:** a viewer must identify The Doctor in silhouette next episode.  
8. **Version upgrades** require VERSION bump + changelog + intentional art direction.  
9. **Do not collapse** into Dash / Professor Gen stick IPs.  
10. **Home world** remains GMRI (`LOC-GMRI`) unless a production explicitly travels.  
11. **Wardrobe variants** may change; silhouette keys must remain readable.  
12. **Voice identity** maps to `VOICE-THE-DOCTOR-001` — do not randomly swap voices.  
13. **Master Concept Art** in `MASTER_CONCEPT_ART/` is the permanent visual identity lock — hero portrait + official reference sheet are recognition keys. Procedural plates must not supersede them.
"""
