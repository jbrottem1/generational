"""Professional shot vocabulary — the Director's camera department.

Fourteen shot types with real cinematography metadata (lens, depth of field,
camera motion, motion intensity, energy). Scene purposes map to shot
sequences so every script becomes a professional shot list, and the shot
table is data — adding a shot type never touches the planner.
"""

from __future__ import annotations

# The professional shot vocabulary. Each entry is one complete camera setup.
SHOT_TYPES = {
    "wide": {
        "label": "Wide",
        "lens": "18mm wide, f/8",
        "depth_of_field": "deep focus — environment and subject sharp",
        "camera_motion": "slow lateral drift",
        "motion_intensity": 30,
        "energy": "establishing",
    },
    "medium": {
        "label": "Medium",
        "lens": "35mm prime, f/2.8",
        "depth_of_field": "moderate — subject sharp, background readable",
        "camera_motion": "handheld drift",
        "motion_intensity": 45,
        "energy": "conversational",
    },
    "close_up": {
        "label": "Close-Up",
        "lens": "85mm prime, f/1.8",
        "depth_of_field": "shallow — face sharp, background melts",
        "camera_motion": "slow push-in",
        "motion_intensity": 40,
        "energy": "intimate",
    },
    "extreme_close_up": {
        "label": "Extreme Close-Up",
        "lens": "100mm macro, f/2.8",
        "depth_of_field": "razor thin — single detail in focus",
        "camera_motion": "crash zoom",
        "motion_intensity": 85,
        "energy": "arresting",
    },
    "drone": {
        "label": "Drone",
        "lens": "24mm aerial, f/5.6",
        "depth_of_field": "deep focus — full landscape sharp",
        "camera_motion": "drone rise",
        "motion_intensity": 70,
        "energy": "scale reveal",
    },
    "pov": {
        "label": "POV",
        "lens": "21mm wide, f/4",
        "depth_of_field": "natural — mimics human vision",
        "camera_motion": "first-person handheld",
        "motion_intensity": 65,
        "energy": "immersive",
    },
    "tracking": {
        "label": "Tracking",
        "lens": "35mm anamorphic, f/2.8",
        "depth_of_field": "moderate — subject locked, world streaking past",
        "camera_motion": "tracking",
        "motion_intensity": 65,
        "energy": "propulsive",
    },
    "orbit": {
        "label": "Orbit",
        "lens": "50mm prime, f/2.0",
        "depth_of_field": "shallow — hero subject isolated",
        "camera_motion": "orbit",
        "motion_intensity": 60,
        "energy": "reverent",
    },
    "push_in": {
        "label": "Push-In",
        "lens": "40mm prime, f/2.2",
        "depth_of_field": "tightening — focus narrows as camera closes",
        "camera_motion": "slow push-in",
        "motion_intensity": 45,
        "energy": "building tension",
    },
    "pull_out": {
        "label": "Pull-Out",
        "lens": "32mm prime, f/4",
        "depth_of_field": "widening — context revealed on the move",
        "camera_motion": "slow pull-back",
        "motion_intensity": 40,
        "energy": "context reveal",
    },
    "static": {
        "label": "Static",
        "lens": "50mm prime, f/2.0",
        "depth_of_field": "moderate — composed and stable",
        "camera_motion": "locked-off",
        "motion_intensity": 15,
        "energy": "sincere",
    },
    "macro": {
        "label": "Macro",
        "lens": "100mm macro, f/4",
        "depth_of_field": "paper thin — texture becomes landscape",
        "camera_motion": "micro slider",
        "motion_intensity": 35,
        "energy": "hypnotic detail",
    },
    "slow_motion": {
        "label": "Slow Motion",
        "lens": "85mm prime at 120fps, f/1.4",
        "depth_of_field": "shallow — every particle visible",
        "camera_motion": "slow-motion settle",
        "motion_intensity": 55,
        "energy": "suspended payoff",
    },
    "hyperlapse": {
        "label": "Hyperlapse",
        "lens": "20mm wide, f/8",
        "depth_of_field": "deep focus — world compressing through time",
        "camera_motion": "hyperlapse",
        "motion_intensity": 90,
        "energy": "time compression",
    },
}

# Which shots each scene purpose cycles through. The Director alternates
# within the sequence so consecutive story beats never repeat a setup.
PURPOSE_SHOT_SEQUENCES = {
    "hook": ["extreme_close_up"],
    "pattern_interrupt": ["pov"],
    "curiosity_loop": ["push_in"],
    "story_beat": ["medium", "tracking", "drone", "macro", "wide", "hyperlapse"],
    "payoff": ["slow_motion", "orbit"],
    "cta": ["static"],
}


def shot_for(purpose: str, occurrence: int = 0) -> "tuple[str, dict]":
    """Pick the shot for the Nth occurrence of a purpose (variety by rotation)."""
    sequence = PURPOSE_SHOT_SEQUENCES.get(purpose, ["medium"])
    key = sequence[occurrence % len(sequence)]
    return key, SHOT_TYPES[key]


def build_shot_list(scenes: list) -> list:
    """Convert the storyboard into a professional shot list."""
    return [
        {
            "shot_number": scene["scene_number"],
            "shot_type": scene.get("shot_type", "medium"),
            "shot_label": SHOT_TYPES.get(scene.get("shot_type", "medium"), SHOT_TYPES["medium"])["label"],
            "duration_sec": scene["length_sec"],
            "purpose": scene["purpose"],
            "lens": scene.get("lens_recommendation", ""),
            "depth_of_field": scene.get("depth_of_field", ""),
            "camera_motion": scene.get("camera_motion", ""),
            "composition": scene.get("shot_composition", ""),
            "description": scene.get("visual_description", ""),
        }
        for scene in scenes
    ]
