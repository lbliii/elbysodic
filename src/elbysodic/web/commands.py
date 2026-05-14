"""Rendered command helpers."""

from __future__ import annotations

import secrets


def idempotency_key() -> str:
    return secrets.token_urlsafe(24)
