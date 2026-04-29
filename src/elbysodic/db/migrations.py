"""Small ordered migration runner for SQLite database upgrades."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

CURRENT_SCHEMA_VERSION = 4
BASELINE_MIGRATION_NAME = "baseline-current-schema"


@dataclass(frozen=True, slots=True)
class Migration:
    version: int
    name: str
    apply: Callable[[sqlite3.Connection], None]


def _add_plotting_room_planning_fields(connection: sqlite3.Connection) -> None:
    columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(plotting_rooms)").fetchall()
    }
    for name, definition in {
        "notes": "TEXT NOT NULL DEFAULT ''",
        "next_step": "TEXT NOT NULL DEFAULT ''",
        "target_board_id": "INTEGER REFERENCES boards(id) ON DELETE SET NULL",
        "target_thread_id": "INTEGER REFERENCES threads(id) ON DELETE SET NULL",
    }.items():
        if name not in columns:
            connection.execute(f"ALTER TABLE plotting_rooms ADD COLUMN {name} {definition}")
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_plotting_rooms_target_thread
        ON plotting_rooms(community_id, target_thread_id)
        """
    )


def _add_plotting_room_messages(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS plotting_room_messages (
            id INTEGER PRIMARY KEY,
            community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
            plotting_room_id INTEGER NOT NULL REFERENCES plotting_rooms(id) ON DELETE CASCADE,
            author_membership_id INTEGER NOT NULL REFERENCES community_memberships(id) ON DELETE CASCADE,
            author_character_id INTEGER REFERENCES characters(id) ON DELETE SET NULL,
            body TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_plotting_room_messages_room
        ON plotting_room_messages(community_id, plotting_room_id, id)
        """
    )


def _add_application_review_rooms(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY,
            community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
            membership_id INTEGER NOT NULL REFERENCES community_memberships(id) ON DELETE CASCADE,
            character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
            source_wanted_ad_id INTEGER REFERENCES wanted_ads(id) ON DELETE SET NULL,
            source_wanted_ad_interest_id INTEGER REFERENCES wanted_ad_interests(id) ON DELETE SET NULL,
            title TEXT NOT NULL,
            summary TEXT NOT NULL DEFAULT '',
            body TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'draft',
            revision_notes TEXT NOT NULL DEFAULT '',
            staff_notes TEXT NOT NULL DEFAULT '',
            checklist TEXT NOT NULL DEFAULT '',
            submitted_at TEXT,
            reviewed_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE (community_id, character_id)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS application_events (
            id INTEGER PRIMARY KEY,
            community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
            application_id INTEGER NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
            actor_membership_id INTEGER NOT NULL REFERENCES community_memberships(id) ON DELETE CASCADE,
            actor_character_id INTEGER REFERENCES characters(id) ON DELETE SET NULL,
            from_status TEXT,
            to_status TEXT NOT NULL,
            note TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_applications_status
        ON applications(community_id, status, updated_at)
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_applications_membership
        ON applications(community_id, membership_id, status)
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_application_events_application
        ON application_events(community_id, application_id, created_at, id)
        """
    )


MIGRATIONS: tuple[Migration, ...] = (
    Migration(2, "plotting-room-planning-fields", _add_plotting_room_planning_fields),
    Migration(3, "plotting-room-messages", _add_plotting_room_messages),
    Migration(4, "application-review-rooms", _add_application_review_rooms),
)


def apply_migrations(connection: sqlite3.Connection) -> None:
    """Record the current schema baseline and apply future ordered migrations."""

    _ensure_migration_table(connection)
    applied_versions = _applied_versions(connection)
    if not applied_versions:
        _record_migration(connection, CURRENT_SCHEMA_VERSION, BASELINE_MIGRATION_NAME)
        applied_versions.update(migration.version for migration in MIGRATIONS)
        applied_versions.add(CURRENT_SCHEMA_VERSION)

    baseline_version = max(applied_versions)
    for migration in sorted(MIGRATIONS, key=lambda item: item.version):
        if migration.version in applied_versions or migration.version <= baseline_version:
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
