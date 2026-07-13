"""Sprint Wave 2 — additional educational science Shorts for remaining time budget."""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import importlib.util
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.env import load_application_env

load_application_env()

_spec = importlib.util.spec_from_file_location(
    "sprint_100min_batch",
    ROOT / "scripts" / "sprint_100min_batch.py",
)
_batch = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_batch)

MAX_WORKERS = _batch.MAX_WORKERS
REPORT_DIR = _batch.REPORT_DIR
aggregate = _batch.aggregate
run_one = _batch.run_one
_seo_score = _batch._seo_score

from services.media_production import ffmpeg_available
from services.provider_runtime.config import has_credential

# Remaining wall-clock budget passed as argv minutes (default 85)
BUDGET_MIN = float(sys.argv[1]) if len(sys.argv) > 1 else 85.0

TOPICS = [
    {
        "asset_id": "sp100w2_mitochondria_001",
        "title": "Why Mitochondria Are the Powerhouses",
        "hook": "Your cells run on tiny ancient power plants — and they have their own DNA.",
        "description": "Explain mitochondria, ATP, endosymbiotic origin. Accurate cell biology for general audience.",
        "hashtags": ["#biology", "#cells", "#science", "#shorts"],
        "keywords": ["mitochondria", "ATP", "endosymbiosis"],
        "cta": "Follow for biology that sticks",
        "niche": "science",
        "music_style": "cellular ambient",
        "thumbnail_concept": "mitochondrion as power plant inside cell",
        "seo": {"demand": 4, "evergreen": 5, "education": 5, "interest": 4, "short_form": 5},
    },
    {
        "asset_id": "sp100w2_dopamine_001",
        "title": "Dopamine Is Not the Pleasure Molecule",
        "hook": "Dopamine isn't happiness in a bottle — it's your brain's prediction and pursuit signal.",
        "description": "Explain dopamine as motivation/reward prediction error, not pure pleasure. Ground in neuroscience consensus; avoid biohacker overclaims.",
        "hashtags": ["#dopamine", "#neuroscience", "#psychology", "#shorts"],
        "keywords": ["dopamine", "reward prediction", "motivation"],
        "cta": "Follow for neuroscience without myths",
        "niche": "science",
        "music_style": "focus electronic ambient",
        "thumbnail_concept": "brain chasing a goal not a trophy",
        "seo": {"demand": 5, "evergreen": 4, "education": 5, "interest": 5, "short_form": 5},
    },
    {
        "asset_id": "sp100w2_exoplanets_001",
        "title": "How We Find Planets We Can't See",
        "hook": "Most exoplanets are invisible — we find them by watching stars wobble and dim.",
        "description": "Explain transit and radial velocity methods. Cite NASA exoplanet science. No claim of confirmed alien life.",
        "hashtags": ["#exoplanets", "#space", "#astronomy", "#shorts"],
        "keywords": ["exoplanet", "transit method", "radial velocity"],
        "cta": "Follow for space discovery science",
        "niche": "science",
        "music_style": "cosmic discovery",
        "thumbnail_concept": "star dimming as planet crosses",
        "seo": {"demand": 4, "evergreen": 5, "education": 5, "interest": 5, "short_form": 5},
    },
    {
        "asset_id": "sp100w2_vaccines_herd_001",
        "title": "What Herd Immunity Actually Means",
        "hook": "Herd immunity isn't a vibe — it's a math threshold that protects people who can't be vaccinated.",
        "description": "Explain basic reproduction number and coverage thresholds. Ground in epidemiology/CDC education. Avoid politicization.",
        "hashtags": ["#vaccines", "#epidemiology", "#science", "#shorts"],
        "keywords": ["herd immunity", "R0", "vaccination"],
        "cta": "Follow for public health explained",
        "niche": "science",
        "music_style": "clear educational ambient",
        "thumbnail_concept": "community shield protecting vulnerable",
        "seo": {"demand": 4, "evergreen": 4, "education": 5, "interest": 4, "short_form": 5},
    },
    {
        "asset_id": "sp100w2_neural_networks_001",
        "title": "Neural Nets Are Not Digital Brains",
        "hook": "An artificial neural network borrows a metaphor — not a copy of your cortex.",
        "description": "Explain layers, weights, training vs biological neurons. Accurate AI literacy; avoid AGI hype.",
        "hashtags": ["#AI", "#neuralnetworks", "#technology", "#shorts"],
        "keywords": ["neural network", "deep learning", "weights"],
        "cta": "Follow for AI literacy",
        "niche": "science",
        "music_style": "clean tech",
        "thumbnail_concept": "simple layered network vs brain",
        "seo": {"demand": 5, "evergreen": 3, "education": 5, "interest": 5, "short_form": 5},
    },
    {
        "asset_id": "sp100w2_aurora_001",
        "title": "What Causes the Northern Lights",
        "hook": "The aurora is solar wind slamming into Earth's magnetic shield — and making the sky glow.",
        "description": "Explain solar wind, magnetosphere, atmospheric excitation. Cite NASA space weather education.",
        "hashtags": ["#aurora", "#spaceweather", "#science", "#shorts"],
        "keywords": ["northern lights", "solar wind", "magnetosphere"],
        "cta": "Follow for Earth and space science",
        "niche": "science",
        "music_style": "ethereal night ambient",
        "thumbnail_concept": "green aurora over magnetic field lines",
        "seo": {"demand": 4, "evergreen": 5, "education": 5, "interest": 5, "short_form": 5},
    },
    {
        "asset_id": "sp100w2_stem_cells_001",
        "title": "What Stem Cells Can and Can't Do",
        "hook": "Stem cells can become many cell types — but they are not magic cure-alls.",
        "description": "Explain pluripotency vs adult stem cells; approved uses vs experimental. Ground in NIH stem cell basics. Warn against unproven clinics.",
        "hashtags": ["#stemcells", "#medicine", "#science", "#shorts"],
        "keywords": ["stem cells", "regenerative medicine"],
        "cta": "Follow for medicine without the hype",
        "niche": "science",
        "music_style": "clinical hopeful",
        "thumbnail_concept": "cell differentiating into multiple types",
        "seo": {"demand": 4, "evergreen": 4, "education": 5, "interest": 4, "short_form": 4},
    },
    {
        "asset_id": "sp100w2_entropy_001",
        "title": "Entropy: Why Mess Spreads",
        "hook": "The universe prefers disorder — and that idea powers engines and explains time's arrow.",
        "description": "Explain entropy and second law simply without fatalism. Accurate thermodynamics for general audience.",
        "hashtags": ["#physics", "#entropy", "#science", "#shorts"],
        "keywords": ["entropy", "second law", "thermodynamics"],
        "cta": "Follow for physics that clicks",
        "niche": "science",
        "music_style": "ordered to chaos ambient",
        "thumbnail_concept": "neat room becoming disordered particles",
        "seo": {"demand": 4, "evergreen": 5, "education": 5, "interest": 4, "short_form": 4},
    },
    {
        "asset_id": "sp100w2_whale_song_001",
        "title": "Why Humpback Whales Sing",
        "hook": "Humpback songs can travel for miles — and they change like cultural hits.",
        "description": "Explain whale song as complex communication/cultural transmission in males. Ground in marine mammal research; note open questions.",
        "hashtags": ["#whales", "#ocean", "#animals", "#shorts"],
        "keywords": ["humpback whale song", "animal culture"],
        "cta": "Follow for ocean animal science",
        "niche": "science",
        "music_style": "deep ocean whale ambient",
        "thumbnail_concept": "humpback with sound waves underwater",
        "seo": {"demand": 3, "evergreen": 5, "education": 4, "interest": 5, "short_form": 5},
    },
    {
        "asset_id": "sp100w2_gps_relativity_001",
        "title": "GPS Needs Einstein to Work",
        "hook": "Without relativity corrections, your phone's GPS would drift by kilometers every day.",
        "description": "Explain special/general relativity time dilation effects on GPS satellites. Accurate applied physics.",
        "hashtags": ["#GPS", "#relativity", "#physics", "#shorts"],
        "keywords": ["GPS relativity", "time dilation"],
        "cta": "Follow for physics in everyday tech",
        "niche": "science",
        "music_style": "precise tech ambient",
        "thumbnail_concept": "satellite and phone with clock skew",
        "seo": {"demand": 4, "evergreen": 5, "education": 5, "interest": 5, "short_form": 5},
    },
    {
        "asset_id": "sp100w2_immune_memory_001",
        "title": "How Your Immune System Remembers",
        "hook": "After an infection or vaccine, memory cells stand guard for the next encounter.",
        "description": "Explain adaptive immunity memory B/T cells simply. Ground in immunology textbooks/CDC education.",
        "hashtags": ["#immunity", "#medicine", "#science", "#shorts"],
        "keywords": ["immune memory", "antibodies", "T cells"],
        "cta": "Follow for immune system explainers",
        "niche": "science",
        "music_style": "defensive calm ambient",
        "thumbnail_concept": "memory cells recognizing invader",
        "seo": {"demand": 4, "evergreen": 5, "education": 5, "interest": 4, "short_form": 5},
    },
    {
        "asset_id": "sp100w2_tidal_locking_001",
        "title": "Why We Only See One Side of the Moon",
        "hook": "The Moon isn't hiding — it's tidally locked, rotating in sync with its orbit.",
        "description": "Explain tidal locking simply. Accurate astronomy education.",
        "hashtags": ["#moon", "#astronomy", "#science", "#shorts"],
        "keywords": ["tidal locking", "moon phases"],
        "cta": "Follow for space explained simply",
        "niche": "science",
        "music_style": "lunar ambient",
        "thumbnail_concept": "Earth-Moon sync rotation diagram",
        "seo": {"demand": 4, "evergreen": 5, "education": 5, "interest": 4, "short_form": 5},
    },
    {
        "asset_id": "sp100w2_confirmation_bias_001",
        "title": "Confirmation Bias Hijacks Your Brain",
        "hook": "Your brain loves evidence that agrees with you — and quietly ignores the rest.",
        "description": "Explain confirmation bias with a concrete example. Ground in cognitive psychology. No partisan framing.",
        "hashtags": ["#psychology", "#bias", "#thinking", "#shorts"],
        "keywords": ["confirmation bias", "critical thinking"],
        "cta": "Follow for psychology that sharpens thinking",
        "niche": "science",
        "music_style": "thoughtful underscore",
        "thumbnail_concept": "brain filtering matching puzzle pieces",
        "seo": {"demand": 5, "evergreen": 5, "education": 5, "interest": 5, "short_form": 5},
    },
    {
        "asset_id": "sp100w2_carbon_cycle_001",
        "title": "The Carbon Cycle in 60 Seconds",
        "hook": "Carbon moves between air, oceans, rocks, and life — until we overload one reservoir.",
        "description": "Explain carbon cycle reservoirs and human fossil emissions. Ground in NOAA/IPCC educational framing without doomism.",
        "hashtags": ["#climate", "#carbon", "#science", "#shorts"],
        "keywords": ["carbon cycle", "CO2", "climate science"],
        "cta": "Follow for climate science clarity",
        "niche": "science",
        "music_style": "earth systems ambient",
        "thumbnail_concept": "carbon flowing between earth systems",
        "seo": {"demand": 4, "evergreen": 5, "education": 5, "interest": 4, "short_form": 5},
    },
    {
        "asset_id": "sp100w2_crispr_agriculture_001",
        "title": "CRISPR Crops Are Not the Same as GMOs of the 90s",
        "hook": "Gene-edited crops can make precise DNA edits — and regulation is still catching up.",
        "description": "Explain gene editing in agriculture vs transgenic GMOs at high level. Note regulatory differences by country. Accurate, non-sensational.",
        "hashtags": ["#CRISPR", "#agriculture", "#biotech", "#shorts"],
        "keywords": ["gene edited crops", "CRISPR agriculture"],
        "cta": "Follow for biotech explained",
        "niche": "science",
        "music_style": "green tech ambient",
        "thumbnail_concept": "crop leaf with precise DNA edit icon",
        "seo": {"demand": 3, "evergreen": 4, "education": 5, "interest": 4, "short_form": 4},
    },
    {
        "asset_id": "sp100w2_pain_gate_001",
        "title": "Why Rubbing a Hurt Spot Can Help",
        "hook": "Pain isn't a raw wire to the brain — your spinal cord can gate the signal.",
        "description": "Explain gate control theory of pain simply. Ground in neuroscience/pain research. Not medical advice.",
        "hashtags": ["#pain", "#neuroscience", "#medicine", "#shorts"],
        "keywords": ["gate control theory", "pain"],
        "cta": "Follow for body science explained",
        "niche": "science",
        "music_style": "soft clinical",
        "thumbnail_concept": "spinal gate modulating pain signal",
        "seo": {"demand": 3, "evergreen": 5, "education": 5, "interest": 4, "short_form": 5},
    },
    {
        "asset_id": "sp100w2_supernova_001",
        "title": "How a Star's Death Makes Your Atoms",
        "hook": "The iron in your blood was forged in a dying star.",
        "description": "Explain stellar nucleosynthesis and supernovae creating heavy elements. Accurate astrophysics education.",
        "hashtags": ["#supernova", "#astronomy", "#science", "#shorts"],
        "keywords": ["nucleosynthesis", "supernova", "elements"],
        "cta": "Follow for cosmic origin science",
        "niche": "science",
        "music_style": "epic stellar ambient",
        "thumbnail_concept": "supernova forging elements into human silhouette",
        "seo": {"demand": 4, "evergreen": 5, "education": 5, "interest": 5, "short_form": 5},
    },
    {
        "asset_id": "sp100w2_ Circadian_001",
        "title": "Your Body Clock Runs on Light",
        "hook": "A cluster of neurons times your sleep, hormones, and alertness to daylight.",
        "description": "Explain circadian rhythms and SCN light entrainment. Ground in chronobiology. Avoid extreme biohacking claims.",
        "hashtags": ["#circadian", "#sleep", "#biology", "#shorts"],
        "keywords": ["circadian rhythm", "body clock", "melatonin"],
        "cta": "Follow for sleep science",
        "niche": "science",
        "music_style": "day night cycle ambient",
        "thumbnail_concept": "brain clock synced to sun",
        "seo": {"demand": 5, "evergreen": 5, "education": 5, "interest": 5, "short_form": 5},
    },
    {
        "asset_id": "sp100w2_hydrothermal_origin_001",
        "title": "Did Life Start at Ocean Vents?",
        "hook": "One leading idea: life began where hot chemistry met cold ocean water.",
        "description": "Present alkaline vent / hydrothermal origin hypothesis as active research, not settled fact. Contrast with other hypotheses briefly.",
        "hashtags": ["#originoflife", "#ocean", "#science", "#shorts"],
        "keywords": ["origin of life", "hydrothermal vents"],
        "cta": "Follow for big science questions",
        "niche": "science",
        "music_style": "primordial deep ambient",
        "thumbnail_concept": "vent chemistry sparking early metabolism",
        "seo": {"demand": 3, "evergreen": 5, "education": 5, "interest": 5, "short_form": 4},
    },
    {
        "asset_id": "sp100w2_radar_invent_001",
        "title": "How Radar Sees Through Fog",
        "hook": "Radar doesn't need light — it listens for radio echoes bouncing off objects.",
        "description": "Explain basic radar: pulse, reflection, timing for distance. Engineering education.",
        "hashtags": ["#radar", "#engineering", "#physics", "#shorts"],
        "keywords": ["radar", "radio waves", "echo location"],
        "cta": "Follow for engineering explained",
        "niche": "science",
        "music_style": "tech pulse",
        "thumbnail_concept": "radio waves bouncing off airplane",
        "seo": {"demand": 3, "evergreen": 5, "education": 5, "interest": 4, "short_form": 5},
    },
    {
        "asset_id": "sp100w2_serotonin_001",
        "title": "Serotonin Is More Than Mood",
        "hook": "Most of your serotonin isn't in your brain — and it does far more than 'make you happy.'",
        "description": "Explain serotonin roles in gut and CNS; nuance SSRI narrative. Not medical advice. Ground in neuroscience/pharmacology education.",
        "hashtags": ["#serotonin", "#neuroscience", "#mentalhealth", "#shorts"],
        "keywords": ["serotonin", "SSRI", "gut serotonin"],
        "cta": "Follow for brain chemistry without myths",
        "niche": "science",
        "music_style": "balanced calm ambient",
        "thumbnail_concept": "gut and brain serotonin pathways",
        "seo": {"demand": 4, "evergreen": 4, "education": 5, "interest": 5, "short_form": 5},
    },
    {
        "asset_id": "sp100w2_comet_vs_asteroid_001",
        "title": "Comet vs Asteroid — What's the Difference?",
        "hook": "Both are leftover building blocks of the solar system — but one carries ice that can bloom into a tail.",
        "description": "Explain composition and orbital differences. Accurate planetary science.",
        "hashtags": ["#comet", "#asteroid", "#space", "#shorts"],
        "keywords": ["comet", "asteroid", "solar system"],
        "cta": "Follow for solar system science",
        "niche": "science",
        "music_style": "space educational",
        "thumbnail_concept": "icy comet vs rocky asteroid split screen",
        "seo": {"demand": 3, "evergreen": 5, "education": 5, "interest": 4, "short_form": 5},
    },
    {
        "asset_id": "sp100w2_biofilm_001",
        "title": "Bacteria Build Cities Called Biofilms",
        "hook": "Many infections are hard to treat because bacteria live in slimy fortified cities.",
        "description": "Explain biofilms and antibiotic tolerance. Ground in microbiology. Not medical advice.",
        "hashtags": ["#bacteria", "#microbiology", "#medicine", "#shorts"],
        "keywords": ["biofilm", "antibiotic tolerance"],
        "cta": "Follow for microbe science",
        "niche": "science",
        "music_style": "microscopic curious",
        "thumbnail_concept": "bacterial city in slime matrix",
        "seo": {"demand": 3, "evergreen": 4, "education": 5, "interest": 4, "short_form": 5},
    },
    {
        "asset_id": "sp100w2_ Perseverance_oxygen_001",
        "title": "How a Mars Robot Made Oxygen",
        "hook": "NASA's MOXIE experiment pulled oxygen out of Mars' thin carbon dioxide air.",
        "description": "Explain MOXIE solid oxide electrolysis milestone. Cite NASA. Note it's a demo, not a full life-support plant.",
        "hashtags": ["#Mars", "#NASA", "#engineering", "#shorts"],
        "keywords": ["MOXIE", "Mars oxygen", "ISRU"],
        "cta": "Follow for space engineering",
        "niche": "science",
        "music_style": "mission engineering",
        "thumbnail_concept": "rover making oxygen from CO2",
        "seo": {"demand": 3, "evergreen": 3, "education": 5, "interest": 5, "short_form": 5},
    },
    {
        "asset_id": "sp100w2_synaptic_pruning_001",
        "title": "Teen Brains Prune Extra Connections",
        "hook": "Adolescence isn't just hormones — the brain is deleting unused wiring to get faster.",
        "description": "Explain synaptic pruning in adolescence. Ground in developmental neuroscience. Avoid stigma.",
        "hashtags": ["#brain", "#adolescence", "#neuroscience", "#shorts"],
        "keywords": ["synaptic pruning", "teen brain"],
        "cta": "Follow for brain development science",
        "niche": "science",
        "music_style": "growing mind ambient",
        "thumbnail_concept": "neural network pruning extra branches",
        "seo": {"demand": 4, "evergreen": 5, "education": 5, "interest": 4, "short_form": 5},
    },
    {
        "asset_id": "sp100w2_photon_001",
        "title": "What Is a Photon, Really?",
        "hook": "Light is both wave and particle — a photon is the particle packet of electromagnetic energy.",
        "description": "Explain photons and wave-particle duality at intro level without mysticism.",
        "hashtags": ["#physics", "#light", "#quantum", "#shorts"],
        "keywords": ["photon", "wave particle duality"],
        "cta": "Follow for physics fundamentals",
        "niche": "science",
        "music_style": "bright precise ambient",
        "thumbnail_concept": "wave and particle light duality",
        "seo": {"demand": 4, "evergreen": 5, "education": 5, "interest": 4, "short_form": 4},
    },
    {
        "asset_id": "sp100w2_mycelium_001",
        "title": "Mycelium: The Living Network Under Forests",
        "hook": "Under the forest floor, fungal threads form a living network linking trees and soil.",
        "description": "Explain mycelium and mycorrhizal networks. Avoid overstating 'wood wide web' communication claims; present evidence and debate fairly.",
        "hashtags": ["#fungi", "#ecology", "#nature", "#shorts"],
        "keywords": ["mycelium", "mycorrhizal network"],
        "cta": "Follow for ecology science",
        "niche": "science",
        "music_style": "forest underground ambient",
        "thumbnail_concept": "glowing fungal network under trees",
        "seo": {"demand": 4, "evergreen": 5, "education": 5, "interest": 5, "short_form": 5},
    },
    {
        "asset_id": "sp100w2_ Habitable_zone_001",
        "title": "What the Habitable Zone Really Means",
        "hook": "The habitable zone is where liquid water could exist — not a guarantee of life.",
        "description": "Explain circumstellar habitable zone carefully. Cite NASA exoplanet education. No alien life claims.",
        "hashtags": ["#exoplanets", "#astrobiology", "#space", "#shorts"],
        "keywords": ["habitable zone", "Goldilocks zone"],
        "cta": "Follow for astrobiology explained",
        "niche": "science",
        "music_style": "space hopeful",
        "thumbnail_concept": "star with green habitable ring",
        "seo": {"demand": 4, "evergreen": 5, "education": 5, "interest": 5, "short_form": 5},
    },
    {
        "asset_id": "sp100w2_fMRI_001",
        "title": "What fMRI Actually Measures",
        "hook": "fMRI doesn't watch thoughts — it tracks blood-oxygen changes linked to brain activity.",
        "description": "Explain BOLD signal and limits of reverse inference. Accurate neuroscience methods literacy.",
        "hashtags": ["#fMRI", "#neuroscience", "#science", "#shorts"],
        "keywords": ["fMRI", "BOLD signal", "brain imaging"],
        "cta": "Follow for neuroscience methods explained",
        "niche": "science",
        "music_style": "clinical research ambient",
        "thumbnail_concept": "brain scan with blood oxygen map",
        "seo": {"demand": 3, "evergreen": 5, "education": 5, "interest": 4, "short_form": 4},
    },
    {
        "asset_id": "sp100w2_lithium_batteries_001",
        "title": "How Lithium-Ion Batteries Store Energy",
        "hook": "Your phone battery works by shuttling lithium ions between two electrodes.",
        "description": "Explain charge/discharge ion movement simply. Engineering/chemistry education.",
        "hashtags": ["#battery", "#chemistry", "#technology", "#shorts"],
        "keywords": ["lithium ion battery", "electrodes"],
        "cta": "Follow for tech chemistry explained",
        "niche": "science",
        "music_style": "energy tech ambient",
        "thumbnail_concept": "ions moving between battery electrodes",
        "seo": {"demand": 4, "evergreen": 4, "education": 5, "interest": 4, "short_form": 5},
    },
    {
        "asset_id": "sp100w2_ crow_tools_001",
        "title": "Crows Make and Use Tools",
        "hook": "Some crows bend wires into hooks — culture and cognition in a bird brain.",
        "description": "Explain New Caledonian crow tool use from ethology research. Accurate animal cognition.",
        "hashtags": ["#crows", "#animals", "#cognition", "#shorts"],
        "keywords": ["crow tools", "animal intelligence"],
        "cta": "Follow for animal intelligence science",
        "niche": "science",
        "music_style": "clever nature",
        "thumbnail_concept": "crow bending wire into hook",
        "seo": {"demand": 3, "evergreen": 5, "education": 5, "interest": 5, "short_form": 5},
    },
    {
        "asset_id": "sp100w2_neutrinos_001",
        "title": "Neutrinos Pass Through You Every Second",
        "hook": "Trillions of neutrinos stream through your body right now — almost never interacting.",
        "description": "Explain neutrinos and weak interaction. Accurate particle physics intro.",
        "hashtags": ["#neutrino", "#physics", "#science", "#shorts"],
        "keywords": ["neutrino", "particle physics"],
        "cta": "Follow for particle physics explained",
        "niche": "science",
        "music_style": "subtle cosmic",
        "thumbnail_concept": "ghost particles passing through Earth",
        "seo": {"demand": 3, "evergreen": 5, "education": 5, "interest": 5, "short_form": 5},
    },
    {
        "asset_id": "sp100w2_telomeres_001",
        "title": "Telomeres: The Caps on Your Chromosomes",
        "hook": "Chromosome tips wear down as cells divide — and that matters for aging research.",
        "description": "Explain telomeres and telomerase carefully. Avoid anti-aging product claims. Ground in molecular biology.",
        "hashtags": ["#telomeres", "#aging", "#genetics", "#shorts"],
        "keywords": ["telomeres", "telomerase", "aging"],
        "cta": "Follow for genetics without the hype",
        "niche": "science",
        "music_style": "molecular soft",
        "thumbnail_concept": "chromosome with protective caps",
        "seo": {"demand": 4, "evergreen": 4, "education": 5, "interest": 4, "short_form": 4},
    },
    {
        "asset_id": "sp100w2_sound_speed_001",
        "title": "Why Thunder Comes After Lightning",
        "hook": "Light outruns sound — so you see the flash before you hear the boom.",
        "description": "Explain speed of light vs sound and distance estimation roughly. Accurate physics.",
        "hashtags": ["#thunder", "#physics", "#weather", "#shorts"],
        "keywords": ["speed of sound", "lightning thunder"],
        "cta": "Follow for everyday physics",
        "niche": "science",
        "music_style": "storm ambient",
        "thumbnail_concept": "lightning then delayed sound waves",
        "seo": {"demand": 3, "evergreen": 5, "education": 5, "interest": 4, "short_form": 5},
    },
    {
        "asset_id": "sp100w2_plastics_ocean_001",
        "title": "What Microplastics Are Doing in Oceans",
        "hook": "Plastic doesn't disappear — it breaks into fragments that move through food webs.",
        "description": "Explain microplastics pathways and research status. Avoid panic; stick to established environmental science (NOAA/peer review).",
        "hashtags": ["#microplastics", "#ocean", "#environment", "#shorts"],
        "keywords": ["microplastics", "ocean pollution"],
        "cta": "Follow for environmental science",
        "niche": "science",
        "music_style": "somber ocean",
        "thumbnail_concept": "tiny plastic particles in seawater food web",
        "seo": {"demand": 4, "evergreen": 4, "education": 5, "interest": 4, "short_form": 5},
    },
    {
        "asset_id": "sp100w2_working_memory_001",
        "title": "Working Memory Holds Only a Few Items",
        "hook": "Your mental scratchpad is tiny — that's why phone numbers feel hard to keep.",
        "description": "Explain working memory capacity and chunking. Ground in cognitive psychology (Miller/Cowans nuance).",
        "hashtags": ["#psychology", "#memory", "#learning", "#shorts"],
        "keywords": ["working memory", "chunking"],
        "cta": "Follow for learning science",
        "niche": "science",
        "music_style": "focus soft",
        "thumbnail_concept": "brain scratchpad with limited slots",
        "seo": {"demand": 4, "evergreen": 5, "education": 5, "interest": 4, "short_form": 5},
    },
]


