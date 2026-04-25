"""SQLite schema setup for the tenant-aware forum core."""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS communities (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    host TEXT UNIQUE,
    default_theme_id INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY,
    community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    slug TEXT NOT NULL,
    name TEXT NOT NULL,
    is_admin INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (community_id, slug)
);

CREATE TABLE IF NOT EXISTS community_memberships (
    id INTEGER PRIMARY KEY,
    community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    username TEXT NOT NULL,
    display_name TEXT NOT NULL,
    avatar_url TEXT,
    role_id INTEGER NOT NULL REFERENCES roles(id),
    default_character_id INTEGER REFERENCES characters(id) ON DELETE SET NULL,
    post_count INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    joined_at TEXT NOT NULL,
    UNIQUE (community_id, user_id),
    UNIQUE (community_id, username)
);

CREATE TABLE IF NOT EXISTS characters (
    id INTEGER PRIMARY KEY,
    community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    membership_id INTEGER NOT NULL REFERENCES community_memberships(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    slug TEXT NOT NULL,
    avatar_url TEXT,
    summary TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (community_id, slug)
);

CREATE TABLE IF NOT EXISTS boards (
    id INTEGER PRIMARY KEY,
    community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    slug TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_private INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (community_id, slug)
);

CREATE TABLE IF NOT EXISTS threads (
    id INTEGER PRIMARY KEY,
    community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    board_id INTEGER NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
    author_membership_id INTEGER NOT NULL REFERENCES community_memberships(id),
    author_character_id INTEGER NOT NULL REFERENCES characters(id),
    slug TEXT NOT NULL,
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    location TEXT NOT NULL DEFAULT '',
    timeline TEXT NOT NULL DEFAULT '',
    summary TEXT NOT NULL DEFAULT '',
    posting_mode TEXT NOT NULL DEFAULT 'freeform',
    is_locked INTEGER NOT NULL DEFAULT 0,
    is_pinned INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (community_id, board_id, slug)
);

CREATE TABLE IF NOT EXISTS thread_participants (
    id INTEGER PRIMARY KEY,
    community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    thread_id INTEGER NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    added_at TEXT NOT NULL,
    UNIQUE (community_id, thread_id, character_id)
);

CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY,
    community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    thread_id INTEGER NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
    author_membership_id INTEGER NOT NULL REFERENCES community_memberships(id),
    author_character_id INTEGER NOT NULL REFERENCES characters(id),
    body TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS post_revisions (
    id INTEGER PRIMARY KEY,
    community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    editor_membership_id INTEGER NOT NULL REFERENCES community_memberships(id),
    previous_body TEXT NOT NULL,
    new_body TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS themes (
    id INTEGER PRIMARY KEY,
    community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    slug TEXT NOT NULL,
    name TEXT NOT NULL,
    tokens_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (community_id, slug)
);

CREATE TABLE IF NOT EXISTS reactions (
    id INTEGER PRIMARY KEY,
    community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    membership_id INTEGER NOT NULL REFERENCES community_memberships(id) ON DELETE CASCADE,
    reaction_key TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (community_id, post_id, membership_id, reaction_key)
);

CREATE TABLE IF NOT EXISTS thread_reads (
    id INTEGER PRIMARY KEY,
    community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    thread_id INTEGER NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
    membership_id INTEGER NOT NULL REFERENCES community_memberships(id) ON DELETE CASCADE,
    read_at TEXT NOT NULL,
    UNIQUE (community_id, thread_id, membership_id)
);

CREATE TABLE IF NOT EXISTS thread_watches (
    id INTEGER PRIMARY KEY,
    community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    thread_id INTEGER NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
    membership_id INTEGER NOT NULL REFERENCES community_memberships(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL,
    UNIQUE (community_id, thread_id, membership_id)
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY,
    community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    membership_id INTEGER NOT NULL REFERENCES community_memberships(id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    thread_id INTEGER NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    actor_membership_id INTEGER NOT NULL REFERENCES community_memberships(id),
    actor_character_id INTEGER NOT NULL REFERENCES characters(id),
    read_at TEXT,
    created_at TEXT NOT NULL,
    UNIQUE (community_id, membership_id, kind, post_id)
);

CREATE INDEX IF NOT EXISTS idx_boards_community_sort ON boards(community_id, sort_order, name);
CREATE INDEX IF NOT EXISTS idx_threads_community_board ON threads(community_id, board_id, updated_at);
CREATE INDEX IF NOT EXISTS idx_thread_participants_thread ON thread_participants(community_id, thread_id, added_at);
CREATE INDEX IF NOT EXISTS idx_thread_participants_character ON thread_participants(community_id, character_id, thread_id);
CREATE INDEX IF NOT EXISTS idx_posts_community_thread ON posts(community_id, thread_id, created_at);
CREATE INDEX IF NOT EXISTS idx_post_revisions_post ON post_revisions(community_id, post_id, created_at);
CREATE INDEX IF NOT EXISTS idx_memberships_user ON community_memberships(user_id, community_id);
CREATE INDEX IF NOT EXISTS idx_characters_membership ON characters(community_id, membership_id, name);
CREATE INDEX IF NOT EXISTS idx_thread_reads_membership ON thread_reads(community_id, membership_id, thread_id);
CREATE INDEX IF NOT EXISTS idx_thread_watches_membership ON thread_watches(community_id, membership_id, thread_id);
CREATE INDEX IF NOT EXISTS idx_notifications_membership ON notifications(community_id, membership_id, read_at, created_at);
"""


def connect(path: str | Path = ":memory:", *, check_same_thread: bool = True) -> sqlite3.Connection:
    connection = sqlite3.connect(path, check_same_thread=check_same_thread)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(SCHEMA)
    _migrate_schema(connection)
    connection.commit()


def _migrate_schema(connection: sqlite3.Connection) -> None:
    columns = {row["name"] for row in connection.execute("PRAGMA table_info(threads)").fetchall()}
    for name, definition in {
        "status": "TEXT NOT NULL DEFAULT 'active'",
        "location": "TEXT NOT NULL DEFAULT ''",
        "timeline": "TEXT NOT NULL DEFAULT ''",
        "summary": "TEXT NOT NULL DEFAULT ''",
        "posting_mode": "TEXT NOT NULL DEFAULT 'freeform'",
    }.items():
        if name not in columns:
            connection.execute(f"ALTER TABLE threads ADD COLUMN {name} {definition}")
    connection.execute(
        """
        INSERT OR IGNORE INTO thread_participants (
            community_id, thread_id, character_id, added_at
        )
        SELECT community_id, id, author_character_id, created_at
        FROM threads
        """
    )
    connection.execute(
        """
        INSERT OR IGNORE INTO thread_participants (
            community_id, thread_id, character_id, added_at
        )
        SELECT community_id, thread_id, author_character_id, MIN(created_at)
        FROM posts
        GROUP BY community_id, thread_id, author_character_id
        """
    )
