"""Central logging setup for Generational.

Every module gets its logger via `get_logger(__name__)`. Logs go to the
console and to `data/logs/generational.log` so autonomous runs leave an
auditable trail.
"""

from __future__ import annotations

import logging
import os

_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "logs")
_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
_configured = False


def _configure() -> None:
    global _configured
    if _configured:
        return

    root = logging.getLogger("generational")
    root.setLevel(logging.INFO)
    formatter = logging.Formatter(_FORMAT)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root.addHandler(console)

    try:
        os.makedirs(_LOG_DIR, exist_ok=True)
        file_handler = logging.FileHandler(os.path.join(_LOG_DIR, "generational.log"), encoding="utf-8")
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
    except OSError:  # e.g. read-only filesystem — console logging still works
        root.warning("Could not create log file directory; logging to console only.")

    _configured = True


def get_logger(name: str) -> logging.Logger:
    _configure()
    short_name = name.replace("generational.", "")
    return logging.getLogger(f"generational.{short_name}")
