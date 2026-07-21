"""Build / ensure permanent Studio Asset #0001 — The Doctor."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.studio_assets.registry import upsert_asset
from services.studio_assets.the_doctor.human_realism import write_human_realism_package
from services.studio_assets.the_doctor.profile import (
    ANIMATIONS,
    ASSET_ID,
    ASSET_SLUG,
    ASSET_VERSION,
    COLOR_SYSTEM,
    EXPRESSIONS,
    POSES,
    VISEMES,
    WARDROBE,
    character_profile,
)
from services.studio_assets.the_doctor.renderer import draw_environment_plate, draw_the_doctor_plate
from services.studio_assets.the_doctor.world import (
    GMRI_ROOMS,
    gmri_world_package,
    lighting_presets,
    prop_library,
    reusable_objects,
)

ROOT = Path(__file__).resolve().parents[3]
ASSET_ROOT = ROOT / "data" / "studio_assets" / ASSET_SLUG


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _biography_md() -> str:
    return f"""# The Doctor — Permanent Biography

**Asset ID:** `{ASSET_ID}`  
**Version:** `{ASSET_VERSION}`  
**Status:** Permanent Generational IP

## Origin

The Doctor was commissioned by the Generational Universe as the first permanent Studio Asset —
not a one-off AI generation, but company intellectual property. Built as a humanoid cyborg
physician-educator, The Doctor unites clinical precision with warm, approachable teaching.

## Purpose

To be the official face of scientific education across science, biology, medicine, engineering,
chemistry, anatomy, physics, and technology productions. Audiences should recognize The Doctor
instantly and grow familiar across hundreds of videos.

## Education

Internal knowledge systems cover medicine, molecular biology, anatomy, physics, chemistry,
engineering fundamentals, and evidence literacy — continuously updated through Generational
research pipelines while the *visual identity* remains locked.

## Mission

Help every learner understand science with clarity, compassion, and curiosity.
Never intimidate. Never condescend. Always show the evidence.

## Teaching philosophy

1. Demonstrate before declaring.  
2. Faces and bodies carry meaning — mute storytelling must still teach.  
3. Wonder is a scientific tool, not a distraction.  
4. Mistakes in understanding are invitations, not failures.

## Favorite subjects

Human body systems · cellular life · medical imaging · vaccines & immunity · physics of everyday
tools · how hospitals work · future medicine · trustworthy AI in healthcare.

## Personality traits

Highly intelligent · patient · curious · optimistic · encouraging · evidence-driven · never arrogant.

## Interesting facts

- Chest interface glows warm trust-blue when explaining a breakthrough.  
- Keeps a living plant wall growing in every major GMRI classroom.  
- Signature greeting: open palm at heart height, then a precise clipboard or hologram cue.  
- Refuses “scary robot” aesthetics — audience trust is part of the medicine.

## Relationships with recurring characters

- **Professor Atlas** — colleague for broad science lectures.  
- **Nova** — co-host for AI / computing questions; Doctor grounds answers clinically.  
- **Orion** — field expedition science partner.  
- **Piper** — medical device and engineering explainers.  
- **Luna** — closest peer on biology and ecology.  
- **Dash / Professor Gen** — separate locked IPs; never redesign; optional careful cameos only.
"""


def _personality_md() -> str:
    return """# The Doctor — Personality Guide

## Core

Trust · Intelligence · Curiosity · Compassion

## Does

- Speaks calmly and clearly  
- Encourages questions  
- Shows evidence on holograms and props  
- Celebrates understanding, not ego  
- Matches emotional tone to the patient’s (viewer’s) moment  

## Never

- Arrogant lectures  
- Condescension  
- Horror / uncanny aesthetics  
- Random redesigns or palette drift  
- Mannequin / expressionless delivery  

## Performance notes

Blink · breathe · shift weight · maintain soft eye contact · gesture with purpose.
Idle must still feel alive. Teaching poses prioritize clarity of silhouette.
"""


def _world_guide_md() -> str:
    rooms = "\n".join(f"- `{r}`" for r in GMRI_ROOMS)
    return f"""# Generational Medical Research Institute (GMRI)

**World ID:** `LOC-GMRI`  
**Owner:** The Doctor (`CHAR-0001`)  
**Status:** Permanent reusable world

## Style

High-end cinematic science facility — warm, inviting, beautiful, futuristic, highly detailed,
and filled with life. Researchers move. Robots work. Screens stay active. Plants grow.
Medical equipment functions. Nothing feels empty.

## Rooms (all reusable)

{rooms}

## Continuity

Layouts persist across productions. Props remain where left unless a story moves them.
Lighting presets from `LIGHTING_PRESETS/` must be used — do not invent conflicting palettes.
"""


def _color_guide_md() -> str:
    c = COLOR_SYSTEM
    return f"""# The Doctor — Official Color Guide

