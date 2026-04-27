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
    identity_accent_facet_group_id INTEGER REFERENCES facet_groups(id) ON DELETE SET NULL,
    enabled_post_profile_variants TEXT NOT NULL DEFAULT '',
    enabled_post_accent_styles TEXT NOT NULL DEFAULT '',
    enabled_post_border_styles TEXT NOT NULL DEFAULT '',
    enabled_post_title_styles TEXT NOT NULL DEFAULT '',
    enabled_post_densities TEXT NOT NULL DEFAULT '',
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
    poster_url TEXT,
    poster_alt TEXT NOT NULL DEFAULT '',
    tagline TEXT NOT NULL DEFAULT '',
    accent_color TEXT NOT NULL DEFAULT '',
    summary TEXT NOT NULL DEFAULT '',
    post_profile_variant TEXT NOT NULL DEFAULT 'bio',
    post_accent_style TEXT NOT NULL DEFAULT 'soft',
    post_border_style TEXT NOT NULL DEFAULT 'hairline',
    post_title_style TEXT NOT NULL DEFAULT 'standard',
    post_density TEXT NOT NULL DEFAULT 'calm',
    application_status TEXT NOT NULL DEFAULT 'accepted',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (community_id, slug)
);

CREATE TABLE IF NOT EXISTS boards (
    id INTEGER PRIMARY KEY,
    community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    parent_board_id INTEGER REFERENCES boards(id) ON DELETE SET NULL,
    slug TEXT NOT NULL,
    name TEXT NOT NULL,
    board_kind TEXT NOT NULL DEFAULT 'location',
    tagline TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    image_url TEXT,
    image_alt TEXT NOT NULL DEFAULT '',
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_private INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (community_id, slug)
);

CREATE TABLE IF NOT EXISTS facet_groups (
    id INTEGER PRIMARY KEY,
    community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    slug TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    selection_mode TEXT NOT NULL DEFAULT 'multiple',
    visibility TEXT NOT NULL DEFAULT 'public',
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (community_id, slug)
);

CREATE TABLE IF NOT EXISTS facets (
    id INTEGER PRIMARY KEY,
    community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    facet_group_id INTEGER NOT NULL REFERENCES facet_groups(id) ON DELETE CASCADE,
    slug TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    accent_color TEXT NOT NULL DEFAULT '',
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (community_id, slug),
    UNIQUE (community_id, facet_group_id, slug)
);

