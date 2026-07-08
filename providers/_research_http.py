"""HTTP helpers for live research providers — graceful failure, demo fallback."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from core.log import get_logger, log_event

logger = get_logger(__name__)

USER_AGENT = "Generational/6.0 (https://github.com/jbrottem1/generational; research bot)"
DEFAULT_TIMEOUT = 10


def fetch_json(url: str, timeout: int = DEFAULT_TIMEOUT) -> dict | list | None:
    try:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError, OSError) as exc:
        log_event(logger, "research.http_failed", level=30, url=url[:120], error=str(exc))
        return None


def fetch_text(url: str, timeout: int = DEFAULT_TIMEOUT) -> str | None:
    try:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
        log_event(logger, "research.http_failed", level=30, url=url[:120], error=str(exc))
        return None


def fetch_xml(url: str, timeout: int = DEFAULT_TIMEOUT) -> ET.Element | None:
    text = fetch_text(url, timeout=timeout)
    if not text:
        return None
    try:
        return ET.fromstring(text)
    except ET.ParseError as exc:
        log_event(logger, "research.xml_parse_failed", level=30, error=str(exc))
        return None


def quote(value: str) -> str:
    return urllib.parse.quote(value)
