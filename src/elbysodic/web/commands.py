"""Rendered command helpers."""

from __future__ import annotations

import secrets


def command_token() -> str:
    return secrets.token_urlsafe(24)
