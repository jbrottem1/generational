"""100-minute autonomous content production sprint.

Produces educational science Shorts via the existing asset production chain.
Only QC-passed MP4s are exported to Desktop (handled inside run_asset_production).
"""

from __future__ import annotations

import json
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from core.env import load_application_env

load_application_env()

from core.script_models import PIPELINE_STAGE_KEYS
from services.asset_production.executor import run_asset_production
from services.media_production import ffmpeg_available
from services.provider_runtime.config import has_credential

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "data" / "productions" / "_validation" / "sprint_100min"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

SPRINT_MINUTES = 100
MAX_WORKERS = 2  # parallel productions; keep low for OpenAI rate limits
TTS_PER_1K_CHARS = 0.015
CHAT_PER_RUN = 0.01
IMAGE_PER = 0.04

# SEO-scored educational science queue (demand / evergreen / education / interest / short-form = 1–5)
TOPICS: list[dict] = [
    {
        "asset_id": "sp100_crispr_001",
        "title": "How CRISPR Actually Edits DNA",
        "hook": "Scientists can now cut DNA like text — and this is how CRISPR works.",
        "description": (
            "Explain CRISPR-Cas9 gene editing for a general audience: guide RNA, Cas9 cut, "
            "repair. Note clinical use is carefully regulated and many applications remain "
            "experimental. Ground in Nobel-recognized CRISPR research (Doudna/Charpentier)."
        ),
        "hashtags": ["#CRISPR", "#genetics", "#science", "#shorts"],
        "keywords": ["CRISPR", "gene editing", "Cas9", "DNA"],
        "cta": "Follow for more genetics explained",
        "niche": "science",
        "music_style": "precise tech ambient",
        "thumbnail_concept": "DNA helix with scissors metaphor, clean educational look",
        "seo": {"demand": 5, "evergreen": 5, "education": 5, "interest": 5, "short_form": 5},
    },
    {
        "asset_id": "sp100_jwst_001",
        "title": "What JWST Sees That Hubble Can't",
        "hook": "The James Webb Space Telescope sees a universe Hubble never could.",
        "description": (
            "Explain infrared astronomy: JWST sees through dust and looks farther back in time "
            "than Hubble's optical view. Cite NASA/ESA/CSA JWST mission science. Avoid claiming "
            "it 'proved' contested theories — stick to what infrared imaging enables."
        ),
        "hashtags": ["#JWST", "#space", "#NASA", "#shorts"],
        "keywords": ["James Webb", "infrared telescope", "Hubble", "astronomy"],
        "cta": "Follow for more space science",
        "niche": "science",
        "music_style": "cosmic ambient",
        "thumbnail_concept": "JWST golden mirrors vs deep-field galaxies",
        "seo": {"demand": 5, "evergreen": 4, "education": 5, "interest": 5, "short_form": 5},
    },
    {
        "asset_id": "sp100_mRNA_001",
        "title": "How mRNA Vaccines Teach Your Cells",
        "hook": "mRNA vaccines don't rewrite your DNA — they deliver temporary instructions.",
        "description": (
            "Explain mRNA vaccine mechanism: lipid nanoparticle delivery, temporary protein "
            "instructions, immune recognition. Clarify mRNA does not integrate into DNA. "
            "Ground in peer-reviewed immunology and CDC/NIH educational materials."
        ),
        "hashtags": ["#mRNA", "#medicine", "#science", "#shorts"],
        "keywords": ["mRNA vaccine", "immune system", "lipid nanoparticle"],
        "cta": "Follow for clear medicine explainers",
        "niche": "science",
        "music_style": "calm clinical ambient",
        "thumbnail_concept": "cell receiving temporary message, not DNA rewrite",
        "seo": {"demand": 5, "evergreen": 4, "education": 5, "interest": 4, "short_form": 5},
    },
    {
        "asset_id": "sp100_neuroplasticity_001",
        "title": "Your Brain Rewires Itself",
        "hook": "Your brain is not fixed — it rewires with every skill you practice.",
        "description": (
            "Explain neuroplasticity: synaptic strengthening, practice-driven change, "
            "limits of adult plasticity. Avoid miracle-brain claims. Ground in cognitive "
            "neuroscience consensus (Hebbian learning, skill acquisition studies)."
        ),
        "hashtags": ["#neuroscience", "#brain", "#psychology", "#shorts"],
        "keywords": ["neuroplasticity", "brain rewiring", "learning"],
        "cta": "Follow for brain science without the myths",
        "niche": "science",
        "music_style": "focused ambient",
        "thumbnail_concept": "neural network lighting up with practice",
        "seo": {"demand": 5, "evergreen": 5, "education": 5, "interest": 5, "short_form": 5},
    },
    {
        "asset_id": "sp100_quantum_entanglement_001",
        "title": "Quantum Entanglement in Plain English",
        "hook": "Two particles can share a link Einstein called 'spooky' — here's what that means.",
        "description": (
            "Explain entanglement without mysticism: correlated quantum states, measurement, "
            "no faster-than-light messaging. Mention Bell tests as experimental confirmation. "
            "State clearly that entanglement does not enable FTL communication."
        ),
        "hashtags": ["#quantum", "#physics", "#science", "#shorts"],
        "keywords": ["quantum entanglement", "Bell test", "physics"],
        "cta": "Follow for physics without the hype",
        "niche": "science",
        "music_style": "minimal precise ambient",
        "thumbnail_concept": "two linked particles, clean diagram aesthetic",
        "seo": {"demand": 5, "evergreen": 5, "education": 5, "interest": 5, "short_form": 4},
    },
    {
        "asset_id": "sp100_deep_sea_vents_001",
        "title": "Life Without Sunlight at Deep Sea Vents",
        "hook": "Entire ecosystems thrive in total darkness — powered by chemistry, not sunlight.",
        "description": (
            "Explain hydrothermal vent ecosystems and chemosynthesis. Cite NOAA/WHOI-style "
            "oceanography. Avoid overstating 'origin of life' certainty — present as a leading "
            "hypothesis area, not settled fact."
        ),
        "hashtags": ["#ocean", "#marinebiology", "#science", "#shorts"],
        "keywords": ["hydrothermal vents", "chemosynthesis", "deep sea"],
        "cta": "Follow for ocean science",
        "niche": "science",
        "music_style": "deep underwater drone",
        "thumbnail_concept": "black smoker vent with glowing tube worms",
        "seo": {"demand": 4, "evergreen": 5, "education": 5, "interest": 5, "short_form": 5},
    },
    {
        "asset_id": "sp100_gut_brain_001",
        "title": "The Gut-Brain Axis Explained",
        "hook": "Your gut and brain are in constant conversation — through nerves and chemistry.",
        "description": (
            "Explain the gut-brain axis: vagus nerve, microbial metabolites, mood research. "
            "Mark microbiome-mood claims as emerging where evidence is preliminary. Ground in "
            "NIH/peer-reviewed gastroenterology and neuroscience reviews."
        ),
        "hashtags": ["#microbiome", "#neuroscience", "#health", "#shorts"],
        "keywords": ["gut brain axis", "microbiome", "vagus nerve"],
        "cta": "Follow for science-backed health explainers",
        "niche": "science",
        "music_style": "soft biological ambient",
        "thumbnail_concept": "gut and brain connected by glowing pathway",
        "seo": {"demand": 5, "evergreen": 4, "education": 5, "interest": 5, "short_form": 5},
    },
    {
        "asset_id": "sp100_photosynthesis_001",
        "title": "Photosynthesis Is a Solar Power Plant",
        "hook": "Every green leaf is a solar factory older than civilization.",
        "description": (
            "Explain light reactions and carbon fixation simply: photons, chlorophyll, sugars, "
            "oxygen. Accurate chemistry without overload. Ground in standard plant physiology."
        ),
        "hashtags": ["#photosynthesis", "#biology", "#science", "#shorts"],
        "keywords": ["photosynthesis", "chlorophyll", "plants"],
        "cta": "Follow for biology that clicks",
        "niche": "science",
        "music_style": "bright nature ambient",
        "thumbnail_concept": "leaf cross-section as solar factory",
        "seo": {"demand": 4, "evergreen": 5, "education": 5, "interest": 4, "short_form": 5},
    },
    {
        "asset_id": "sp100_black_hole_image_001",
        "title": "How We Photographed a Black Hole",
        "hook": "You can't see a black hole — so scientists photographed its shadow.",
        "description": (
            "Explain Event Horizon Telescope: Earth-sized interferometry, M87* image, "
            "photon ring / shadow concept. Cite EHT Collaboration papers. Avoid sci-fi claims."
        ),
        "hashtags": ["#blackhole", "#EHT", "#astronomy", "#shorts"],
        "keywords": ["Event Horizon Telescope", "M87", "black hole image"],
        "cta": "Follow for cosmic science",
        "niche": "science",
        "music_style": "deep space pulse",
        "thumbnail_concept": "orange ring black hole image style educational",
        "seo": {"demand": 5, "evergreen": 4, "education": 5, "interest": 5, "short_form": 5},
    },
    {
        "asset_id": "sp100_sleep_memory_001",
        "title": "Why Sleep Locks In Your Memories",
        "hook": "While you sleep, your brain is filing today's memories for long-term storage.",
        "description": (
            "Explain sleep-dependent memory consolidation: slow-wave and REM roles at a "
            "high level. Avoid overclaiming exact mechanisms still under study. Ground in "
            "sleep neuroscience reviews."
        ),
        "hashtags": ["#sleep", "#neuroscience", "#psychology", "#shorts"],
        "keywords": ["sleep memory", "memory consolidation", "REM"],
        "cta": "Follow for brain science you can use",
        "niche": "science",
        "music_style": "night calm ambient",
        "thumbnail_concept": "sleeping brain sorting glowing memory files",
        "seo": {"demand": 5, "evergreen": 5, "education": 5, "interest": 5, "short_form": 5},
    },
    {
        "asset_id": "sp100_antibiotic_resistance_001",
        "title": "Why Antibiotics Stop Working",
        "hook": "Bacteria evolve faster than our drugs — and misuse speeds them up.",
        "description": (
            "Explain antibiotic resistance: selection pressure, gene transfer, stewardship. "
            "Cite CDC/WHO framing. No fearmongering — accurate public-health education."
        ),
        "hashtags": ["#antibiotics", "#medicine", "#science", "#shorts"],
        "keywords": ["antibiotic resistance", "superbugs", "CDC"],
        "cta": "Follow for medicine explained clearly",
        "niche": "science",
        "music_style": "urgent but calm underscore",
        "thumbnail_concept": "bacteria adapting around antibiotic molecules",
        "seo": {"demand": 4, "evergreen": 5, "education": 5, "interest": 4, "short_form": 5},
    },
    {
        "asset_id": "sp100_plate_tectonics_001",
        "title": "Earth's Crust Is Moving Under You",
        "hook": "The ground beneath you is slowly sliding on giant tectonic plates.",
        "description": (
            "Explain plate tectonics: lithosphere plates, mid-ocean ridges, subduction, "
            "earthquakes/volcanoes. Ground in USGS geoscience education."
        ),
        "hashtags": ["#geology", "#earth", "#science", "#shorts"],
        "keywords": ["plate tectonics", "earthquakes", "continental drift"],
        "cta": "Follow for Earth science",
        "niche": "science",
        "music_style": "deep earth rumble ambient",
        "thumbnail_concept": "Earth cutaway with sliding plates",
        "seo": {"demand": 4, "evergreen": 5, "education": 5, "interest": 4, "short_form": 5},
    },
    {
        "asset_id": "sp100_octopus_camouflage_001",
        "title": "How Octopuses Change Color Instantly",
        "hook": "An octopus can vanish into a reef in under a second — here's the biology.",
        "description": (
            "Explain chromatophores, iridophores, papillae for texture. Ground in marine "
            "biology literature. Distinct from prior 'octopus intelligence' short."
        ),
        "hashtags": ["#octopus", "#marinebiology", "#animals", "#shorts"],
        "keywords": ["octopus camouflage", "chromatophores"],
        "cta": "Follow for animal science",
        "niche": "science",
        "music_style": "curious underwater",
        "thumbnail_concept": "octopus matching coral texture",
        "seo": {"demand": 4, "evergreen": 5, "education": 5, "interest": 5, "short_form": 5},
    },
    {
        "asset_id": "sp100_llm_tokens_001",
        "title": "How AI Models Predict the Next Word",
        "hook": "Large language models don't 'think' like you — they predict the next token.",
        "description": (
            "Explain transformers at a high level: tokens, attention, next-token prediction. "
            "Avoid AGI hype. Clarify limitations and hallucination risk. Educational AI literacy."
        ),
        "hashtags": ["#AI", "#LLM", "#technology", "#shorts"],
        "keywords": ["large language model", "tokens", "transformer"],
        "cta": "Follow for AI explained without the hype",
        "niche": "science",
        "music_style": "clean tech pulse",
        "thumbnail_concept": "tokens flowing into next-word prediction",
        "seo": {"demand": 5, "evergreen": 3, "education": 5, "interest": 5, "short_form": 5},
    },
    {
        "asset_id": "sp100_corals_bleaching_001",
        "title": "Why Coral Reefs Turn White",
        "hook": "When oceans get too warm, corals evict their partners — and turn ghostly white.",
        "description": (
            "Explain coral-zooxanthellae symbiosis and bleaching under heat stress. Cite NOAA "
            "coral reef science. Note recovery is possible but repeated stress raises mortality."
        ),
        "hashtags": ["#coral", "#climate", "#ocean", "#shorts"],
        "keywords": ["coral bleaching", "zooxanthellae", "ocean warming"],
        "cta": "Follow for climate science explained",
        "niche": "science",
        "music_style": "somber ocean ambient",
        "thumbnail_concept": "vibrant reef fading to white",
        "seo": {"demand": 4, "evergreen": 4, "education": 5, "interest": 4, "short_form": 5},
    },
    {
        "asset_id": "sp100_placebo_001",
        "title": "The Placebo Effect Is Real Biology",
        "hook": "A sugar pill can reduce pain — not because you're fooled, but because your brain changes.",
        "description": (
            "Explain placebo as measurable psychobiology: expectation, endogenous opioids, "
            "context. Not 'all in your head' dismissively. Ground in clinical research reviews."
        ),
        "hashtags": ["#placebo", "#psychology", "#medicine", "#shorts"],
        "keywords": ["placebo effect", "expectation", "pain"],
        "cta": "Follow for psychology that surprises",
        "niche": "science",
        "music_style": "curious soft underscore",
        "thumbnail_concept": "pill and brain releasing chemistry",
        "seo": {"demand": 4, "evergreen": 5, "education": 5, "interest": 5, "short_form": 5},
    },
    {
        "asset_id": "sp100_mars_perseverance_001",
        "title": "What Perseverance Is Hunting on Mars",
        "hook": "NASA's Perseverance isn't joyriding — it's hunting ancient signs of life.",
        "description": (
            "Explain Jezero crater science goals: past habitability, sample caching for return. "
            "Cite NASA Mars 2020. Do not claim life has been found."
        ),
        "hashtags": ["#Mars", "#NASA", "#space", "#shorts"],
        "keywords": ["Perseverance rover", "Jezero crater", "astrobiology"],
        "cta": "Follow for space missions explained",
        "niche": "science",
        "music_style": "mission documentary ambient",
        "thumbnail_concept": "rover on red crater lakebed",
        "seo": {"demand": 4, "evergreen": 3, "education": 5, "interest": 5, "short_form": 5},
    },
    {
        "asset_id": "sp100_epigenetics_001",
        "title": "Epigenetics: Switches on Your Genes",
        "hook": "Your DNA sequence isn't the whole story — chemical switches change what genes do.",
        "description": (
            "Explain epigenetics simply: methylation, histone marks, environment influence. "
            "Avoid Lamarckian overclaims and 'trauma permanently rewrites DNA' sensationalism. "
            "Mark inheritance claims carefully as an active research area."
        ),
        "hashtags": ["#epigenetics", "#genetics", "#science", "#shorts"],
        "keywords": ["epigenetics", "gene expression", "methylation"],
        "cta": "Follow for genetics without myths",
        "niche": "science",
        "music_style": "subtle molecular ambient",
        "thumbnail_concept": "DNA with on/off switches",
        "seo": {"demand": 4, "evergreen": 5, "education": 5, "interest": 4, "short_form": 4},
    },
    {
        "asset_id": "sp100_fusion_energy_001",
        "title": "Why Fusion Energy Is So Hard",
        "hook": "Fusion powers the Sun — so why can't we bottle it on Earth yet?",
        "description": (
            "Explain confinement challenge: temperature, pressure, net energy gain. Mention "
            "recent net-gain experiments as milestones, not commercial readiness. Ground in "
            "DOE/ITER educational framing."
        ),
        "hashtags": ["#fusion", "#energy", "#physics", "#shorts"],
        "keywords": ["nuclear fusion", "tokamak", "net energy"],
        "cta": "Follow for energy science",
        "niche": "science",
        "music_style": "powerful controlled energy ambient",
        "thumbnail_concept": "plasma ring inside reactor",
        "seo": {"demand": 4, "evergreen": 4, "education": 5, "interest": 5, "short_form": 5},
    },
    {
        "asset_id": "sp100_mirror_neurons_001",
        "title": "Do Mirror Neurons Explain Empathy?",
        "hook": "Some neurons fire when you act — and when you watch someone else act.",
        "description": (
            "Explain mirror neuron findings and the debate: useful for action understanding, "
            "but empathy is not fully explained by them alone. Present scientific uncertainty "
            "honestly. Ground in cognitive neuroscience reviews."
        ),
        "hashtags": ["#psychology", "#neuroscience", "#empathy", "#shorts"],
        "keywords": ["mirror neurons", "empathy", "social cognition"],
        "cta": "Follow for psychology with nuance",
        "niche": "science",
        "music_style": "human soft ambient",
        "thumbnail_concept": "two brains mirroring activity",
        "seo": {"demand": 3, "evergreen": 4, "education": 5, "interest": 4, "short_form": 4},
    },
    {
        "asset_id": "sp100_dark_matter_001",
        "title": "Why Physicists Think Dark Matter Exists",
        "hook": "Galaxies spin too fast for visible matter alone — something unseen is holding them.",
        "description": (
            "Explain rotation curves and gravitational evidence for dark matter. Clarify it is "
            "inferred, not directly detected. Mention alternatives exist but dark matter remains "
            "leading model. No conspiracy framing."
        ),
        "hashtags": ["#darkmatter", "#physics", "#cosmology", "#shorts"],
        "keywords": ["dark matter", "galaxy rotation", "cosmology"],
        "cta": "Follow for cosmology explained",
        "niche": "science",
        "music_style": "mysterious space ambient",
        "thumbnail_concept": "galaxy with invisible halo outline",
        "seo": {"demand": 4, "evergreen": 5, "education": 5, "interest": 5, "short_form": 4},
    },
    {
        "asset_id": "sp100_bee_waggle_001",
        "title": "How Bees Tell Each Other Where Food Is",
        "hook": "Honeybees dance to share GPS-like directions to flowers.",
        "description": (
            "Explain the waggle dance: angle relative to sun, duration for distance. Cite "
            "classic ethology (von Frisch) and modern confirmations."
        ),
        "hashtags": ["#bees", "#animals", "#biology", "#shorts"],
        "keywords": ["waggle dance", "honeybee communication"],
        "cta": "Follow for animal behavior science",
        "niche": "science",
        "music_style": "light curious nature",
        "thumbnail_concept": "bee dancing figure-eight in hive",
        "seo": {"demand": 3, "evergreen": 5, "education": 5, "interest": 5, "short_form": 5},
    },
    {
        "asset_id": "sp100_crispr_base_editing_001",
        "title": "Base Editing: CRISPR Without the Double Cut",
        "hook": "A newer gene tool can change a single DNA letter — without cutting both strands.",
        "description": (
            "Explain base editing vs classic CRISPR cut-and-repair. Note it is still largely "
            "in research/clinical trial stages. Ground in Liu lab / Nature reviews style accuracy."
        ),
        "hashtags": ["#geneediting", "#CRISPR", "#biotech", "#shorts"],
        "keywords": ["base editing", "CRISPR", "gene therapy"],
        "cta": "Follow for biotech explained",
        "niche": "science",
        "music_style": "precise biotech ambient",
        "thumbnail_concept": "single DNA letter being rewritten",
        "seo": {"demand": 3, "evergreen": 4, "education": 5, "interest": 4, "short_form": 4},
    },
    {
        "asset_id": "sp100_ozone_recovery_001",
        "title": "The Ozone Hole Is Healing",
        "hook": "Humanity broke the ozone layer — then cooperated to help it heal.",
        "description": (
            "Explain CFC damage, Montreal Protocol, and observed recovery trends from NOAA/NASA/"
            "UN assessments. Accurate hopeful science without claiming the problem is fully gone."
        ),
        "hashtags": ["#ozone", "#climate", "#environment", "#shorts"],
        "keywords": ["ozone hole", "Montreal Protocol", "CFCs"],
        "cta": "Follow for environmental science wins",
        "niche": "science",
        "music_style": "hopeful atmospheric",
        "thumbnail_concept": "Earth ozone layer repairing",
        "seo": {"demand": 3, "evergreen": 4, "education": 5, "interest": 4, "short_form": 5},
    },
    {
        "asset_id": "sp100_robot_learning_001",
        "title": "How Robots Learn by Trial and Error",
        "hook": "Modern robots don't just follow scripts — they learn policies from rewards.",
        "description": (
            "Explain reinforcement learning for robotics at a high level: trial, reward, policy. "
            "Note sim-to-real gaps. Avoid claiming human-level robot general intelligence."
        ),
        "hashtags": ["#robotics", "#AI", "#engineering", "#shorts"],
        "keywords": ["reinforcement learning", "robotics", "sim to real"],
        "cta": "Follow for robotics explained",
        "niche": "science",
        "music_style": "mechanical curious pulse",
        "thumbnail_concept": "robot arm learning a task with reward signals",
        "seo": {"demand": 4, "evergreen": 3, "education": 5, "interest": 5, "short_form": 5},
    },
    {
        "asset_id": "sp100_archaeology_dna_001",
        "title": "Ancient DNA Is Rewriting Human History",
        "hook": "A tooth or bone can now reveal migrations we never wrote down.",
        "description": (
            "Explain aDNA methods and how they inform migration/admixture models. Note "
            "uncertainty and revision as samples grow. Ground in population genetics / archaeology "
            "consensus without overclaiming single-study narratives."
        ),
        "hashtags": ["#archaeology", "#DNA", "#history", "#shorts"],
        "keywords": ["ancient DNA", "human migration", "archaeology"],
        "cta": "Follow for science rewriting history",
        "niche": "science",
        "music_style": "ancient discovery ambient",
        "thumbnail_concept": "fossil and DNA helix overlay",
        "seo": {"demand": 4, "evergreen": 4, "education": 5, "interest": 5, "short_form": 4},
    },
    {
        "asset_id": "sp100_water_memory_myth_001",
        "title": "Does Water Have Memory? Science Says No",
        "hook": "A viral claim says water remembers — chemistry disagrees.",
        "description": (
            "Debunk water memory / homeopathy molecular memory claims with chemistry: "
            "hydrogen bond lifetimes are fleeting; dilution past Avogadro leaves no solute. "
            "Educational myth-busting grounded in physical chemistry."
        ),
        "hashtags": ["#chemistry", "#mythbusting", "#science", "#shorts"],
        "keywords": ["water memory", "homeopathy science", "chemistry"],
        "cta": "Follow for myth-busting science",
        "niche": "science",
        "music_style": "sharp investigative ambient",
        "thumbnail_concept": "water drop with myth vs molecule",
        "seo": {"demand": 3, "evergreen": 4, "education": 5, "interest": 4, "short_form": 5},
    },
    {
        "asset_id": "sp100_gravitational_waves_001",
        "title": "How LIGO Hears Colliding Black Holes",
        "hook": "In 2015, Earth felt spacetime ripple — and LIGO heard it.",
        "description": (
            "Explain gravitational waves and laser interferometry detection. Cite LIGO/Virgo "
            "GW150914 as first detection. Accurate, non-sensational."
        ),
        "hashtags": ["#LIGO", "#physics", "#blackholes", "#shorts"],
        "keywords": ["gravitational waves", "LIGO", "spacetime"],
        "cta": "Follow for physics breakthroughs explained",
        "niche": "science",
        "music_style": "ripple spacetime ambient",
        "thumbnail_concept": "interferometer arms and spacetime ripple",
        "seo": {"demand": 4, "evergreen": 5, "education": 5, "interest": 5, "short_form": 4},
    },
    {
        "asset_id": "sp100_attention_span_001",
        "title": "Your Attention Is a Limited Battery",
        "hook": "Attention isn't infinite — your brain budgets it like energy.",
        "description": (
            "Explain selective attention and cognitive load simply. Avoid viral 'goldfish "
            "attention span' myth. Ground in cognitive psychology."
        ),
        "hashtags": ["#psychology", "#attention", "#focus", "#shorts"],
        "keywords": ["selective attention", "cognitive load", "focus"],
        "cta": "Follow for psychology that helps you focus",
        "niche": "science",
        "music_style": "focus minimal electronic",
        "thumbnail_concept": "brain battery draining with notifications",
        "seo": {"demand": 5, "evergreen": 4, "education": 4, "interest": 5, "short_form": 5},
    },
    {
        "asset_id": "sp100_tardigrades_001",
        "title": "How Tardigrades Survive the Impossible",
        "hook": "Tardigrades can survive space vacuum — by nearly shutting life down.",
        "description": (
            "Explain cryptobiosis / tun state and extreme tolerance. Cite peer-reviewed "
            "tardigrade physiology. Avoid claiming they are immortal."
        ),
        "hashtags": ["#tardigrade", "#biology", "#extremophile", "#shorts"],
        "keywords": ["tardigrade", "cryptobiosis", "extremophile"],
        "cta": "Follow for wild biology facts that are true",
        "niche": "science",
        "music_style": "quirky micro nature",
        "thumbnail_concept": "tardigrade in tun state vs space",
        "seo": {"demand": 4, "evergreen": 5, "education": 5, "interest": 5, "short_form": 5},
    },
]


