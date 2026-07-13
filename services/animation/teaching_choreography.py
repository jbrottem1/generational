"""Purposeful teaching choreography — The Generational Method.

Gestures fire only on lesson beats. Default = calm confident idle.
"""

from __future__ import annotations

from typing import Any


# Normalized timeline 0–1 for a standard Generational Method Short
DEFAULT_LESSON_BEATS: list[dict[str, Any]] = [
    # Hook — still, eye contact
    {"start": 0.00, "end": 0.08, "gesture": "idle", "walk": 0.0, "label": "hook"},
    # Micro think before demo
    {"start": 0.08, "end": 0.11, "gesture": "think", "walk": 0.0, "label": "think"},
    # Demonstration — point at what is happening
    {"start": 0.11, "end": 0.42, "gesture": "point", "walk": 0.0, "label": "demonstrate"},
    # Brief purposeful step toward the board/demo (one walk only)
    {"start": 0.42, "end": 0.48, "gesture": "idle", "walk": 1.0, "label": "walk_to_explain"},
    # Explanation — calm present once, then idle
    {"start": 0.48, "end": 0.52, "gesture": "present", "walk": 0.0, "label": "explain_open"},
    {"start": 0.52, "end": 0.68, "gesture": "idle", "walk": 0.0, "label": "explain"},
    # Real-world — point again at analogy
    {"start": 0.68, "end": 0.82, "gesture": "point", "walk": 0.0, "label": "real_world"},
    # Takeaway — still and clear
    {"start": 0.82, "end": 0.94, "gesture": "idle", "walk": 0.0, "label": "takeaway"},
    # Curiosity bridge — tiny react optional
    {"start": 0.94, "end": 1.00, "gesture": "idle", "walk": 0.0, "label": "bridge"},
]

# Bowling lesson: push during heavy-ball beat
BOWLING_BEATS: list[dict[str, Any]] = [
    {"start": 0.00, "end": 0.07, "gesture": "idle", "walk": 0.0, "label": "hook"},
    {"start": 0.07, "end": 0.10, "gesture": "think", "walk": 0.0, "label": "think"},
    {"start": 0.10, "end": 0.22, "gesture": "point", "walk": 0.0, "label": "show_both"},
    {"start": 0.22, "end": 0.40, "gesture": "push", "walk": 0.0, "label": "push_light"},
    {"start": 0.40, "end": 0.45, "gesture": "idle", "walk": 0.35, "label": "step"},
    {"start": 0.45, "end": 0.62, "gesture": "push", "walk": 0.0, "label": "push_heavy"},
    {"start": 0.62, "end": 0.78, "gesture": "point", "walk": 0.0, "label": "name_concepts"},
    {"start": 0.78, "end": 0.92, "gesture": "idle", "walk": 0.0, "label": "real_world"},
    {"start": 0.92, "end": 1.00, "gesture": "idle", "walk": 0.0, "label": "takeaway"},
]

# Gravity lesson: point at globe/apple; react once when arrows appear
GRAVITY_BEATS: list[dict[str, Any]] = [
    {"start": 0.00, "end": 0.08, "gesture": "idle", "walk": 0.0, "label": "hook"},
    {"start": 0.08, "end": 0.11, "gesture": "think", "walk": 0.0, "label": "think"},
    {"start": 0.11, "end": 0.35, "gesture": "point", "walk": 0.0, "label": "apple_falls"},
    {"start": 0.35, "end": 0.40, "gesture": "react", "walk": 0.0, "label": "arrows_reveal"},
    {"start": 0.40, "end": 0.45, "gesture": "idle", "walk": 0.3, "label": "step"},
    {"start": 0.45, "end": 0.70, "gesture": "point", "walk": 0.0, "label": "center"},
    {"start": 0.70, "end": 0.88, "gesture": "idle", "walk": 0.0, "label": "explain"},
    {"start": 0.88, "end": 1.00, "gesture": "idle", "walk": 0.0, "label": "takeaway"},
]

