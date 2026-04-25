"""Tenant-aware SQLite repository for forum-domain operations."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta

from elbysodic.domain.context import DEFAULT_COMMUNITY_ID, DEFAULT_COMMUNITY_SLUG
from elbysodic.domain.models import (
    Board,
    Character,
    Community,
    CommunityMembership,
    Facet,
    FacetGroup,
    Material,
    Notification,
    Post,
    PostRevision,
    Role,
    Thread,
    ThreadParticipant,
    ThreadWatch,
    User,
    WantedAd,
    WantedAdInterest,
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

    def update_character(
        self,
        community_id: int,
        character_id: int,
        *,
        slug: str,
        name: str,
        avatar_url: str | None,
        summary: str,
    ) -> Character:
        self.get_character(community_id, character_id)
        self.connection.execute(
            """
            UPDATE characters
            SET slug = ?, name = ?, avatar_url = ?, summary = ?, updated_at = ?
            WHERE community_id = ? AND id = ?
            """,
            (slug, name, avatar_url, summary, _utc_now(), community_id, character_id),
        )
        self.connection.commit()
        return self.get_character(community_id, character_id)

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

    def list_community_characters(self, community_id: int) -> list[Character]:
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
            WHERE community_id = ?
            ORDER BY name, id
            """,
            (community_id,),
        ).fetchall()
        return [_character_from_row(row) for row in rows]

    def search_characters(
        self,
        community_id: int,
        query: str,
        *,
        limit: int = 8,
        exclude_membership_ids: list[int] | None = None,
    ) -> list[Character]:
        normalized = query.strip().lower().lstrip("@")
        if not normalized:
            return []
        excluded_ids = exclude_membership_ids or []
        like = f"%{normalized}%"
        prefix = f"{normalized}%"
        exclude_clause = ""
        params: list[object] = [community_id, like, like]
        if excluded_ids:
            placeholders = ", ".join("?" for _ in excluded_ids)
            exclude_clause = f"AND characters.membership_id NOT IN ({placeholders})"
            params.extend(excluded_ids)
        params.extend([normalized, prefix, prefix])
        params.append(limit)
        rows = self.connection.execute(
            f"""
            SELECT
                characters.id,
                characters.community_id,
                characters.membership_id,
                characters.name,
                characters.slug,
                characters.avatar_url,
                characters.summary,
                characters.created_at,
                characters.updated_at
            FROM characters
            JOIN community_memberships
              ON community_memberships.community_id = characters.community_id
             AND community_memberships.id = characters.membership_id
            WHERE characters.community_id = ?
              AND community_memberships.is_active = 1
              AND (
                lower(characters.slug) LIKE ?
                OR lower(characters.name) LIKE ?
              )
              {exclude_clause}
            ORDER BY
                CASE
                  WHEN lower(characters.slug) = ? THEN 0
                  WHEN lower(characters.slug) LIKE ? THEN 1
                  WHEN lower(characters.name) LIKE ? THEN 2
                  ELSE 3
                END,
                characters.name,
                characters.id
            LIMIT ?
            """,
            tuple(params),
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

    def create_facet_group(
        self,
        community_id: int,
        slug: str,
        name: str,
        description: str = "",
        *,
        selection_mode: str = "multiple",
        visibility: str = "public",
        sort_order: int = 0,
    ) -> FacetGroup:
        self.get_community(community_id)
        now = _utc_now()
        cursor = self.connection.execute(
            """
            INSERT INTO facet_groups (
                community_id,
                slug,
                name,
                description,
                selection_mode,
                visibility,
                sort_order,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                community_id,
                slug,
                name,
                description,
                selection_mode,
                visibility,
                sort_order,
                now,
                now,
            ),
        )
        self.connection.commit()
        return self.get_facet_group(community_id, _last_id(cursor))

    def get_facet_group(self, community_id: int, facet_group_id: int) -> FacetGroup:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                slug,
                name,
                description,
                selection_mode,
                visibility,
                sort_order,
                created_at,
                updated_at
            FROM facet_groups
            WHERE community_id = ? AND id = ?
            """,
            (community_id, facet_group_id),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"facet group not found in community {community_id}: {facet_group_id}"
            )
        return _facet_group_from_row(row)

    def get_facet_group_by_slug(self, community_id: int, slug: str) -> FacetGroup:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                slug,
                name,
                description,
                selection_mode,
                visibility,
                sort_order,
                created_at,
                updated_at
            FROM facet_groups
            WHERE community_id = ? AND slug = ?
            """,
            (community_id, slug),
        ).fetchone()
        if row is None:
            raise LookupError(f"facet group not found in community {community_id}: {slug}")
        return _facet_group_from_row(row)

    def list_facet_groups(self, community_id: int) -> list[FacetGroup]:
        rows = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                slug,
                name,
                description,
                selection_mode,
                visibility,
                sort_order,
                created_at,
                updated_at
            FROM facet_groups
            WHERE community_id = ?
            ORDER BY sort_order, name, id
            """,
            (community_id,),
        ).fetchall()
        return [_facet_group_from_row(row) for row in rows]

    def create_facet(
        self,
        community_id: int,
        facet_group_id: int,
        slug: str,
        name: str,
        description: str = "",
        *,
        accent_color: str = "",
        sort_order: int = 0,
    ) -> Facet:
        group = self.get_facet_group(community_id, facet_group_id)
        now = _utc_now()
        cursor = self.connection.execute(
            """
            INSERT INTO facets (
                community_id,
                facet_group_id,
                slug,
                name,
                description,
                accent_color,
                sort_order,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                group.community_id,
                group.id,
                slug,
                name,
                description,
                accent_color,
                sort_order,
                now,
                now,
            ),
        )
        self.connection.commit()
        return self.get_facet(community_id, _last_id(cursor))

    def get_facet(self, community_id: int, facet_id: int) -> Facet:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                facet_group_id,
                slug,
                name,
                description,
                accent_color,
                sort_order,
                created_at,
                updated_at
            FROM facets
            WHERE community_id = ? AND id = ?
            """,
            (community_id, facet_id),
        ).fetchone()
        if row is None:
            raise LookupError(f"facet not found in community {community_id}: {facet_id}")
        return _facet_from_row(row)

    def get_facet_by_slug(self, community_id: int, slug: str) -> Facet:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                facet_group_id,
                slug,
                name,
                description,
                accent_color,
                sort_order,
                created_at,
                updated_at
            FROM facets
            WHERE community_id = ? AND slug = ?
            """,
            (community_id, slug),
        ).fetchone()
        if row is None:
            raise LookupError(f"facet not found in community {community_id}: {slug}")
        return _facet_from_row(row)

    def list_facets(self, community_id: int) -> list[Facet]:
        rows = self.connection.execute(
            """
            SELECT
                facets.id,
                facets.community_id,
                facets.facet_group_id,
                facets.slug,
                facets.name,
                facets.description,
                facets.accent_color,
                facets.sort_order,
                facets.created_at,
                facets.updated_at
            FROM facets
            JOIN facet_groups
              ON facet_groups.community_id = facets.community_id
             AND facet_groups.id = facets.facet_group_id
            WHERE facets.community_id = ?
            ORDER BY facet_groups.sort_order, facet_groups.name, facets.sort_order, facets.name
            """,
            (community_id,),
        ).fetchall()
        return [_facet_from_row(row) for row in rows]

    def list_character_facets(self, community_id: int, character_id: int) -> list[Facet]:
        self.get_character(community_id, character_id)
        return self._list_facets_for_assignment(
            "character_facets",
            "character_id",
            community_id,
            character_id,
        )

    def list_board_facets(self, community_id: int, board_id: int) -> list[Facet]:
        self.get_board(community_id, board_id)
        return self._list_facets_for_assignment(
            "board_facets",
            "board_id",
            community_id,
            board_id,
        )

    def list_thread_facets(self, community_id: int, thread_id: int) -> list[Facet]:
        self.get_thread(community_id, thread_id)
        return self._list_facets_for_assignment(
            "thread_facets",
            "thread_id",
            community_id,
            thread_id,
        )

    def list_material_facets(self, community_id: int, material_id: int) -> list[Facet]:
        self.get_material(community_id, material_id)
        return self._list_facets_for_assignment(
            "material_facets",
            "material_id",
            community_id,
            material_id,
        )

    def list_wanted_ad_facets(self, community_id: int, wanted_ad_id: int) -> list[Facet]:
        self.get_wanted_ad(community_id, wanted_ad_id)
        return self._list_facets_for_assignment(
            "wanted_ad_facets",
            "wanted_ad_id",
            community_id,
            wanted_ad_id,
        )

    def list_character_ids_for_facets(
        self,
        community_id: int,
        facet_ids: list[int],
    ) -> set[int]:
        return self._list_entity_ids_for_facets(
            "character_facets",
            "character_id",
            community_id,
            facet_ids,
        )

    def list_thread_ids_for_facets(
        self,
        community_id: int,
        facet_ids: list[int],
    ) -> set[int]:
        return self._list_entity_ids_for_facets(
            "thread_facets",
            "thread_id",
            community_id,
            facet_ids,
        )

    def assign_character_facet(
        self,
        community_id: int,
        character_id: int,
        facet_id: int,
    ) -> None:
        self.get_character(community_id, character_id)
        self.get_facet(community_id, facet_id)
        self._assign_facet("character_facets", "character_id", community_id, character_id, facet_id)

    def assign_board_facet(self, community_id: int, board_id: int, facet_id: int) -> None:
        self.get_board(community_id, board_id)
        self.get_facet(community_id, facet_id)
        self._assign_facet("board_facets", "board_id", community_id, board_id, facet_id)

    def assign_thread_facet(self, community_id: int, thread_id: int, facet_id: int) -> None:
        self.get_thread(community_id, thread_id)
        self.get_facet(community_id, facet_id)
        self._assign_facet("thread_facets", "thread_id", community_id, thread_id, facet_id)

    def assign_material_facet(self, community_id: int, material_id: int, facet_id: int) -> None:
        self.get_material(community_id, material_id)
        self.get_facet(community_id, facet_id)
        self._assign_facet(
            "material_facets",
            "material_id",
            community_id,
            material_id,
            facet_id,
        )

    def assign_wanted_ad_facet(self, community_id: int, wanted_ad_id: int, facet_id: int) -> None:
        self.get_wanted_ad(community_id, wanted_ad_id)
        self.get_facet(community_id, facet_id)
        self._assign_facet(
            "wanted_ad_facets",
            "wanted_ad_id",
            community_id,
            wanted_ad_id,
            facet_id,
        )

    def _list_facets_for_assignment(
        self,
        table: str,
        column: str,
        community_id: int,
        entity_id: int,
    ) -> list[Facet]:
        rows = self.connection.execute(
            f"""
            SELECT
                facets.id,
                facets.community_id,
                facets.facet_group_id,
                facets.slug,
                facets.name,
                facets.description,
                facets.accent_color,
                facets.sort_order,
                facets.created_at,
                facets.updated_at
            FROM {table}
            JOIN facets
              ON facets.community_id = {table}.community_id
             AND facets.id = {table}.facet_id
            JOIN facet_groups
              ON facet_groups.community_id = facets.community_id
             AND facet_groups.id = facets.facet_group_id
            WHERE {table}.community_id = ? AND {table}.{column} = ?
            ORDER BY facet_groups.sort_order, facet_groups.name, facets.sort_order, facets.name
            """,
            (community_id, entity_id),
        ).fetchall()
        return [_facet_from_row(row) for row in rows]

    def _list_entity_ids_for_facets(
        self,
        table: str,
        column: str,
        community_id: int,
        facet_ids: list[int],
    ) -> set[int]:
        cleaned_facet_ids = list(dict.fromkeys(facet_ids))
        if not cleaned_facet_ids:
            return set()
        placeholders = ", ".join("?" for _ in cleaned_facet_ids)
        rows = self.connection.execute(
            f"""
            SELECT {column}
            FROM {table}
            WHERE community_id = ? AND facet_id IN ({placeholders})
            GROUP BY {column}
            HAVING COUNT(DISTINCT facet_id) = ?
            """,
            (community_id, *cleaned_facet_ids, len(cleaned_facet_ids)),
        ).fetchall()
        return {int(row[column]) for row in rows}

    def _assign_facet(
        self,
        table: str,
        column: str,
        community_id: int,
        entity_id: int,
        facet_id: int,
    ) -> None:
        self.connection.execute(
            f"""
            INSERT OR IGNORE INTO {table} (community_id, {column}, facet_id, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (community_id, entity_id, facet_id, _utc_now()),
        )
        self.connection.commit()

    def create_material(
        self,
        community_id: int,
        slug: str,
        title: str,
        *,
        material_type: str = "guide",
        summary: str = "",
        body: str = "",
        status: str = "published",
        sort_order: int = 0,
        is_featured: bool = False,
    ) -> Material:
        self.get_community(community_id)
        now = _utc_now()
        cursor = self.connection.execute(
            """
            INSERT INTO materials (
                community_id,
                slug,
                title,
                material_type,
                summary,
                body,
                status,
                sort_order,
                is_featured,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                community_id,
                slug,
                title,
                material_type,
                summary,
                body,
                status,
                sort_order,
                int(is_featured),
                now,
                now,
            ),
        )
        self.connection.commit()
        return self.get_material(community_id, _last_id(cursor))

    def get_material(self, community_id: int, material_id: int) -> Material:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                slug,
                title,
                material_type,
                summary,
                body,
                status,
                sort_order,
                is_featured,
                created_at,
                updated_at
            FROM materials
            WHERE community_id = ? AND id = ?
            """,
            (community_id, material_id),
        ).fetchone()
        if row is None:
            raise LookupError(f"material not found in community {community_id}: {material_id}")
        return _material_from_row(row)

    def get_material_by_slug(self, community_id: int, slug: str) -> Material:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                slug,
                title,
                material_type,
                summary,
                body,
                status,
                sort_order,
                is_featured,
                created_at,
                updated_at
            FROM materials
            WHERE community_id = ? AND slug = ?
            """,
            (community_id, slug),
        ).fetchone()
        if row is None:
            raise LookupError(f"material not found in community {community_id}: {slug}")
        return _material_from_row(row)

    def list_materials(
        self, community_id: int, *, status: str | None = "published"
    ) -> list[Material]:
        where = "WHERE community_id = ?"
        params: tuple[object, ...] = (community_id,)
        if status is not None:
            where = f"{where} AND status = ?"
            params = (community_id, status)
        rows = self.connection.execute(
            f"""
            SELECT
                id,
                community_id,
                slug,
                title,
                material_type,
                summary,
                body,
                status,
                sort_order,
                is_featured,
                created_at,
                updated_at
            FROM materials
            {where}
            ORDER BY is_featured DESC, sort_order, title, id
            """,
            params,
        ).fetchall()
        return [_material_from_row(row) for row in rows]

    def create_wanted_ad(
        self,
        community_id: int,
        creator_membership_id: int,
        slug: str,
        title: str,
        *,
        creator_character_id: int | None = None,
        related_material_id: int | None = None,
        wanted_type: str = "plot_role",
        summary: str = "",
        body: str = "",
        status: str = "open",
    ) -> WantedAd:
        self.get_membership(community_id, creator_membership_id)
        if creator_character_id is not None:
            character = self.get_character(community_id, creator_character_id)
            if character.membership_id != creator_membership_id:
                raise TenantBoundaryError(
                    "wanted ad creator character must belong to creator membership"
                )
        if related_material_id is not None:
            self.get_material(community_id, related_material_id)
        now = _utc_now()
        cursor = self.connection.execute(
            """
            INSERT INTO wanted_ads (
                community_id,
                creator_membership_id,
                creator_character_id,
                related_material_id,
                slug,
                title,
                wanted_type,
                summary,
                body,
                status,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                community_id,
                creator_membership_id,
                creator_character_id,
                related_material_id,
                slug,
                title,
                wanted_type,
                summary,
                body,
                status,
                now,
                now,
            ),
        )
        self.connection.commit()
        return self.get_wanted_ad(community_id, _last_id(cursor))

    def get_wanted_ad(self, community_id: int, wanted_ad_id: int) -> WantedAd:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                creator_membership_id,
                creator_character_id,
                related_material_id,
                slug,
                title,
                wanted_type,
                summary,
                body,
                status,
                created_at,
                updated_at
            FROM wanted_ads
            WHERE community_id = ? AND id = ?
            """,
            (community_id, wanted_ad_id),
        ).fetchone()
        if row is None:
            raise LookupError(f"wanted ad not found in community {community_id}: {wanted_ad_id}")
        return _wanted_ad_from_row(row)

    def get_wanted_ad_by_slug(self, community_id: int, slug: str) -> WantedAd:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                creator_membership_id,
                creator_character_id,
                related_material_id,
                slug,
                title,
                wanted_type,
                summary,
                body,
                status,
                created_at,
                updated_at
            FROM wanted_ads
            WHERE community_id = ? AND slug = ?
            """,
            (community_id, slug),
        ).fetchone()
        if row is None:
            raise LookupError(f"wanted ad not found in community {community_id}: {slug}")
        return _wanted_ad_from_row(row)

    def list_wanted_ads(
        self,
        community_id: int,
        *,
        status: str | None = "open",
    ) -> list[WantedAd]:
        where = "WHERE community_id = ?"
        params: tuple[object, ...] = (community_id,)
        if status is not None:
            where = f"{where} AND status = ?"
            params = (community_id, status)
        rows = self.connection.execute(
            f"""
            SELECT
                id,
                community_id,
                creator_membership_id,
                creator_character_id,
                related_material_id,
                slug,
                title,
                wanted_type,
                summary,
                body,
                status,
                created_at,
                updated_at
            FROM wanted_ads
            {where}
            ORDER BY updated_at DESC, title, id
            """,
            params,
        ).fetchall()
        return [_wanted_ad_from_row(row) for row in rows]

    def list_wanted_ads_for_character(
        self,
        community_id: int,
        character_id: int,
        *,
        status: str | None = "open",
    ) -> list[WantedAd]:
        self.get_character(community_id, character_id)
        where = """
            WHERE wanted_ads.community_id = ?
              AND (
                wanted_ads.creator_character_id = ?
                OR wanted_ad_related_characters.character_id = ?
              )
        """
        params: tuple[object, ...] = (community_id, character_id, character_id)
        if status is not None:
            where = f"{where} AND wanted_ads.status = ?"
            params = (*params, status)
        rows = self.connection.execute(
            f"""
            SELECT DISTINCT
                wanted_ads.id,
                wanted_ads.community_id,
                wanted_ads.creator_membership_id,
                wanted_ads.creator_character_id,
                wanted_ads.related_material_id,
                wanted_ads.slug,
                wanted_ads.title,
                wanted_ads.wanted_type,
                wanted_ads.summary,
                wanted_ads.body,
                wanted_ads.status,
                wanted_ads.created_at,
                wanted_ads.updated_at
            FROM wanted_ads
            LEFT JOIN wanted_ad_related_characters
              ON wanted_ad_related_characters.community_id = wanted_ads.community_id
             AND wanted_ad_related_characters.wanted_ad_id = wanted_ads.id
            {where}
            ORDER BY wanted_ads.updated_at DESC, wanted_ads.title, wanted_ads.id
            """,
            params,
        ).fetchall()
        return [_wanted_ad_from_row(row) for row in rows]

    def add_wanted_ad_related_character(
        self,
        community_id: int,
        wanted_ad_id: int,
        character_id: int,
    ) -> None:
        self.get_wanted_ad(community_id, wanted_ad_id)
        self.get_character(community_id, character_id)
        self.connection.execute(
            """
            INSERT OR IGNORE INTO wanted_ad_related_characters (
                community_id,
                wanted_ad_id,
                character_id,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (community_id, wanted_ad_id, character_id, _utc_now()),
        )
        self.connection.commit()

    def list_wanted_ad_related_characters(
        self,
        community_id: int,
        wanted_ad_id: int,
    ) -> list[Character]:
        self.get_wanted_ad(community_id, wanted_ad_id)
        rows = self.connection.execute(
            """
            SELECT
                characters.id,
                characters.community_id,
                characters.membership_id,
                characters.name,
                characters.slug,
                characters.avatar_url,
                characters.summary,
                characters.created_at,
                characters.updated_at
            FROM wanted_ad_related_characters
            JOIN characters
              ON characters.community_id = wanted_ad_related_characters.community_id
             AND characters.id = wanted_ad_related_characters.character_id
            WHERE wanted_ad_related_characters.community_id = ?
              AND wanted_ad_related_characters.wanted_ad_id = ?
            ORDER BY characters.name, characters.id
            """,
            (community_id, wanted_ad_id),
        ).fetchall()
        return [_character_from_row(row) for row in rows]

    def update_wanted_ad_status(
        self,
        community_id: int,
        wanted_ad_id: int,
        status: str,
    ) -> WantedAd:
        self.get_wanted_ad(community_id, wanted_ad_id)
        self.connection.execute(
            """
            UPDATE wanted_ads
            SET status = ?, updated_at = ?
            WHERE community_id = ? AND id = ?
            """,
            (status, _utc_now(), community_id, wanted_ad_id),
        )
        self.connection.commit()
        return self.get_wanted_ad(community_id, wanted_ad_id)

    def create_wanted_ad_interest(
        self,
        community_id: int,
        wanted_ad_id: int,
        membership_id: int,
        character_id: int,
        *,
        note: str = "",
        status: str = "interested",
    ) -> WantedAdInterest:
        self.get_wanted_ad(community_id, wanted_ad_id)
        self.get_membership(community_id, membership_id)
        character = self.get_character(community_id, character_id)
        if character.membership_id != membership_id:
            raise TenantBoundaryError(
                f"character {character_id} does not belong to membership {membership_id}"
            )
        now = _utc_now()
        self.connection.execute(
            """
            INSERT OR IGNORE INTO wanted_ad_interests (
                community_id,
                wanted_ad_id,
                membership_id,
                character_id,
                note,
                status,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                community_id,
                wanted_ad_id,
                membership_id,
                character_id,
                note,
                status,
                now,
                now,
            ),
        )
        self.connection.commit()
        return self.get_wanted_ad_interest_for_character(
            community_id,
            wanted_ad_id,
            character_id,
        )

    def get_wanted_ad_interest(
        self,
        community_id: int,
        interest_id: int,
    ) -> WantedAdInterest:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                wanted_ad_id,
                membership_id,
                character_id,
                note,
                status,
                created_at,
                updated_at
            FROM wanted_ad_interests
            WHERE community_id = ? AND id = ?
            """,
            (community_id, interest_id),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"wanted interest not found in community {community_id}: {interest_id}"
            )
        return _wanted_ad_interest_from_row(row)

    def get_wanted_ad_interest_for_character(
        self,
        community_id: int,
        wanted_ad_id: int,
        character_id: int,
    ) -> WantedAdInterest:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                wanted_ad_id,
                membership_id,
                character_id,
                note,
                status,
                created_at,
                updated_at
            FROM wanted_ad_interests
            WHERE community_id = ? AND wanted_ad_id = ? AND character_id = ?
            """,
            (community_id, wanted_ad_id, character_id),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"wanted interest not found in community {community_id}: {wanted_ad_id}/{character_id}"
            )
        return _wanted_ad_interest_from_row(row)

    def list_wanted_ad_interests(
        self,
        community_id: int,
        wanted_ad_id: int,
        *,
        status: str | None = None,
    ) -> list[WantedAdInterest]:
        self.get_wanted_ad(community_id, wanted_ad_id)
        where = "WHERE community_id = ? AND wanted_ad_id = ?"
        params: tuple[object, ...] = (community_id, wanted_ad_id)
        if status is not None:
            where = f"{where} AND status = ?"
            params = (*params, status)
        rows = self.connection.execute(
            f"""
            SELECT
                id,
                community_id,
                wanted_ad_id,
                membership_id,
                character_id,
                note,
                status,
                created_at,
                updated_at
            FROM wanted_ad_interests
            {where}
            ORDER BY created_at DESC, id DESC
            """,
            params,
        ).fetchall()
        return [_wanted_ad_interest_from_row(row) for row in rows]

    def update_wanted_ad_interest_status(
        self,
        community_id: int,
        interest_id: int,
        status: str,
    ) -> WantedAdInterest:
        self.get_wanted_ad_interest(community_id, interest_id)
        self.connection.execute(
            """
            UPDATE wanted_ad_interests
            SET status = ?, updated_at = ?
            WHERE community_id = ? AND id = ?
            """,
            (status, _utc_now(), community_id, interest_id),
        )
        self.connection.commit()
        return self.get_wanted_ad_interest(community_id, interest_id)

    def create_thread(
        self,
        community_id: int,
        board_id: int,
        author_character_id: int,
        slug: str,
        title: str,
        *,
        status: str = "active",
        location: str = "",
        timeline: str = "",
        summary: str = "",
        posting_mode: str = "freeform",
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
                status,
                location,
                timeline,
                summary,
                posting_mode,
                is_locked,
                is_pinned,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                community_id,
                board_id,
                character.membership_id,
                author_character_id,
                slug,
                title,
                status,
                location,
                timeline,
                summary,
                posting_mode,
                int(is_locked),
                int(is_pinned),
                now,
                now,
            ),
        )
        thread_id = _last_id(cursor)
        self.connection.execute(
            """
            INSERT OR IGNORE INTO thread_participants (
                community_id, thread_id, character_id, added_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (community_id, thread_id, author_character_id, now),
        )
        self.connection.commit()
        return self.get_thread(community_id, thread_id)

    def update_thread_scene(
        self,
        community_id: int,
        thread_id: int,
        *,
        status: str | None = None,
        location: str | None = None,
        timeline: str | None = None,
        summary: str | None = None,
        posting_mode: str | None = None,
    ) -> Thread:
        thread = self.get_thread(community_id, thread_id)
        self.connection.execute(
            """
            UPDATE threads
            SET status = ?,
                location = ?,
                timeline = ?,
                summary = ?,
                posting_mode = ?
            WHERE community_id = ? AND id = ?
            """,
            (
                thread.status if status is None else status,
                thread.location if location is None else location,
                thread.timeline if timeline is None else timeline,
                thread.summary if summary is None else summary,
                thread.posting_mode if posting_mode is None else posting_mode,
                community_id,
                thread_id,
            ),
        )
        self.connection.commit()
        return self.get_thread(community_id, thread_id)

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

    def move_thread(self, community_id: int, thread_id: int, board_id: int) -> Thread:
        self.get_thread(community_id, thread_id)
        self.get_board(community_id, board_id)
        self.connection.execute(
            """
            UPDATE threads
            SET board_id = ?
            WHERE community_id = ? AND id = ?
            """,
            (board_id, community_id, thread_id),
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
                status,
                location,
                timeline,
                summary,
                posting_mode,
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
                status,
                location,
                timeline,
                summary,
                posting_mode,
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
                    status,
                    location,
                    timeline,
                    summary,
                    posting_mode,
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
                    status,
                    location,
                    timeline,
                    summary,
                    posting_mode,
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

    def add_thread_participant(
        self,
        community_id: int,
        thread_id: int,
        character_id: int,
    ) -> ThreadParticipant:
        self.get_thread(community_id, thread_id)
        self.get_character(community_id, character_id)
        self.connection.execute(
            """
            INSERT OR IGNORE INTO thread_participants (
                community_id, thread_id, character_id, added_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (community_id, thread_id, character_id, _utc_now()),
        )
        self.connection.commit()
        return self.get_thread_participant(community_id, thread_id, character_id)

    def set_thread_participants(
        self,
        community_id: int,
        thread_id: int,
        character_ids: list[int],
    ) -> list[Character]:
        thread = self.get_thread(community_id, thread_id)
        posted_rows = self.connection.execute(
            """
            SELECT author_character_id
            FROM posts
            WHERE community_id = ? AND thread_id = ?
            GROUP BY author_character_id
            ORDER BY MIN(created_at), author_character_id
            """,
            (community_id, thread_id),
        ).fetchall()
        unique_ids: list[int] = []
        posted_character_ids = [row["author_character_id"] for row in posted_rows]
        for character_id in [thread.author_character_id, *posted_character_ids, *character_ids]:
            if character_id not in unique_ids:
                self.get_character(community_id, character_id)
                unique_ids.append(character_id)
        self.connection.execute(
            """
            DELETE FROM thread_participants
            WHERE community_id = ? AND thread_id = ?
            """,
            (community_id, thread_id),
        )
        now = _utc_now()
        self.connection.executemany(
            """
            INSERT INTO thread_participants (
                community_id, thread_id, character_id, added_at
            )
            VALUES (?, ?, ?, ?)
            """,
            [(community_id, thread_id, character_id, now) for character_id in unique_ids],
        )
        self.connection.commit()
        return self.list_thread_participants(community_id, thread_id)

    def get_thread_participant(
        self,
        community_id: int,
        thread_id: int,
        character_id: int,
    ) -> ThreadParticipant:
        row = self.connection.execute(
            """
            SELECT id, community_id, thread_id, character_id, added_at
            FROM thread_participants
            WHERE community_id = ? AND thread_id = ? AND character_id = ?
            """,
            (community_id, thread_id, character_id),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"thread participant not found in community {community_id}: {thread_id}/{character_id}"
            )
        return _thread_participant_from_row(row)

    def list_thread_participants(self, community_id: int, thread_id: int) -> list[Character]:
        self.get_thread(community_id, thread_id)
        rows = self.connection.execute(
            """
            SELECT
                characters.id,
                characters.community_id,
                characters.membership_id,
                characters.name,
                characters.slug,
                characters.avatar_url,
                characters.summary,
                characters.created_at,
                characters.updated_at
            FROM thread_participants
            JOIN characters
              ON characters.community_id = thread_participants.community_id
             AND characters.id = thread_participants.character_id
            WHERE thread_participants.community_id = ?
              AND thread_participants.thread_id = ?
            ORDER BY thread_participants.added_at, characters.name, characters.id
            """,
            (community_id, thread_id),
        ).fetchall()
        return [_character_from_row(row) for row in rows]

    def list_thread_participant_ids(self, community_id: int, thread_id: int) -> set[int]:
        rows = self.connection.execute(
            """
            SELECT character_id
            FROM thread_participants
            WHERE community_id = ? AND thread_id = ?
            """,
            (community_id, thread_id),
        ).fetchall()
        return {row["character_id"] for row in rows}

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
        self.connection.execute(
            """
            INSERT OR IGNORE INTO thread_participants (
                community_id, thread_id, character_id, added_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (community_id, thread_id, author_character_id, now),
        )
        self.connection.commit()
        return self.get_post(community_id, _last_id(cursor))

    def update_post_body(self, community_id: int, post_id: int, body: str) -> Post:
        post = self.get_post(community_id, post_id)
        self.connection.execute(
            """
            UPDATE posts
            SET body = ?, updated_at = ?
            WHERE community_id = ? AND id = ?
            """,
            (body, _next_update_stamp(post.updated_at), community_id, post_id),
        )
        self.connection.commit()
        return self.get_post(community_id, post_id)

    def create_post_revision(
        self,
        community_id: int,
        post_id: int,
        editor_membership_id: int,
        previous_body: str,
        new_body: str,
    ) -> PostRevision:
        self.get_post(community_id, post_id)
        self.get_membership(community_id, editor_membership_id)
        cursor = self.connection.execute(
            """
            INSERT INTO post_revisions (
                community_id,
                post_id,
                editor_membership_id,
                previous_body,
                new_body,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (community_id, post_id, editor_membership_id, previous_body, new_body, _utc_now()),
        )
        self.connection.commit()
        return self.get_post_revision(community_id, _last_id(cursor))

    def get_post_revision(self, community_id: int, revision_id: int) -> PostRevision:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                post_id,
                editor_membership_id,
                previous_body,
                new_body,
                created_at
            FROM post_revisions
            WHERE community_id = ? AND id = ?
            """,
            (community_id, revision_id),
        ).fetchone()
        if row is None:
            raise LookupError(f"post revision not found in community {community_id}: {revision_id}")
        return _post_revision_from_row(row)

    def list_post_revisions(self, community_id: int, post_id: int) -> list[PostRevision]:
        self.get_post(community_id, post_id)
        rows = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                post_id,
                editor_membership_id,
                previous_body,
                new_body,
                created_at
            FROM post_revisions
            WHERE community_id = ? AND post_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (community_id, post_id),
        ).fetchall()
        return [_post_revision_from_row(row) for row in rows]

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
                status,
                location,
                timeline,
                summary,
                posting_mode,
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

    def watch_thread(
        self,
        community_id: int,
        thread_id: int,
        membership_id: int,
    ) -> ThreadWatch:
        self.get_thread(community_id, thread_id)
        self.get_membership(community_id, membership_id)
        now = _utc_now()
        self.connection.execute(
            """
            INSERT OR IGNORE INTO thread_watches (
                community_id, thread_id, membership_id, created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (community_id, thread_id, membership_id, now),
        )
        self.connection.commit()
        return self.get_thread_watch(community_id, thread_id, membership_id)

    def unwatch_thread(self, community_id: int, thread_id: int, membership_id: int) -> None:
        self.connection.execute(
            """
            DELETE FROM thread_watches
            WHERE community_id = ? AND thread_id = ? AND membership_id = ?
            """,
            (community_id, thread_id, membership_id),
        )
        self.connection.commit()

    def get_thread_watch(
        self,
        community_id: int,
        thread_id: int,
        membership_id: int,
    ) -> ThreadWatch:
        row = self.connection.execute(
            """
            SELECT id, community_id, thread_id, membership_id, created_at
            FROM thread_watches
            WHERE community_id = ? AND thread_id = ? AND membership_id = ?
            """,
            (community_id, thread_id, membership_id),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"thread watch not found in community {community_id}: {thread_id}/{membership_id}"
            )
        return _thread_watch_from_row(row)

    def is_thread_watched(self, community_id: int, thread_id: int, membership_id: int) -> bool:
        row = self.connection.execute(
            """
            SELECT 1
            FROM thread_watches
            WHERE community_id = ? AND thread_id = ? AND membership_id = ?
            """,
            (community_id, thread_id, membership_id),
        ).fetchone()
        return row is not None

    def list_thread_watch_membership_ids(self, community_id: int, thread_id: int) -> list[int]:
        self.get_thread(community_id, thread_id)
        rows = self.connection.execute(
            """
            SELECT membership_id
            FROM thread_watches
            WHERE community_id = ? AND thread_id = ?
            ORDER BY created_at, id
            """,
            (community_id, thread_id),
        ).fetchall()
        return [int(row["membership_id"]) for row in rows]

    def create_notification(
        self,
        community_id: int,
        membership_id: int,
        *,
        kind: str,
        thread_id: int | None = None,
        post_id: int | None = None,
        wanted_ad_id: int | None = None,
        wanted_ad_interest_id: int | None = None,
        actor_membership_id: int,
        actor_character_id: int,
    ) -> Notification:
        self.get_membership(community_id, membership_id)
        self.get_membership(community_id, actor_membership_id)
        actor = self.get_character(community_id, actor_character_id)
        if actor.membership_id != actor_membership_id:
            raise TenantBoundaryError(
                f"character {actor_character_id} does not belong to membership {actor_membership_id}"
            )
        post_target_id: int | None = None
        wanted_interest_target_id: int | None = None
        has_post_target = thread_id is not None and post_id is not None
        has_wanted_target = wanted_ad_id is not None and wanted_ad_interest_id is not None
        if has_post_target == has_wanted_target:
            raise ValueError("notification must target exactly one post or wanted interest")
        if thread_id is not None and post_id is not None:
            post_target_id = post_id
            thread = self.get_thread(community_id, thread_id)
            post = self.get_post(community_id, post_target_id)
            if post.thread_id != thread.id:
                raise TenantBoundaryError(f"post {post_id} does not belong to thread {thread_id}")
        elif wanted_ad_id is not None and wanted_ad_interest_id is not None:
            wanted_interest_target_id = wanted_ad_interest_id
            wanted_ad = self.get_wanted_ad(community_id, wanted_ad_id)
            interest = self.get_wanted_ad_interest(community_id, wanted_interest_target_id)
            if interest.wanted_ad_id != wanted_ad.id:
                raise TenantBoundaryError(
                    f"wanted interest {wanted_ad_interest_id} does not belong to wanted ad {wanted_ad_id}"
                )
        now = _utc_now()
        self.connection.execute(
            """
            INSERT OR IGNORE INTO notifications (
                community_id,
                membership_id,
                kind,
                thread_id,
                post_id,
                wanted_ad_id,
                wanted_ad_interest_id,
                actor_membership_id,
                actor_character_id,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                community_id,
                membership_id,
                kind,
                thread_id,
                post_id,
                wanted_ad_id,
                wanted_ad_interest_id,
                actor_membership_id,
                actor_character_id,
                now,
            ),
        )
        self.connection.commit()
        if post_target_id is not None:
            return self.get_notification_for_post(community_id, membership_id, kind, post_target_id)
        if wanted_interest_target_id is None:
            raise ValueError("notification must target exactly one post or wanted interest")
        return self.get_notification_for_wanted_interest(
            community_id,
            membership_id,
            kind,
            wanted_interest_target_id,
        )

    def get_notification(self, community_id: int, notification_id: int) -> Notification:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                membership_id,
                kind,
                thread_id,
                post_id,
                wanted_ad_id,
                wanted_ad_interest_id,
                actor_membership_id,
                actor_character_id,
                read_at,
                created_at
            FROM notifications
            WHERE community_id = ? AND id = ?
            """,
            (community_id, notification_id),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"notification not found in community {community_id}: {notification_id}"
            )
        return _notification_from_row(row)

    def get_notification_for_post(
        self,
        community_id: int,
        membership_id: int,
        kind: str,
        post_id: int,
    ) -> Notification:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                membership_id,
                kind,
                thread_id,
                post_id,
                wanted_ad_id,
                wanted_ad_interest_id,
                actor_membership_id,
                actor_character_id,
                read_at,
                created_at
            FROM notifications
            WHERE community_id = ? AND membership_id = ? AND kind = ? AND post_id = ?
            """,
            (community_id, membership_id, kind, post_id),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"notification not found in community {community_id}: {membership_id}/{kind}/{post_id}"
            )
        return _notification_from_row(row)

    def get_notification_for_wanted_interest(
        self,
        community_id: int,
        membership_id: int,
        kind: str,
        wanted_ad_interest_id: int,
    ) -> Notification:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                membership_id,
                kind,
                thread_id,
                post_id,
                wanted_ad_id,
                wanted_ad_interest_id,
                actor_membership_id,
                actor_character_id,
                read_at,
                created_at
            FROM notifications
            WHERE community_id = ?
              AND membership_id = ?
              AND kind = ?
              AND wanted_ad_interest_id = ?
            """,
            (community_id, membership_id, kind, wanted_ad_interest_id),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"notification not found in community {community_id}: {membership_id}/{kind}/{wanted_ad_interest_id}"
            )
        return _notification_from_row(row)

    def list_notifications(
        self,
        community_id: int,
        membership_id: int,
        *,
        limit: int = 50,
    ) -> list[Notification]:
        self.get_membership(community_id, membership_id)
        rows = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                membership_id,
                kind,
                thread_id,
                post_id,
                wanted_ad_id,
                wanted_ad_interest_id,
                actor_membership_id,
                actor_character_id,
                read_at,
                created_at
            FROM notifications
            WHERE community_id = ? AND membership_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (community_id, membership_id, limit),
        ).fetchall()
        return [_notification_from_row(row) for row in rows]

    def count_unread_notifications(self, community_id: int, membership_id: int) -> int:
        self.get_membership(community_id, membership_id)
        row = self.connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM notifications
            WHERE community_id = ? AND membership_id = ? AND read_at IS NULL
            """,
            (community_id, membership_id),
        ).fetchone()
        return int(row["count"] if row is not None else 0)

    def mark_notification_read(self, community_id: int, notification_id: int) -> Notification:
        notification = self.get_notification(community_id, notification_id)
        if notification.read_at is None:
            self.connection.execute(
                """
                UPDATE notifications
                SET read_at = ?
                WHERE community_id = ? AND id = ?
                """,
                (_utc_now(), community_id, notification_id),
            )
            self.connection.commit()
        return self.get_notification(community_id, notification_id)

    def mark_all_notifications_read(self, community_id: int, membership_id: int) -> None:
        self.get_membership(community_id, membership_id)
        self.connection.execute(
            """
            UPDATE notifications
            SET read_at = COALESCE(read_at, ?)
            WHERE community_id = ? AND membership_id = ?
            """,
            (_utc_now(), community_id, membership_id),
        )
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


def _facet_group_from_row(row: sqlite3.Row) -> FacetGroup:
    return FacetGroup(
        id=row["id"],
        community_id=row["community_id"],
        slug=row["slug"],
        name=row["name"],
        description=row["description"],
        selection_mode=row["selection_mode"],
        visibility=row["visibility"],
        sort_order=row["sort_order"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _facet_from_row(row: sqlite3.Row) -> Facet:
    return Facet(
        id=row["id"],
        community_id=row["community_id"],
        facet_group_id=row["facet_group_id"],
        slug=row["slug"],
        name=row["name"],
        description=row["description"],
        accent_color=row["accent_color"],
        sort_order=row["sort_order"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _material_from_row(row: sqlite3.Row) -> Material:
    return Material(
        id=row["id"],
        community_id=row["community_id"],
        slug=row["slug"],
        title=row["title"],
        material_type=row["material_type"],
        summary=row["summary"],
        body=row["body"],
        status=row["status"],
        sort_order=row["sort_order"],
        is_featured=bool(row["is_featured"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _wanted_ad_from_row(row: sqlite3.Row) -> WantedAd:
    return WantedAd(
        id=row["id"],
        community_id=row["community_id"],
        creator_membership_id=row["creator_membership_id"],
        creator_character_id=row["creator_character_id"],
        related_material_id=row["related_material_id"],
        slug=row["slug"],
        title=row["title"],
        wanted_type=row["wanted_type"],
        summary=row["summary"],
        body=row["body"],
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _wanted_ad_interest_from_row(row: sqlite3.Row) -> WantedAdInterest:
    return WantedAdInterest(
        id=row["id"],
        community_id=row["community_id"],
        wanted_ad_id=row["wanted_ad_id"],
        membership_id=row["membership_id"],
        character_id=row["character_id"],
        note=row["note"],
        status=row["status"],
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
        status=row["status"],
        location=row["location"],
        timeline=row["timeline"],
        summary=row["summary"],
        posting_mode=row["posting_mode"],
        is_locked=bool(row["is_locked"]),
        is_pinned=bool(row["is_pinned"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _thread_participant_from_row(row: sqlite3.Row) -> ThreadParticipant:
    return ThreadParticipant(
        id=row["id"],
        community_id=row["community_id"],
        thread_id=row["thread_id"],
        character_id=row["character_id"],
        added_at=row["added_at"],
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


def _post_revision_from_row(row: sqlite3.Row) -> PostRevision:
    return PostRevision(
        id=row["id"],
        community_id=row["community_id"],
        post_id=row["post_id"],
        editor_membership_id=row["editor_membership_id"],
        previous_body=row["previous_body"],
        new_body=row["new_body"],
        created_at=row["created_at"],
    )


def _thread_watch_from_row(row: sqlite3.Row) -> ThreadWatch:
    return ThreadWatch(
        id=row["id"],
        community_id=row["community_id"],
        thread_id=row["thread_id"],
        membership_id=row["membership_id"],
        created_at=row["created_at"],
    )


def _notification_from_row(row: sqlite3.Row) -> Notification:
    return Notification(
        id=row["id"],
        community_id=row["community_id"],
        membership_id=row["membership_id"],
        kind=row["kind"],
        thread_id=row["thread_id"],
        post_id=row["post_id"],
        wanted_ad_id=row["wanted_ad_id"],
        wanted_ad_interest_id=row["wanted_ad_interest_id"],
        actor_membership_id=row["actor_membership_id"],
        actor_character_id=row["actor_character_id"],
        read_at=row["read_at"],
        created_at=row["created_at"],
    )