CREATE TABLE IF NOT EXISTS character_facets (
    id INTEGER PRIMARY KEY,
    community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    facet_id INTEGER NOT NULL REFERENCES facets(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL,
    UNIQUE (community_id, character_id, facet_id)
);

CREATE TABLE IF NOT EXISTS board_facets (
    id INTEGER PRIMARY KEY,
    community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    board_id INTEGER NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
    facet_id INTEGER NOT NULL REFERENCES facets(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL,
    UNIQUE (community_id, board_id, facet_id)
);

CREATE TABLE IF NOT EXISTS materials (
    id INTEGER PRIMARY KEY,
    community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    slug TEXT NOT NULL,
    title TEXT NOT NULL,
    material_type TEXT NOT NULL DEFAULT 'guide',
    summary TEXT NOT NULL DEFAULT '',
    body TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'published',
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_featured INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (community_id, slug)
);

CREATE TABLE IF NOT EXISTS material_facets (
    id INTEGER PRIMARY KEY,
    community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    material_id INTEGER NOT NULL REFERENCES materials(id) ON DELETE CASCADE,
    facet_id INTEGER NOT NULL REFERENCES facets(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL,
    UNIQUE (community_id, material_id, facet_id)
);

CREATE TABLE IF NOT EXISTS wanted_ads (
    id INTEGER PRIMARY KEY,
    community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    creator_membership_id INTEGER NOT NULL REFERENCES community_memberships(id),
    creator_character_id INTEGER REFERENCES characters(id) ON DELETE SET NULL,
    related_material_id INTEGER REFERENCES materials(id) ON DELETE SET NULL,
    slug TEXT NOT NULL,
    title TEXT NOT NULL,
    wanted_type TEXT NOT NULL DEFAULT 'plot_role',
    summary TEXT NOT NULL DEFAULT '',
    body TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'open',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (community_id, slug)
);

CREATE TABLE IF NOT EXISTS wanted_ad_facets (
    id INTEGER PRIMARY KEY,
    community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    wanted_ad_id INTEGER NOT NULL REFERENCES wanted_ads(id) ON DELETE CASCADE,
    facet_id INTEGER NOT NULL REFERENCES facets(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL,
    UNIQUE (community_id, wanted_ad_id, facet_id)
);

CREATE TABLE IF NOT EXISTS wanted_ad_related_characters (
    id INTEGER PRIMARY KEY,
    community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    wanted_ad_id INTEGER NOT NULL REFERENCES wanted_ads(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL,
    UNIQUE (community_id, wanted_ad_id, character_id)
);

CREATE TABLE IF NOT EXISTS character_plot_hooks (
    id INTEGER PRIMARY KEY,
    community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    author_membership_id INTEGER NOT NULL REFERENCES community_memberships(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    related_material_id INTEGER REFERENCES materials(id) ON DELETE SET NULL,
    slug TEXT NOT NULL,
    title TEXT NOT NULL,
    hook_type TEXT NOT NULL DEFAULT 'scene',
    summary TEXT NOT NULL DEFAULT '',
    body TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'open',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (community_id, character_id, slug)
);

CREATE TABLE IF NOT EXISTS character_plot_hook_facets (
    id INTEGER PRIMARY KEY,
    community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    plot_hook_id INTEGER NOT NULL REFERENCES character_plot_hooks(id) ON DELETE CASCADE,
    facet_id INTEGER NOT NULL REFERENCES facets(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL,
    UNIQUE (community_id, plot_hook_id, facet_id)
);

CREATE TABLE IF NOT EXISTS character_plot_hook_interests (
    id INTEGER PRIMARY KEY,
    community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    plot_hook_id INTEGER NOT NULL REFERENCES character_plot_hooks(id) ON DELETE CASCADE,
    membership_id INTEGER NOT NULL REFERENCES community_memberships(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    note TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'interested',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (community_id, plot_hook_id, membership_id, character_id)
);

CREATE TABLE IF NOT EXISTS wanted_ad_interests (
    id INTEGER PRIMARY KEY,
    community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    wanted_ad_id INTEGER NOT NULL REFERENCES wanted_ads(id) ON DELETE CASCADE,
    membership_id INTEGER NOT NULL REFERENCES community_memberships(id) ON DELETE CASCADE,
    character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
    prospective_character_name TEXT NOT NULL DEFAULT '',
    note TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'interested',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS plotting_rooms (
    id INTEGER PRIMARY KEY,
    community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    owner_membership_id INTEGER NOT NULL REFERENCES community_memberships(id) ON DELETE CASCADE,
    source_plot_hook_id INTEGER REFERENCES character_plot_hooks(id) ON DELETE SET NULL,
    source_plot_hook_interest_id INTEGER REFERENCES character_plot_hook_interests(id) ON DELETE SET NULL,
    source_wanted_ad_id INTEGER REFERENCES wanted_ads(id) ON DELETE SET NULL,
    source_wanted_ad_interest_id INTEGER REFERENCES wanted_ad_interests(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'brainstorming',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (community_id, source_plot_hook_interest_id),
    UNIQUE (community_id, source_wanted_ad_interest_id)
);

CREATE TABLE IF NOT EXISTS plotting_room_participants (
    id INTEGER PRIMARY KEY,
    community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    plotting_room_id INTEGER NOT NULL REFERENCES plotting_rooms(id) ON DELETE CASCADE,
    membership_id INTEGER NOT NULL REFERENCES community_memberships(id) ON DELETE CASCADE,
    character_id INTEGER REFERENCES characters(id) ON DELETE SET NULL,
    prospective_character_name TEXT NOT NULL DEFAULT '',
    participant_role TEXT NOT NULL DEFAULT 'participant',
    created_at TEXT NOT NULL,
    UNIQUE (community_id, plotting_room_id, membership_id, character_id)
);

CREATE TABLE IF NOT EXISTS character_reserves (
    id INTEGER PRIMARY KEY,
    community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    membership_id INTEGER NOT NULL REFERENCES community_memberships(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    wanted_ad_id INTEGER REFERENCES wanted_ads(id) ON DELETE SET NULL,
    wanted_ad_interest_id INTEGER REFERENCES wanted_ad_interests(id) ON DELETE SET NULL,
    reserve_type TEXT NOT NULL DEFAULT 'wanted',
    title TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (community_id, wanted_ad_interest_id)
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

CREATE TABLE IF NOT EXISTS thread_facets (
    id INTEGER PRIMARY KEY,
    community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    thread_id INTEGER NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
    facet_id INTEGER NOT NULL REFERENCES facets(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL,
    UNIQUE (community_id, thread_id, facet_id)
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
    thread_id INTEGER REFERENCES threads(id) ON DELETE CASCADE,
    post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
    wanted_ad_id INTEGER REFERENCES wanted_ads(id) ON DELETE CASCADE,
    wanted_ad_interest_id INTEGER REFERENCES wanted_ad_interests(id) ON DELETE CASCADE,
    character_plot_hook_id INTEGER REFERENCES character_plot_hooks(id) ON DELETE CASCADE,
    plotting_room_id INTEGER REFERENCES plotting_rooms(id) ON DELETE CASCADE,
    character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
    actor_membership_id INTEGER NOT NULL REFERENCES community_memberships(id),
    actor_character_id INTEGER REFERENCES characters(id),
    read_at TEXT,
    created_at TEXT NOT NULL,
    UNIQUE (community_id, membership_id, kind, post_id),
    UNIQUE (community_id, membership_id, kind, wanted_ad_interest_id),
    UNIQUE (community_id, membership_id, kind, character_plot_hook_id),
    UNIQUE (community_id, membership_id, kind, plotting_room_id)
);

CREATE INDEX IF NOT EXISTS idx_boards_community_sort ON boards(community_id, sort_order, name);
CREATE INDEX IF NOT EXISTS idx_threads_community_board ON threads(community_id, board_id, updated_at);
CREATE INDEX IF NOT EXISTS idx_thread_participants_thread ON thread_participants(community_id, thread_id, added_at);
CREATE INDEX IF NOT EXISTS idx_thread_participants_character ON thread_participants(community_id, character_id, thread_id);
CREATE INDEX IF NOT EXISTS idx_posts_community_thread ON posts(community_id, thread_id, created_at);
CREATE INDEX IF NOT EXISTS idx_post_revisions_post ON post_revisions(community_id, post_id, created_at);
CREATE INDEX IF NOT EXISTS idx_memberships_user ON community_memberships(user_id, community_id);
CREATE INDEX IF NOT EXISTS idx_characters_membership ON characters(community_id, membership_id, name);
CREATE INDEX IF NOT EXISTS idx_facet_groups_community_sort ON facet_groups(community_id, sort_order, name);
CREATE INDEX IF NOT EXISTS idx_facets_group_sort ON facets(community_id, facet_group_id, sort_order, name);
CREATE INDEX IF NOT EXISTS idx_character_facets_character ON character_facets(community_id, character_id, facet_id);
CREATE INDEX IF NOT EXISTS idx_character_facets_facet ON character_facets(community_id, facet_id, character_id);
CREATE INDEX IF NOT EXISTS idx_board_facets_board ON board_facets(community_id, board_id, facet_id);
CREATE INDEX IF NOT EXISTS idx_materials_community_sort ON materials(community_id, status, sort_order, title);
CREATE INDEX IF NOT EXISTS idx_material_facets_material ON material_facets(community_id, material_id, facet_id);
CREATE INDEX IF NOT EXISTS idx_material_facets_facet ON material_facets(community_id, facet_id, material_id);
CREATE INDEX IF NOT EXISTS idx_wanted_ads_community_status ON wanted_ads(community_id, status, updated_at);
CREATE INDEX IF NOT EXISTS idx_wanted_ads_creator ON wanted_ads(community_id, creator_character_id, status);
CREATE INDEX IF NOT EXISTS idx_wanted_ad_facets_ad ON wanted_ad_facets(community_id, wanted_ad_id, facet_id);
CREATE INDEX IF NOT EXISTS idx_wanted_ad_related_characters_character ON wanted_ad_related_characters(community_id, character_id, wanted_ad_id);
CREATE INDEX IF NOT EXISTS idx_wanted_ad_interests_ad ON wanted_ad_interests(community_id, wanted_ad_id, status);
CREATE INDEX IF NOT EXISTS idx_wanted_ad_interests_character ON wanted_ad_interests(community_id, character_id, status);
CREATE UNIQUE INDEX IF NOT EXISTS idx_wanted_ad_interests_unique_character
ON wanted_ad_interests(community_id, wanted_ad_id, character_id)
WHERE character_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_wanted_ad_interests_unique_prospective
ON wanted_ad_interests(community_id, wanted_ad_id, membership_id)
WHERE character_id IS NULL;
CREATE INDEX IF NOT EXISTS idx_character_plot_hooks_community_status ON character_plot_hooks(community_id, status, updated_at);
CREATE INDEX IF NOT EXISTS idx_character_plot_hooks_character ON character_plot_hooks(community_id, character_id, status);
CREATE INDEX IF NOT EXISTS idx_character_plot_hook_facets_hook ON character_plot_hook_facets(community_id, plot_hook_id, facet_id);
CREATE INDEX IF NOT EXISTS idx_character_plot_hook_facets_facet ON character_plot_hook_facets(community_id, facet_id, plot_hook_id);
CREATE INDEX IF NOT EXISTS idx_character_plot_hook_interests_hook ON character_plot_hook_interests(community_id, plot_hook_id, status);
CREATE INDEX IF NOT EXISTS idx_character_plot_hook_interests_character ON character_plot_hook_interests(community_id, character_id, status);
CREATE INDEX IF NOT EXISTS idx_plotting_rooms_owner ON plotting_rooms(community_id, owner_membership_id, status, updated_at);
CREATE INDEX IF NOT EXISTS idx_plotting_room_participants_membership ON plotting_room_participants(community_id, membership_id, plotting_room_id);
CREATE INDEX IF NOT EXISTS idx_character_reserves_character ON character_reserves(community_id, character_id, status);
CREATE INDEX IF NOT EXISTS idx_character_reserves_wanted ON character_reserves(community_id, wanted_ad_id, status);
CREATE INDEX IF NOT EXISTS idx_thread_facets_thread ON thread_facets(community_id, thread_id, facet_id);
CREATE INDEX IF NOT EXISTS idx_thread_facets_facet ON thread_facets(community_id, facet_id, thread_id);
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
    community_columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(communities)").fetchall()
    }
    if "identity_accent_facet_group_id" not in community_columns:
        connection.execute(
            "ALTER TABLE communities ADD COLUMN identity_accent_facet_group_id INTEGER"
        )
    for name in {
        "enabled_post_profile_variants",
        "enabled_post_accent_styles",
        "enabled_post_border_styles",
        "enabled_post_title_styles",
        "enabled_post_densities",
    }:
        if name not in community_columns:
            connection.execute(
                f"ALTER TABLE communities ADD COLUMN {name} TEXT NOT NULL DEFAULT ''"
            )

    board_columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(boards)").fetchall()
    }
    for name, definition in {
        "parent_board_id": "INTEGER REFERENCES boards(id) ON DELETE SET NULL",
        "board_kind": "TEXT NOT NULL DEFAULT 'location'",
        "tagline": "TEXT NOT NULL DEFAULT ''",
        "image_url": "TEXT",
        "image_alt": "TEXT NOT NULL DEFAULT ''",
    }.items():
        if name not in board_columns:
            connection.execute(f"ALTER TABLE boards ADD COLUMN {name} {definition}")
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_boards_parent_sort
        ON boards(community_id, parent_board_id, sort_order, name)
        """
    )

    character_columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(characters)").fetchall()
    }
    if "application_status" not in character_columns:
        connection.execute(
            "ALTER TABLE characters ADD COLUMN application_status TEXT NOT NULL DEFAULT 'accepted'"
        )
    for name, definition in {
        "poster_url": "TEXT",
        "poster_alt": "TEXT NOT NULL DEFAULT ''",
        "tagline": "TEXT NOT NULL DEFAULT ''",
        "accent_color": "TEXT NOT NULL DEFAULT ''",
        "post_profile_variant": "TEXT NOT NULL DEFAULT 'bio'",
        "post_accent_style": "TEXT NOT NULL DEFAULT 'soft'",
        "post_border_style": "TEXT NOT NULL DEFAULT 'hairline'",
        "post_title_style": "TEXT NOT NULL DEFAULT 'standard'",
        "post_density": "TEXT NOT NULL DEFAULT 'calm'",
    }.items():
        if name not in character_columns:
            connection.execute(f"ALTER TABLE characters ADD COLUMN {name} {definition}")
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_characters_application_status
        ON characters(community_id, application_status, updated_at)
        """
    )
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
    _migrate_wanted_ad_interests_schema(connection)
    _migrate_notifications_schema(connection)


def _migrate_wanted_ad_interests_schema(connection: sqlite3.Connection) -> None:
    columns = {
        row["name"]: row
        for row in connection.execute("PRAGMA table_info(wanted_ad_interests)").fetchall()
    }
    if "prospective_character_name" in columns and not columns["character_id"]["notnull"]:
        _ensure_wanted_ad_interest_indexes(connection)
        return

    connection.execute("PRAGMA foreign_keys = OFF")
    if "prospective_character_name" not in columns:
        connection.execute(
            """
            ALTER TABLE wanted_ad_interests
            ADD COLUMN prospective_character_name TEXT NOT NULL DEFAULT ''
            """
        )
    connection.execute(
        """
        CREATE TABLE wanted_ad_interests_new (
            id INTEGER PRIMARY KEY,
            community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
            wanted_ad_id INTEGER NOT NULL REFERENCES wanted_ads(id) ON DELETE CASCADE,
            membership_id INTEGER NOT NULL REFERENCES community_memberships(id) ON DELETE CASCADE,
            character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
            prospective_character_name TEXT NOT NULL DEFAULT '',
            note TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'interested',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        INSERT INTO wanted_ad_interests_new (
            id,
            community_id,
            wanted_ad_id,
            membership_id,
            character_id,
            prospective_character_name,
            note,
            status,
            created_at,
            updated_at
        )
        SELECT
            id,
            community_id,
            wanted_ad_id,
            membership_id,
            character_id,
            prospective_character_name,
            note,
            status,
            created_at,
            updated_at
        FROM wanted_ad_interests
        """
    )
    connection.execute("DROP TABLE wanted_ad_interests")
    connection.execute("ALTER TABLE wanted_ad_interests_new RENAME TO wanted_ad_interests")
    _ensure_wanted_ad_interest_indexes(connection)
    connection.execute("PRAGMA foreign_keys = ON")


def _ensure_wanted_ad_interest_indexes(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_wanted_ad_interests_ad
        ON wanted_ad_interests(community_id, wanted_ad_id, status)
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_wanted_ad_interests_character
        ON wanted_ad_interests(community_id, character_id, status)
        """
    )
    connection.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_wanted_ad_interests_unique_character
        ON wanted_ad_interests(community_id, wanted_ad_id, character_id)
        WHERE character_id IS NOT NULL
        """
    )
    connection.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_wanted_ad_interests_unique_prospective
        ON wanted_ad_interests(community_id, wanted_ad_id, membership_id)
        WHERE character_id IS NULL
        """
    )


def _migrate_notifications_schema(connection: sqlite3.Connection) -> None:
    columns = {
        row["name"]: row
        for row in connection.execute("PRAGMA table_info(notifications)").fetchall()
    }
    if (
        "wanted_ad_id" in columns
        and "wanted_ad_interest_id" in columns
        and "character_plot_hook_id" in columns
        and "plotting_room_id" in columns
        and "character_id" in columns
        and not columns["actor_character_id"]["notnull"]
        and not columns["thread_id"]["notnull"]
        and not columns["post_id"]["notnull"]
    ):
        return

    connection.execute("PRAGMA foreign_keys = OFF")
    for name in (
        "wanted_ad_id",
        "wanted_ad_interest_id",
        "character_plot_hook_id",
        "plotting_room_id",
        "character_id",
    ):
        if name not in columns:
            connection.execute(f"ALTER TABLE notifications ADD COLUMN {name} INTEGER")
    connection.execute(
        """
        CREATE TABLE notifications_new (
            id INTEGER PRIMARY KEY,
            community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
            membership_id INTEGER NOT NULL REFERENCES community_memberships(id) ON DELETE CASCADE,
            kind TEXT NOT NULL,
            thread_id INTEGER REFERENCES threads(id) ON DELETE CASCADE,
            post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
            wanted_ad_id INTEGER REFERENCES wanted_ads(id) ON DELETE CASCADE,
            wanted_ad_interest_id INTEGER REFERENCES wanted_ad_interests(id) ON DELETE CASCADE,
            character_plot_hook_id INTEGER REFERENCES character_plot_hooks(id) ON DELETE CASCADE,
            plotting_room_id INTEGER REFERENCES plotting_rooms(id) ON DELETE CASCADE,
            character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
            actor_membership_id INTEGER NOT NULL REFERENCES community_memberships(id),
            actor_character_id INTEGER REFERENCES characters(id),
            read_at TEXT,
            created_at TEXT NOT NULL,
            UNIQUE (community_id, membership_id, kind, post_id),
            UNIQUE (community_id, membership_id, kind, wanted_ad_interest_id),
            UNIQUE (community_id, membership_id, kind, character_plot_hook_id),
            UNIQUE (community_id, membership_id, kind, plotting_room_id)
        )
        """
    )
    notification_insert = """
    INSERT INTO notifications_new (
        id,
        community_id,
        membership_id,
        kind,
        thread_id,
        post_id,
        wanted_ad_id,
        wanted_ad_interest_id,
        character_plot_hook_id,
        plotting_room_id,
        character_id,
        actor_membership_id,
        actor_character_id,
        read_at,
        created_at
    )
    """
    connection.execute(
        notification_insert
        + """
        SELECT
            id,
            community_id,
            membership_id,
            kind,
            thread_id,
            post_id,
            wanted_ad_id,
            wanted_ad_interest_id,
            character_plot_hook_id,
            plotting_room_id,
            character_id,
            actor_membership_id,
            actor_character_id,
            read_at,
            created_at
        FROM notifications
        """
    )
    connection.execute("DROP TABLE notifications")
    connection.execute("ALTER TABLE notifications_new RENAME TO notifications")
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_notifications_membership
        ON notifications(community_id, membership_id, read_at, created_at)
        """
    )
    connection.execute("PRAGMA foreign_keys = ON")