# Biology Academy — purposeful lab teaching (point / present / one step)
BIO_DEFAULT_BEATS: list[dict[str, Any]] = [
    {"start": 0.00, "end": 0.10, "gesture": "idle", "walk": 0.0, "label": "hook"},
    {"start": 0.10, "end": 0.13, "gesture": "think", "walk": 0.0, "label": "think"},
    {"start": 0.13, "end": 0.40, "gesture": "point", "walk": 0.0, "label": "demonstrate"},
    {"start": 0.40, "end": 0.46, "gesture": "idle", "walk": 0.4, "label": "step"},
    {"start": 0.46, "end": 0.52, "gesture": "present", "walk": 0.0, "label": "explain_open"},
    {"start": 0.52, "end": 0.72, "gesture": "point", "walk": 0.0, "label": "explain"},
    {"start": 0.72, "end": 0.88, "gesture": "idle", "walk": 0.0, "label": "real_world"},
    {"start": 0.88, "end": 1.00, "gesture": "idle", "walk": 0.0, "label": "takeaway"},
]

BIO_IMMUNE_BEATS: list[dict[str, Any]] = [
    {"start": 0.00, "end": 0.12, "gesture": "idle", "walk": 0.0, "label": "hook"},
    {"start": 0.12, "end": 0.15, "gesture": "think", "walk": 0.0, "label": "think"},
    {"start": 0.15, "end": 0.40, "gesture": "point", "walk": 0.0, "label": "patrol"},
    {"start": 0.40, "end": 0.45, "gesture": "react", "walk": 0.0, "label": "match"},
    {"start": 0.45, "end": 0.50, "gesture": "idle", "walk": 0.3, "label": "step"},
    {"start": 0.50, "end": 0.72, "gesture": "point", "walk": 0.0, "label": "tag"},
    {"start": 0.72, "end": 0.90, "gesture": "idle", "walk": 0.0, "label": "protect"},
    {"start": 0.90, "end": 1.00, "gesture": "idle", "walk": 0.0, "label": "takeaway"},
]

BIO_MUSCLE_BEATS: list[dict[str, Any]] = [
    {"start": 0.00, "end": 0.10, "gesture": "idle", "walk": 0.0, "label": "hook"},
    {"start": 0.10, "end": 0.13, "gesture": "think", "walk": 0.0, "label": "think"},
    {"start": 0.13, "end": 0.35, "gesture": "push", "walk": 0.0, "label": "stress"},
    {"start": 0.35, "end": 0.42, "gesture": "idle", "walk": 0.35, "label": "step"},
    {"start": 0.42, "end": 0.65, "gesture": "point", "walk": 0.0, "label": "repair"},
    {"start": 0.65, "end": 0.85, "gesture": "present", "walk": 0.0, "label": "grow"},
    {"start": 0.85, "end": 1.00, "gesture": "idle", "walk": 0.0, "label": "takeaway"},
]

# MacroCenter flagship — interact with hologram membrane (calm default)
MACRO_MEMBRANE_BEATS: list[dict[str, Any]] = [
    {"start": 0.00, "end": 0.08, "gesture": "idle", "walk": 0.0, "label": "welcome"},
    {"start": 0.08, "end": 0.12, "gesture": "present", "walk": 0.0, "label": "open_arms"},
    {"start": 0.12, "end": 0.16, "gesture": "think", "walk": 0.0, "label": "hook"},
    {"start": 0.16, "end": 0.30, "gesture": "point", "walk": 0.0, "label": "chaos"},
    {"start": 0.30, "end": 0.36, "gesture": "idle", "walk": 0.4, "label": "step_to_holo"},
    {"start": 0.36, "end": 0.50, "gesture": "point", "walk": 0.0, "label": "bilayer"},
    {"start": 0.50, "end": 0.58, "gesture": "present", "walk": 0.0, "label": "heads_tails"},
    {"start": 0.58, "end": 0.70, "gesture": "idle", "walk": 0.0, "label": "explain"},
    {"start": 0.70, "end": 0.82, "gesture": "push", "walk": 0.0, "label": "selective"},
    {"start": 0.82, "end": 0.90, "gesture": "point", "walk": 0.0, "label": "gates"},
    {"start": 0.90, "end": 1.00, "gesture": "idle", "walk": 0.0, "label": "takeaway"},
]

