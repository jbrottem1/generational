"""Sprint Wave 3 — large SEO science topic generator for remaining sprint time."""

from __future__ import annotations

import importlib.util
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

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

BUDGET_MIN = float(sys.argv[1]) if len(sys.argv) > 1 else 70.0

# (slug, title, hook, description, tags, keywords, seo tuple demand/evergreen/edu/interest/short)
RAW = [
    ("chimps_tools", "Chimpanzees Use Tools Too", "Tool use isn't uniquely human — chimpanzees fish for termites with crafted sticks.", "Explain chimpanzee tool use from primatology. Accurate animal cognition.", ["#chimps", "#animals", "#science"], ["chimpanzee tools"], (4, 5, 5, 5, 5)),
    ("red_shift", "What Redshift Tells Astronomers", "When galaxies look redder, space itself has stretched their light.", "Explain cosmological redshift simply. Accurate astronomy.", ["#redshift", "#cosmology", "#space"], ["redshift", "expanding universe"], (4, 5, 5, 4, 4)),
    ("vaccines_mrna_vs_traditional", "mRNA vs Traditional Vaccines", "One delivers instructions; the other often delivers a weakened or piece of a pathogen.", "Compare platforms accurately. Educational immunology. Not medical advice.", ["#vaccines", "#mRNA", "#medicine"], ["vaccine platforms"], (4, 4, 5, 4, 5)),
    ("ocean_acidification", "Ocean Acidification Explained", "Extra CO2 doesn't just warm air — it changes ocean chemistry.", "Explain carbonate chemistry simply. NOAA framing. Avoid doomism.", ["#ocean", "#climate", "#science"], ["ocean acidification"], (4, 4, 5, 4, 5)),
    ("crispr_sickle", "CRISPR and Sickle Cell Therapy", "Gene editing has reached approved treatments for sickle cell disease — carefully.", "Explain concept of ex vivo editing therapies at high level. Note medical supervision. Ground in FDA/clinical framing without overclaiming cures for all.", ["#CRISPR", "#medicine", "#genetics"], ["sickle cell CRISPR"], (4, 3, 5, 5, 4)),
    ("pareidolia", "Why You See Faces in Toast", "Your brain is wired to find faces — even where none exist.", "Explain pareidolia from cognitive psychology.", ["#psychology", "#brain", "#science"], ["pareidolia"], (4, 5, 4, 5, 5)),
    ("kepler_laws", "Kepler's Laws in Plain English", "Planets don't orbit in perfect circles — and Kepler figured out the pattern.", "Explain elliptical orbits and sweep equal areas simply.", ["#astronomy", "#physics", "#science"], ["Kepler laws"], (3, 5, 5, 3, 4)),
    ("antibiotics_vs_antivirals", "Antibiotics Don't Kill Viruses", "Antibiotics target bacteria — using them for viruses fuels resistance.", "Public health education. CDC framing.", ["#antibiotics", "#viruses", "#health"], ["antibiotics viruses"], (5, 5, 5, 4, 5)),
    ("deep_learning_vs_ml", "Deep Learning vs Machine Learning", "Deep learning is a subset of machine learning that stacks many layers of representation.", "Accurate AI literacy without hype.", ["#AI", "#ML", "#technology"], ["deep learning", "machine learning"], (5, 3, 5, 5, 5)),
    ("volcano_types", "Shield vs Stratovolcano", "Not all volcanoes explode the same way — shape follows lava chemistry.", "Explain viscosity and eruption style. USGS education.", ["#volcano", "#geology", "#science"], ["shield volcano", "stratovolcano"], (3, 5, 5, 4, 5)),
    ("hippocampus", "What the Hippocampus Does", "This seahorse-shaped brain region is central to forming new episodic memories.", "Neuroscience education. Mention HM case carefully as historical.", ["#brain", "#memory", "#neuroscience"], ["hippocampus"], (4, 5, 5, 4, 4)),
    ("solar_panels", "How Solar Panels Make Electricity", "Photons knock electrons loose in silicon — that's the photovoltaic effect.", "Physics/engineering education.", ["#solar", "#energy", "#physics"], ["photovoltaic"], (4, 5, 5, 4, 5)),
    ("coral_polyps", "Corals Are Animals, Not Plants", "A reef is built by tiny animals hosting algae partners.", "Marine biology education.", ["#coral", "#ocean", "#biology"], ["coral polyps"], (3, 5, 5, 4, 5)),
    ("double_slit", "The Double-Slit Experiment", "Light acts like a wave — until you try to watch which path it takes.", "Intro quantum classic experiment without mysticism.", ["#quantum", "#physics", "#science"], ["double slit"], (5, 5, 5, 5, 4)),
    ("sleep_stages", "The Stages of Sleep", "Sleep cycles through light, deep, and REM stages — each with a job.", "Sleep science education. Avoid extreme claims.", ["#sleep", "#biology", "#health"], ["sleep stages", "REM"], (5, 5, 5, 5, 5)),
    ("plate_boundaries", "Three Ways Plates Meet", "Plates collide, pull apart, or slide — and each boundary builds different hazards.", "USGS geoscience education.", ["#geology", "#earthquakes", "#science"], ["plate boundaries"], (3, 5, 5, 4, 5)),
    ("antibody", "What Antibodies Actually Do", "Antibodies are Y-shaped proteins that tag threats for your immune system.", "Immunology basics.", ["#immunity", "#biology", "#medicine"], ["antibodies"], (4, 5, 5, 4, 5)),
    ("blackbody", "Why Hot Metal Glows", "Temperature changes the color of thermal radiation — that's blackbody physics.", "Physics education.", ["#physics", "#light", "#science"], ["blackbody radiation"], (3, 5, 5, 3, 4)),
    ("octopus_ink", "Why Octopuses Squirt Ink", "Ink is a smoke screen — and sometimes a decoy — for escape.", "Marine biology.", ["#octopus", "#ocean", "#animals"], ["octopus ink"], (3, 5, 4, 5, 5)),
    ("crispr_ethics", "The Hard Ethics of Editing Embryos", "Editing heritable human DNA raises risks and global ethical lines most scientists won't cross.", "Present scientific consensus caution after He Jiankui. Educational ethics, not sensational.", ["#CRISPR", "#ethics", "#science"], ["germline editing ethics"], (4, 4, 5, 4, 4)),
    ("diffusion", "Diffusion Moves Life's Molecules", "From lungs to cells, random molecular motion drives essential transport.", "Chemistry/biology education.", ["#biology", "#chemistry", "#science"], ["diffusion"], (3, 5, 5, 3, 5)),
    ("magnetosphere", "Earth's Invisible Shield", "Our magnetic field deflects much of the solar wind that would strip an unprotected atmosphere.", "Space/Earth science. NASA education.", ["#earth", "#spaceweather", "#science"], ["magnetosphere"], (3, 5, 5, 4, 5)),
    ("operant_conditioning", "How Rewards Shape Behavior", "Actions followed by reinforcers become more likely — that's operant conditioning.", "Psychology education. Skinner basics without caricature.", ["#psychology", "#learning", "#science"], ["operant conditioning"], (4, 5, 5, 4, 5)),
    ("graphene", "Why Graphene Is Special", "A one-atom-thick carbon sheet with extraordinary strength and conductivity.", "Materials science. Note applications are still maturing.", ["#graphene", "#materials", "#science"], ["graphene"], (4, 4, 5, 4, 4)),
    ("tidal_forces", "How Tides Really Work", "The Moon's gravity stretches Earth — oceans rise where the pull is strongest and on the opposite side too.", "Accurate tidal explanation.", ["#tides", "#astronomy", "#earth"], ["tides moon"], (4, 5, 5, 4, 5)),
    ("cytokines", "Cytokines: Immune Text Messages", "Immune cells coordinate with chemical signals called cytokines — helpful until the storm.", "Immunology. Mention cytokine storm carefully as dysregulation.", ["#immunity", "#medicine", "#science"], ["cytokines"], (3, 4, 5, 4, 4)),
    ("parallax", "How Parallax Measures Star Distance", "Nearby stars shift against the background as Earth orbits — that shift is distance.", "Astronomy methods.", ["#astronomy", "#stars", "#science"], ["stellar parallax"], (3, 5, 5, 3, 4)),
    ("gut_microbiome_diversity", "Why Microbiome Diversity Matters", "A diverse gut microbial community is linked to resilience — but causality is still being mapped.", "Mark preliminary areas. NIH-style caution.", ["#microbiome", "#health", "#science"], ["microbiome diversity"], (4, 4, 5, 4, 5)),
    ("newton_third", "Action and Reaction Explained", "Forces come in pairs — rockets push exhaust, exhaust pushes rockets.", "Physics education.", ["#physics", "#newton", "#science"], ["Newton third law"], (4, 5, 5, 4, 5)),
    ("bird_migration", "How Birds Navigate Migration", "Birds use sun, stars, magnetism, and landmarks — a multi-sensor navigation system.", "Ethology. Note research ongoing on magnetoreception mechanisms.", ["#birds", "#migration", "#biology"], ["bird migration"], (3, 5, 5, 5, 5)),
    ("semiconductors", "Why Silicon Runs the Modern World", "Semiconductors control electron flow — the switch fabric of computers.", "Engineering education.", ["#semiconductor", "#technology", "#engineering"], ["silicon semiconductor"], (4, 5, 5, 4, 5)),
    ("apoptosis", "Programmed Cell Death Is Healthy", "Apoptosis is a controlled cell self-destruct that shapes organs and prevents damage.", "Cell biology.", ["#biology", "#cells", "#science"], ["apoptosis"], (3, 5, 5, 3, 4)),
    ("cosmic_microwave", "The Universe's Baby Picture", "The cosmic microwave background is leftover light from when the universe became transparent.", "Cosmology education.", ["#CMB", "#cosmology", "#science"], ["cosmic microwave background"], (4, 5, 5, 4, 4)),
    ("placebo_surgery", "Even Fake Surgery Can Reduce Pain", "In some trials, sham procedures show real symptom changes — expectation is powerful biology.", "Clinical research literacy. Not anti-medicine.", ["#placebo", "#medicine", "#psychology"], ["sham surgery placebo"], (3, 4, 5, 5, 4)),
    ("enzyme", "Enzymes Are Molecular Machines", "Enzymes speed reactions by lowering activation energy — life depends on them.", "Biochemistry basics.", ["#enzymes", "#biology", "#chemistry"], ["enzymes"], (3, 5, 5, 3, 5)),
    ("lagrange", "What Are Lagrange Points?", "Special orbital parking spots where gravity balances — home to JWST at L2.", "Orbital mechanics intro.", ["#space", "#JWST", "#physics"], ["Lagrange points"], (3, 5, 5, 4, 4)),
    ("synaptic_vesicles", "How Neurons Talk With Chemicals", "Electrical spikes trigger neurotransmitter release across tiny gaps called synapses.", "Neuroscience basics.", ["#neurons", "#brain", "#science"], ["neurotransmitters", "synapse"], (4, 5, 5, 4, 5)),
    ("albedo", "Why Ice Melt Speeds Warming", "Bright ice reflects sunlight; dark water absorbs it — a feedback called albedo.", "Climate science education.", ["#climate", "#arctic", "#science"], ["albedo feedback"], (4, 4, 5, 4, 5)),
    ("crayfish_anxiety", "Do Crayfish Feel Anxiety-Like States?", "Researchers found anxiety-like behavior in crayfish that responded to anti-anxiety drugs — carefully interpreted.", "Present as animal model research with limits. Peer-reviewed ethology/neuroscience.", ["#animals", "#neuroscience", "#science"], ["crayfish anxiety"], (3, 3, 5, 5, 5)),
    ("fusion_vs_fission", "Fusion vs Fission", "Fission splits heavy nuclei; fusion joins light ones — both release energy, differently.", "Nuclear physics education.", ["#energy", "#physics", "#nuclear"], ["fusion fission"], (4, 5, 5, 4, 5)),
    ("working_memory_chunking", "Chunking Supercharges Memory", "Grouping information into meaningful chunks expands what working memory can hold.", "Cognitive psychology.", ["#memory", "#learning", "#psychology"], ["chunking"], (4, 5, 5, 4, 5)),
    ("hydrothermal_black_smokers", "Black Smokers Explained", "Superheated mineral-rich water erupts from seafloor vents, building chimneys in the dark.", "Oceanography.", ["#ocean", "#geology", "#science"], ["black smokers"], (3, 5, 5, 4, 5)),
    ("crispr_diagnostics", "CRISPR Can Also Detect Disease", "Beyond editing, CRISPR systems are being built into rapid diagnostic tools.", "Biotech education. Note many are still in development/rollout stages.", ["#CRISPR", "#diagnostics", "#biotech"], ["CRISPR diagnostics"], (3, 3, 5, 4, 4)),
    ("refraction", "Why Straws Look Bent in Water", "Light changes speed between air and water — that bend is refraction.", "Optics education.", ["#physics", "#optics", "#science"], ["refraction"], (3, 5, 5, 4, 5)),
    ("default_mode_network", "Your Brain's Default Mode Network", "When you daydream, a network of brain regions becomes more active — the default mode network.", "Neuroscience. Avoid overclaiming mindfulness miracles.", ["#brain", "#neuroscience", "#psychology"], ["default mode network"], (4, 4, 5, 4, 4)),
    ("exoplanet_atmospheres", "Sniffing Exoplanet Atmospheres", "When a planet crosses its star, starlight filters through its air — revealing molecules.", "Transmission spectroscopy intro. NASA education.", ["#exoplanets", "#astronomy", "#science"], ["exoplanet atmosphere"], (4, 4, 5, 5, 4)),
    ("biofluorescence", "Biofluorescence vs Bioluminescence", "One absorbs light and re-emits it; the other makes its own light chemically.", "Marine biology clarity.", ["#ocean", "#biology", "#science"], ["biofluorescence", "bioluminescence"], (3, 5, 5, 4, 5)),
    ("hebbian", "Neurons That Fire Together Wire Together", "Repeated co-activation strengthens synapses — a core idea in learning research.", "Neuroscience. Attribute as Hebbian principle with modern nuance.", ["#learning", "#brain", "#science"], ["Hebbian learning"], (4, 5, 5, 4, 5)),
    ("asteroid_deflection", "How We Deflected an Asteroid", "NASA's DART mission slammed into Dimorphos and changed its orbit — a planetary defense test.", "Cite NASA DART results. Engineering/space.", ["#NASA", "#asteroid", "#space"], ["DART mission"], (4, 3, 5, 5, 5)),
    ("ph_scale", "What pH Actually Measures", "pH tracks hydrogen ion activity — acids donate, bases accept, in water chemistry.", "Chemistry education.", ["#chemistry", "#science", "#shorts"], ["pH scale"], (3, 5, 5, 3, 5)),
    ("mirror_test", "The Mirror Test for Self-Recognition", "Some animals pass the mark test — evidence of self-recognition, not a full theory of mind.", "Comparative psychology. Note debates and limits.", ["#animals", "#psychology", "#science"], ["mirror test"], (3, 5, 5, 5, 5)),
    ("quantum_tunneling", "Quantum Tunneling Explained", "Particles can cross barriers they classically shouldn't — and fusion in the Sun needs it.", "Physics education without mysticism.", ["#quantum", "#physics", "#science"], ["quantum tunneling"], (4, 5, 5, 5, 4)),
    ("lymph_nodes", "What Lymph Nodes Are Doing", "Lymph nodes are immune checkpoints where cells meet antigens and mount responses.", "Anatomy/immunology.", ["#immunity", "#health", "#science"], ["lymph nodes"], (3, 5, 5, 3, 5)),
    ("perihelion", "Why Seasons Aren't About Distance", "Earth is closest to the Sun in January — seasons come from axial tilt, not distance.", "Astronomy myth-bust.", ["#seasons", "#earth", "#science"], ["axial tilt", "seasons"], (4, 5, 5, 4, 5)),
    ("crispr_offtarget", "CRISPR Off-Target Effects", "Gene editors can sometimes cut the wrong place — so researchers test and engineer higher specificity.", "Accurate biotech risk literacy.", ["#CRISPR", "#biotech", "#science"], ["off-target CRISPR"], (3, 4, 5, 3, 4)),
    ("sonar_bats", "How Bats See With Sound", "Bats emit calls and read returning echoes to map the night.", "Echolocation biology.", ["#bats", "#biology", "#animals"], ["bat echolocation"], (3, 5, 5, 5, 5)),
    ("half_life", "What Radioactive Half-Life Means", "Half-life is the time for half the nuclei in a sample to decay — a statistical clock.", "Nuclear physics/chemistry.", ["#physics", "#chemistry", "#science"], ["half life"], (3, 5, 5, 3, 4)),
    ("oxytocin_myth", "Oxytocin Is Not Just the Love Hormone", "Oxytocin is involved in social bonding — and also more complex, context-dependent effects.", "Neuroscience myth nuance.", ["#oxytocin", "#psychology", "#science"], ["oxytocin"], (4, 4, 5, 4, 5)),
    ("kuiper_belt", "What Is the Kuiper Belt?", "A region of icy bodies beyond Neptune — home to Pluto and countless leftovers.", "Planetary science.", ["#Pluto", "#solarsystem", "#space"], ["Kuiper Belt"], (3, 5, 5, 4, 5)),
    ("transcription", "DNA to RNA: Transcription", "Genes are read into messenger RNA before proteins are built.", "Molecular biology basics.", ["#DNA", "#biology", "#genetics"], ["transcription"], (3, 5, 5, 3, 4)),
    ("heat_death_myth", "Heat Death Isn't Tomorrow", "The heat death of the universe is a far-future thermodynamic idea — not a near-term forecast.", "Cosmology/physics literacy; reduce anxiety hype.", ["#physics", "#cosmology", "#science"], ["heat death"], (3, 5, 4, 4, 4)),
    ("ant_colony", "How Ant Colonies Decide Without a Boss", "Simple local rules create colony-level problem solving — swarm intelligence.", "Ethology/complex systems.", ["#ants", "#biology", "#science"], ["swarm intelligence"], (3, 5, 5, 5, 5)),
    ("led_light", "How LEDs Make Light", "LEDs emit photons when electrons drop across a semiconductor band gap.", "Engineering/physics.", ["#LED", "#technology", "#physics"], ["LED"], (3, 5, 5, 3, 5)),
    ("synaptic_plasticity_ltp", "Long-Term Potentiation Explained", "Repeated activity can strengthen synapses for hours or longer — a cellular learning mechanism.", "Neuroscience. Note it's one mechanism among many.", ["#learning", "#neuroscience", "#science"], ["LTP"], (3, 5, 5, 3, 4)),
    ("venus_greenhouse", "Why Venus Is an Inferno", "A runaway greenhouse turned Venus into a crushing, scorching world.", "Planetary science.", ["#Venus", "#climate", "#space"], ["Venus greenhouse"], (4, 5, 5, 4, 5)),
    ("pcr_test", "How PCR Finds Tiny DNA Traces", "PCR copies DNA exponentially so scarce genetic material becomes detectable.", "Molecular biology / diagnostics literacy.", ["#PCR", "#biology", "#science"], ["PCR"], (4, 5, 5, 4, 5)),
    ("confirmation_vs_myside", "Myside Bias vs Confirmation Bias", "Related thinking traps: favoring your side's arguments and seeking agreeing evidence.", "Cognitive psychology literacy.", ["#psychology", "#bias", "#thinking"], ["myside bias"], (3, 5, 5, 4, 4)),
    ("neutron_star", "What Neutron Stars Are", "Collapsed stellar cores so dense a teaspoon would weigh billions of tons.", "Astrophysics education.", ["#neutronstar", "#astronomy", "#science"], ["neutron star"], (4, 5, 5, 5, 4)),
    ("skin_microbiome", "Your Skin Has an Ecosystem", "Billions of microbes live on skin — mostly partners, sometimes pathogens.", "Microbiology. Avoid product hype.", ["#microbiome", "#biology", "#health"], ["skin microbiome"], (3, 4, 5, 4, 5)),
    ("inertia", "Inertia in Everyday Life", "Objects resist changes in motion — that's why seatbelts matter.", "Physics education.", ["#physics", "#newton", "#science"], ["inertia"], (3, 5, 5, 3, 5)),
    ("gene_drive", "What Gene Drives Are", "Gene drives bias inheritance to spread traits fast — powerful and ethically fraught.", "Biotech education with caution. Research/regulatory context.", ["#genedrive", "#biotech", "#science"], ["gene drive"], (3, 3, 5, 4, 4)),
    ("saturn_rings", "What Saturn's Rings Are Made Of", "Countless icy particles orbiting in a thin disk — not solid hoops.", "Planetary science.", ["#Saturn", "#space", "#science"], ["Saturn rings"], (4, 5, 5, 4, 5)),
    ("blooms_taxonomy_myth", "Learning Isn't a Strict Pyramid", "Bloom's taxonomy is a useful planning tool — not a rigid law of how brains learn.", "Education science nuance.", ["#learning", "#education", "#psychology"], ["Bloom taxonomy"], (3, 4, 4, 3, 4)),
    ("chemosynthesis_vs_photo", "Chemosynthesis vs Photosynthesis", "One harvests chemical energy; the other harvests light — both build ecosystems.", "Biology comparison.", ["#biology", "#ocean", "#science"], ["chemosynthesis"], (3, 5, 5, 4, 5)),
    ("event_horizon", "What an Event Horizon Is", "The boundary where escape speed hits light speed — not a physical surface you can stand on.", "Black hole physics literacy.", ["#blackhole", "#physics", "#space"], ["event horizon"], (5, 5, 5, 5, 4)),
    ("interleaving", "Interleaving Beats Blocked Practice", "Mixing related skills often improves long-term learning versus repeating one skill only.", "Learning science. Cite cognitive psychology findings carefully.", ["#learning", "#psychology", "#education"], ["interleaving practice"], (4, 5, 5, 4, 5)),
    ("mars_atmosphere", "Why Mars Lost Its Thick Air", "Without a strong magnetic shield and with lower gravity, Mars struggled to keep atmosphere.", "Planetary science. Note research nuances.", ["#Mars", "#space", "#science"], ["Mars atmosphere"], (4, 5, 5, 4, 5)),
    ("ribosome", "Ribosomes Build Your Proteins", "These molecular factories read RNA and assemble amino acids into proteins.", "Cell biology.", ["#biology", "#cells", "#science"], ["ribosome"], (3, 5, 5, 3, 4)),
    ("spruce_goose_myth", "Bigger Wings Aren't Always Better", "Aircraft design balances lift, drag, weight, and power — scale has limits.", "Engineering literacy using aviation intuition.", ["#engineering", "#aviation", "#science"], ["aircraft design"], (2, 4, 4, 3, 4)),
    ("polar_vortex", "What the Polar Vortex Is", "A large cyclone of cold stratospheric air — when disrupted, cold can spill south.", "Atmospheric science. Avoid weather panic framing.", ["#weather", "#climate", "#science"], ["polar vortex"], (4, 4, 5, 4, 5)),
    ("epigenetic_clock", "Epigenetic Clocks Estimate Biological Age", "DNA methylation patterns can estimate biological age — useful research tools, not destiny.", "Genetics. Avoid anti-aging product claims.", ["#epigenetics", "#aging", "#science"], ["epigenetic clock"], (3, 3, 5, 4, 4)),
    ("sound_in_space", "Why Space Is Silent", "Sound needs a medium — vacuum doesn't carry pressure waves like air does.", "Physics myth-bust.", ["#space", "#physics", "#science"], ["sound in space"], (4, 5, 5, 4, 5)),
    ("t_cells", "What T Cells Do", "T cells hunt infected cells and help coordinate immune responses.", "Immunology basics.", ["#immunity", "#medicine", "#science"], ["T cells"], (4, 5, 5, 4, 5)),
    ("brownian_motion", "Brownian Motion Explained", "Pollen jitters because invisible water molecules slam into it — early evidence for atoms.", "Physics/chemistry history+science.", ["#physics", "#atoms", "#science"], ["Brownian motion"], (3, 5, 5, 3, 4)),
    ("ai_hallucination", "Why AI Hallucinates", "Language models predict plausible text — not guaranteed truth — so they can invent confidently.", "AI literacy.", ["#AI", "#LLM", "#technology"], ["AI hallucination"], (5, 3, 5, 5, 5)),
    ("comet_tails", "Why Comets Have Tails", "Sunlight and solar wind push dust and gas away from the nucleus into glowing tails.", "Planetary science.", ["#comet", "#space", "#science"], ["comet tail"], (3, 5, 5, 4, 5)),
    ("homeostasis", "Homeostasis Keeps You Alive", "Your body constantly corrects toward set points — temperature, blood sugar, and more.", "Physiology.", ["#biology", "#health", "#science"], ["homeostasis"], (4, 5, 5, 4, 5)),
    ("gravitational_lensing", "Gravity Can Bend Light", "Massive objects warp spacetime so background galaxies appear distorted or multiplied.", "Astrophysics. Einstein prediction confirmed.", ["#gravity", "#astronomy", "#science"], ["gravitational lensing"], (4, 5, 5, 5, 4)),
    ("sleep_spindles", "Sleep Spindles and Memory", "Brief bursts of brain activity in sleep are linked to memory consolidation research.", "Neuroscience. Mark as active research area.", ["#sleep", "#memory", "#neuroscience"], ["sleep spindles"], (3, 4, 5, 3, 4)),
    ("isotope", "What Isotopes Are", "Same element, different neutron count — used in dating, medicine, and climate science.", "Chemistry education.", ["#chemistry", "#science", "#shorts"], ["isotopes"], (3, 5, 5, 3, 4)),
    ("crow_funeral", "Why Crows Gather Around Dead Crows", "Crows investigate dead conspecifics — likely threat learning, not a human funeral.", "Ethology. Avoid over-anthropomorphizing.", ["#crows", "#animals", "#science"], ["crow behavior"], (3, 4, 4, 5, 5)),
    ("tokamak", "What a Tokamak Is", "A doughnut-shaped magnetic bottle designed to confine fusion plasma.", "Fusion engineering intro.", ["#fusion", "#energy", "#engineering"], ["tokamak"], (3, 4, 5, 4, 4)),
    ("retina", "How Your Retina Detects Light", "Photoreceptors convert photons into neural signals your brain turns into vision.", "Neuroscience/biology.", ["#vision", "#biology", "#science"], ["retina"], (3, 5, 5, 3, 5)),
    ("milankovitch", "Milankovitch Cycles Explained", "Slow changes in Earth's orbit and tilt help pace ice ages over tens of thousands of years.", "Climate/paleoclimate education. Not a denial of modern warming.", ["#climate", "#earth", "#science"], ["Milankovitch cycles"], (3, 5, 5, 3, 4)),
    ("plasmid", "What Plasmids Are", "Small DNA loops in bacteria that can carry useful genes — including resistance.", "Microbiology.", ["#bacteria", "#genetics", "#science"], ["plasmids"], (3, 5, 5, 3, 4)),
    ("james_webb_infrared", "Why Infrared Sees Through Dust", "Infrared wavelengths slip through dust clouds that block visible light.", "Astronomy education.", ["#JWST", "#infrared", "#space"], ["infrared astronomy"], (4, 5, 5, 4, 5)),
    ("cognitive_load", "Cognitive Load Theory Basics", "Working memory is limited — instructional design should avoid unnecessary overload.", "Learning science.", ["#learning", "#psychology", "#education"], ["cognitive load"], (4, 5, 5, 4, 5)),
    ("europa_ocean", "Why Europa Might Have an Ocean", "Jupiter's moon shows evidence of a subsurface saltwater ocean beneath ice.", "Planetary science. Habitability possibility, not life detected.", ["#Europa", "#astrobiology", "#space"], ["Europa ocean"], (4, 5, 5, 5, 5)),
    ("catalyst", "What Catalysts Do", "Catalysts speed reactions without being consumed — industry and biology rely on them.", "Chemistry.", ["#chemistry", "#science", "#shorts"], ["catalyst"], (3, 5, 5, 3, 5)),
    ("fmri_limit", "fMRI Can't Read Your Thoughts", "Group brain maps are not mind-reading machines — resolution and interpretation have limits.", "Methods literacy.", ["#fMRI", "#neuroscience", "#science"], ["fMRI limits"], (3, 5, 5, 4, 5)),
]


