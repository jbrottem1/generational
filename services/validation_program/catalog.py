"""V1 Validation Program — 100-video catalog across educational categories."""

from __future__ import annotations

from typing import Any

CATEGORIES: tuple[str, ...] = (
    "biology",
    "physics",
    "astronomy",
    "medicine",
    "psychology",
    "technology",
    "artificial_intelligence",
    "history",
    "engineering",
    "nature",
)

# Mission measurement dimensions (map onto CE / AI / ops — no new scorers)
MEASUREMENT_DIMENSIONS: tuple[str, ...] = (
    "research_accuracy",
    "psychology_effectiveness",
    "hook_strength",
    "story_flow",
    "educational_clarity",
    "world_continuity",
    "visual_quality",
    "cinematic_quality",
    "narration_quality",
    "caption_accuracy",
    "audio_mix",
    "thumbnail_appeal",
    "packaging",
    "overall_professionalism",
)

# 10 topics × 10 categories = 100
_TOPICS: dict[str, tuple[str, ...]] = {
    "biology": (
        "Why Octopuses Have Three Hearts",
        "How Coral Reefs Build Underwater Cities",
        "Why Leaves Change Color in Autumn",
        "How Photosynthesis Stores Solar Energy",
        "Why Bees Are Disappearing",
        "How Memory Forms in the Brain",
        "Why Ice Floats on Water",
        "How Enzymes Speed Up Life",
        "Why Birds Can Migrate Thousands of Miles",
        "How mRNA Instructions Build Proteins",
    ),
    "physics": (
        "What Gravity Really Does to Time",
        "How Magnets Attract Iron",
        "Why Light Behaves Like a Wave and a Particle",
        "How Entropy Explains Everyday Disorder",
        "Why Sound Needs a Medium",
        "How GPS Satellites Measure Time",
        "Why Hot Air Rises",
        "How Electric Currents Create Magnetic Fields",
        "Why Quantum Entanglement Confuses Physicists",
        "How Friction Steals Energy",
    ),
    "astronomy": (
        "How James Webb Sees the First Galaxies",
        "Why the Moon Controls Tides",
        "How Black Holes Bend Time",
        "Why Stars Have Different Colors",
        "How Planets Form From Dust Disks",
        "Why Saturn Has Rings",
        "How Pulsars Keep Cosmic Time",
        "Why the Night Sky Changes Across Seasons",
        "How Solar Flares Affect Earth",
        "Why Exoplanets Are Hard to Spot",
    ),
    "medicine": (
        "How Vaccines Train the Immune System",
        "Why Antibiotics Fail Against Viruses",
        "How Sleep Repairs the Brain",
        "Why Blood Types Matter",
        "How Heart Valves Keep Circulation One-Way",
        "Why Fevers Help Fight Infection",
        "How Insulin Controls Blood Sugar",
        "Why Placebos Sometimes Work",
        "How Anesthesia Turns Consciousness Off Safely",
        "Why Hydration Affects Every Organ",
    ),
    "psychology": (
        "Why Confirmation Bias Feels Like Truth",
        "How Habit Loops Hijack Decisions",
        "Why We Dream",
        "How Attention Cascades Collapse Focus",
        "Why Social Proof Changes Behavior",
        "How Fear Memories Stick",
        "Why Dopamine Anticipates Reward",
        "How Cognitive Load Makes Learning Fail",
        "Why Names Stick Better Than Facts",
        "How Mirror Neurons Shape Empathy",
    ),
    "technology": (
        "How Cameras Capture Light",
        "Why Your Phone Battery Degrades",
        "How Fiber Optics Carry the Internet",
        "Why GPS Needs Relativity Corrections",
        "How Compression Makes Files Smaller",
        "Why Semiconductors Switch Currents",
        "How Touchscreens Detect Fingers",
        "Why Encryption Hides Messages",
        "How Cloud Computers Are Just Other Computers",
        "Why Solid-State Drives Are Faster",
    ),
    "artificial_intelligence": (
        "What Artificial Intelligence Actually Is",
        "How Neural Networks Learn",
        "Why Large Language Models Hallucinate",
        "How Training Data Shapes AI Behavior",
        "Why Transformers Changed Machine Learning",
        "How Recommendation Engines Predict Clicks",
        "Why Computer Vision Mistakes Objects",
        "How Reinforcement Learning Teaches Agents",
        "Why AI Needs Human Evaluation",
        "How Tokens Turn Words Into Numbers",
    ),
    "history": (
        "Why the Library of Alexandria Still Matters",
        "How the Printing Press Changed Knowledge",
        "Why Rome Built Roads That Last",
        "How the Scientific Method Emerged",
        "Why the Antikythera Mechanism Amazes Engineers",
        "How Longitude Was Solved at Sea",
        "Why the Silk Road Connected Sciences",
        "How Vaccination Began With Cowpox",
        "Why the Enigma Machine Failed",
        "How Radio Transformed News Speed",
    ),
    "engineering": (
        "How Bridges Carry Impossible Weight",
        "Why Airplanes Stay Up",
        "How Dams Hold Back Rivers",
        "Why Skyscrapers Don't Tip Over",
        "How Tunnel Boring Machines Carve Cities",
        "Why Suspension Bridges Flex",
        "How Wind Turbines Capture Energy",
        "Why Concrete Needs Reinforcing Steel",
        "How Elevators Made Tall Buildings Possible",
        "Why Bullet Trains Stay Stable",
    ),
    "nature": (
        "How Plants Make Oxygen",
        "Why Volcanoes Erupt",
        "How Earth Has a Magnetic Field",
        "Why the Ocean Is Salty",
        "How Seasons Work",
        "Why Lightning Prefers Tall Targets",
        "How Glaciers Carve Valleys",
        "Why Deserts Form Rain Shadows",
        "How Rivers Find the Sea",
        "Why Aurora Lights Dance",
    ),
}


def build_validation_catalog() -> list[dict[str, Any]]:
    """Return 100 production briefs for the V1 Validation Program."""
    catalog: list[dict[str, Any]] = []
    idx = 0
    for category in CATEGORIES:
        for topic in _TOPICS[category]:
            idx += 1
            catalog.append(
                {
                    "validation_id": f"vp_{idx:03d}_{category}",
                    "index": idx,
                    "category": category,
                    "domain": category,
                    "topic": topic,
                    "platform": "youtube_shorts",
                    "length_sec": 45,
                    "style": "educational",
                    "audience": f"{category.replace('_', ' ')} learners",
                    "voice": "professor",
                    "narrator": "professor",
                }
            )
    assert len(catalog) == 100
    return catalog


def filter_catalog(
    *,
    categories: list[str] | None = None,
    limit: int | None = None,
    offset: int = 0,
    ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    rows = build_validation_catalog()
    if ids:
        wanted = set(ids)
        rows = [r for r in rows if r["validation_id"] in wanted]
    if categories:
        wanted_c = {c.lower().replace(" ", "_") for c in categories}
        rows = [r for r in rows if r["category"] in wanted_c]
    if offset:
        rows = rows[offset:]
    if limit is not None:
        rows = rows[: max(0, int(limit))]
    return rows
