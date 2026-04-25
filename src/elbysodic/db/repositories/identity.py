"""Community, user, role, and membership repository methods."""

from __future__ import annotations

from elbysodic.db.repositories.base import RepositoryBase, _last_id, _utc_now
from elbysodic.db.repositories.rows import (
    _community_from_row,
    _membership_from_row,
    _role_from_row,
    _user_from_row,
)
from elbysodic.domain.context import DEFAULT_COMMUNITY_ID, DEFAULT_COMMUNITY_SLUG
from elbysodic.domain.models import Community, CommunityMembership, Role, User


class IdentityRepositoryMixin(RepositoryBase):
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

    def get_membership_by_username(self, community_id: int, username: str) -> CommunityMembership:
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
            WHERE community_id = ? AND username = ?
            """,
            (community_id, username),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"membership not found in community {community_id} for username {username}"
            )
        return _membership_from_row(row)

    def list_memberships(self, community_id: int) -> list[CommunityMembership]:
        rows = self.connection.execute(
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
            WHERE community_id = ?
            ORDER BY display_name, username, id
            """,
            (community_id,),
        ).fetchall()
        return [_membership_from_row(row) for row in rows]

    def search_memberships(
        self,
        community_id: int,
        query: str,
        *,
        limit: int = 8,
    ) -> list[CommunityMembership]:
        normalized = query.strip().lower().lstrip("@")
        if not normalized:
            return []
        like = f"%{normalized}%"
        prefix = f"{normalized}%"
        rows = self.connection.execute(
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
            WHERE community_id = ?
              AND is_active = 1
              AND (
                lower(username) LIKE ?
                OR lower(display_name) LIKE ?
              )
            ORDER BY
                CASE
                  WHEN lower(username) = ? THEN 0
                  WHEN lower(username) LIKE ? THEN 1
                  WHEN lower(display_name) LIKE ? THEN 2
                  ELSE 3
                END,
                display_name,
                username,
                id
            LIMIT ?
            """,
            (community_id, like, like, normalized, prefix, prefix, limit),
        ).fetchall()
        return [_membership_from_row(row) for row in rows]
