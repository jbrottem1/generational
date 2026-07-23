"""Global Localization — architecture and interfaces, not translation.

Prepares every ContentPackage for multi-language, multi-country
distribution: per-locale plans with keyword-replacement slots, regional
hashtags, regional posting strategy, and a readiness score. Full
translation is intentionally NOT performed yet — every localized string
slot is marked `pending_translation` and a `LocalizationAdapter`
implementation (human, machine, or provider-backed) fills it in later
without any interface change.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


def _clamp(value: float, low: int = 5, high: int = 98) -> int:
    return int(max(low, min(high, value)))

from services.publishing.targets import LOCALIZATION_TARGETS


class LocalizationAdapter(ABC):
    """Contract for future localization backends (human, MT, provider APIs).

    The Optimization Engine only ever calls these three methods; swapping a
    heuristic adapter for a real translation provider changes nothing
    downstream.
    """

    key: str = ""
    label: str = ""

    def is_available(self) -> bool:
        return True

    @abstractmethod
    def localize_keywords(self, keywords: "list[str]", country: str, language: str) -> "list[dict]":
        """Per-keyword replacement slots: {base, localized, status}."""

    @abstractmethod
    def localize_hashtags(self, hashtags: "list[str]", country: str, language: str) -> "list[str]":
        """Regional hashtag set for the locale."""

    @abstractmethod
    def posting_strategy(self, country: str, language: str, platform: str) -> dict:
        """Regional posting plan: timezone, peak hours, cadence notes."""


class HeuristicLocalizationAdapter(LocalizationAdapter):
    """Default adapter — prepares structure only; performs NO translation."""

    key = "heuristic"
    label = "Heuristic (structure only, no translation)"

    def localize_keywords(self, keywords, country, language):
        return [
            {"base": keyword, "localized": None, "status": "pending_translation"}
            for keyword in keywords
        ]

    def localize_hashtags(self, hashtags, country, language):
        regional = [f"#{country}"] if country else []
        return list(dict.fromkeys(hashtags + regional))

    def posting_strategy(self, country, language, platform):
        target = next((t for t in LOCALIZATION_TARGETS if t[0] == country), None)
        utc_offset, peak = (target[2], target[3]) if target else (0, (17, 21))
        return {
            "platform": platform,
            "country": country,
            "language": language,
            "utc_offset_hours": utc_offset,
            "peak_hours_local": list(peak),
            "cadence_note": f"Post during {peak[0]}:00-{peak[1]}:00 local time for the {country} audience.",
        }


def locale_code(country: str, language: str) -> str:
    return f"{language.lower()}-{country.upper()}"


def build_localization_package(
    base_country: str,
    base_language: str,
    keywords: "list[str]",
    hashtags: "list[str]",
    platform: str = "youtube",
    targets: "list | None" = None,
    adapter: "LocalizationAdapter | None" = None,
) -> dict:
    """Per-locale preparation plans (see LOCALIZATION_TARGET_FIELDS).

    Structure-complete, translation-pending: readiness reflects that the
    architecture is in place but localized copy is not yet produced.
    """
    adapter = adapter or HeuristicLocalizationAdapter()
    targets = targets if targets is not None else [(t[0], t[1]) for t in LOCALIZATION_TARGETS]

    plans = []
    for country, language in targets:
        is_base = country == base_country and language == base_language
        replacements = adapter.localize_keywords(keywords, country, language)
        translation_pending = (not is_base) and any(
            item["status"] == "pending_translation" for item in replacements
        )
        readiness = 100 if is_base else _clamp(
            40 + (10 if replacements else 0) + (10 if hashtags else 0), low=0, high=70
        )
        plans.append({
            "country": country,
            "language": language,
            "locale": locale_code(country, language),
            "status": "ready" if is_base else "prepared",
            "translation_pending": translation_pending,
            "keyword_replacements": replacements if not is_base else [],
            "regional_hashtags": adapter.localize_hashtags(hashtags, country, language),
            "regional_posting": adapter.posting_strategy(country, language, platform),
            "regional_seo_notes": (
                "Base locale — no localization needed."
                if is_base
                else f"Replace keyword slots with {language} search terms before publishing to {country}."
            ),
            "readiness": readiness,
        })

    overall = int(round(sum(plan["readiness"] for plan in plans) / len(plans))) if plans else 0
    return {
        "base_locale": locale_code(base_country, base_language),
        "adapter": adapter.key,
        "translation_performed": False,
        "supported_countries": sorted({plan["country"] for plan in plans}),
        "supported_languages": sorted({plan["language"] for plan in plans}),
        "targets": plans,
        "readiness": overall,
    }