def _seo_score(topic: dict) -> float:
    s = topic.get("seo") or {}
    return float(
        s.get("demand", 0)
        + s.get("evergreen", 0)
        + s.get("education", 0)
        + s.get("interest", 0)
        + s.get("short_form", 0)
    )


def _estimate_cost(result: dict, voice_chars: int, image_count: int) -> dict:
    tts = round((voice_chars / 1000.0) * TTS_PER_1K_CHARS, 4)
    images = round(image_count * IMAGE_PER, 4)
    total = round(tts + CHAT_PER_RUN + images, 4)
    return {
        "estimated_cost_usd": total,
        "breakdown": {
            "openai_tts_usd": tts,
            "openai_chat_usd": CHAT_PER_RUN,
            "openai_images_usd": images,
        },
    }


def run_one(topic: dict, index: int, total: int) -> dict:
    project = {
        "name": f"Sprint100 — {topic['title']}",
        "model": "gpt-4o-mini",
        "niche": topic.get("niche") or "science",
        "platform": "youtube_shorts",
        "provider": "openai",
    }
    events: list[dict] = []
    t0 = time.perf_counter()

    def on_progress(event: dict) -> None:
        slim = {k: v for k, v in event.items() if k != "asset"}
        slim["at"] = datetime.now(timezone.utc).isoformat()
        events.append(slim)
        print(
            f"  [{index}/{total}][{slim.get('status')}] {slim.get('label')}: "
            f"{slim.get('message')} (t={slim.get('execution_time_sec')}s)",
            flush=True,
        )

    print(f"\n=== SPRINT RUN {index}/{total}: {topic['title']} (SEO={_seo_score(topic)}) ===", flush=True)
    try:
        result = run_asset_production(topic, project, on_progress=on_progress, max_images=4)
    except Exception as exc:  # noqa: BLE001
        result = {
            **topic,
            "production_ok": False,
            "production_error": str(exc),
            "traceback": traceback.format_exc(),
        }

    elapsed = round(time.perf_counter() - t0, 2)
    stages = ((result.get("production_pipeline") or {}).get("stages") or {})
    rows = []
    for key in PIPELINE_STAGE_KEYS:
        raw = stages.get(key) or {}
        if isinstance(raw, str):
            raw = {"status": raw}
        rows.append({"stage": key, "status": raw.get("status"), "error": raw.get("error") or ""})

    render = result.get("render_package") or {}
    qc = result.get("production_qc") or {}
    script = result.get("video_script") or {}
    voiceover = str(script.get("full_voiceover") or result.get("script") or "")
    images = result.get("generated_images") or []
    real_images = [i for i in images if i.get("path") and not i.get("placeholder")]
    mp4 = render.get("mp4_path") or result.get("mp4_path") or ""
    mp4_bytes = 0
    if mp4:
        mp = Path(mp4) if Path(mp4).is_absolute() else ROOT / mp4
        if mp.exists():
            mp4_bytes = mp.stat().st_size

    success = bool(
        result.get("production_ok")
        and qc.get("passed")
        and mp4_bytes > 500
        and not render.get("mock", True)
        and (result.get("final_export_path") or qc.get("final_export_path"))
    )

    report = {
        "run_index": index,
        "topic": topic["title"],
        "asset_id": topic["asset_id"],
        "seo_score": _seo_score(topic),
        "seo": topic.get("seo"),
        "runtime_sec": elapsed,
        "production_ok": bool(result.get("production_ok")),
        "production_error": result.get("production_error") or "",
        "success": success,
        "qc_score": qc.get("score"),
        "qc_passed": qc.get("passed"),
        "stages": rows,
        "cost": _estimate_cost(result, len(voiceover), len(real_images)),
        "mp4_path": mp4,
        "mp4_bytes": mp4_bytes,
        "mock_render": bool(render.get("mock", True)),
        "final_export_path": result.get("final_export_path") or qc.get("final_export_path") or "",
        "title": topic["title"],
        "description": topic.get("description"),
        "hashtags": topic.get("hashtags"),
        "thumbnail_concept": topic.get("thumbnail_concept"),
    }
    out = REPORT_DIR / f"run_{index:02d}_{topic['asset_id']}.json"
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(
        f"  RESULT ok={success} runtime={elapsed}s qc={qc.get('score')} "
        f"export={bool(report['final_export_path'])}",
        flush=True,
    )
    return report


