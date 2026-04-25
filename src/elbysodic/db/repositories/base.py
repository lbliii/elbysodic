"""Shared repository helpers."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta


class TenantBoundaryError(ValueError):
    """Raised when a write attempts to join rows from different communities."""


class RepositoryBase:
    """Base connection holder shared by repository mixins."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _next_update_stamp(previous: str) -> str:
    now = _utc_now()
    try:
        previous_stamp = datetime.fromisoformat(previous)
        now_stamp = datetime.fromisoformat(now)
    except ValueError:
        return now
    if now_stamp <= previous_stamp:
        return (previous_stamp + timedelta(seconds=1)).isoformat(timespec="seconds")
    return now


def _last_id(cursor: sqlite3.Cursor) -> int:
    value = cursor.lastrowid
    if value is None:
        raise RuntimeError("insert did not return a row id")
    return value
