"""Publishing provider interface — the contract every platform adapter implements.

Platform SDKs and APIs live behind this interface; the Publishing Engine,
queue, and scheduler never import a vendor SDK. Mock adapters live in
`providers/publishing/` — a real integration replaces one adapter without
changing the engine, queue, retry, or scheduling logic.

Contract:
- `key` is the canonical platform id ("youtube_shorts", "tiktok", ...).
- `constraints()` describes platform metadata limits the package builder
  applies (title/description length, hashtag count, duration, ...).
- `retry_policy()` returns provider-specific overrides merged over the
  RetryManager's default policy (empty dict = defaults).
- `validate()` reports problems with a publishing package (empty = valid).
- `format_metadata()` fits package metadata to the platform's constraints
  and returns the adjusted fields plus `format_warnings`.
- `publish()` performs (or mocks) one publish attempt and returns a
  standardized attempt result — it must never raise for expected failures.
"""

from __future__ import annotations

from abc import abstractmethod

from providers.base import Provider


class PublishingProvider(Provider):
    key: str = ""       # canonical platform id — doubles as the registry key
    label: str = ""
    aliases: "tuple[str, ...]" = ()   # alternate platform ids that map here

    def is_available(self) -> bool:
        return True

    def constraints(self) -> dict:
        """Platform metadata limits; adapters override the defaults."""
        return {
            "max_title_chars": 100,
            "max_description_chars": 5000,
            "max_hashtags": 15,
            "max_duration_sec": 60,
            "supports_playlists": False,
            "supports_categories": False,
            "visibility_options": ["public", "unlisted", "private"],
        }

    def retry_policy(self) -> dict:
        """Provider-specific retry overrides (see DEFAULT_RETRY_POLICY)."""
        return {}

    def validate(self, package: dict) -> "list[str]":
        """Problems that would block a publish on this platform (empty = ok)."""
        problems = []
        limits = self.constraints()
        if not package.get("title"):
            problems.append("missing title")
        if len(package.get("title", "")) > limits["max_title_chars"]:
            problems.append(f"title exceeds {limits['max_title_chars']} chars")
        if len(package.get("description", "")) > limits["max_description_chars"]:
            problems.append(f"description exceeds {limits['max_description_chars']} chars")
        if len(package.get("hashtags", [])) > limits["max_hashtags"]:
            problems.append(f"more than {limits['max_hashtags']} hashtags")
        duration = float(package.get("video", {}).get("duration_sec", 0) or 0)
        if limits.get("max_duration_sec") and duration > limits["max_duration_sec"]:
            problems.append(f"video exceeds {limits['max_duration_sec']}s")
        return problems

    def format_metadata(self, package: dict) -> dict:
        """Fit metadata to the platform limits; returns adjusted fields.

        Result: {title, description, hashtags, format_warnings}. Truncation
        is reported, never silent.
        """
        limits = self.constraints()
        warnings = []
        title = package.get("title", "")
        if len(title) > limits["max_title_chars"]:
            title = title[: limits["max_title_chars"] - 1].rstrip() + "…"
            warnings.append(f"title truncated to {limits['max_title_chars']} chars")
        description = package.get("description", "")
        if len(description) > limits["max_description_chars"]:
            description = description[: limits["max_description_chars"]]
            warnings.append(f"description truncated to {limits['max_description_chars']} chars")
        hashtags = list(package.get("hashtags", []))
        if len(hashtags) > limits["max_hashtags"]:
            hashtags = hashtags[: limits["max_hashtags"]]
            warnings.append(f"hashtags capped at {limits['max_hashtags']}")
        return {
            "title": title,
            "description": description,
            "hashtags": hashtags,
            "format_warnings": warnings,
        }

    @abstractmethod
    def publish(self, package: dict) -> dict:
        """One publish attempt. Returns the standardized attempt result:

        {status: "published"|"failed", provider, platform, post_id,
         post_url, published_at, error, mock}
        """