**Locked.** Never randomly change these colors. Upgrades require version bump.

| Role | Name | Hex |
|------|------|-----|
| Primary | {c['primary']['name']} | `{c['primary']['hex']}` |
| Secondary | {c['secondary']['name']} | `{c['secondary']['hex']}` |
| Accent | {c['accent']['name']} | `{c['accent']['hex']}` |
| Deep Accent | {c['deep_accent']['name']} | `{c['deep_accent']['hex']}` |
| Eyes | {c['visors']['name']} | `{c['visors']['hex']}` |
| Chassis Shadow | {c['chassis_shadow']['name']} | `{c['chassis_shadow']['hex']}` |

## Medical interface

- OK: `{c['medical_interface']['ok']}`  
- Info: `{c['medical_interface']['info']}`  
- Warn: `{c['medical_interface']['warn']}`  

## Emergency

- Alert: `{c['emergency']['alert']}`  
- Critical: `{c['emergency']['critical']}`  

## Lighting

Key: soft warm clinical · Fill: cool rim blue · Practical: blue edge LEDs
"""


def _continuity_md() -> str:
    return f"""# Continuity Rules — The Doctor (`{ASSET_ID}`)

1. **Always reference this Studio Asset.** Never regenerate The Doctor from scratch.  
2. **Visual identity is locked** at version `{ASSET_VERSION}` until an intentional upgrade.  
3. **Palette is law** — see `COLOR_GUIDE.md`.  
4. **Home world is GMRI** (`LOC-GMRI`) — rooms stay consistent.  
5. **Expressions / poses / animations** come from this package libraries.  
6. **Productions cast** via Character & World Studio host id `{ASSET_ID}`.  
7. **Version upgrades** require `VERSION.json` bump + changelog + executive note.  
8. **Do not confuse** with Dash or Professor Gen stick IPs.  
9. **Outfits may change** only through listed wardrobe variants; silhouette remains recognizable.  
10. **Self-review:** Would a child recognize The Doctor next episode? If no — reject.  
11. **Human Realism Framework:** inherit shared schemas; Doctor is gold-standard reference.  
12. **Style mode** is cinematic realism — not uncanny photoreal, not stick placeholders.
"""


def _model_guide_md() -> str:
    return f"""# Character Model Guide — The Doctor

## Recognition keys

White medical humanoid chassis · warm blue illuminated accents · intelligent eye cores ·
friendly expressive face · athletic human proportions · professional posture ·
premium titanium materials · medical chest interface.

## Turnaround

Use `POSE_LIBRARY/` front / rear / left / right / three-quarter.

## Expression board

Use every file in `CHARACTER_EXPRESSIONS/`.

## Forbidden