def main() -> dict:
    # Fix accidental spaces in asset_ids
    for t in TOPICS:
        t["asset_id"] = t["asset_id"].replace(" ", "")

    deadline = time.time() + BUDGET_MIN * 60
    queue = sorted(TOPICS, key=_seo_score, reverse=True)
    print(f"=== WAVE 2 PREFLIGHT budget={BUDGET_MIN}m topics={len(queue)} ===", flush=True)
    if not has_credential("OPENAI_API_KEY") or not ffmpeg_available():
        raise SystemExit("missing openai or ffmpeg")

    batch_t0 = time.perf_counter()
    runs: list[dict] = []
    next_index = 100  # offset from wave 1
    i = 0
    while i < len(queue):
        if deadline - time.time() <= 30:
            print("=== WAVE 2 TIME BUDGET DONE ===", flush=True)
            break
        wave = []
        while len(wave) < MAX_WORKERS and i < len(queue):
            wave.append((queue[i], next_index))
            i += 1
            next_index += 1
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futs = {pool.submit(run_one, topic, idx, len(queue)): (topic, idx) for topic, idx in wave}
            for fut in as_completed(futs):
                try:
                    runs.append(fut.result())
                except Exception as exc:  # noqa: BLE001
                    topic, idx = futs[fut]
                    runs.append(
                        {
                            "run_index": idx,
                            "topic": topic["title"],
                            "asset_id": topic["asset_id"],
                            "success": False,
                            "production_error": str(exc),
                            "cost": {"estimated_cost_usd": 0},
                        }
                    )
        live = {
            "wave": 2,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "seconds_remaining": max(0, int(deadline - time.time())),
            "completed": sum(1 for r in runs if r.get("success")),
            "attempted": len(runs),
            "queue_remaining": max(0, len(queue) - i),
        }
        (REPORT_DIR / "LIVE_BOARD_WAVE2.json").write_text(json.dumps(live, indent=2), encoding="utf-8")

    agg = aggregate(runs, round(time.perf_counter() - batch_t0, 2), len(queue))
    agg["wave"] = 2
    path = REPORT_DIR / "SPRINT_WAVE2_REPORT.json"
    path.write_text(json.dumps(agg, indent=2, default=str), encoding="utf-8")
    print("WAVE2 completed", agg["completed_ready_to_post"], "report", path, flush=True)
    return agg


if __name__ == "__main__":
    main()
