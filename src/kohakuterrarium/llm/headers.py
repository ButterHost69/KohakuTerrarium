"""Validation and merge rules for provider-configured HTTP headers.

Header maps arrive from user YAML, preset ``extra_body``, and runtime
session binding; every source funnels through these helpers so an invalid
name or a control character can never reach a request, and so two maps
that spell one header with different casing never send it twice.
"""

import re
from collections.abc import Mapping
from typing import Any

# RFC 7230 token characters accepted in an HTTP header name.
_HEADER_NAME_RE = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")
# Bytes that must never appear inside a header value on the wire.
_ILLEGAL_VALUE_RE = re.compile(r"[\r\n\x00-\x1f\x7f]")


def normalize_header_name(name: Any) -> str:
    """Return ``name`` when it is a valid header token, else ``""``."""
    if isinstance(name, str) and _HEADER_NAME_RE.match(name):
        return name
    return ""


def validate_header_name(name: Any) -> str:
    """Strict variant for save paths; raises ``ValueError`` on a bad name."""
    normalized = normalize_header_name(name)
    if not normalized:
        raise ValueError(f"invalid header name: {name!r}")
    return normalized


def normalize_header_map(raw: Any) -> dict[str, str]:
    """Coerce config input into a ``{name: value}`` map, dropping bad rows.

    Tolerant by design for deserialization: non-mapping input becomes
    ``{}``, unusable names and ``None`` values are dropped, scalar values
    are stringified, and values carrying control characters are skipped.
    """
    if not isinstance(raw, Mapping):
        return {}
    headers: dict[str, str] = {}
    for name, value in raw.items():
        normalized = normalize_header_name(name)
        if not normalized or value is None:
            continue
        text = value if isinstance(value, str) else str(value)
        if _ILLEGAL_VALUE_RE.search(text):
            continue
        headers[normalized] = text
    return headers


def validate_header_map(raw: Any) -> dict[str, str]:
    """Strict variant for save paths; raises ``ValueError`` on any bad row."""
    if raw is None:
        return {}
    if not isinstance(raw, Mapping):
        raise ValueError("extra_headers must be a mapping of names to values")
    headers: dict[str, str] = {}
    for name, value in raw.items():
        normalized = validate_header_name(name)
        if value is None:
            continue
        text = value if isinstance(value, str) else str(value)
        if _ILLEGAL_VALUE_RE.search(text):
            raise ValueError(f"header {normalized!r} value has control characters")
        headers[normalized] = text
    return headers


def merge_header_maps(*maps: Mapping[str, str] | None) -> dict[str, str]:
    """Merge header maps case-insensitively; later maps win.

    The winner keeps its own casing and replaces any earlier entry whose
    lowercased name matches, so a session header can never be sent twice
    under different casing.
    """
    winners: dict[str, tuple[str, str]] = {}
    for mapping in maps:
        if not mapping:
            continue
        for name, value in mapping.items():
            winners[name.lower()] = (name, value)
    return {name: value for name, value in winners.values()}