# MacroCenter V2 — dense reveals; calm default; action only when teaching
MACRO_MEMBRANE_V2_BEATS: list[dict[str, Any]] = [
    {"start": 0.00, "end": 0.08, "gesture": "idle", "walk": 0.0, "label": "hook"},
    {"start": 0.08, "end": 0.12, "gesture": "point", "walk": 0.0, "label": "watch"},
    {"start": 0.12, "end": 0.32, "gesture": "point", "walk": 0.0, "label": "allow"},
    {"start": 0.32, "end": 0.36, "gesture": "react", "walk": 0.0, "label": "block_react"},
    {"start": 0.36, "end": 0.46, "gesture": "push", "walk": 0.0, "label": "block"},
    {"start": 0.46, "end": 0.52, "gesture": "idle", "walk": 0.35, "label": "step"},
    {"start": 0.52, "end": 0.62, "gesture": "present", "walk": 0.0, "label": "bilayer"},
    {"start": 0.62, "end": 0.78, "gesture": "point", "walk": 0.0, "label": "gates"},
    {"start": 0.78, "end": 0.90, "gesture": "idle", "walk": 0.0, "label": "takeaway"},
    {"start": 0.90, "end": 1.00, "gesture": "idle", "walk": 0.0, "label": "bridge"},
]

