"""Small ordered migration runner for SQLite database upgrades."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

CURRENT_SCHEMA_VERSION = 1
BASELINE_MIGRATION_NAME = "baseline-current-schema"


@dataclass(frozen=True, slots=True)
class Migration:
    version: int
    name: str
    apply: Callable[[sqlite3.Connection], None]


MIGRATIONS: tuple[Migration, ...] = ()


def apply_migrations(connection: sqlite3.Connection) -> None:
    """Record the current schema baseline and apply future ordered migrations."""

    _ensure_migration_table(connection)
    applied_versions = _applied_versions(connection)
    if not applied_versions:
        _record_migration(connection, CURRENT_SCHEMA_VERSION, BASELINE_MIGRATION_NAME)
        applied_versions.add(CURRENT_SCHEMA_VERSION)

    for migration in sorted(MIGRATIONS, key=lambda item: item.version):
        if migration.version in applied_versions:
            continue
        migration.apply(connection)
        _record_migration(connection, migration.version, migration.name)
        applied_versions.add(migration.version)

    connection.execute(f"PRAGMA user_version = {CURRENT_SCHEMA_VERSION}")


def _ensure_migration_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TEXT NOT NULL
        )
        """
    )


def _applied_versions(connection: sqlite3.Connection) -> set[int]:
    rows = connection.execute("SELECT version FROM schema_migrations").fetchall()
    return {int(row["version"]) for row in rows}


def _record_migration(connection: sqlite3.Connection, version: int, name: str) -> None:
    connection.execute(
        """
        INSERT OR IGNORE INTO schema_migrations (version, name, applied_at)
        VALUES (?, ?, ?)
        """,
        (version, name, datetime.now(UTC).isoformat(timespec="seconds")),
    )
