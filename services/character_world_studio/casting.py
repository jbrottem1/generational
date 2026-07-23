"""Cast hosts + pick locations from topic / VFD / world package."""

from __future__ import annotations

from typing import Any

from services.character_world_studio.cast import HOST_CAST, get_host
from services.character_world_studio.locations import LOCATIONS, get_location


def _blob(candidate: dict[str, Any], topic: str) -> str:
    parts = [
        topic,
        str(candidate.get("title") or ""),
        str(candidate.get("niche") or ""),
        str((candidate.get("world_package") or {}).get("world_type") or ""),
        str((candidate.get("world_package") or {}).get("theme") or ""),
    ]
    vp = candidate.get("visual_package") if isinstance(candidate.get("visual_package"), dict) else {}
    for s in vp.get("scenes") or []:
        if isinstance(s, dict):
            parts.append(str(s.get("narration") or ""))
            parts.append(str(s.get("subject") or ""))
    return " ".join(parts).lower()


def choose_location(candidate: dict[str, Any], *, topic: str = "") -> dict[str, Any]:
    text = _blob(candidate, topic)
    if any(w in text for w in ("hydrant", "pipe", "valve", "engineer", "factory", "workshop")):
        text += " engineering infrastructure factory"
    if any(w in text for w in ("ocean", "reef", "octopus", "marine")):
        text += " ocean biology"
    if any(w in text for w in ("medical", "doctor", "hospital", "anatomy", "dna", "clinical", "vaccine", "body")):
        text += " medicine biology health anatomy science"
    if any(w in text for w in ("legend", "myth", "folklore", "leprechaun", "medieval")):
        text += " history folklore village library"
    # Prefer existing world_builder id if mapped
    wp = candidate.get("world_package") if isinstance(candidate.get("world_package"), dict) else {}
    wid = str(wp.get("world_id") or "").upper()
    for loc in LOCATIONS.values():
        hint = str(loc.get("world_builder_hint") or "").upper()
        if wid and hint and hint == wid:
            return dict(loc)
    # Domain keyword scoring
    best = None
    best_score = -1
    for loc in LOCATIONS.values():
        score = 0
        for d in loc.get("domains") or []:
            if d in text:
                score += 3
        name = str(loc.get("name") or "").lower()
        for token in name.split():
            if len(token) > 3 and token in text:
                score += 1
        if score > best_score:
            best_score = score
            best = loc
    return dict(best or LOCATIONS["LOC-SCIENCE-MUSEUM"])


