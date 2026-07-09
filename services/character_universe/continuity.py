"""Continuity engine — the studio's contradiction detector.

Two responsibilities:

1. Record every character appearance (content id, outfit, location, voice,
   visual signature) so history is queryable.
2. Validate the whole IP catalog and every new appearance against it —
   duplicates, contradictory history, missing references, timeline errors,
   relationship errors, lore violations, and visual/voice/brand drift.

Findings are ContinuityIssue dicts (never exceptions): severity "error"
or "warning", filtered by the configured strictness. Detection is
deterministic — no LLM required.
"""

from __future__ import annotations

from difflib import SequenceMatcher

from services.character_universe.config import get_character_universe_config
from services.character_universe.models import (
    CharacterStatus,
    build_appearance,
    build_continuity_issue,
)
from services.character_universe.registry import CharacterUniverseRegistry, get_character_universe_registry


def _issue(severity: str, category: str, entity_type: str, entity_id: str,
           description: str, suggestion: str = "", **evidence) -> dict:
    return build_continuity_issue(
        {
            "severity": severity, "category": category, "entity_type": entity_type,
            "entity_id": entity_id, "description": description,
            "suggestion": suggestion, "evidence": evidence,
        }
    )


class ContinuityEngine:
    def __init__(self, registry: "CharacterUniverseRegistry | None" = None) -> None:
        self.registry = registry or get_character_universe_registry()

    # -------------------------------------------------- appearance history

    def record_appearance(self, spec: dict) -> dict:
        """Log one character appearance in one piece of content, and return
        {"appearance": ..., "issues": [...]} — drift is detected at write
        time, against the character's own canonical profile and history."""
        appearance = build_appearance(spec)
        character = self.registry.get("characters", appearance["character_id"])
        issues = self._check_appearance(appearance, character)
        self.registry.store.save("appearances", appearance, appearance["appearance_id"])
        return {"appearance": appearance, "issues": self._apply_strictness(issues)}

    def history_for(self, character_id: str) -> list:
        appearances = self.registry.list("appearances", character_id=character_id)
        appearances.sort(key=lambda appearance: appearance.get("recorded_at", ""))
        return appearances

    def outfit_history(self, character_id: str) -> list:
        return [
            {"content_id": appearance.get("content_id", ""), "outfit": appearance.get("outfit", ""),
             "recorded_at": appearance.get("recorded_at", "")}
            for appearance in self.history_for(character_id)
            if appearance.get("outfit")
        ]

    # ------------------------------------------------------ catalog audit

    def validate_all(self, universe_id: str = "") -> list:
        """Full continuity audit; optionally scoped to one universe."""
        issues = []
        characters = (
            self.registry.characters_in_universe(universe_id)
            if universe_id else self.registry.list("characters")
        )
        issues += self._check_duplicates(characters)
        issues += self._check_references(characters, universe_id)
        issues += self._check_relationships(characters)
        issues += self._check_timelines(universe_id)
        issues += self._check_lore(characters, universe_id)
        for character in characters:
            for appearance in self.history_for(character["character_id"]):
                issues += self._check_appearance(appearance, character, historical=True)
        return self._apply_strictness(issues)

    # -------------------------------------------------------------- checks

    def _check_duplicates(self, characters: list) -> list:
        issues = []
        threshold = get_character_universe_config().duplicate_name_threshold
        seen: "list[dict]" = []
        for character in characters:
            if character.get("status") == CharacterStatus.ARCHIVED:
                continue
            name = (character.get("name") or "").strip().lower()
            for earlier in seen:
                other = (earlier.get("name") or "").strip().lower()
                if not name or not other:
                    continue
                similarity = SequenceMatcher(None, name, other).ratio()
                if similarity >= threshold and character.get("universe_id") == earlier.get("universe_id"):
                    issues.append(_issue(
                        "error", "duplicate_character", "character", character["character_id"],
                        f"'{character.get('name')}' duplicates '{earlier.get('name')}' "
                        f"({earlier['character_id']}) in the same universe",
                        "merge the characters or rename one",
                        similarity=round(similarity, 3), other_id=earlier["character_id"],
                    ))
            seen.append(character)
        return issues

    def _check_references(self, characters: list, universe_id: str = "") -> list:
        issues = []
        universe_ids = {universe["universe_id"] for universe in self.registry.list("universes")}
        location_ids = {location["location_id"] for location in self.registry.list("locations")}
        for character in characters:
            ref = character.get("universe_id")
            if ref and ref not in universe_ids:
                issues.append(_issue(
                    "error", "missing_reference", "character", character["character_id"],
                    f"character references unknown universe '{ref}'",
                    "create the universe or clear the reference",
                ))
        events = self.registry.list("canon_events", universe_id=universe_id) if universe_id \
            else self.registry.list("canon_events")
        character_ids = {character["character_id"] for character in self.registry.list("characters")}
        for event in events:
            for participant in event.get("participants", []):
                if participant not in character_ids:
                    issues.append(_issue(
                        "warning", "missing_reference", "canon_event", event["event_id"],
                        f"canon event '{event.get('title')}' references unknown participant '{participant}'",
                    ))
            loc = event.get("location_id")
            if loc and loc not in location_ids:
                issues.append(_issue(
                    "warning", "missing_reference", "canon_event", event["event_id"],
                    f"canon event '{event.get('title')}' references unknown location '{loc}'",
                ))
        return issues

    def _check_relationships(self, characters: list) -> list:
        issues = []
        character_ids = {character["character_id"] for character in self.registry.list("characters")}
        for relationship in self.registry.list("relationships"):
            for endpoint in ("source_id", "target_id"):
                if relationship.get(endpoint) not in character_ids:
                    issues.append(_issue(
                        "error", "relationship_error", "relationship", relationship["relationship_id"],
                        f"relationship {endpoint} '{relationship.get(endpoint)}' does not exist",
                    ))
            if relationship.get("source_id") == relationship.get("target_id"):
                issues.append(_issue(
                    "warning", "relationship_error", "relationship", relationship["relationship_id"],
                    "relationship links a character to itself",
                ))
        return issues

    def _check_timelines(self, universe_id: str = "") -> list:
        issues = []
        universes = (
            [self.registry.get("universes", universe_id)] if universe_id
            else self.registry.list("universes")
        )
        for universe in universes:
            if not universe:
                continue
            events = self.registry.canon_events_for(universe["universe_id"])
            sequences = [event.get("sequence", 0) for event in events]
            duplicated = {seq for seq in sequences if seq and sequences.count(seq) > 1}
            for seq in sorted(duplicated):
                clashing = [event["event_id"] for event in events if event.get("sequence") == seq]
                issues.append(_issue(
                    "warning", "timeline_error", "universe", universe["universe_id"],
                    f"multiple canon events share timeline sequence {seq}",
                    "give each canon event a unique sequence", events=clashing,
                ))
        return issues

    def _check_lore(self, characters: list, universe_id: str = "") -> list:
        """Rule packs: each lore/universe/brand rule is a dict like
        {"forbid": "time travel", "scope": "biography", "reason": "..."} —
        the forbidden phrase must not appear in the scoped text fields."""
        issues = []
        config = get_character_universe_config()
        rules = list(config.lore_rules) + list(config.universe_rules)
        universe = self.registry.get("universes", universe_id) if universe_id else None
        if universe:
            rules += [rule for rule in universe.get("rules", []) if isinstance(rule, dict)]
        for rule in rules:
            phrase = str(rule.get("forbid", "")).lower()
            if not phrase:
                continue
            scope = rule.get("scope", "biography")
            for character in characters:
                text = str(character.get(scope, "")).lower()
                if phrase in text:
                    issues.append(_issue(
                        "error", "lore_violation", "character", character["character_id"],
                        f"'{phrase}' violates lore rule in {scope}: {rule.get('reason', 'forbidden')}",
                        rule=rule,
                    ))
        return issues

    def _check_appearance(self, appearance: dict, character: "dict | None",
                          historical: bool = False) -> list:
        issues = []
        if character is None:
            return [_issue(
                "error", "missing_reference", "appearance", appearance["appearance_id"],
                f"appearance references unknown character '{appearance.get('character_id')}'",
            )]

        character_id = character["character_id"]
        if character.get("status") in (CharacterStatus.DECEASED, CharacterStatus.RETIRED) and not historical:
            issues.append(_issue(
                "warning", "status_error", "character", character_id,
                f"'{character.get('name')}' is {character.get('status')} but appears in new content",
                "revive the character explicitly or recast the scene",
            ))

        canonical_visual = character.get("visual_profile", {}).get("visual_signature", "")
        appearing_visual = appearance.get("visual_signature", "")
        if canonical_visual and appearing_visual and appearing_visual != canonical_visual:
            issues.append(_issue(
                "warning", "visual_drift", "character", character_id,
                f"appearance visual signature diverges from canon for '{character.get('name')}'",
                "regenerate with the canonical reference prompt",
                canonical=canonical_visual, appeared=appearing_visual,
                content_id=appearance.get("content_id", ""),
            ))

        canonical_voice = character.get("voice_profile", {}).get("voice_id", "")
        appearing_voice = appearance.get("voice_id", "")
        if canonical_voice and appearing_voice and appearing_voice != canonical_voice:
            issues.append(_issue(
                "warning", "voice_drift", "character", character_id,
                f"appearance voice '{appearing_voice}' differs from canonical voice "
                f"'{canonical_voice}' for '{character.get('name')}'",
                "re-narrate with the canonical voice id",
                content_id=appearance.get("content_id", ""),
            ))

        brand_rules = get_character_universe_config().brand_rules
        for rule in brand_rules:
            phrase = str(rule.get("forbid", "")).lower()
            if phrase and phrase in str(appearance.get("outfit", "")).lower():
                issues.append(_issue(
                    "warning", "brand_drift", "character", character_id,
                    f"outfit '{appearance.get('outfit')}' violates brand rule: "
                    f"{rule.get('reason', 'forbidden')}",
                    rule=rule,
                ))
        return issues

    # ------------------------------------------------------------ policies

    def _apply_strictness(self, issues: list) -> list:
        strictness = get_character_universe_config().continuity_strictness
        if strictness == "strict":
            for issue in issues:
                issue["severity"] = "error"
            return issues
        if strictness == "relaxed":
            return [issue for issue in issues if issue["severity"] == "error"]
        return issues
