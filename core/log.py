"""Central structured logging for Generational.

Every module gets its logger via `get_logger(__name__)`. Logs go to the
console and to `data/logs/generational.log` so autonomous runs leave an
auditable trail.

For machine-parseable operational events, use `log_event`:

    log_event(logger, "job.completed", job_id=job.id, status=job.status)

which emits `job.completed | job_id=... status=...` — a stable
`event | key=value` format that later log pipelines can parse without
changing call sites.
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


def _format_value(value) -> str:
    text = str(value)
    if " " in text or "=" in text:
        return f'"{text}"'
    return text


def log_event(logger: logging.Logger, event: str, level: int = logging.INFO, **fields) -> None:
    """Emit a structured `event | key=value ...` log line."""
    if fields:
        pairs = " ".join(f"{key}={_format_value(value)}" for key, value in fields.items())
        logger.log(level, "%s | %s", event, pairs)
    else:
        logger.log(level, "%s", event)