PLANS: dict[str, list[dict[str, Any]]] = {
    "default": DEFAULT_LESSON_BEATS,
    "bowling_momentum": BOWLING_BEATS,
    "gravity_direction": GRAVITY_BEATS,
    "bio_cells": BIO_DEFAULT_BEATS,
    "bio_dna": BIO_DEFAULT_BEATS,
    "bio_immune": BIO_IMMUNE_BEATS,
    "bio_muscle": BIO_MUSCLE_BEATS,
    "bio_oxygen": BIO_DEFAULT_BEATS,
    "macro_cell_membrane": MACRO_MEMBRANE_BEATS,
    "macro_cell_membrane_v2": MACRO_MEMBRANE_V2_BEATS,
    "excellence_stomach": [
        {"start": 0.00, "end": 0.12, "gesture": "idle", "walk": 0.0, "label": "show"},
        {"start": 0.12, "end": 0.16, "gesture": "think", "walk": 0.0, "label": "mystery"},
        {"start": 0.16, "end": 0.28, "gesture": "point", "walk": 0.0, "label": "question"},
        {"start": 0.28, "end": 0.34, "gesture": "react", "walk": 0.0, "label": "reveal"},
        {"start": 0.34, "end": 0.48, "gesture": "present", "walk": 0.0, "label": "mucus"},
        {"start": 0.48, "end": 0.54, "gesture": "idle", "walk": 0.25, "label": "step"},
        {"start": 0.54, "end": 0.68, "gesture": "point", "walk": 0.0, "label": "renew"},
        {"start": 0.68, "end": 0.86, "gesture": "idle", "walk": 0.0, "label": "clarity"},
        {"start": 0.86, "end": 1.00, "gesture": "idle", "walk": 0.0, "label": "takeaway"},
    ],
    "excellence_brain_energy": [
        {"start": 0.00, "end": 0.10, "gesture": "idle", "walk": 0.0, "label": "hook"},
        {"start": 0.10, "end": 0.14, "gesture": "think", "walk": 0.0, "label": "curiosity"},
        {"start": 0.14, "end": 0.28, "gesture": "point", "walk": 0.0, "label": "show_energy"},
        {"start": 0.28, "end": 0.36, "gesture": "react", "walk": 0.0, "label": "wait_what"},
        {"start": 0.36, "end": 0.42, "gesture": "present", "walk": 0.0, "label": "reveal_numbers"},
        {"start": 0.42, "end": 0.48, "gesture": "idle", "walk": 0.3, "label": "step"},
        {"start": 0.48, "end": 0.62, "gesture": "point", "walk": 0.0, "label": "neurons"},
        {"start": 0.62, "end": 0.80, "gesture": "idle", "walk": 0.0, "label": "real_world"},
        {"start": 0.80, "end": 1.00, "gesture": "idle", "walk": 0.0, "label": "punchline"},
    ],
    "skydive_stomach": [
        {"start": 0.00, "end": 0.10, "gesture": "idle", "walk": 0.0, "label": "door"},
        {"start": 0.10, "end": 0.18, "gesture": "present", "walk": 0.0, "label": "jump"},
        {"start": 0.18, "end": 0.32, "gesture": "point", "walk": 0.0, "label": "show_acid"},
        {"start": 0.32, "end": 0.38, "gesture": "think", "walk": 0.0, "label": "question"},
        {"start": 0.38, "end": 0.48, "gesture": "point", "walk": 0.0, "label": "intact"},
        {"start": 0.48, "end": 0.55, "gesture": "react", "walk": 0.0, "label": "reveal"},
        {"start": 0.55, "end": 0.68, "gesture": "present", "walk": 0.0, "label": "mucus"},
        {"start": 0.68, "end": 0.82, "gesture": "idle", "walk": 0.0, "label": "analogy"},
        {"start": 0.82, "end": 0.90, "gesture": "idle", "walk": 0.0, "label": "takeaway"},
        {"start": 0.90, "end": 0.96, "gesture": "react", "walk": 0.0, "label": "impact"},
        {"start": 0.96, "end": 1.00, "gesture": "wave", "walk": 0.0, "label": "bye"},
    ],
    # Project Fluid Motion — sparse beats; stillness is intentional; one walk only
    "fluid_cells": [
        {"start": 0.00, "end": 0.14, "gesture": "idle", "walk": 0.0, "label": "hook_still"},
        {"start": 0.14, "end": 0.20, "gesture": "think", "walk": 0.0, "label": "curiosity"},
        {"start": 0.20, "end": 0.24, "gesture": "idle", "walk": 0.0, "label": "pause_before"},
        {"start": 0.24, "end": 0.42, "gesture": "point", "walk": 0.0, "label": "show_cells"},
        {"start": 0.42, "end": 0.50, "gesture": "idle", "walk": 0.45, "label": "step_to_demo"},
        {"start": 0.50, "end": 0.58, "gesture": "present", "walk": 0.0, "label": "invite"},
        {"start": 0.58, "end": 0.62, "gesture": "idle", "walk": 0.0, "label": "pause_reveal"},
        {"start": 0.62, "end": 0.78, "gesture": "point", "walk": 0.0, "label": "reveal"},
        {"start": 0.78, "end": 0.92, "gesture": "idle", "walk": 0.0, "label": "land"},
        {"start": 0.92, "end": 1.00, "gesture": "idle", "walk": 0.0, "label": "takeaway"},
    ],
    # PROJECT FOUNDATION — white studio + whiteboard writing
    "foundation_f_equals_ma": [
        {"start": 0.00, "end": 0.08, "gesture": "idle", "walk": 0.0, "label": "welcome"},
        {"start": 0.08, "end": 0.14, "gesture": "think", "walk": 0.0, "label": "question"},
        {"start": 0.14, "end": 0.22, "gesture": "idle", "walk": 0.55, "label": "walk_to_board"},
        {"start": 0.22, "end": 0.42, "gesture": "write", "walk": 0.0, "label": "write_equation"},
        {"start": 0.42, "end": 0.58, "gesture": "point", "walk": 0.0, "label": "explain_terms"},
        {"start": 0.58, "end": 0.72, "gesture": "present", "walk": 0.0, "label": "cart_example"},
        {"start": 0.72, "end": 0.82, "gesture": "point", "walk": 0.0, "label": "circle_key"},
        {"start": 0.82, "end": 0.94, "gesture": "idle", "walk": 0.0, "label": "summary"},
        {"start": 0.94, "end": 1.00, "gesture": "idle", "walk": 0.0, "label": "next"},
    ],
    "foundation_force_mass": [
        {"start": 0.00, "end": 0.08, "gesture": "idle", "walk": 0.0, "label": "welcome"},
        {"start": 0.08, "end": 0.14, "gesture": "think", "walk": 0.0, "label": "question"},
        {"start": 0.14, "end": 0.22, "gesture": "idle", "walk": 0.55, "label": "walk_to_board"},
        {"start": 0.22, "end": 0.40, "gesture": "write", "walk": 0.0, "label": "write_a_equals"},
        {"start": 0.40, "end": 0.55, "gesture": "point", "walk": 0.0, "label": "inertia"},
        {"start": 0.55, "end": 0.70, "gesture": "push", "walk": 0.0, "label": "need_more_force"},
        {"start": 0.70, "end": 0.84, "gesture": "write", "walk": 0.0, "label": "return_to_fma"},
        {"start": 0.84, "end": 0.94, "gesture": "idle", "walk": 0.0, "label": "summary"},
        {"start": 0.94, "end": 1.00, "gesture": "idle", "walk": 0.0, "label": "next"},
    ],
    "foundation_newton_everyday": [
        {"start": 0.00, "end": 0.08, "gesture": "idle", "walk": 0.0, "label": "welcome"},
        {"start": 0.08, "end": 0.14, "gesture": "think", "walk": 0.0, "label": "question"},
        {"start": 0.14, "end": 0.20, "gesture": "idle", "walk": 0.50, "label": "walk_to_board"},
        {"start": 0.20, "end": 0.32, "gesture": "write", "walk": 0.0, "label": "write_fma"},
        {"start": 0.32, "end": 0.50, "gesture": "point", "walk": 0.0, "label": "cars_sports"},
        {"start": 0.50, "end": 0.68, "gesture": "present", "walk": 0.0, "label": "furniture_bike"},
        {"start": 0.68, "end": 0.82, "gesture": "point", "walk": 0.0, "label": "connect"},
        {"start": 0.82, "end": 0.94, "gesture": "idle", "walk": 0.0, "label": "summary"},
        {"start": 0.94, "end": 1.00, "gesture": "idle", "walk": 0.0, "label": "next"},
    ],
    "foundation_confirmation_bias": [
        {"start": 0.00, "end": 0.08, "gesture": "idle", "walk": 0.0, "label": "welcome"},
        {"start": 0.08, "end": 0.14, "gesture": "think", "walk": 0.0, "label": "question"},
        {"start": 0.14, "end": 0.22, "gesture": "idle", "walk": 0.55, "label": "walk_to_board"},
        {"start": 0.22, "end": 0.42, "gesture": "write", "walk": 0.0, "label": "write_term"},
        {"start": 0.42, "end": 0.58, "gesture": "point", "walk": 0.0, "label": "explain"},
        {"start": 0.58, "end": 0.72, "gesture": "present", "walk": 0.0, "label": "examples"},
        {"start": 0.72, "end": 0.84, "gesture": "point", "walk": 0.0, "label": "circle_key"},
        {"start": 0.84, "end": 0.94, "gesture": "idle", "walk": 0.0, "label": "summary"},
        {"start": 0.94, "end": 1.00, "gesture": "idle", "walk": 0.0, "label": "next"},
    ],
    # Batesian mimicry biology benchmark — Reality panels synced to point beats
    "foundation_batesian_101": [
        {"start": 0.00, "end": 0.10, "gesture": "think", "walk": 0.0, "label": "curiosity"},
        {"start": 0.10, "end": 0.18, "gesture": "idle", "walk": 0.50, "label": "walk_to_board"},
        {"start": 0.18, "end": 0.28, "gesture": "point", "walk": 0.0, "label": "show_hoverfly"},
        {"start": 0.28, "end": 0.38, "gesture": "idle", "walk": 0.0, "label": "hold_photo"},
        {"start": 0.38, "end": 0.55, "gesture": "write", "walk": 0.0, "label": "write_term"},
        {"start": 0.55, "end": 0.68, "gesture": "point", "walk": 0.0, "label": "compare_wasp"},
        {"start": 0.68, "end": 0.78, "gesture": "present", "walk": 0.0, "label": "stripe_highlight"},
        {"start": 0.78, "end": 0.88, "gesture": "point", "walk": 0.0, "label": "circle"},
        {"start": 0.88, "end": 0.94, "gesture": "idle", "walk": 0.0, "label": "takeaway"},
        {"start": 0.94, "end": 1.00, "gesture": "idle", "walk": 0.0, "label": "bridge"},
    ],
    "foundation_coral_102": [
        {"start": 0.00, "end": 0.12, "gesture": "think", "walk": 0.0, "label": "curiosity"},
        {"start": 0.12, "end": 0.18, "gesture": "idle", "walk": 0.35, "label": "walk_to_board"},
        {"start": 0.18, "end": 0.28, "gesture": "point", "walk": 0.0, "label": "show_snakes"},
        {"start": 0.28, "end": 0.38, "gesture": "idle", "walk": 0.0, "label": "hold"},
        {"start": 0.38, "end": 0.52, "gesture": "point", "walk": 0.0, "label": "compare"},
        {"start": 0.52, "end": 0.62, "gesture": "idle", "walk": 0.0, "label": "pause"},
        {"start": 0.62, "end": 0.72, "gesture": "present", "walk": 0.0, "label": "warning"},
        {"start": 0.72, "end": 0.82, "gesture": "write", "walk": 0.0, "label": "rhyme_limit"},
        {"start": 0.82, "end": 0.90, "gesture": "point", "walk": 0.0, "label": "safety"},
        {"start": 0.90, "end": 1.00, "gesture": "idle", "walk": 0.0, "label": "takeaway"},
    ],
    "foundation_bluffing_103": [
        {"start": 0.00, "end": 0.12, "gesture": "think", "walk": 0.0, "label": "curiosity"},
        {"start": 0.12, "end": 0.18, "gesture": "idle", "walk": 0.35, "label": "walk_to_board"},
        {"start": 0.18, "end": 0.28, "gesture": "point", "walk": 0.0, "label": "show_mimics"},
        {"start": 0.28, "end": 0.38, "gesture": "idle", "walk": 0.0, "label": "hold"},
        {"start": 0.38, "end": 0.48, "gesture": "point", "walk": 0.0, "label": "examples"},
        {"start": 0.48, "end": 0.58, "gesture": "idle", "walk": 0.0, "label": "pause"},
        {"start": 0.58, "end": 0.68, "gesture": "present", "walk": 0.0, "label": "monarch_viceroy"},
        {"start": 0.68, "end": 0.78, "gesture": "write", "walk": 0.0, "label": "arms_race"},
        {"start": 0.78, "end": 0.88, "gesture": "point", "walk": 0.0, "label": "explain"},
        {"start": 0.88, "end": 1.00, "gesture": "idle", "walk": 0.0, "label": "takeaway"},
    ],
    # Foundation V2 — Origin of Turtles (15–30s, pointer-driven)
    "foundation_v2_turtle_202": [
        {"start": 0.00, "end": 0.08, "gesture": "think", "walk": 0.0, "label": "hook"},
        {"start": 0.08, "end": 0.14, "gesture": "idle", "walk": 0.45, "label": "walk_to_board"},
        {"start": 0.14, "end": 0.22, "gesture": "point", "walk": 0.0, "label": "show_turtle"},
        {"start": 0.22, "end": 0.30, "gesture": "point", "walk": 0.0, "label": "timeline"},
        {"start": 0.30, "end": 0.38, "gesture": "present", "walk": 0.0, "label": "early_reptiles"},
        {"start": 0.38, "end": 0.42, "gesture": "idle", "walk": 0.0, "label": "pause"},
        {"start": 0.42, "end": 0.52, "gesture": "write", "walk": 0.0, "label": "shell_sketch"},
        {"start": 0.52, "end": 0.58, "gesture": "point", "walk": 0.0, "label": "gradual"},
        {"start": 0.58, "end": 0.68, "gesture": "point", "walk": 0.0, "label": "fossils"},
        {"start": 0.68, "end": 0.78, "gesture": "idle", "walk": 0.0, "label": "hold_fossil"},
        {"start": 0.78, "end": 0.88, "gesture": "present", "walk": 0.0, "label": "connect"},
        {"start": 0.88, "end": 1.00, "gesture": "idle", "walk": 0.0, "label": "takeaway"},
    ],
}


def resolve_beat(plan: list[dict[str, Any]], p: float) -> dict[str, Any]:
    p = max(0.0, min(1.0, float(p)))
    for beat in plan:
        if float(beat["start"]) <= p < float(beat["end"]):
            return beat
    return plan[-1]


def choreography_at(
    t: float,
    duration: float,
    *,
    plan_id: str | None = None,
) -> dict[str, Any]:
    """Return purposeful gesture/walk for time t."""
    plan = PLANS.get(plan_id or "default") or DEFAULT_LESSON_BEATS
    p = t / max(duration, 0.1)
    beat = resolve_beat(plan, p)
    return {
        "gesture": str(beat.get("gesture") or "idle"),
        "walk": float(beat.get("walk") or 0.0),
        "label": str(beat.get("label") or ""),
        "p": p,
    }