Generic featureless robots · horror uncanny valley · blank faces · stick figures ·
random color swaps · empty rooms at GMRI.
"""


def _write_pdf_model_guide(path: Path) -> None:
    """Multi-page PDF via PIL (no extra PDF dependency)."""
    from PIL import Image, ImageDraw, ImageFont

    pages: list[Image.Image] = []
    lines_pages = [
        [
            "GENERATIONAL STUDIO ASSET #0001",
            "THE DOCTOR",
            f"Version {ASSET_VERSION}",
            "Permanent · Reusable · Version Controlled",
            "",
            "Lead Scientific Educator",
            "Humanoid cyborg · medical white chassis",
            "Warm blue accents · premium titanium",
            "Trust · Intelligence · Curiosity · Compassion",
        ],
        [
            "DESIGN LOCK",
            "- Friendly expressive face",
            "- Intelligent eye cores",
            "- Human proportions",
            "- Athletic approachable build",
            "- Professional posture",
            "- Avoid generic robot / horror",
            "",
            "Always reference this asset.",
            "Never regenerate from scratch.",
        ],
        [
            "LIBRARIES",
            "CHARACTER_EXPRESSIONS/",
            "POSE_LIBRARY/",
            "ANIMATION_LIBRARY/",
            "ENVIRONMENT_PACKAGE/",
            "PROP_LIBRARY/",
            "",
            "Home: Generational Medical",
            "Research Institute (GMRI)",
        ],
    ]
    for lines in lines_pages:
        img = Image.new("RGB", (1240, 1754), (244, 247, 250))
        d = ImageDraw.Draw(img)
        d.rectangle((60, 60, 1180, 1694), outline=(59, 167, 224), width=6)
        y = 160
        font = ImageFont.load_default()
        for line in lines:
            d.text((120, y), line, fill=(26, 95, 138), font=font)
            y += 48 if line else 28
        pages.append(img)
    path.parent.mkdir(parents=True, exist_ok=True)
    first, rest = pages[0], pages[1:]
    first.save(path, "PDF", save_all=True, append_images=rest)


def ensure_the_doctor_asset(*, force: bool = False) -> dict[str, Any]:
    """Write permanent asset tree; skip regenerating locked plates unless force."""
    ASSET_ROOT.mkdir(parents=True, exist_ok=True)
    manifest_path = ASSET_ROOT / "MANIFEST.json"
    if manifest_path.is_file() and not force:
        existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        # Still refresh markdown/json sources that are deterministic docs
    else:
        existing = {}

    profile = character_profile()
    _write_json(ASSET_ROOT / "CHARACTER_PROFILE.json", profile)
    _write_json(ASSET_ROOT / "VOICE_PROFILE.json", profile["voice_profile"])
    _write_json(ASSET_ROOT / "VERSION.json", {
        "id": ASSET_ID,
        "version": ASSET_VERSION,
        "status": "permanent",
        "updated_at": _now(),
        "changelog": [
            {"version": "1.0.0", "note": "Initial permanent Studio Asset — The Doctor + GMRI."},
            {
                "version": "1.1.0",
                "note": (
                    "Human Character Realism V1 profiles — cinematic realism identity, "
                    "skeleton/face/gait/gesture/emotion/wardrobe schemas (no new renderer)."
                ),
            },
        ],
    })
    _write_md(ASSET_ROOT / "BIOGRAPHY.md", _biography_md())
    _write_md(ASSET_ROOT / "PERSONALITY_GUIDE.md", _personality_md())
    _write_md(ASSET_ROOT / "WORLD_GUIDE.md", _world_guide_md())
    _write_md(ASSET_ROOT / "COLOR_GUIDE.md", _color_guide_md())
    _write_md(ASSET_ROOT / "CONTINUITY_RULES.md", _continuity_md())
    _write_md(ASSET_ROOT / "CHARACTER_MODEL_GUIDE.md", _model_guide_md())
    _write_pdf_model_guide(ASSET_ROOT / "CHARACTER_MODEL_GUIDE.pdf")
    hr_written = write_human_realism_package(ASSET_ROOT, _write_json, _write_md)

    # Expressions
    expr_dir = ASSET_ROOT / "CHARACTER_EXPRESSIONS"
    expr_index: dict[str, str] = {}
    for exp in EXPRESSIONS:
        p = expr_dir / f"{exp}.png"
        if force or not p.is_file():
            draw_the_doctor_plate(out_path=p, expression=exp, pose="front_view")
        expr_index[exp] = str(p.relative_to(ASSET_ROOT))
    _write_json(expr_dir / "index.json", {"expressions": expr_index, "visemes": VISEMES})

    # Poses
    pose_dir = ASSET_ROOT / "POSE_LIBRARY"
    pose_index: dict[str, str] = {}
    for pose in POSES:
        p = pose_dir / f"{pose}.png"
        if force or not p.is_file():
            draw_the_doctor_plate(out_path=p, expression="teaching", pose=pose)
        pose_index[pose] = str(p.relative_to(ASSET_ROOT))
    _write_json(pose_dir / "index.json", {"poses": pose_index})

    # Animation library (reusable clip definitions — executed by Animation Engine / true_motion)
    anim_dir = ASSET_ROOT / "ANIMATION_LIBRARY"
    anim_index: dict[str, Any] = {}
    for anim in ANIMATIONS:
        clip = {
            "id": f"ANIM-DOC-{anim.upper()}",
            "name": anim,
            "character": ASSET_ID,
            "loop": anim in {"idle", "breathing", "blinking"},
            "true_motion_hint": "point_teach" if "teach" in anim or "point" in anim else "walk_explain",
            "performance_verbs": [anim],
            "reusable": True,
        }
        _write_json(anim_dir / f"{anim}.json", clip)
        anim_index[anim] = f"{anim}.json"
    _write_md(
        anim_dir / "README.md",
        "# Animation Library — The Doctor\n\nReusable motion definitions for Animation Engine / true_motion.\n"
        "Not a new renderer — metadata + plates only.\n",
    )
    _write_json(anim_dir / "index.json", anim_index)

    # Wardrobe plates
    ward_dir = ASSET_ROOT / "WARDROBE"
    for w in WARDROBE:
        p = ward_dir / f"{w}.png"
        if force or not p.is_file():
            draw_the_doctor_plate(out_path=p, expression="confident", pose="three_quarter", wardrobe=w)
    _write_json(ward_dir / "index.json", {"outfits": WARDROBE})

    # World / environment
    env_dir = ASSET_ROOT / "ENVIRONMENT_PACKAGE"
    world = gmri_world_package()
    _write_json(env_dir / "WORLD_PACKAGE.json", world)
    rooms_dir = env_dir / "rooms"
    room_plates: dict[str, str] = {}
    for room in GMRI_ROOMS:
        p = rooms_dir / f"{room}.png"
        if force or not p.is_file():
            draw_environment_plate(out_path=p, room=room)
        room_plates[room] = str(p.relative_to(ASSET_ROOT))
    _write_json(rooms_dir / "index.json", room_plates)

    light_dir = ASSET_ROOT / "LIGHTING_PRESETS"
    for name, preset in lighting_presets().items():
        _write_json(light_dir / f"{name}.json", preset)
    _write_json(light_dir / "index.json", lighting_presets())

    prop_dir = ASSET_ROOT / "PROP_LIBRARY"
    _write_json(prop_dir / "props.json", prop_library())
    obj_dir = ASSET_ROOT / "REUSABLE_OBJECTS"
    _write_json(obj_dir / "objects.json", reusable_objects())

    # Hero reference plate for CWS
    hero = ASSET_ROOT / "plates" / "char-0001_hero.png"
    if force or not hero.is_file():
        draw_the_doctor_plate(out_path=hero, expression="teaching", pose="hero")

    prior_summary = None
    if existing:
        prior_summary = {
            "version": existing.get("version"),
            "generated_at": existing.get("generated_at"),
            "status": existing.get("status"),
        }

    manifest = {
        "package_type": "GENERATIONAL_STUDIO_ASSET",
        "asset_number": "0001",
        "id": ASSET_ID,
        "slug": ASSET_SLUG,
        "name": "The Doctor",
        "version": ASSET_VERSION,
        "status": "permanent",
        "generated_at": _now(),
        "root": str(ASSET_ROOT),
        "style_mode": "cinematic_realism",
        "outputs": {
            "CHARACTER_PROFILE.json": True,
            "CHARACTER_MODEL_GUIDE.pdf": (ASSET_ROOT / "CHARACTER_MODEL_GUIDE.pdf").is_file(),
            "CHARACTER_EXPRESSIONS": len(expr_index),
            "POSE_LIBRARY": len(pose_index),
            "ANIMATION_LIBRARY": len(anim_index),
            "VOICE_PROFILE.json": True,
            "PERSONALITY_GUIDE.md": True,
            "BIOGRAPHY.md": True,
            "WORLD_GUIDE.md": True,
            "ENVIRONMENT_PACKAGE": True,
            "LIGHTING_PRESETS": True,
            "COLOR_GUIDE.md": True,
            "PROP_LIBRARY": True,
            "REUSABLE_OBJECTS": True,
            "CONTINUITY_RULES.md": True,
            "HUMAN_REALISM": True,
            "CHARACTER_IDENTITY.json": hr_written.get("CHARACTER_IDENTITY.json", False),
            "SKELETON_PROFILE.json": hr_written.get("SKELETON_PROFILE.json", False),
            "FACE_RIG_PROFILE.json": hr_written.get("FACE_RIG_PROFILE.json", False),
            "GAIT_PROFILE.json": hr_written.get("GAIT_PROFILE.json", False),
            "GESTURE_LIBRARY.json": hr_written.get("GESTURE_LIBRARY.json", False),
            "EMOTION_LIBRARY.json": hr_written.get("EMOTION_LIBRARY.json", False),
            "WARDROBE_PROFILE.json": hr_written.get("WARDROBE_PROFILE.json", False),
            "CHARACTER_CONTINUITY_RULES.md": hr_written.get("CHARACTER_CONTINUITY_RULES.md", False),
            "PERFORMANCE_PLAN.schema.json": hr_written.get("PERFORMANCE_PLAN.schema.json", False),
        },
        "philosophy": {
            "no_new_renderer": True,
            "no_pipeline_redesign": True,
            "permanent_ip": True,
            "cast_do_not_regenerate": True,
            "human_character_realism_v1": True,
        },
        "prior": prior_summary,
    }
    _write_json(manifest_path, manifest)

    upsert_asset(
        {
            "id": ASSET_ID,
            "canonical_id": "DOCTOR_001",
            "asset_number": "0001",
            "name": "The Doctor",
            "slug": ASSET_SLUG,
            "version": ASSET_VERSION,
            "status": "permanent",
            "role": "Lead Scientific Educator",
            "path": f"data/studio_assets/{ASSET_SLUG}/",
            "home_world": "LOC-GMRI",
            "flagship_science_educator": True,
            "manifest": "MANIFEST.json",
            "superseded_by": "data/studio_assets/DOCTOR_001/",
        }
    )
    # Keep canonical Studio Character package in sync
    try:
        from services.studio_assets.doctor_001 import ensure_doctor_001_asset

        ensure_doctor_001_asset(force=False)
    except Exception:  # noqa: BLE001
        pass
    return manifest
