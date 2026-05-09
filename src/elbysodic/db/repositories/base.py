"""Shared repository helpers."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta


class TenantBoundaryError(ValueError):
    """Raised when a write attempts to join rows from different communities."""


class RepositoryBase:
    """Base connection holder shared by repository mixins."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self._transaction_depth = 0

    @contextmanager
    def transaction(self) -> Iterator[None]:
        outermost = self._transaction_depth == 0
        if outermost:
            self.connection.execute("BEGIN")
        self._transaction_depth += 1
        try:
            yield
        except Exception:
            self._transaction_depth -= 1
            if outermost:
                self.connection.rollback()
            raise
        else:
            self._transaction_depth -= 1
            if outermost:
                self._commit()

    def _commit(self) -> None:
        if self._transaction_depth == 0:
            self.connection.commit()


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
