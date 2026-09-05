"""Rendered command helpers."""

from __future__ import annotations

import secrets
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def idempotency_key() -> str:
    return secrets.token_urlsafe(24)


def draft_ack_path(path: str, token: str) -> str:
    if not token:
        return path
    parts = urlsplit(path)
    query = parse_qsl(parts.query, keep_blank_values=True)
    query.append(("draft_ack", token))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))