def build_topics() -> list[dict]:
    topics = []
    for slug, title, hook, description, tags, keywords, seo in RAW:
        d, e, edu, interest, short = seo
        topics.append(
            {
                "asset_id": f"sp100w3_{slug}_001",
                "title": title,
                "hook": hook,
                "description": (
                    description
                    + " Stay scientifically accurate for a general audience. "
                    "If research is preliminary, say so. No sensationalism."
                ),
                "hashtags": tags + ["#shorts"],
                "keywords": keywords,
                "cta": "Follow for science explained clearly",
                "niche": "science",
                "music_style": "educational ambient",
                "thumbnail_concept": f"Clean educational visual for: {title}",
                "seo": {
                    "demand": d,
                    "evergreen": e,
                    "education": edu,
                    "interest": interest,
                    "short_form": short,
                },
            }
        )
    return topics


def main() -> dict:
    deadline = time.time() + BUDGET_MIN * 60
    queue = sorted(build_topics(), key=_seo_score, reverse=True)
    print(f"=== WAVE 3 PREFLIGHT budget={BUDGET_MIN}m topics={len(queue)} ===", flush=True)
    if not has_credential("OPENAI_API_KEY") or not ffmpeg_available():
        raise SystemExit("missing openai or ffmpeg")

    batch_t0 = time.perf_counter()
    runs: list[dict] = []
    next_index = 200
    i = 0
    while i < len(queue):
        if deadline - time.time() <= 30:
            print("=== WAVE 3 TIME BUDGET DONE ===", flush=True)
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
            "wave": 3,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "seconds_remaining": max(0, int(deadline - time.time())),
            "completed": sum(1 for r in runs if r.get("success")),
            "attempted": len(runs),
            "queue_remaining": max(0, len(queue) - i),
        }
        (REPORT_DIR / "LIVE_BOARD_WAVE3.json").write_text(json.dumps(live, indent=2), encoding="utf-8")

    agg = aggregate(runs, round(time.perf_counter() - batch_t0, 2), len(queue))
    agg["wave"] = 3
    path = REPORT_DIR / "SPRINT_WAVE3_REPORT.json"
    path.write_text(json.dumps(agg, indent=2, default=str), encoding="utf-8")
    print("WAVE3 completed", agg["completed_ready_to_post"], "report", path, flush=True)
    return agg


if __name__ == "__main__":
    main()