def aggregate(runs: list[dict], batch_runtime: float, planned: int) -> dict:
    successes = [r for r in runs if r.get("success")]
    n = len(runs) or 1
    return {
        "report_type": "100-Minute Autonomous Content Sprint",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sprint_minutes": SPRINT_MINUTES,
        "topics_queued": planned,
        "runs_attempted": len(runs),
        "completed_ready_to_post": len(successes),
        "in_progress_or_failed": len(runs) - len(successes),
        "success_rate_percent": round(100.0 * len(successes) / n, 1),
        "batch_runtime_sec": batch_runtime,
        "average_runtime_sec": round(sum(r.get("runtime_sec") or 0 for r in runs) / n, 2),
        "total_estimated_cost_usd": round(
            sum((r.get("cost") or {}).get("estimated_cost_usd") or 0 for r in runs), 4
        ),
        "completed_topics": [r["topic"] for r in successes],
        "failed_topics": [
            {"topic": r["topic"], "error": r.get("production_error") or "qc/export failed"}
            for r in runs
            if not r.get("success")
        ],
        "exports": [r.get("final_export_path") for r in successes if r.get("final_export_path")],
        "runs": runs,
        "preflight": {
            "ffmpeg": ffmpeg_available(),
            "openai": has_credential("OPENAI_API_KEY"),
            "youtube_oauth": has_credential("YOUTUBE_ACCESS_TOKEN"),
        },
        "blockers": [
            x
            for x in [
                None if has_credential("YOUTUBE_ACCESS_TOKEN") else "YouTube OAuth (live publish)",
                None if has_credential("ELEVENLABS_API_KEY") else "ElevenLabs (premium voice)",
                None
                if (has_credential("RUNWAY_API_KEY") or has_credential("FAL_KEY"))
                else "Runway/Fal (generative video clips)",
            ]
            if x
        ],
    }


