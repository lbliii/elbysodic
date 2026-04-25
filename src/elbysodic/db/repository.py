"""Tenant-aware SQLite repository for forum-domain operations."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

from elbysodic.domain.context import DEFAULT_COMMUNITY_ID, DEFAULT_COMMUNITY_SLUG
from elbysodic.domain.models import (
    Board,
    Character,
    Community,
    CommunityMembership,
    Post,
    Role,
    Thread,
    User,
)


class TenantBoundaryError(ValueError):
    """Raised when a write attempts to join rows from different communities."""


class ForumRepository:
    """Small repository layer that keeps community scope explicit."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def seed_default_community(self, name: str = "Elbysodic") -> Community:
        now = _utc_now()
        self.connection.execute(
            """
            INSERT OR IGNORE INTO communities (id, name, slug, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (DEFAULT_COMMUNITY_ID, name, DEFAULT_COMMUNITY_SLUG, now, now),
        )
        self.connection.commit()
        return self.get_community(DEFAULT_COMMUNITY_ID)

    def create_community(self, slug: str, name: str, host: str | None = None) -> Community:
        now = _utc_now()
        cursor = self.connection.execute(
            """
            INSERT INTO communities (name, slug, host, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, slug, host, now, now),
        )
        self.connection.commit()
        return self.get_community(_last_id(cursor))

    def get_community(self, community_id: int) -> Community:
        row = self.connection.execute(
            """
            SELECT id, name, slug, host, default_theme_id, created_at, updated_at
            FROM communities
            WHERE id = ?
            """,
            (community_id,),
        ).fetchone()
        if row is None:
            raise LookupError(f"community not found: {community_id}")
        return _community_from_row(row)

    def create_user(self, email: str, password_hash: str) -> User:
        cursor = self.connection.execute(
            """
            INSERT INTO users (email, password_hash, created_at)
            VALUES (?, ?, ?)
            """,
            (email, password_hash, _utc_now()),
        )
        self.connection.commit()
        return self.get_user(_last_id(cursor))

    def get_user(self, user_id: int) -> User:
        row = self.connection.execute(
            """
            SELECT id, email, password_hash, created_at
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()
        if row is None:
            raise LookupError(f"user not found: {user_id}")
        return _user_from_row(row)

    def get_user_by_email(self, email: str) -> User:
        row = self.connection.execute(
            """
            SELECT id, email, password_hash, created_at
            FROM users
            WHERE email = ?
            """,
            (email,),
        ).fetchone()
        if row is None:
            raise LookupError(f"user not found: {email}")
        return _user_from_row(row)

    def create_role(
        self,
        community_id: int,
        slug: str,
        name: str,
        *,
        is_admin: bool = False,
    ) -> Role:
        now = _utc_now()
        cursor = self.connection.execute(
            """
            INSERT INTO roles (community_id, slug, name, is_admin, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (community_id, slug, name, int(is_admin), now, now),
        )
        self.connection.commit()
        return self.get_role(community_id, _last_id(cursor))

    def get_role(self, community_id: int, role_id: int) -> Role:
        row = self.connection.execute(
            """
            SELECT id, community_id, slug, name, is_admin, created_at, updated_at
            FROM roles
            WHERE community_id = ? AND id = ?
            """,
            (community_id, role_id),
        ).fetchone()
        if row is None:
            raise LookupError(f"role not found in community {community_id}: {role_id}")
        return _role_from_row(row)

    def get_role_by_slug(self, community_id: int, slug: str) -> Role:
        row = self.connection.execute(
            """
            SELECT id, community_id, slug, name, is_admin, created_at, updated_at
            FROM roles
            WHERE community_id = ? AND slug = ?
            """,
            (community_id, slug),
        ).fetchone()
        if row is None:
            raise LookupError(f"role not found in community {community_id}: {slug}")
        return _role_from_row(row)

    def create_membership(
        self,
        community_id: int,
        user_id: int,
        role_id: int,
        username: str,
        display_name: str,
        avatar_url: str | None = None,
    ) -> CommunityMembership:
        self.get_role(community_id, role_id)
        cursor = self.connection.execute(
            """
            INSERT INTO community_memberships (
                community_id, user_id, username, display_name, avatar_url, role_id, joined_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (community_id, user_id, username, display_name, avatar_url, role_id, _utc_now()),
        )
        self.connection.commit()
        return self.get_membership(community_id, _last_id(cursor))

    def get_membership(self, community_id: int, membership_id: int) -> CommunityMembership:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                user_id,
                username,
                display_name,
                avatar_url,
                role_id,
                default_character_id,
                post_count,
                is_active,
                joined_at
            FROM community_memberships
            WHERE community_id = ? AND id = ?
            """,
            (community_id, membership_id),
        ).fetchone()
        if row is None:
            raise LookupError(f"membership not found in community {community_id}: {membership_id}")
        return _membership_from_row(row)

    def get_membership_for_user(self, community_id: int, user_id: int) -> CommunityMembership:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                user_id,
                username,
                display_name,
                avatar_url,
                role_id,
                default_character_id,
                post_count,
                is_active,
                joined_at
            FROM community_memberships
            WHERE community_id = ? AND user_id = ?
            """,
            (community_id, user_id),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"membership not found in community {community_id} for user {user_id}"
            )
        return _membership_from_row(row)

    def create_character(
        self,
        community_id: int,
        membership_id: int,
        slug: str,
        name: str,
        avatar_url: str | None = None,
        summary: str = "",
        *,
        make_default: bool = False,
    ) -> Character:
        self.get_membership(community_id, membership_id)
        now = _utc_now()
        cursor = self.connection.execute(
            """
            INSERT INTO characters (
                community_id, membership_id, slug, name, avatar_url, summary, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (community_id, membership_id, slug, name, avatar_url, summary, now, now),
        )
        character = self.get_character(community_id, _last_id(cursor))
        if make_default:
            self.set_default_character(community_id, membership_id, character.id)
            character = self.get_character(community_id, character.id)
        self.connection.commit()
        return character

    def get_character(self, community_id: int, character_id: int) -> Character:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                membership_id,
                name,
                slug,
                avatar_url,
                summary,
                created_at,
                updated_at
            FROM characters
            WHERE community_id = ? AND id = ?
            """,
            (community_id, character_id),
        ).fetchone()
        if row is None:
            raise LookupError(f"character not found in community {community_id}: {character_id}")
        return _character_from_row(row)

    def get_character_by_slug(self, community_id: int, slug: str) -> Character:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                membership_id,
                name,
                slug,
                avatar_url,
                summary,
                created_at,
                updated_at
            FROM characters
            WHERE community_id = ? AND slug = ?
            """,
            (community_id, slug),
        ).fetchone()
        if row is None:
            raise LookupError(f"character not found in community {community_id}: {slug}")
        return _character_from_row(row)

    def list_characters(self, community_id: int, membership_id: int) -> list[Character]:
        self.get_membership(community_id, membership_id)
        rows = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                membership_id,
                name,
                slug,
                avatar_url,
                summary,
                created_at,
                updated_at
            FROM characters
            WHERE community_id = ? AND membership_id = ?
            ORDER BY name, id
            """,
            (community_id, membership_id),
        ).fetchall()
        return [_character_from_row(row) for row in rows]

    def set_default_character(
        self,
        community_id: int,
        membership_id: int,
        character_id: int,
    ) -> CommunityMembership:
        character = self.get_character(community_id, character_id)
        if character.membership_id != membership_id:
            raise LookupError(
                f"character {character_id} does not belong to membership {membership_id}"
            )
        self.connection.execute(
            """
            UPDATE community_memberships
            SET default_character_id = ?
            WHERE community_id = ? AND id = ?
            """,
            (character_id, community_id, membership_id),
        )
        self.connection.commit()
        return self.get_membership(community_id, membership_id)

    def create_board(
        self,
        community_id: int,
        slug: str,
        name: str,
        description: str = "",
        *,
        sort_order: int = 0,
        is_private: bool = False,
    ) -> Board:
        now = _utc_now()
        cursor = self.connection.execute(
            """
            INSERT INTO boards (
                community_id, slug, name, description, sort_order, is_private, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (community_id, slug, name, description, sort_order, int(is_private), now, now),
        )
        self.connection.commit()
        return self.get_board(community_id, _last_id(cursor))

    def get_board(self, community_id: int, board_id: int) -> Board:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                slug,
                name,
                description,
                sort_order,
                is_private,
                created_at,
                updated_at
            FROM boards
            WHERE community_id = ? AND id = ?
            """,
            (community_id, board_id),
        ).fetchone()
        if row is None:
            raise LookupError(f"board not found in community {community_id}: {board_id}")
        return _board_from_row(row)

    def get_board_by_slug(self, community_id: int, slug: str) -> Board:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                slug,
                name,
                description,
                sort_order,
                is_private,
                created_at,
                updated_at
            FROM boards
            WHERE community_id = ? AND slug = ?
            """,
            (community_id, slug),
        ).fetchone()
        if row is None:
            raise LookupError(f"board not found in community {community_id}: {slug}")
        return _board_from_row(row)

    def list_boards(self, community_id: int) -> list[Board]:
        rows = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                slug,
                name,
                description,
                sort_order,
                is_private,
                created_at,
                updated_at
            FROM boards
            WHERE community_id = ?
            ORDER BY sort_order, name
            """,
            (community_id,),
        ).fetchall()
        return [_board_from_row(row) for row in rows]

    def create_thread(
        self,
        community_id: int,
        board_id: int,
        author_character_id: int,
        slug: str,
        title: str,
        *,
        is_locked: bool = False,
        is_pinned: bool = False,
    ) -> Thread:
        self.get_board(community_id, board_id)
        character = self.get_character(community_id, author_character_id)
        now = _utc_now()
        cursor = self.connection.execute(
            """
            INSERT INTO threads (
                community_id,
                board_id,
                author_membership_id,
                author_character_id,
                slug,
                title,
                is_locked,
                is_pinned,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                community_id,
                board_id,
                character.membership_id,
                author_character_id,
                slug,
                title,
                int(is_locked),
                int(is_pinned),
                now,
                now,
            ),
        )
        self.connection.commit()
        return self.get_thread(community_id, _last_id(cursor))

    def update_thread_flags(
        self,
        community_id: int,
        thread_id: int,
        *,
        is_locked: bool | None = None,
        is_pinned: bool | None = None,
    ) -> Thread:
        thread = self.get_thread(community_id, thread_id)
        locked = thread.is_locked if is_locked is None else is_locked
        pinned = thread.is_pinned if is_pinned is None else is_pinned
        self.connection.execute(
            """
            UPDATE threads
            SET is_locked = ?, is_pinned = ?
            WHERE community_id = ? AND id = ?
            """,
            (int(locked), int(pinned), community_id, thread_id),
        )
        self.connection.commit()
        return self.get_thread(community_id, thread_id)

    def get_thread(self, community_id: int, thread_id: int) -> Thread:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                board_id,
                author_membership_id,
                author_character_id,
                slug,
                title,
                is_locked,
                is_pinned,
                created_at,
                updated_at
            FROM threads
            WHERE community_id = ? AND id = ?
            """,
            (community_id, thread_id),
        ).fetchone()
        if row is None:
            raise LookupError(f"thread not found in community {community_id}: {thread_id}")
        return _thread_from_row(row)

    def get_thread_by_slug(self, community_id: int, board_id: int, slug: str) -> Thread:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                board_id,
                author_membership_id,
                author_character_id,
                slug,
                title,
                is_locked,
                is_pinned,
                created_at,
                updated_at
            FROM threads
            WHERE community_id = ? AND board_id = ? AND slug = ?
            """,
            (community_id, board_id, slug),
        ).fetchone()
        if row is None:
            raise LookupError(f"thread not found in community {community_id}: {slug}")
        return _thread_from_row(row)

    def list_threads(self, community_id: int, board_id: int | None = None) -> list[Thread]:
        if board_id is None:
            rows = self.connection.execute(
                """
                SELECT
                    id,
                    community_id,
                    board_id,
                    author_membership_id,
                    author_character_id,
                    slug,
                    title,
                    is_locked,
                    is_pinned,
                    created_at,
                    updated_at
                FROM threads
                WHERE community_id = ?
                ORDER BY is_pinned DESC, updated_at DESC, id DESC
                """,
                (community_id,),
            ).fetchall()
        else:
            rows = self.connection.execute(
                """
                SELECT
                    id,
                    community_id,
                    board_id,
                    author_membership_id,
                    author_character_id,
                    slug,
                    title,
                    is_locked,
                    is_pinned,
                    created_at,
                    updated_at
                FROM threads
                WHERE community_id = ? AND board_id = ?
                ORDER BY is_pinned DESC, updated_at DESC, id DESC
                """,
                (community_id, board_id),
            ).fetchall()
        return [_thread_from_row(row) for row in rows]

    def create_post(
        self,
        community_id: int,
        thread_id: int,
        author_character_id: int,
        body: str,
    ) -> Post:
        self.get_thread(community_id, thread_id)
        character = self.get_character(community_id, author_character_id)
        now = _utc_now()
        cursor = self.connection.execute(
            """
            INSERT INTO posts (
                community_id,
                thread_id,
                author_membership_id,
                author_character_id,
                body,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (community_id, thread_id, character.membership_id, author_character_id, body, now, now),
        )
        self.connection.execute(
            """
            UPDATE community_memberships
            SET post_count = post_count + 1
            WHERE community_id = ? AND id = ?
            """,
            (community_id, character.membership_id),
        )
        self.connection.execute(
            """
            UPDATE threads
            SET updated_at = ?
            WHERE community_id = ? AND id = ?
            """,
            (now, community_id, thread_id),
        )
        self.connection.commit()
        return self.get_post(community_id, _last_id(cursor))

    def get_post(self, community_id: int, post_id: int) -> Post:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                thread_id,
                author_membership_id,
                author_character_id,
                body,
                created_at,
                updated_at
            FROM posts
            WHERE community_id = ? AND id = ?
            """,
            (community_id, post_id),
        ).fetchone()
        if row is None:
            raise LookupError(f"post not found in community {community_id}: {post_id}")
        return _post_from_row(row)

    def list_posts(self, community_id: int, thread_id: int) -> list[Post]:
        rows = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                thread_id,
                author_membership_id,
                author_character_id,
                body,
                created_at,
                updated_at
            FROM posts
            WHERE community_id = ? AND thread_id = ?
            ORDER BY created_at, id
            """,
            (community_id, thread_id),
        ).fetchall()
        return [_post_from_row(row) for row in rows]

    def list_posts_by_character(self, community_id: int, character_id: int) -> list[Post]:
        self.get_character(community_id, character_id)
        rows = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                thread_id,
                author_membership_id,
                author_character_id,
                body,
                created_at,
                updated_at
            FROM posts
            WHERE community_id = ? AND author_character_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (community_id, character_id),
        ).fetchall()
        return [_post_from_row(row) for row in rows]

    def list_threads_by_character(self, community_id: int, character_id: int) -> list[Thread]:
        self.get_character(community_id, character_id)
        rows = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                board_id,
                author_membership_id,
                author_character_id,
                slug,
                title,
                is_locked,
                is_pinned,
                created_at,
                updated_at
            FROM threads
            WHERE community_id = ? AND author_character_id = ?
            ORDER BY updated_at DESC, id DESC
            """,
            (community_id, character_id),
        ).fetchall()
        return [_thread_from_row(row) for row in rows]

    def get_thread_read_at(
        self,
        community_id: int,
        thread_id: int,
        membership_id: int,
    ) -> str | None:
        row = self.connection.execute(
            """
            SELECT read_at
            FROM thread_reads
            WHERE community_id = ? AND thread_id = ? AND membership_id = ?
            """,
            (community_id, thread_id, membership_id),
        ).fetchone()
        if row is None:
            return None
        return str(row["read_at"])

    def mark_thread_read(
        self,
        community_id: int,
        thread_id: int,
        membership_id: int,
        *,
        read_at: str | None = None,
    ) -> None:
        self.get_thread(community_id, thread_id)
        self.get_membership(community_id, membership_id)
        stamp = read_at or _utc_now()
        self.connection.execute(
            """
            INSERT INTO thread_reads (community_id, thread_id, membership_id, read_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT (community_id, thread_id, membership_id)
            DO UPDATE SET read_at = excluded.read_at
            """,
            (community_id, thread_id, membership_id, stamp),
        )
        self.connection.commit()


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _last_id(cursor: sqlite3.Cursor) -> int:
    value = cursor.lastrowid
    if value is None:
        raise RuntimeError("insert did not return a row id")
    return value


