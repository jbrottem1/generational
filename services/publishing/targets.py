"""Publishing localization targets — shared constants without circular imports."""

from __future__ import annotations

# (country, language, UTC offset of main audience timezone, peak local hours).
LOCALIZATION_TARGETS = (
    ("US", "en", -5, (17, 21)),
    ("GB", "en", 0, (17, 20)),
    ("ES", "es", 1, (18, 22)),
    ("MX", "es", -6, (18, 22)),
    ("BR", "pt", -3, (18, 22)),
    ("DE", "de", 1, (17, 20)),
    ("FR", "fr", 1, (18, 21)),
    ("IN", "hi", 5, (19, 22)),
    ("JP", "ja", 9, (19, 22)),
    ("ID", "id", 7, (18, 21)),
)