def main() -> dict:
    deadline = time.time() + SPRINT_MINUTES * 60
    queue = sorted(TOPICS, key=_seo_score, reverse=True)
    print("=== SPRINT 100 PREFLIGHT ===", flush=True)
    print("ffmpeg", ffmpeg_available(), flush=True)
    print("openai", has_credential("OPENAI_API_KEY"), flush=True)
    print("queued", len(queue), "workers", MAX_WORKERS, flush=True)
    if not has_credential("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY required")
    if not ffmpeg_available():
        raise SystemExit("ffmpeg required")

    batch_t0 = time.perf_counter()
    runs: list[dict] = []
    next_index = 1
    total_planned = len(queue)

    # Process in waves of MAX_WORKERS until time expires or queue empty.
    i = 0
    while i < len(queue):
        remaining = deadline - time.time()
        if remaining <= 30:
            print(f"\n=== TIME BUDGET EXHAUSTED ({remaining:.0f}s left) — stopping queue ===", flush=True)
            break
        wave = []
        while len(wave) < MAX_WORKERS and i < len(queue):
            wave.append((queue[i], next_index))
            i += 1
            next_index += 1

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futures = {
                pool.submit(run_one, topic, idx, total_planned): (topic, idx)
                for topic, idx in wave
            }
            for fut in as_completed(futures):
                try:
                    runs.append(fut.result())
                except Exception as exc:  # noqa: BLE001
                    topic, idx = futures[fut]
                    runs.append(
                        {
                            "run_index": idx,
                            "topic": topic["title"],
                            "asset_id": topic["asset_id"],
                            "success": False,
                            "production_error": str(exc),
                            "runtime_sec": 0,
                            "cost": {"estimated_cost_usd": 0},
                        }
                    )

        # Persist live board after each wave
        live = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "seconds_remaining": max(0, int(deadline - time.time())),
            "completed": sum(1 for r in runs if r.get("success")),
            "attempted": len(runs),
            "queue_remaining": max(0, len(queue) - i),
        }
        (REPORT_DIR / "LIVE_BOARD.json").write_text(json.dumps(live, indent=2), encoding="utf-8")

    batch_runtime = round(time.perf_counter() - batch_t0, 2)
    agg = aggregate(runs, batch_runtime, len(queue))
    json_path = REPORT_DIR / "SPRINT_100MIN_REPORT.json"
    json_path.write_text(json.dumps(agg, indent=2, default=str), encoding="utf-8")

    md_lines = [
        "# 100-Minute Sprint Report",
        "",
        f"**Generated:** {agg['generated_at']}",
        f"**Completed ready-to-post:** {agg['completed_ready_to_post']}/{agg['runs_attempted']}",
        f"**Success rate:** {agg['success_rate_percent']}%",
        f"**Batch runtime:** {agg['batch_runtime_sec']}s",
        f"**Est. cost:** ${agg['total_estimated_cost_usd']}",
        "",
        "## Completed topics",
        "",
    ]
    for t in agg["completed_topics"]:
        md_lines.append(f"- {t}")
    if agg["failed_topics"]:
        md_lines.extend(["", "## Failed / incomplete", ""])
        for f in agg["failed_topics"]:
            md_lines.append(f"- {f['topic']}: {f['error']}")
    md_lines.extend(["", "## Blockers", ""])
    for b in agg["blockers"] or ["None"]:
        md_lines.append(f"- {b}")
    md_path = REPORT_DIR / "SPRINT_100MIN_REPORT.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    print("\n=== SPRINT COMPLETE ===", flush=True)
    print("completed:", agg["completed_ready_to_post"], flush=True)
    print("success_rate:", agg["success_rate_percent"], flush=True)
    print("cost:", agg["total_estimated_cost_usd"], flush=True)
    print("report:", json_path, flush=True)
    return agg


if __name__ == "__main__":
    main()