def choose_hosts(candidate: dict[str, Any], *, topic: str = "", location: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    text = _blob(candidate, topic)
    location = location or choose_location(candidate, topic=topic)
    # Lightweight synonym boosts for educational niches
    if any(w in text for w in ("hydrant", "pipe", "valve", "infrastructure", "engineer", "factory", " mechan")):
        text += " engineering infrastructure mechanics invention"
    if any(w in text for w in ("ocean", "reef", "octopus", "marine", "whale")):
        text += " ocean biology nature animals exploration"
    if any(w in text for w in ("ai", "model", "neural", "algorithm", "computer")):
        text += " ai technology computing patterns"
    if any(w in text for w in ("cell", "dna", "heart", "medical", "biology", "animal", "anatomy", "vaccine")):
        text += " biology medicine health nature anatomy"
    if any(w in text for w in ("chemistry", "molecule", "atom", "physics", "force", "energy")):
        text += " chemistry physics science"
    if any(w in text for w in ("legend", "myth", "folklore", "medieval", "ancient", "history")):
        text += " history folklore mythology"
    # Prefer The Doctor's permanent home for clinical / science education
    if any(w in text for w in ("medical", "doctor", "hospital", "anatomy", "dna", "clinical", "vaccine")):
        text += " medicine biology health anatomy"

    scores: list[tuple[int, dict[str, Any]]] = []
    for host in HOST_CAST.values():
        score = 0
        for d in host.get("domains") or []:
            if d in text:
                score += 4
        for env in host.get("recurring_environments") or []:
            if env == location.get("id"):
                score += 5
        # Permanent flagship science educator — prefer over ephemeral presenters
        if host.get("flagship_science_educator") or host["id"] in {"DOCTOR_001", "CHAR-0001"}:
            # Prefer canonical DOCTOR_001 over legacy alias when both present
            if host["id"] == "CHAR-0001":
                score -= 20
            clinical = any(
                d in text
                for d in (
                    "biology",
                    "medicine",
                    "chemistry",
                    "anatomy",
                    "health",
                    "physics",
                    "science",
                )
            )
            infra = any(
                d in text
                for d in ("infrastructure", "hydrant", "factory", "workshop", "valve", "pipe")
            )
            if clinical and not infra:
                score += 8
            elif "technology" in text and not infra:
                score += 5
            elif "engineering" in text and not infra:
                score += 4
            else:
                score += 1
        if host["id"] == "CHAR-PIPER" and any(
            d in text for d in ("infrastructure", "hydrant", "factory", "workshop", "mechanics")
        ):
            score += 8
        if host["id"] == "CHAR-ATLAS":
            score += 1
        scores.append((score, host))
    scores.sort(key=lambda x: (-x[0], x[1]["id"]))
    primary = dict(scores[0][1])
    cast = [primary]
    if len(scores) > 1 and scores[1][0] >= 4 and scores[1][1]["id"] != primary["id"]:
        cast.append(dict(scores[1][1]))
    return cast


def assign_scene_performers(
    scenes: list[dict[str, Any]],
    hosts: list[dict[str, Any]],
    *,
    location: dict[str, Any] | str | None = None,
) -> list[dict[str, Any]]:
    """Each scene gets a primary performer + Human Realism PerformancePlan."""
    from services.human_realism import attach_performance_plans

    if not hosts:
        hosts = [
            get_host("DOCTOR_001")
            or get_host("CHAR-0001")
            or get_host("CHAR-ATLAS")
            or next(iter(HOST_CAST.values()))
        ]
    primary = hosts[0]
    secondary = hosts[1] if len(hosts) > 1 else None
    out = []
    for i, scene in enumerate(scenes):
        row = dict(scene)
        # Alternate lightly for dialogue energy; keep Atlas as default teacher
        use = secondary if secondary and i % 3 == 1 else primary
        row["studio_character_id"] = use["id"]
        row["studio_character_name"] = use["name"]
        row["studio_performance"] = use.get("true_motion_performance") or "point_teach"
        row["studio_gestures"] = list(use.get("favorite_gestures") or [])
        row["studio_expression"] = (use.get("facial_range") or ["focus"])[i % max(1, len(use.get("facial_range") or ["focus"]))]
        out.append(row)
    hosts_by_id = {str(h["id"]).upper(): h for h in hosts}
    out = attach_performance_plans(out, hosts_by_id=hosts_by_id)
    # Facial Performance Standard — soft-attach structured face plans
    try:
        from services.character_performance import attach_facial_performance_plans

        out = attach_facial_performance_plans(out, hosts_by_id=hosts_by_id)
    except Exception:  # noqa: BLE001
        pass
    # Character Performance Engine — blocking / locomotion / actor paths (pre-render)
    try:
        from services.character_performance_engine import attach_character_performances

        out = attach_character_performances(
            out, hosts_by_id=hosts_by_id, location=location
        )
    except Exception:  # noqa: BLE001
        pass
    # Character Rig Studio — permanent digital actor refs (never regenerate)
    try:
        from services.character_rig_studio import attach_character_rigs

        out = attach_character_rigs(out, hosts_by_id=hosts_by_id)
    except Exception:  # noqa: BLE001
        pass
    # Stage & World Simulation — persistent explorable stages (not photo backdrops)
    try:
        from services.stage_world_simulation import attach_world_simulation

        out = attach_world_simulation(out, location=location)
    except Exception:  # noqa: BLE001
        pass
    # Physics & Interaction — physical behavior for actors/objects
    try:
        from services.physics_interaction import attach_physics_interactions

        out = attach_physics_interactions(
            out, hosts_by_id=hosts_by_id, location=location
        )
    except Exception:  # noqa: BLE001
        pass
    # Cinematic Direction Studio — intentional shot / actor direction
    try:
        from services.cinematic_direction_studio import attach_cinematic_direction

        out = attach_cinematic_direction(out, location=location)
    except Exception:  # noqa: BLE001
        pass
    return out
