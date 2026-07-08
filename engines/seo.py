"""SEO engine (planned) — keyword optimization for titles, tags, descriptions."""

from __future__ import annotations

from engines.base import PlannedEngine


class SeoEngine(PlannedEngine):
    key = "seo"
    label = "SEO"
    icon = "🔑"
    description = "Keyword research and metadata optimization."