def _community_from_row(row: sqlite3.Row) -> Community:
    return Community(
        id=row["id"],
        name=row["name"],
        slug=row["slug"],
        host=row["host"],
        default_theme_id=row["default_theme_id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _user_from_row(row: sqlite3.Row) -> User:
    return User(
        id=row["id"],
        email=row["email"],
        password_hash=row["password_hash"],
        created_at=row["created_at"],
    )


def _role_from_row(row: sqlite3.Row) -> Role:
    return Role(
        id=row["id"],
        community_id=row["community_id"],
        slug=row["slug"],
        name=row["name"],
        is_admin=bool(row["is_admin"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _membership_from_row(row: sqlite3.Row) -> CommunityMembership:
    return CommunityMembership(
        id=row["id"],
        community_id=row["community_id"],
        user_id=row["user_id"],
        username=row["username"],
        display_name=row["display_name"],
        avatar_url=row["avatar_url"],
        role_id=row["role_id"],
        default_character_id=row["default_character_id"],
        post_count=row["post_count"],
        is_active=bool(row["is_active"]),
        joined_at=row["joined_at"],
    )


def _board_from_row(row: sqlite3.Row) -> Board:
    return Board(
        id=row["id"],
        community_id=row["community_id"],
        slug=row["slug"],
        name=row["name"],
        description=row["description"],
        sort_order=row["sort_order"],
        is_private=bool(row["is_private"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _character_from_row(row: sqlite3.Row) -> Character:
    return Character(
        id=row["id"],
        community_id=row["community_id"],
        membership_id=row["membership_id"],
        name=row["name"],
        slug=row["slug"],
        avatar_url=row["avatar_url"],
        summary=row["summary"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _thread_from_row(row: sqlite3.Row) -> Thread:
    return Thread(
        id=row["id"],
        community_id=row["community_id"],
        board_id=row["board_id"],
        author_membership_id=row["author_membership_id"],
        author_character_id=row["author_character_id"],
        slug=row["slug"],
        title=row["title"],
        is_locked=bool(row["is_locked"]),
        is_pinned=bool(row["is_pinned"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _post_from_row(row: sqlite3.Row) -> Post:
    return Post(
        id=row["id"],
        community_id=row["community_id"],
        thread_id=row["thread_id"],
        author_membership_id=row["author_membership_id"],
        author_character_id=row["author_character_id"],
        body=row["body"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
