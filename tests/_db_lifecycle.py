"""Explicit ownership registry for test-scoped SQLite connections."""

from __future__ import annotations

import sqlite3

_PERSISTENT_CONNECTIONS: list[sqlite3.Connection] = []


def preserve_test_connection(connection: sqlite3.Connection) -> None:
    """Keep a shared fixture connection open across per-test teardown."""

    if not any(candidate is connection for candidate in _PERSISTENT_CONNECTIONS):
        _PERSISTENT_CONNECTIONS.append(connection)


def release_test_connection(connection: sqlite3.Connection) -> None:
    """Return a shared fixture connection to ordinary teardown ownership."""

    _PERSISTENT_CONNECTIONS[:] = [
        candidate for candidate in _PERSISTENT_CONNECTIONS if candidate is not connection
    ]


def is_persistent_test_connection(connection: sqlite3.Connection) -> bool:
    return any(candidate is connection for candidate in _PERSISTENT_CONNECTIONS)
