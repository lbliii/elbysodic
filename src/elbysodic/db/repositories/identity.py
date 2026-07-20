"""Community, user, role, and membership repository methods."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, Protocol, cast

from elbysodic.db.repositories.base import RepositoryBase, _last_id, _utc_now
from elbysodic.db.repositories.rows import (
    _community_access_request_event_from_row,
    _community_access_request_from_row,
    _community_from_row,
    _community_invitation_from_row,
    _community_theme_from_row,
    _membership_from_row,
    _role_from_row,
    _user_from_row,
    _user_session_from_row,
)
from elbysodic.domain.capabilities import STAFF_CAPABILITIES
from elbysodic.domain.context import DEFAULT_COMMUNITY_ID, DEFAULT_COMMUNITY_SLUG
from elbysodic.domain.models import (
    Community,
    CommunityAccessRequest,
    CommunityAccessRequestEvent,
    CommunityInvitation,
    CommunityMembership,
    CommunityTheme,
    Role,
    User,
    UserSession,
)

COMMUNITY_LAUNCH_STATUSES = {"backstage", "invite-only", "public-preview"}
ACCESS_REQUEST_TRANSITIONS = {
    "pending": {"reviewed", "invited", "declined", "withdrawn", "expired"},
    "reviewed": {"invited", "declined", "withdrawn", "expired"},
    "invited": {"accepted", "reviewed", "withdrawn", "expired"},
    "accepted": {"archived"},
    "declined": {"archived"},
    "withdrawn": {"archived"},
    "expired": {"archived"},
    "archived": set(),
}
ACCESS_REQUEST_EVENT_TYPES = {
    "accepted",
    "account_linked",
    "archived",
    "declined",
    "expired",
    "invitation_reissued",
    "invitation_revoked",
    "invited",
    "reviewed",
    "submitted",
    "withdrawn",
}


class _SidebarDefaultsRepository(Protocol):
    def ensure_sidebar_section_defaults(self, community_id: int) -> None: ...


@dataclass(frozen=True, slots=True)
class MembershipRoleIntegrityIssue:
    community_id: int
    membership_id: int
    role_id: int


@dataclass(frozen=True, slots=True)
class SessionIdentityIntegrityIssue:
    session_id: int
    user_id: int
    selected_community_id: int | None
    selected_membership_id: int | None
    reason: str


@dataclass(frozen=True, slots=True)
class TenantPairIntegrityIssue:
    table_name: str
    row_id: int
    community_id: int
    reason: str


@dataclass(frozen=True, slots=True)
class CommandSubmission:
    id: int
    community_id: int
    membership_id: int
    command_key: str
    result_path: str | None


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
        self.connection.execute(
            """
            UPDATE communities
               SET name = ?,
                   slug = ?,
                   updated_at = ?
             WHERE id = ?
               AND (name != ? OR slug != ?)
            """,
            (
                name,
                DEFAULT_COMMUNITY_SLUG,
                now,
                DEFAULT_COMMUNITY_ID,
                name,
                DEFAULT_COMMUNITY_SLUG,
            ),
        )
        self._commit()
        community = self.get_community(DEFAULT_COMMUNITY_ID)
        cast(_SidebarDefaultsRepository, self).ensure_sidebar_section_defaults(community.id)
        return community

    def create_community(self, slug: str, name: str, host: str | None = None) -> Community:
        now = _utc_now()
        cursor = self.connection.execute(
            """
            INSERT INTO communities (name, slug, host, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, slug, host, now, now),
        )
        self._commit()
        community = self.get_community(_last_id(cursor))
        cast(_SidebarDefaultsRepository, self).ensure_sidebar_section_defaults(community.id)
        return community

    def get_community(self, community_id: int) -> Community:
        row = self.connection.execute(
            """
            SELECT
                id,
                name,
                slug,
                host,
                launch_status,
                default_theme_id,
                identity_accent_facet_group_id,
                community_mark_url,
                community_mark_alt,
                world_hero_image_url,
                world_hero_image_alt,
                world_hero_treatment,
                world_hero_focal_point,
                world_hero_overlay,
                world_hero_height,
                enabled_post_profile_variants,
                enabled_post_accent_styles,
                enabled_post_border_styles,
                enabled_post_title_styles,
                enabled_post_densities,
                created_at,
                updated_at
            FROM communities
            WHERE id = ?
            """,
            (community_id,),
        ).fetchone()
        if row is None:
            raise LookupError(f"community not found: {community_id}")
        return _community_from_row(row)

    def get_community_by_slug(self, slug: str) -> Community:
        row = self.connection.execute(
            """
            SELECT
                id,
                name,
                slug,
                host,
                launch_status,
                default_theme_id,
                identity_accent_facet_group_id,
                community_mark_url,
                community_mark_alt,
                world_hero_image_url,
                world_hero_image_alt,
                world_hero_treatment,
                world_hero_focal_point,
                world_hero_overlay,
                world_hero_height,
                enabled_post_profile_variants,
                enabled_post_accent_styles,
                enabled_post_border_styles,
                enabled_post_title_styles,
                enabled_post_densities,
                created_at,
                updated_at
            FROM communities
            WHERE slug = ?
            """,
            (slug,),
        ).fetchone()
        if row is None:
            raise LookupError(f"community not found for slug: {slug}")
        return _community_from_row(row)

    def get_community_by_host(self, host: str) -> Community:
        row = self.connection.execute(
            """
            SELECT
                id,
                name,
                slug,
                host,
                launch_status,
                default_theme_id,
                identity_accent_facet_group_id,
                community_mark_url,
                community_mark_alt,
                world_hero_image_url,
                world_hero_image_alt,
                world_hero_treatment,
                world_hero_focal_point,
                world_hero_overlay,
                world_hero_height,
                enabled_post_profile_variants,
                enabled_post_accent_styles,
                enabled_post_border_styles,
                enabled_post_title_styles,
                enabled_post_densities,
                created_at,
                updated_at
            FROM communities
            WHERE host = ?
            """,
            (host,),
        ).fetchone()
        if row is None:
            raise LookupError(f"community not found for host: {host}")
        return _community_from_row(row)

    def list_communities(self) -> list[Community]:
        rows = self.connection.execute(
            """
            SELECT
                id,
                name,
                slug,
                host,
                launch_status,
                default_theme_id,
                identity_accent_facet_group_id,
                community_mark_url,
                community_mark_alt,
                world_hero_image_url,
                world_hero_image_alt,
                world_hero_treatment,
                world_hero_focal_point,
                world_hero_overlay,
                world_hero_height,
                enabled_post_profile_variants,
                enabled_post_accent_styles,
                enabled_post_border_styles,
                enabled_post_title_styles,
                enabled_post_densities,
                created_at,
                updated_at
            FROM communities
            ORDER BY name, id
            """
        ).fetchall()
        return [_community_from_row(row) for row in rows]

    def list_communities_by_ids(self, community_ids: list[int]) -> dict[int, Community]:
        if not community_ids:
            return {}
        rows = self.connection.execute(
            """
            SELECT
                id,
                name,
                slug,
                host,
                launch_status,
                default_theme_id,
                identity_accent_facet_group_id,
                community_mark_url,
                community_mark_alt,
                world_hero_image_url,
                world_hero_image_alt,
                world_hero_treatment,
                world_hero_focal_point,
                world_hero_overlay,
                world_hero_height,
                enabled_post_profile_variants,
                enabled_post_accent_styles,
                enabled_post_border_styles,
                enabled_post_title_styles,
                enabled_post_densities,
                created_at,
                updated_at
            FROM communities
            WHERE id IN (SELECT value FROM json_each(?))
            """,
            (json.dumps(community_ids),),
        ).fetchall()
        return {int(row["id"]): _community_from_row(row) for row in rows}

    def roles_for_memberships(self, membership_ids: list[int]) -> dict[int, Role]:
        if not membership_ids:
            return {}
        rows = self.connection.execute(
            """
            SELECT
                community_memberships.id AS membership_id,
                roles.id,
                roles.community_id,
                roles.slug,
                roles.name,
                roles.is_admin,
                roles.created_at,
                roles.updated_at,
                COALESCE((
                    SELECT group_concat(role_capabilities.capability, ',')
                    FROM role_capabilities
                    WHERE role_capabilities.community_id = roles.community_id
                      AND role_capabilities.role_id = roles.id
                ), '') AS capabilities
            FROM community_memberships
            JOIN roles
              ON roles.community_id = community_memberships.community_id
             AND roles.id = community_memberships.role_id
            WHERE community_memberships.id IN (SELECT value FROM json_each(?))
            """,
            (json.dumps(membership_ids),),
        ).fetchall()
        return {int(row["membership_id"]): _role_from_row(row) for row in rows}

    def network_program_counts(self, community_ids: list[int]) -> dict[int, dict[str, int | str]]:
        if not community_ids:
            return {}
        rows = self.connection.execute(
            """
            SELECT
                communities.id AS community_id,
                (
                    SELECT COUNT(*)
                    FROM characters
                    WHERE characters.community_id = communities.id
                ) AS roster_count,
                (
                    SELECT COUNT(*)
                    FROM wanted_ads
                    WHERE wanted_ads.community_id = communities.id
                      AND wanted_ads.status = 'open'
                ) AS open_wanted_count,
                (
                    SELECT COUNT(*)
                    FROM materials
                    WHERE materials.community_id = communities.id
                      AND materials.material_type = 'application'
                ) AS application_material_count,
                (
                    SELECT COUNT(*)
                    FROM claim_types
                    WHERE claim_types.community_id = communities.id
                ) AS claim_type_count,
                MAX(
                    COALESCE((
                        SELECT MAX(materials.updated_at)
                        FROM materials
                        WHERE materials.community_id = communities.id
                          AND materials.status = 'published'
                    ), ''),
                    COALESCE((
                        SELECT MAX(wanted_ads.updated_at)
                        FROM wanted_ads
                        WHERE wanted_ads.community_id = communities.id
                          AND wanted_ads.status = 'open'
                    ), ''),
                    COALESCE((
                        SELECT MAX(threads.updated_at)
                        FROM threads
                        JOIN boards
                          ON boards.community_id = threads.community_id
                         AND boards.id = threads.board_id
                        WHERE threads.community_id = communities.id
                          AND boards.is_private = 0
                          AND threads.status != 'private'
                    ), ''),
                    COALESCE((
                        SELECT MAX(posts.updated_at)
                        FROM posts
                        JOIN threads
                          ON threads.community_id = posts.community_id
                         AND threads.id = posts.thread_id
                        JOIN boards
                          ON boards.community_id = threads.community_id
                         AND boards.id = threads.board_id
                        WHERE posts.community_id = communities.id
                          AND boards.is_private = 0
                          AND threads.status != 'private'
                    ), '')
                ) AS latest_public_activity_at
            FROM communities
            WHERE communities.id IN (SELECT value FROM json_each(?))
            """,
            (json.dumps(community_ids),),
        ).fetchall()
        return {
            int(row["community_id"]): {
                "roster_count": int(row["roster_count"]),
                "open_wanted_count": int(row["open_wanted_count"]),
                "application_material_count": int(row["application_material_count"]),
                "claim_type_count": int(row["claim_type_count"]),
                "latest_public_activity_at": str(row["latest_public_activity_at"] or ""),
            }
            for row in rows
        }

    def network_membership_counts(self, membership_ids: list[int]) -> dict[int, dict[str, int]]:
        if not membership_ids:
            return {}
        rows = self.connection.execute(
            """
            SELECT
                memberships.id AS membership_id,
                (
                    SELECT COUNT(*)
                    FROM characters
                    WHERE characters.community_id = memberships.community_id
                      AND characters.application_status IN (
                        'draft',
                        'submitted',
                        'revision_requested'
                      )
                ) AS reviewable_application_count,
                (
                    SELECT COUNT(*)
                    FROM characters
                    WHERE characters.community_id = memberships.community_id
                      AND characters.membership_id = memberships.id
                      AND characters.application_status IN (
                        'draft',
                        'submitted',
                        'revision_requested'
                      )
                ) AS own_application_count,
                (
                    SELECT COUNT(DISTINCT rooms.id)
                    FROM plotting_rooms AS rooms
                    JOIN plotting_room_participants AS participants
                      ON participants.community_id = rooms.community_id
                     AND participants.plotting_room_id = rooms.id
                    WHERE rooms.community_id = memberships.community_id
                      AND participants.membership_id = memberships.id
                ) AS plotting_room_count
            FROM community_memberships AS memberships
            WHERE memberships.id IN (SELECT value FROM json_each(?))
            """,
            (json.dumps(membership_ids),),
        ).fetchall()
        return {
            int(row["membership_id"]): {
                "reviewable_application_count": int(row["reviewable_application_count"]),
                "own_application_count": int(row["own_application_count"]),
                "plotting_room_count": int(row["plotting_room_count"]),
            }
            for row in rows
        }

    def update_community_launch_status(self, community_id: int, launch_status: str) -> Community:
        status = launch_status.strip().lower()
        if status not in COMMUNITY_LAUNCH_STATUSES:
            raise ValueError("launch status must be backstage, invite-only, or public-preview")
        self.get_community(community_id)
        self.connection.execute(
            """
            UPDATE communities
            SET launch_status = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (status, _utc_now(), community_id),
        )
        self._commit()
        return self.get_community(community_id)

    def update_community_identity_accent_group(
        self,
        community_id: int,
        facet_group_id: int | None,
    ) -> Community:
        self.get_community(community_id)
        if facet_group_id is not None:
            row = self.connection.execute(
                """
                SELECT id
                FROM facet_groups
                WHERE community_id = ? AND id = ?
                """,
                (community_id, facet_group_id),
            ).fetchone()
            if row is None:
                raise LookupError(
                    f"facet group not found in community {community_id}: {facet_group_id}"
                )
        self.connection.execute(
            """
            UPDATE communities
            SET identity_accent_facet_group_id = ?, updated_at = ?
            WHERE id = ?
            """,
            (facet_group_id, _utc_now(), community_id),
        )
        self._commit()
        return self.get_community(community_id)

    def update_community_media(
        self,
        community_id: int,
        *,
        community_mark_url: str | None,
        community_mark_alt: str,
        world_hero_image_url: str | None,
        world_hero_image_alt: str,
        world_hero_treatment: str,
        world_hero_focal_point: str,
        world_hero_overlay: str,
        world_hero_height: str,
    ) -> Community:
        self.get_community(community_id)
        self.connection.execute(
            """
            UPDATE communities
            SET community_mark_url = ?,
                community_mark_alt = ?,
                world_hero_image_url = ?,
                world_hero_image_alt = ?,
                world_hero_treatment = ?,
                world_hero_focal_point = ?,
                world_hero_overlay = ?,
                world_hero_height = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                community_mark_url,
                community_mark_alt,
                world_hero_image_url,
                world_hero_image_alt,
                world_hero_treatment,
                world_hero_focal_point,
                world_hero_overlay,
                world_hero_height,
                _utc_now(),
                community_id,
            ),
        )
        self._commit()
        return self.get_community(community_id)

    def update_community_name_and_slug(
        self, community_id: int, *, slug: str, name: str
    ) -> Community:
        self.get_community(community_id)
        self.connection.execute(
            """
            UPDATE communities
            SET slug = ?, name = ?, updated_at = ?
            WHERE id = ?
            """,
            (slug, name, _utc_now(), community_id),
        )
        self._commit()
        return self.get_community(community_id)

    def create_theme(
        self,
        community_id: int,
        slug: str,
        name: str,
        tokens_json: str,
    ) -> CommunityTheme:
        self.get_community(community_id)
        now = _utc_now()
        cursor = self.connection.execute(
            """
            INSERT INTO themes (community_id, slug, name, tokens_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (community_id, slug, name, tokens_json, now, now),
        )
        self._commit()
        return self.get_theme(community_id, _last_id(cursor))

    def get_theme(self, community_id: int, theme_id: int) -> CommunityTheme:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                slug,
                name,
                tokens_json,
                created_at,
                updated_at
            FROM themes
            WHERE community_id = ? AND id = ?
            """,
            (community_id, theme_id),
        ).fetchone()
        if row is None:
            raise LookupError(f"theme not found in community {community_id}: {theme_id}")
        return _community_theme_from_row(row)

    def get_theme_by_slug(self, community_id: int, slug: str) -> CommunityTheme:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                slug,
                name,
                tokens_json,
                created_at,
                updated_at
            FROM themes
            WHERE community_id = ? AND slug = ?
            """,
            (community_id, slug),
        ).fetchone()
        if row is None:
            raise LookupError(f"theme not found in community {community_id}: {slug}")
        return _community_theme_from_row(row)

    def get_default_theme(self, community_id: int) -> CommunityTheme | None:
        community = self.get_community(community_id)
        if community.default_theme_id is None:
            return None
        return self.get_theme(community_id, community.default_theme_id)

    def default_themes_for_communities(
        self,
        community_ids: list[int],
    ) -> dict[int, CommunityTheme]:
        if not community_ids:
            return {}
        rows = self.connection.execute(
            """
            SELECT
                themes.id,
                themes.community_id,
                themes.slug,
                themes.name,
                themes.tokens_json,
                themes.created_at,
                themes.updated_at
            FROM communities
            JOIN themes
              ON themes.community_id = communities.id
             AND themes.id = communities.default_theme_id
            WHERE communities.id IN (SELECT value FROM json_each(?))
            """,
            (json.dumps(community_ids),),
        ).fetchall()
        return {int(row["community_id"]): _community_theme_from_row(row) for row in rows}

    def update_theme(
        self,
        community_id: int,
        theme_id: int,
        *,
        slug: str,
        name: str,
        tokens_json: str,
    ) -> CommunityTheme:
        self.get_theme(community_id, theme_id)
        self.connection.execute(
            """
            UPDATE themes
            SET slug = ?, name = ?, tokens_json = ?, updated_at = ?
            WHERE community_id = ? AND id = ?
            """,
            (slug, name, tokens_json, _utc_now(), community_id, theme_id),
        )
        self._commit()
        return self.get_theme(community_id, theme_id)

    def set_default_theme(self, community_id: int, theme_id: int | None) -> Community:
        self.get_community(community_id)
        if theme_id is not None:
            self.get_theme(community_id, theme_id)
        self.connection.execute(
            """
            UPDATE communities
            SET default_theme_id = ?, updated_at = ?
            WHERE id = ?
            """,
            (theme_id, _utc_now(), community_id),
        )
        self._commit()
        return self.get_community(community_id)

    def upsert_default_theme(
        self,
        community_id: int,
        *,
        slug: str,
        name: str,
        tokens_json: str,
    ) -> CommunityTheme:
        try:
            theme = self.get_theme_by_slug(community_id, slug)
        except LookupError:
            theme = self.create_theme(community_id, slug, name, tokens_json)
        else:
            theme = self.update_theme(
                community_id,
                theme.id,
                slug=slug,
                name=name,
                tokens_json=tokens_json,
            )
        self.set_default_theme(community_id, theme.id)
        return theme

    def update_community_post_style_policy(
        self,
        community_id: int,
        *,
        enabled_post_profile_variants: str,
        enabled_post_accent_styles: str,
        enabled_post_border_styles: str,
        enabled_post_title_styles: str,
        enabled_post_densities: str,
    ) -> Community:
        self.get_community(community_id)
        self.connection.execute(
            """
            UPDATE communities
            SET enabled_post_profile_variants = ?,
                enabled_post_accent_styles = ?,
                enabled_post_border_styles = ?,
                enabled_post_title_styles = ?,
                enabled_post_densities = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                enabled_post_profile_variants,
                enabled_post_accent_styles,
                enabled_post_border_styles,
                enabled_post_title_styles,
                enabled_post_densities,
                _utc_now(),
                community_id,
            ),
        )
        self._commit()
        return self.get_community(community_id)

    def create_user(self, email: str, password_hash: str) -> User:
        cursor = self.connection.execute(
            """
            INSERT INTO users (email, password_hash, created_at)
            VALUES (?, ?, ?)
            """,
            (email, password_hash, _utc_now()),
        )
        self._commit()
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

    def update_user_password_hash(
        self,
        user_id: int,
        *,
        expected_hash: str,
        new_hash: str,
    ) -> bool:
        """Replace one global account hash only if the caller verified this version."""

        cursor = self.connection.execute(
            """
            UPDATE users
            SET password_hash = ?
            WHERE id = ? AND password_hash = ?
            """,
            (new_hash, user_id, expected_hash),
        )
        self._commit()
        return cursor.rowcount == 1

    def get_or_create_user(self, email: str, password_hash: str) -> User:
        try:
            return self.get_user_by_email(email)
        except LookupError:
            return self.create_user(email, password_hash)

    def create_user_session(
        self,
        user_id: int,
        token_hash: str,
        *,
        expires_at: str | None = None,
    ) -> UserSession:
        self.get_user(user_id)
        now = _utc_now()
        cursor = self.connection.execute(
            """
            INSERT INTO user_sessions (
                user_id,
                token_hash,
                selected_community_id,
                selected_membership_id,
                created_at,
                last_seen_at,
                expires_at,
                revoked_at
            )
            VALUES (?, ?, NULL, NULL, ?, ?, ?, NULL)
            """,
            (user_id, token_hash, now, now, expires_at),
        )
        self._commit()
        return self.get_user_session(_last_id(cursor))

    def get_user_session(self, session_id: int) -> UserSession:
        row = self.connection.execute(
            """
            SELECT
                id,
                user_id,
                token_hash,
                selected_community_id,
                selected_membership_id,
                created_at,
                last_seen_at,
                expires_at,
                revoked_at
            FROM user_sessions
            WHERE id = ?
            """,
            (session_id,),
        ).fetchone()
        if row is None:
            raise LookupError(f"user session not found: {session_id}")
        return _user_session_from_row(row)

    def get_user_session_by_token_hash(self, token_hash: str) -> UserSession:
        row = self.connection.execute(
            """
            SELECT
                id,
                user_id,
                token_hash,
                selected_community_id,
                selected_membership_id,
                created_at,
                last_seen_at,
                expires_at,
                revoked_at
            FROM user_sessions
            WHERE token_hash = ?
            """,
            (token_hash,),
        ).fetchone()
        if row is None:
            raise LookupError("user session not found")
        return _user_session_from_row(row)

    def touch_user_session(self, session_id: int) -> UserSession:
        self.connection.execute(
            """
            UPDATE user_sessions
            SET last_seen_at = ?
            WHERE id = ?
            """,
            (_utc_now(), session_id),
        )
        self._commit()
        return self.get_user_session(session_id)

    def update_user_session_identity(
        self,
        session_id: int,
        *,
        community_id: int,
        membership_id: int,
    ) -> UserSession:
        session = self.get_user_session(session_id)
        membership = self.get_membership(community_id, membership_id)
        if membership.user_id != session.user_id:
            raise PermissionError(
                f"membership {membership_id} does not belong to session user {session.user_id}"
            )
        if not membership.is_active:
            raise PermissionError(f"membership {membership.id} is not active")
        self.connection.execute(
            """
            UPDATE user_sessions
            SET selected_community_id = ?,
                selected_membership_id = ?,
                last_seen_at = ?
            WHERE id = ?
            """,
            (community_id, membership_id, _utc_now(), session_id),
        )
        self._commit()
        return self.get_user_session(session_id)

    def revoke_user_session_by_token_hash(self, token_hash: str) -> None:
        self.connection.execute(
            """
            UPDATE user_sessions
            SET revoked_at = COALESCE(revoked_at, ?),
                selected_community_id = NULL,
                selected_membership_id = NULL
            WHERE token_hash = ?
            """,
            (_utc_now(), token_hash),
        )
        self._commit()

    def create_role(
        self,
        community_id: int,
        slug: str,
        name: str,
        *,
        is_admin: bool = False,
        capabilities: Iterable[str] | None = None,
    ) -> Role:
        grants = set(
            STAFF_CAPABILITIES if capabilities is None and is_admin else capabilities or ()
        )
        unknown = grants - STAFF_CAPABILITIES
        if unknown:
            raise ValueError(f"unknown staff capabilities: {', '.join(sorted(unknown))}")
        now = _utc_now()
        with self.transaction():
            cursor = self.connection.execute(
                """
                INSERT INTO roles (community_id, slug, name, is_admin, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (community_id, slug, name, int(is_admin), now, now),
            )
            role_id = _last_id(cursor)
            self.connection.executemany(
                """
                INSERT INTO role_capabilities (community_id, role_id, capability, created_at)
                VALUES (?, ?, ?, ?)
                """,
                ((community_id, role_id, capability, now) for capability in sorted(grants)),
            )
        return self.get_role(community_id, role_id)

    def get_role(self, community_id: int, role_id: int) -> Role:
        row = self.connection.execute(
            """
            SELECT roles.id, roles.community_id, roles.slug, roles.name, roles.is_admin,
                   roles.created_at, roles.updated_at,
                   COALESCE((
                       SELECT group_concat(role_capabilities.capability, ',')
                       FROM role_capabilities
                       WHERE role_capabilities.community_id = roles.community_id
                         AND role_capabilities.role_id = roles.id
                   ), '') AS capabilities
            FROM roles
            WHERE roles.community_id = ? AND roles.id = ?
            """,
            (community_id, role_id),
        ).fetchone()
        if row is None:
            raise LookupError(f"role not found in community {community_id}: {role_id}")
        return _role_from_row(row)

    def get_role_by_slug(self, community_id: int, slug: str) -> Role:
        row = self.connection.execute(
            """
            SELECT roles.id, roles.community_id, roles.slug, roles.name, roles.is_admin,
                   roles.created_at, roles.updated_at,
                   COALESCE((
                       SELECT group_concat(role_capabilities.capability, ',')
                       FROM role_capabilities
                       WHERE role_capabilities.community_id = roles.community_id
                         AND role_capabilities.role_id = roles.id
                   ), '') AS capabilities
            FROM roles
            WHERE roles.community_id = ? AND roles.slug = ?
            """,
            (community_id, slug),
        ).fetchone()
        if row is None:
            raise LookupError(f"role not found in community {community_id}: {slug}")
        return _role_from_row(row)

    def set_role_capabilities(
        self,
        community_id: int,
        role_id: int,
        capabilities: Iterable[str],
    ) -> Role:
        self.get_role(community_id, role_id)
        grants = set(capabilities)
        unknown = grants - STAFF_CAPABILITIES
        if unknown:
            raise ValueError(f"unknown staff capabilities: {', '.join(sorted(unknown))}")
        now = _utc_now()
        with self.transaction():
            self.connection.execute(
                "DELETE FROM role_capabilities WHERE community_id = ? AND role_id = ?",
                (community_id, role_id),
            )
            self.connection.executemany(
                """
                INSERT INTO role_capabilities (community_id, role_id, capability, created_at)
                VALUES (?, ?, ?, ?)
                """,
                ((community_id, role_id, capability, now) for capability in sorted(grants)),
            )
        return self.get_role(community_id, role_id)

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
        self._commit()
        return self.get_membership(community_id, _last_id(cursor))

    def create_community_invitation(
        self,
        community_id: int,
        *,
        email: str,
        role_id: int,
        invited_by_membership_id: int,
        token_hash: str,
        expires_at: str | None,
    ) -> CommunityInvitation:
        self.get_role(community_id, role_id)
        self.get_membership(community_id, invited_by_membership_id)
        now = _utc_now()
        cursor = self.connection.execute(
            """
            INSERT INTO community_invitations (
                community_id,
                email,
                role_id,
                invited_by_membership_id,
                token_hash,
                status,
                expires_at,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)
            """,
            (community_id, email, role_id, invited_by_membership_id, token_hash, expires_at, now),
        )
        self._commit()
        return self.get_community_invitation(community_id, _last_id(cursor))

    def get_community_invitation(
        self,
        community_id: int,
        invitation_id: int,
    ) -> CommunityInvitation:
        row = self._community_invitation_row(
            "WHERE community_id = ? AND id = ?",
            (community_id, invitation_id),
        )
        if row is None:
            raise LookupError(f"invitation not found in community {community_id}: {invitation_id}")
        return _community_invitation_from_row(row)

    def get_community_invitation_by_id(self, invitation_id: int) -> CommunityInvitation:
        row = self._community_invitation_row("WHERE id = ?", (invitation_id,))
        if row is None:
            raise LookupError(f"invitation not found: {invitation_id}")
        return _community_invitation_from_row(row)

    def get_community_invitation_by_token_hash(self, token_hash: str) -> CommunityInvitation:
        row = self._community_invitation_row("WHERE token_hash = ?", (token_hash,))
        if row is None:
            raise LookupError("invitation not found")
        return _community_invitation_from_row(row)

    def list_community_invitations(self, community_id: int) -> list[CommunityInvitation]:
        rows = self.connection.execute(
            self._community_invitation_select()
            + """
            WHERE community_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (community_id,),
        ).fetchall()
        return [_community_invitation_from_row(row) for row in rows]

    def accept_community_invitation(
        self,
        invitation_id: int,
        *,
        user_id: int,
        membership_id: int,
    ) -> CommunityInvitation:
        invitation = self.get_community_invitation_by_id(invitation_id)
        membership = self.get_membership(invitation.community_id, membership_id)
        if membership.user_id != user_id:
            raise PermissionError("accepted invitation membership must belong to accepted user")
        now = _utc_now()
        self.connection.execute(
            """
            UPDATE community_invitations
            SET status = 'accepted',
                accepted_user_id = ?,
                accepted_membership_id = ?,
                accepted_at = ?,
                revoked_at = NULL
            WHERE id = ?
            """,
            (user_id, membership_id, now, invitation_id),
        )
        self._commit()
        return self.get_community_invitation(invitation.community_id, invitation_id)

    def revoke_community_invitation(
        self,
        community_id: int,
        invitation_id: int,
    ) -> CommunityInvitation:
        self.get_community_invitation(community_id, invitation_id)
        self.connection.execute(
            """
            UPDATE community_invitations
            SET status = 'revoked',
                revoked_at = COALESCE(revoked_at, ?)
            WHERE community_id = ? AND id = ?
            """,
            (_utc_now(), community_id, invitation_id),
        )
        self._commit()
        return self.get_community_invitation(community_id, invitation_id)

    def create_community_access_request(
        self,
        community_id: int,
        *,
        email: str,
        display_name: str,
        face_concept: str,
        wanted_hook: str,
        notes: str,
        account_user_id: int | None = None,
    ) -> CommunityAccessRequest:
        self.get_community(community_id)
        if account_user_id is not None:
            self.get_user(account_user_id)
        now = _utc_now()
        cursor = self.connection.execute(
            """
            INSERT INTO community_access_requests (
                community_id,
                email,
                display_name,
                face_concept,
                wanted_hook,
                notes,
                account_user_id,
                status,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
            """,
            (
                community_id,
                email,
                display_name,
                face_concept,
                wanted_hook,
                notes,
                account_user_id,
                now,
                now,
            ),
        )
        access_request = self.get_community_access_request(community_id, _last_id(cursor))
        self.create_community_access_request_event(
            community_id,
            access_request.id,
            event_type="submitted",
            from_status=None,
            to_status="pending",
        )
        return access_request

    def get_community_access_request(
        self,
        community_id: int,
        request_id: int,
    ) -> CommunityAccessRequest:
        row = self._community_access_request_row(
            "WHERE community_id = ? AND id = ?",
            (community_id, request_id),
        )
        if row is None:
            raise LookupError(f"access request not found in community {community_id}: {request_id}")
        return _community_access_request_from_row(row)

    def find_open_community_access_request(
        self,
        community_id: int,
        *,
        email: str,
    ) -> CommunityAccessRequest | None:
        row = self._community_access_request_row(
            """
            WHERE community_id = ?
              AND lower(email) = lower(?)
              AND status IN ('pending', 'reviewed', 'invited')
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (community_id, email),
        )
        return None if row is None else _community_access_request_from_row(row)

    def find_community_access_request_by_invitation(
        self,
        community_id: int,
        invitation_id: int,
    ) -> CommunityAccessRequest | None:
        row = self._community_access_request_row(
            "WHERE community_id = ? AND invitation_id = ?",
            (community_id, invitation_id),
        )
        return None if row is None else _community_access_request_from_row(row)

    def link_community_access_request_account_user(
        self,
        community_id: int,
        request_id: int,
        account_user_id: int,
    ) -> CommunityAccessRequest:
        access_request = self.get_community_access_request(community_id, request_id)
        self.get_user(account_user_id)
        if access_request.account_user_id is not None:
            if access_request.account_user_id != account_user_id:
                raise PermissionError("access request is already linked to another account")
            return access_request
        with self.transaction():
            self.connection.execute(
                """
                UPDATE community_access_requests
                SET account_user_id = ?,
                    updated_at = ?
                WHERE community_id = ? AND id = ?
                """,
                (account_user_id, _utc_now(), community_id, request_id),
            )
            self.create_community_access_request_event(
                community_id,
                request_id,
                event_type="account_linked",
                from_status=access_request.status,
                to_status=access_request.status,
            )
        return self.get_community_access_request(community_id, request_id)

    def update_community_access_request_status(
        self,
        community_id: int,
        request_id: int,
        *,
        status: str,
        invitation_id: int | None = None,
    ) -> CommunityAccessRequest:
        if status not in ACCESS_REQUEST_TRANSITIONS:
            allowed = ", ".join(ACCESS_REQUEST_TRANSITIONS)
            raise ValueError(f"access request status must be one of: {allowed}")
        access_request = self.get_community_access_request(community_id, request_id)
        if access_request.status not in ACCESS_REQUEST_TRANSITIONS:
            raise ValueError(f"access request has unsupported status: {access_request.status}")
        if status == access_request.status and (
            invitation_id is None or invitation_id == access_request.invitation_id
        ):
            return access_request
        replacing_invitation = (
            status == "invited"
            and status == access_request.status
            and invitation_id is not None
            and invitation_id != access_request.invitation_id
        )
        if (
            not replacing_invitation
            and status not in ACCESS_REQUEST_TRANSITIONS[access_request.status]
        ):
            raise ValueError(f"cannot move access request from {access_request.status} to {status}")
        if status == "invited" and invitation_id is None and access_request.invitation_id is None:
            raise ValueError("invited access requests require an invitation")
        if invitation_id is not None:
            invitation = self.get_community_invitation(community_id, invitation_id)
            invitation_id = invitation.id
        self.connection.execute(
            """
            UPDATE community_access_requests
            SET status = ?,
                invitation_id = COALESCE(?, invitation_id),
                updated_at = ?
            WHERE community_id = ? AND id = ?
            """,
            (status, invitation_id, _utc_now(), community_id, request_id),
        )
        self._commit()
        return self.get_community_access_request(community_id, request_id)

    def create_community_access_request_event(
        self,
        community_id: int,
        request_id: int,
        *,
        event_type: str,
        from_status: str | None,
        to_status: str,
        actor_membership_id: int | None = None,
        invitation_id: int | None = None,
    ) -> CommunityAccessRequestEvent:
        if event_type not in ACCESS_REQUEST_EVENT_TYPES:
            raise ValueError("access request event type is not supported")
        access_request = self.get_community_access_request(community_id, request_id)
        if actor_membership_id is not None:
            self.get_membership(community_id, actor_membership_id)
        if invitation_id is not None:
            invitation = self.get_community_invitation(community_id, invitation_id)
            invitation_id = invitation.id
        cursor = self.connection.execute(
            """
            INSERT INTO community_access_request_events (
                community_id,
                access_request_id,
                actor_membership_id,
                event_type,
                from_status,
                to_status,
                invitation_id,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                community_id,
                access_request.id,
                actor_membership_id,
                event_type,
                from_status,
                to_status,
                invitation_id,
                _utc_now(),
            ),
        )
        self._commit()
        return self.get_community_access_request_event(community_id, _last_id(cursor))

    def get_community_access_request_event(
        self,
        community_id: int,
        event_id: int,
    ) -> CommunityAccessRequestEvent:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                access_request_id,
                actor_membership_id,
                event_type,
                from_status,
                to_status,
                invitation_id,
                created_at
            FROM community_access_request_events
            WHERE community_id = ? AND id = ?
            """,
            (community_id, event_id),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"access request event not found in community {community_id}: {event_id}"
            )
        return _community_access_request_event_from_row(row)

    def list_community_access_request_events(
        self,
        community_id: int,
        request_id: int,
    ) -> list[CommunityAccessRequestEvent]:
        self.get_community_access_request(community_id, request_id)
        rows = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                access_request_id,
                actor_membership_id,
                event_type,
                from_status,
                to_status,
                invitation_id,
                created_at
            FROM community_access_request_events
            WHERE community_id = ? AND access_request_id = ?
            ORDER BY created_at ASC, id ASC
            """,
            (community_id, request_id),
        ).fetchall()
        return [_community_access_request_event_from_row(row) for row in rows]

    def list_community_access_requests(
        self,
        community_id: int,
        *,
        status: str | None = None,
    ) -> list[CommunityAccessRequest]:
        if status is None:
            rows = self.connection.execute(
                self._community_access_request_select()
                + """
                WHERE community_id = ?
                ORDER BY created_at DESC, id DESC
                """,
                (community_id,),
            ).fetchall()
        else:
            rows = self.connection.execute(
                self._community_access_request_select()
                + """
                WHERE community_id = ? AND status = ?
                ORDER BY created_at DESC, id DESC
                """,
                (community_id, status),
            ).fetchall()
        return [_community_access_request_from_row(row) for row in rows]

    def _community_access_request_row(
        self,
        where_clause: str,
        parameters: tuple[object, ...],
    ) -> sqlite3.Row | None:
        return self.connection.execute(
            f"{self._community_access_request_select()} {where_clause}",
            parameters,
        ).fetchone()

    def _community_access_request_select(self) -> str:
        return """
            SELECT
                id,
                community_id,
                email,
                display_name,
                face_concept,
                wanted_hook,
                notes,
                account_user_id,
                invitation_id,
                status,
                created_at,
                updated_at
            FROM community_access_requests
        """

    def _community_invitation_row(
        self,
        where_clause: str,
        parameters: tuple[object, ...],
    ) -> sqlite3.Row | None:
        return self.connection.execute(
            f"{self._community_invitation_select()} {where_clause}",
            parameters,
        ).fetchone()

    def _community_invitation_select(self) -> str:
        return """
            SELECT
                id,
                community_id,
                email,
                role_id,
                invited_by_membership_id,
                token_hash,
                status,
                expires_at,
                accepted_user_id,
                accepted_membership_id,
                created_at,
                accepted_at,
                revoked_at
            FROM community_invitations
        """

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

    def list_memberships_by_ids(
        self,
        community_id: int,
        membership_ids: list[int],
    ) -> dict[int, CommunityMembership]:
        if not membership_ids:
            return {}
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
              AND id IN (SELECT value FROM json_each(?))
            """,
            (community_id, json.dumps(membership_ids)),
        ).fetchall()
        return {int(row["id"]): _membership_from_row(row) for row in rows}

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

    def list_memberships_for_user(self, user_id: int) -> list[CommunityMembership]:
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
            WHERE user_id = ?
            ORDER BY community_id, display_name, username, id
            """,
            (user_id,),
        ).fetchall()
        return [_membership_from_row(row) for row in rows]

    def list_membership_role_integrity_issues(self) -> list[MembershipRoleIntegrityIssue]:
        rows = self.connection.execute(
            """
            SELECT
                membership.community_id,
                membership.id AS membership_id,
                membership.role_id
            FROM community_memberships AS membership
            LEFT JOIN roles AS role
                ON role.id = membership.role_id
                AND role.community_id = membership.community_id
            WHERE role.id IS NULL
            ORDER BY membership.community_id, membership.id
            """
        ).fetchall()
        return [
            MembershipRoleIntegrityIssue(
                community_id=row["community_id"],
                membership_id=row["membership_id"],
                role_id=row["role_id"],
            )
            for row in rows
        ]

    def list_session_identity_integrity_issues(self) -> list[SessionIdentityIntegrityIssue]:
        rows = self.connection.execute(
            """
            SELECT
                session.id AS session_id,
                session.user_id,
                session.selected_community_id,
                session.selected_membership_id,
                membership.id AS membership_id,
                membership.community_id AS membership_community_id,
                membership.user_id AS membership_user_id,
                membership.is_active AS membership_is_active
            FROM user_sessions AS session
            LEFT JOIN community_memberships AS membership
                ON membership.id = session.selected_membership_id
            WHERE session.selected_membership_id IS NOT NULL
                AND (
                    membership.id IS NULL
                    OR membership.community_id != session.selected_community_id
                    OR membership.user_id != session.user_id
                    OR membership.is_active = 0
                )
            ORDER BY session.id
            """
        ).fetchall()
        return [
            SessionIdentityIntegrityIssue(
                session_id=row["session_id"],
                user_id=row["user_id"],
                selected_community_id=row["selected_community_id"],
                selected_membership_id=row["selected_membership_id"],
                reason=_session_identity_integrity_reason(row),
            )
            for row in rows
        ]

    def list_tenant_pair_integrity_issues(self) -> list[TenantPairIntegrityIssue]:
        rows = self.connection.execute(
            """
            SELECT table_name, row_id, community_id, reason
            FROM (
                SELECT
                    'communities' AS table_name,
                    community.id AS row_id,
                    community.id AS community_id,
                    CASE
                        WHEN theme.id IS NULL
                            AND community.default_theme_id IS NOT NULL
                            THEN 'community default theme belongs to another community'
                        WHEN facet_group.id IS NULL
                            AND community.identity_accent_facet_group_id IS NOT NULL
                            THEN 'community identity accent facet group belongs to another community'
                        ELSE 'community tenant pair is invalid'
                    END AS reason
                FROM communities AS community
                LEFT JOIN themes AS theme
                    ON theme.id = community.default_theme_id
                    AND theme.community_id = community.id
                LEFT JOIN facet_groups AS facet_group
                    ON facet_group.id = community.identity_accent_facet_group_id
                    AND facet_group.community_id = community.id
                WHERE (
                        community.default_theme_id IS NOT NULL
                        AND theme.id IS NULL
                    )
                    OR (
                        community.identity_accent_facet_group_id IS NOT NULL
                        AND facet_group.id IS NULL
                    )

                UNION ALL

                SELECT
                    'boards' AS table_name,
                    board.id AS row_id,
                    board.community_id,
                    CASE
                        WHEN board.parent_board_id = board.id THEN 'board cannot be its own parent'
                        WHEN parent.id IS NULL
                            AND board.parent_board_id IS NOT NULL
                            THEN 'board parent belongs to another community'
                        ELSE 'board tenant pair is invalid'
                    END AS reason
                FROM boards AS board
                LEFT JOIN boards AS parent
                    ON parent.id = board.parent_board_id
                    AND parent.community_id = board.community_id
                WHERE board.parent_board_id IS NOT NULL
                    AND (
                        board.parent_board_id = board.id
                        OR parent.id IS NULL
                    )

                UNION ALL

                SELECT
                    'community_memberships' AS table_name,
                    membership.id AS row_id,
                    membership.community_id,
                    CASE
                        WHEN role.id IS NULL THEN 'membership role belongs to another community'
                        WHEN default_character.id IS NULL
                            AND membership.default_character_id IS NOT NULL
                            THEN 'membership default face belongs to another community'
                        WHEN default_character.membership_id != membership.id
                            THEN 'membership default face does not belong to membership'
                        ELSE 'membership tenant pair is invalid'
                    END AS reason
                FROM community_memberships AS membership
                LEFT JOIN roles AS role
                    ON role.id = membership.role_id
                    AND role.community_id = membership.community_id
                LEFT JOIN characters AS default_character
                    ON default_character.id = membership.default_character_id
                    AND default_character.community_id = membership.community_id
                WHERE role.id IS NULL
                    OR (
                        membership.default_character_id IS NOT NULL
                        AND (
                            default_character.id IS NULL
                            OR default_character.membership_id != membership.id
                        )
                    )

                UNION ALL

                SELECT
                    'characters' AS table_name,
                    character.id AS row_id,
                    character.community_id,
                    CASE
                        WHEN membership.id IS NULL THEN 'character membership belongs to another community'
                        ELSE 'character tenant pair is invalid'
                    END AS reason
                FROM characters AS character
                LEFT JOIN community_memberships AS membership
                    ON membership.id = character.membership_id
                    AND membership.community_id = character.community_id
                WHERE membership.id IS NULL

                UNION ALL

                SELECT
                    'command_submissions' AS table_name,
                    command_submission.id AS row_id,
                    command_submission.community_id,
                    CASE
                        WHEN membership.id IS NULL
                            THEN 'command submission membership belongs to another community'
                        ELSE 'command submission tenant pair is invalid'
                    END AS reason
                FROM command_submissions AS command_submission
                LEFT JOIN community_memberships AS membership
                    ON membership.id = command_submission.membership_id
                    AND membership.community_id = command_submission.community_id
                WHERE membership.id IS NULL

                UNION ALL

                SELECT
                    'threads' AS table_name,
                    thread.id AS row_id,
                    thread.community_id,
                    CASE
                        WHEN board.id IS NULL THEN 'thread board belongs to another community'
                        WHEN membership.id IS NULL THEN 'thread author membership belongs to another community'
                        WHEN character.id IS NULL THEN 'thread author character does not match community and membership'
                        ELSE 'thread tenant pair is invalid'
                    END AS reason
                FROM threads AS thread
                LEFT JOIN boards AS board
                    ON board.id = thread.board_id
                    AND board.community_id = thread.community_id
                LEFT JOIN community_memberships AS membership
                    ON membership.id = thread.author_membership_id
                    AND membership.community_id = thread.community_id
                LEFT JOIN characters AS character
                    ON character.id = thread.author_character_id
                    AND character.community_id = thread.community_id
                    AND character.membership_id = thread.author_membership_id
                WHERE board.id IS NULL
                    OR membership.id IS NULL
                    OR character.id IS NULL

                UNION ALL

                SELECT
                    'community_invitations' AS table_name,
                    invitation.id AS row_id,
                    invitation.community_id,
                    CASE
                        WHEN role.id IS NULL THEN 'community invitation role belongs to another community'
                        WHEN invited_by.id IS NULL THEN 'community invitation invited-by membership belongs to another community'
                        WHEN accepted_membership.id IS NULL
                            AND invitation.accepted_membership_id IS NOT NULL
                            THEN 'community invitation accepted membership belongs to another community'
                        WHEN accepted_membership.user_id != invitation.accepted_user_id
                            AND invitation.accepted_membership_id IS NOT NULL
                            AND invitation.accepted_user_id IS NOT NULL
                            THEN 'community invitation accepted membership does not match accepted user'
                        ELSE 'community invitation tenant pair is invalid'
                    END AS reason
                FROM community_invitations AS invitation
                LEFT JOIN roles AS role
                    ON role.id = invitation.role_id
                    AND role.community_id = invitation.community_id
                LEFT JOIN community_memberships AS invited_by
                    ON invited_by.id = invitation.invited_by_membership_id
                    AND invited_by.community_id = invitation.community_id
                LEFT JOIN community_memberships AS accepted_membership
                    ON accepted_membership.id = invitation.accepted_membership_id
                    AND accepted_membership.community_id = invitation.community_id
                WHERE role.id IS NULL
                    OR invited_by.id IS NULL
                    OR (
                        invitation.accepted_membership_id IS NOT NULL
                        AND accepted_membership.id IS NULL
                    )
                    OR (
                        invitation.accepted_membership_id IS NOT NULL
                        AND invitation.accepted_user_id IS NOT NULL
                        AND accepted_membership.user_id != invitation.accepted_user_id
                    )

                UNION ALL

                SELECT
                    'community_access_requests' AS table_name,
                    request.id AS row_id,
                    request.community_id,
                    CASE
                        WHEN invitation.id IS NULL
                            AND request.invitation_id IS NOT NULL
                            THEN 'community access request invitation belongs to another community'
                        ELSE 'community access request tenant pair is invalid'
                    END AS reason
                FROM community_access_requests AS request
                LEFT JOIN community_invitations AS invitation
                    ON invitation.id = request.invitation_id
                    AND invitation.community_id = request.community_id
                WHERE request.invitation_id IS NOT NULL
                    AND invitation.id IS NULL

                UNION ALL

                SELECT
                    'community_access_request_events' AS table_name,
                    event.id AS row_id,
                    event.community_id,
                    CASE
                        WHEN request.id IS NULL THEN 'community access request event request belongs to another community'
                        WHEN actor.id IS NULL
                            AND event.actor_membership_id IS NOT NULL
                            THEN 'community access request event actor membership belongs to another community'
                        WHEN invitation.id IS NULL
                            AND event.invitation_id IS NOT NULL
                            THEN 'community access request event invitation belongs to another community'
                        ELSE 'community access request event tenant pair is invalid'
                    END AS reason
                FROM community_access_request_events AS event
                LEFT JOIN community_access_requests AS request
                    ON request.id = event.access_request_id
                    AND request.community_id = event.community_id
                LEFT JOIN community_memberships AS actor
                    ON actor.id = event.actor_membership_id
                    AND actor.community_id = event.community_id
                LEFT JOIN community_invitations AS invitation
                    ON invitation.id = event.invitation_id
                    AND invitation.community_id = event.community_id
                WHERE request.id IS NULL
                    OR (
                        event.actor_membership_id IS NOT NULL
                        AND actor.id IS NULL
                    )
                    OR (
                        event.invitation_id IS NOT NULL
                        AND invitation.id IS NULL
                    )

                UNION ALL

                SELECT
                    'community_gateway_slots' AS table_name,
                    slot.id AS row_id,
                    slot.community_id,
                    CASE
                        WHEN slot.slot_type = 'scene_hub' AND board.id IS NULL
                            THEN 'community gateway slot scene hub board belongs to another community'
                        WHEN slot.slot_type = 'wanted_hook' AND wanted.id IS NULL
                            THEN 'community gateway slot wanted hook belongs to another community'
                        WHEN slot.slot_type = 'guidebook_material' AND material.id IS NULL
                            THEN 'community gateway slot guidebook material belongs to another community'
                        ELSE 'community gateway slot tenant pair is invalid'
                    END AS reason
                FROM community_gateway_slots AS slot
                LEFT JOIN boards AS board
                    ON board.id = slot.target_id
                    AND board.community_id = slot.community_id
                    AND slot.slot_type = 'scene_hub'
                LEFT JOIN wanted_ads AS wanted
                    ON wanted.id = slot.target_id
                    AND wanted.community_id = slot.community_id
                    AND slot.slot_type = 'wanted_hook'
                LEFT JOIN materials AS material
                    ON material.id = slot.target_id
                    AND material.community_id = slot.community_id
                    AND slot.slot_type = 'guidebook_material'
                WHERE (
                        slot.slot_type = 'scene_hub'
                        AND board.id IS NULL
                    )
                    OR (
                        slot.slot_type = 'wanted_hook'
                        AND wanted.id IS NULL
                    )
                    OR (
                        slot.slot_type = 'guidebook_material'
                        AND material.id IS NULL
                    )

                UNION ALL

                SELECT
                    'community_discovery_profiles' AS table_name,
                    profile.community_id AS row_id,
                    profile.community_id,
                    CASE
                        WHEN material.id IS NULL
                            AND profile.featured_event_material_id IS NOT NULL
                            THEN 'community discovery profile featured event belongs to another community'
                        ELSE 'community discovery profile tenant pair is invalid'
                    END AS reason
                FROM community_discovery_profiles AS profile
                LEFT JOIN materials AS material
                    ON material.id = profile.featured_event_material_id
                    AND material.community_id = profile.community_id
                WHERE profile.featured_event_material_id IS NOT NULL
                    AND material.id IS NULL

                UNION ALL

                SELECT
                    'applications' AS table_name,
                    application.id AS row_id,
                    application.community_id,
                    CASE
                        WHEN membership.id IS NULL THEN 'application membership belongs to another community'
                        WHEN character.id IS NULL THEN 'application character does not match community and membership'
                        ELSE 'application tenant pair is invalid'
                    END AS reason
                FROM applications AS application
                LEFT JOIN community_memberships AS membership
                    ON membership.id = application.membership_id
                    AND membership.community_id = application.community_id
                LEFT JOIN characters AS character
                    ON character.id = application.character_id
                    AND character.community_id = application.community_id
                    AND character.membership_id = application.membership_id
                WHERE membership.id IS NULL
                    OR character.id IS NULL

                UNION ALL

                SELECT
                    'application_events' AS table_name,
                    event.id AS row_id,
                    event.community_id,
                    CASE
                        WHEN application.id IS NULL THEN 'application event application belongs to another community'
                        WHEN membership.id IS NULL THEN 'application event actor membership belongs to another community'
                        WHEN character.id IS NULL
                            AND event.actor_character_id IS NOT NULL
                            THEN 'application event actor character does not match community and membership'
                        ELSE 'application event tenant pair is invalid'
                    END AS reason
                FROM application_events AS event
                LEFT JOIN applications AS application
                    ON application.id = event.application_id
                    AND application.community_id = event.community_id
                LEFT JOIN community_memberships AS membership
                    ON membership.id = event.actor_membership_id
                    AND membership.community_id = event.community_id
                LEFT JOIN characters AS character
                    ON character.id = event.actor_character_id
                    AND character.community_id = event.community_id
                    AND character.membership_id = event.actor_membership_id
                WHERE application.id IS NULL
                    OR membership.id IS NULL
                    OR (
                        event.actor_character_id IS NOT NULL
                        AND character.id IS NULL
                    )

                UNION ALL

                SELECT
                    'application_template_fields' AS table_name,
                    field.id AS row_id,
                    field.community_id,
                    CASE
                        WHEN claim_type.id IS NULL
                            AND field.maps_to_claim_type_id IS NOT NULL
                            THEN 'application template field mapped claim type belongs to another community'
                        ELSE 'application template field tenant pair is invalid'
                    END AS reason
                FROM application_template_fields AS field
                LEFT JOIN claim_types AS claim_type
                    ON claim_type.id = field.maps_to_claim_type_id
                    AND claim_type.community_id = field.community_id
                WHERE field.maps_to_claim_type_id IS NOT NULL
                    AND claim_type.id IS NULL

                UNION ALL

                SELECT
                    'application_field_values' AS table_name,
                    value.id AS row_id,
                    value.community_id,
                    CASE
                        WHEN application.id IS NULL THEN 'application field value application belongs to another community'
                        WHEN field.id IS NULL THEN 'application field value field belongs to another community'
                        ELSE 'application field value tenant pair is invalid'
                    END AS reason
                FROM application_field_values AS value
                LEFT JOIN applications AS application
                    ON application.id = value.application_id
                    AND application.community_id = value.community_id
                LEFT JOIN application_template_fields AS field
                    ON field.id = value.field_id
                    AND field.community_id = value.community_id
                WHERE application.id IS NULL
                    OR field.id IS NULL

                UNION ALL

                SELECT
                    'character_claims' AS table_name,
                    claim.id AS row_id,
                    claim.community_id,
                    CASE
                        WHEN claim_type.id IS NULL THEN 'character claim type belongs to another community'
                        WHEN character.id IS NULL
                            AND claim.character_id IS NOT NULL
                            THEN 'character claim character belongs to another community'
                        WHEN application.id IS NULL
                            AND claim.application_id IS NOT NULL
                            THEN 'character claim application belongs to another community'
                        WHEN reserve.id IS NULL
                            AND claim.source_reserve_id IS NOT NULL
                            THEN 'character claim source reserve belongs to another community'
                        ELSE 'character claim tenant pair is invalid'
                    END AS reason
                FROM character_claims AS claim
                LEFT JOIN claim_types AS claim_type
                    ON claim_type.id = claim.claim_type_id
                    AND claim_type.community_id = claim.community_id
                LEFT JOIN characters AS character
                    ON character.id = claim.character_id
                    AND character.community_id = claim.community_id
                LEFT JOIN applications AS application
                    ON application.id = claim.application_id
                    AND application.community_id = claim.community_id
                LEFT JOIN character_reserves AS reserve
                    ON reserve.id = claim.source_reserve_id
                    AND reserve.community_id = claim.community_id
                WHERE claim_type.id IS NULL
                    OR (
                        claim.character_id IS NOT NULL
                        AND character.id IS NULL
                    )
                    OR (
                        claim.application_id IS NOT NULL
                        AND application.id IS NULL
                    )
                    OR (
                        claim.source_reserve_id IS NOT NULL
                        AND reserve.id IS NULL
                    )

                UNION ALL

                SELECT
                    'character_reserves' AS table_name,
                    reserve.id AS row_id,
                    reserve.community_id,
                    CASE
                        WHEN membership.id IS NULL THEN 'character reserve membership belongs to another community'
                        WHEN character.id IS NULL THEN 'character reserve character does not match community and membership'
                        WHEN wanted_ad.id IS NULL
                            AND reserve.wanted_ad_id IS NOT NULL
                            THEN 'character reserve wanted hook belongs to another community'
                        WHEN interest.id IS NULL
                            AND reserve.wanted_ad_interest_id IS NOT NULL
                            THEN 'character reserve wanted interest does not match reserve owner'
                        ELSE 'character reserve tenant pair is invalid'
                    END AS reason
                FROM character_reserves AS reserve
                LEFT JOIN community_memberships AS membership
                    ON membership.id = reserve.membership_id
                    AND membership.community_id = reserve.community_id
                LEFT JOIN characters AS character
                    ON character.id = reserve.character_id
                    AND character.community_id = reserve.community_id
                    AND character.membership_id = reserve.membership_id
                LEFT JOIN wanted_ads AS wanted_ad
                    ON wanted_ad.id = reserve.wanted_ad_id
                    AND wanted_ad.community_id = reserve.community_id
                LEFT JOIN wanted_ad_interests AS interest
                    ON interest.id = reserve.wanted_ad_interest_id
                    AND interest.community_id = reserve.community_id
                    AND interest.membership_id = reserve.membership_id
                    AND interest.character_id = reserve.character_id
                    AND (
                        reserve.wanted_ad_id IS NULL
                        OR interest.wanted_ad_id = reserve.wanted_ad_id
                    )
                WHERE membership.id IS NULL
                    OR character.id IS NULL
                    OR (
                        reserve.wanted_ad_id IS NOT NULL
                        AND wanted_ad.id IS NULL
                    )
                    OR (
                        reserve.wanted_ad_interest_id IS NOT NULL
                        AND interest.id IS NULL
                    )

                UNION ALL

                SELECT
                    'wanted_ads' AS table_name,
                    wanted.id AS row_id,
                    wanted.community_id,
                    CASE
                        WHEN membership.id IS NULL THEN 'wanted hook creator membership belongs to another community'
                        WHEN character.id IS NULL
                            AND wanted.creator_character_id IS NOT NULL
                            THEN 'wanted hook creator character does not match community and membership'
                        WHEN material.id IS NULL
                            AND wanted.related_material_id IS NOT NULL
                            THEN 'wanted hook related material belongs to another community'
                        ELSE 'wanted hook tenant pair is invalid'
                    END AS reason
                FROM wanted_ads AS wanted
                LEFT JOIN community_memberships AS membership
                    ON membership.id = wanted.creator_membership_id
                    AND membership.community_id = wanted.community_id
                LEFT JOIN characters AS character
                    ON character.id = wanted.creator_character_id
                    AND character.community_id = wanted.community_id
                    AND character.membership_id = wanted.creator_membership_id
                LEFT JOIN materials AS material
                    ON material.id = wanted.related_material_id
                    AND material.community_id = wanted.community_id
                WHERE membership.id IS NULL
                    OR (
                        wanted.creator_character_id IS NOT NULL
                        AND character.id IS NULL
                    )
                    OR (
                        wanted.related_material_id IS NOT NULL
                        AND material.id IS NULL
                    )

                UNION ALL

                SELECT
                    'wanted_ad_interests' AS table_name,
                    interest.id AS row_id,
                    interest.community_id,
                    CASE
                        WHEN wanted.id IS NULL THEN 'wanted interest wanted hook belongs to another community'
                        WHEN membership.id IS NULL THEN 'wanted interest membership belongs to another community'
                        WHEN character.id IS NULL
                            AND interest.character_id IS NOT NULL
                            THEN 'wanted interest character does not match community and membership'
                        ELSE 'wanted interest tenant pair is invalid'
                    END AS reason
                FROM wanted_ad_interests AS interest
                LEFT JOIN wanted_ads AS wanted
                    ON wanted.id = interest.wanted_ad_id
                    AND wanted.community_id = interest.community_id
                LEFT JOIN community_memberships AS membership
                    ON membership.id = interest.membership_id
                    AND membership.community_id = interest.community_id
                LEFT JOIN characters AS character
                    ON character.id = interest.character_id
                    AND character.community_id = interest.community_id
                    AND character.membership_id = interest.membership_id
                WHERE wanted.id IS NULL
                    OR membership.id IS NULL
                    OR (
                        interest.character_id IS NOT NULL
                        AND character.id IS NULL
                    )

                UNION ALL

                SELECT
                    'wanted_ad_related_characters' AS table_name,
                    related.id AS row_id,
                    related.community_id,
                    CASE
                        WHEN wanted.id IS NULL THEN 'wanted related face wanted hook belongs to another community'
                        WHEN character.id IS NULL THEN 'wanted related face character belongs to another community'
                        ELSE 'wanted related face tenant pair is invalid'
                    END AS reason
                FROM wanted_ad_related_characters AS related
                LEFT JOIN wanted_ads AS wanted
                    ON wanted.id = related.wanted_ad_id
                    AND wanted.community_id = related.community_id
                LEFT JOIN characters AS character
                    ON character.id = related.character_id
                    AND character.community_id = related.community_id
                WHERE wanted.id IS NULL
                    OR character.id IS NULL

                UNION ALL

                SELECT
                    'character_plot_hooks' AS table_name,
                    hook.id AS row_id,
                    hook.community_id,
                    CASE
                        WHEN membership.id IS NULL THEN 'plot hook author membership belongs to another community'
                        WHEN character.id IS NULL THEN 'plot hook character does not match community and membership'
                        WHEN material.id IS NULL
                            AND hook.related_material_id IS NOT NULL
                            THEN 'plot hook related material belongs to another community'
                        ELSE 'plot hook tenant pair is invalid'
                    END AS reason
                FROM character_plot_hooks AS hook
                LEFT JOIN community_memberships AS membership
                    ON membership.id = hook.author_membership_id
                    AND membership.community_id = hook.community_id
                LEFT JOIN characters AS character
                    ON character.id = hook.character_id
                    AND character.community_id = hook.community_id
                    AND character.membership_id = hook.author_membership_id
                LEFT JOIN materials AS material
                    ON material.id = hook.related_material_id
                    AND material.community_id = hook.community_id
                WHERE membership.id IS NULL
                    OR character.id IS NULL
                    OR (
                        hook.related_material_id IS NOT NULL
                        AND material.id IS NULL
                    )

                UNION ALL

                SELECT
                    'character_plot_hook_interests' AS table_name,
                    interest.id AS row_id,
                    interest.community_id,
                    CASE
                        WHEN hook.id IS NULL THEN 'plot hook interest hook belongs to another community'
                        WHEN membership.id IS NULL THEN 'plot hook interest membership belongs to another community'
                        WHEN character.id IS NULL THEN 'plot hook interest character does not match community and membership'
                        ELSE 'plot hook interest tenant pair is invalid'
                    END AS reason
                FROM character_plot_hook_interests AS interest
                LEFT JOIN character_plot_hooks AS hook
                    ON hook.id = interest.plot_hook_id
                    AND hook.community_id = interest.community_id
                LEFT JOIN community_memberships AS membership
                    ON membership.id = interest.membership_id
                    AND membership.community_id = interest.community_id
                LEFT JOIN characters AS character
                    ON character.id = interest.character_id
                    AND character.community_id = interest.community_id
                    AND character.membership_id = interest.membership_id
                WHERE hook.id IS NULL
                    OR membership.id IS NULL
                    OR character.id IS NULL

                UNION ALL

                SELECT
                    'character_facets' AS table_name,
                    assignment.id AS row_id,
                    assignment.community_id,
                    CASE
                        WHEN character.id IS NULL THEN 'character facet character belongs to another community'
                        WHEN facet.id IS NULL THEN 'character facet facet belongs to another community'
                        ELSE 'character facet tenant pair is invalid'
                    END AS reason
                FROM character_facets AS assignment
                LEFT JOIN characters AS character
                    ON character.id = assignment.character_id
                    AND character.community_id = assignment.community_id
                LEFT JOIN facets AS facet
                    ON facet.id = assignment.facet_id
                    AND facet.community_id = assignment.community_id
                WHERE character.id IS NULL
                    OR facet.id IS NULL

                UNION ALL

                SELECT
                    'board_facets' AS table_name,
                    assignment.id AS row_id,
                    assignment.community_id,
                    CASE
                        WHEN board.id IS NULL THEN 'board facet board belongs to another community'
                        WHEN facet.id IS NULL THEN 'board facet facet belongs to another community'
                        ELSE 'board facet tenant pair is invalid'
                    END AS reason
                FROM board_facets AS assignment
                LEFT JOIN boards AS board
                    ON board.id = assignment.board_id
                    AND board.community_id = assignment.community_id
                LEFT JOIN facets AS facet
                    ON facet.id = assignment.facet_id
                    AND facet.community_id = assignment.community_id
                WHERE board.id IS NULL
                    OR facet.id IS NULL

                UNION ALL

                SELECT
                    'material_facets' AS table_name,
                    assignment.id AS row_id,
                    assignment.community_id,
                    CASE
                        WHEN material.id IS NULL THEN 'material facet material belongs to another community'
                        WHEN facet.id IS NULL THEN 'material facet facet belongs to another community'
                        ELSE 'material facet tenant pair is invalid'
                    END AS reason
                FROM material_facets AS assignment
                LEFT JOIN materials AS material
                    ON material.id = assignment.material_id
                    AND material.community_id = assignment.community_id
                LEFT JOIN facets AS facet
                    ON facet.id = assignment.facet_id
                    AND facet.community_id = assignment.community_id
                WHERE material.id IS NULL
                    OR facet.id IS NULL

                UNION ALL

                SELECT
                    'wanted_ad_facets' AS table_name,
                    assignment.id AS row_id,
                    assignment.community_id,
                    CASE
                        WHEN wanted.id IS NULL THEN 'wanted hook facet wanted hook belongs to another community'
                        WHEN facet.id IS NULL THEN 'wanted hook facet facet belongs to another community'
                        ELSE 'wanted hook facet tenant pair is invalid'
                    END AS reason
                FROM wanted_ad_facets AS assignment
                LEFT JOIN wanted_ads AS wanted
                    ON wanted.id = assignment.wanted_ad_id
                    AND wanted.community_id = assignment.community_id
                LEFT JOIN facets AS facet
                    ON facet.id = assignment.facet_id
                    AND facet.community_id = assignment.community_id
                WHERE wanted.id IS NULL
                    OR facet.id IS NULL

                UNION ALL

                SELECT
                    'character_plot_hook_facets' AS table_name,
                    assignment.id AS row_id,
                    assignment.community_id,
                    CASE
                        WHEN hook.id IS NULL THEN 'plot hook facet hook belongs to another community'
                        WHEN facet.id IS NULL THEN 'plot hook facet facet belongs to another community'
                        ELSE 'plot hook facet tenant pair is invalid'
                    END AS reason
                FROM character_plot_hook_facets AS assignment
                LEFT JOIN character_plot_hooks AS hook
                    ON hook.id = assignment.plot_hook_id
                    AND hook.community_id = assignment.community_id
                LEFT JOIN facets AS facet
                    ON facet.id = assignment.facet_id
                    AND facet.community_id = assignment.community_id
                WHERE hook.id IS NULL
                    OR facet.id IS NULL

                UNION ALL

                SELECT
                    'thread_facets' AS table_name,
                    assignment.id AS row_id,
                    assignment.community_id,
                    CASE
                        WHEN thread.id IS NULL THEN 'thread facet thread belongs to another community'
                        WHEN facet.id IS NULL THEN 'thread facet facet belongs to another community'
                        ELSE 'thread facet tenant pair is invalid'
                    END AS reason
                FROM thread_facets AS assignment
                LEFT JOIN threads AS thread
                    ON thread.id = assignment.thread_id
                    AND thread.community_id = assignment.community_id
                LEFT JOIN facets AS facet
                    ON facet.id = assignment.facet_id
                    AND facet.community_id = assignment.community_id
                WHERE thread.id IS NULL
                    OR facet.id IS NULL

                UNION ALL

                SELECT
                    'posts' AS table_name,
                    post.id AS row_id,
                    post.community_id,
                    CASE
                        WHEN thread.id IS NULL THEN 'post thread belongs to another community'
                        WHEN membership.id IS NULL THEN 'post author membership belongs to another community'
                        WHEN character.id IS NULL THEN 'post author character does not match community and membership'
                        ELSE 'post tenant pair is invalid'
                    END AS reason
                FROM posts AS post
                LEFT JOIN threads AS thread
                    ON thread.id = post.thread_id
                    AND thread.community_id = post.community_id
                LEFT JOIN community_memberships AS membership
                    ON membership.id = post.author_membership_id
                    AND membership.community_id = post.community_id
                LEFT JOIN characters AS character
                    ON character.id = post.author_character_id
                    AND character.community_id = post.community_id
                    AND character.membership_id = post.author_membership_id
                WHERE thread.id IS NULL
                    OR membership.id IS NULL
                    OR character.id IS NULL

                UNION ALL

                SELECT
                    'post_revisions' AS table_name,
                    revision.id AS row_id,
                    revision.community_id,
                    CASE
                        WHEN post.id IS NULL THEN 'post revision post belongs to another community'
                        WHEN membership.id IS NULL THEN 'post revision editor membership belongs to another community'
                        ELSE 'post revision tenant pair is invalid'
                    END AS reason
                FROM post_revisions AS revision
                LEFT JOIN posts AS post
                    ON post.id = revision.post_id
                    AND post.community_id = revision.community_id
                LEFT JOIN community_memberships AS membership
                    ON membership.id = revision.editor_membership_id
                    AND membership.community_id = revision.community_id
                WHERE post.id IS NULL
                    OR membership.id IS NULL

                UNION ALL

                SELECT
                    'realm_interaction_questions' AS table_name,
                    question.id AS row_id,
                    question.community_id,
                    CASE
                        WHEN interaction.id IS NULL
                            THEN 'realm interaction question interaction belongs to another community'
                        ELSE 'realm interaction question tenant pair is invalid'
                    END AS reason
                FROM realm_interaction_questions AS question
                LEFT JOIN realm_interactions AS interaction
                    ON interaction.id = question.interaction_id
                    AND interaction.community_id = question.community_id
                WHERE interaction.id IS NULL

                UNION ALL

                SELECT
                    'realm_interaction_options' AS table_name,
                    option.id AS row_id,
                    option.community_id,
                    CASE
                        WHEN question.id IS NULL
                            THEN 'realm interaction option question belongs to another community'
                        ELSE 'realm interaction option tenant pair is invalid'
                    END AS reason
                FROM realm_interaction_options AS option
                LEFT JOIN realm_interaction_questions AS question
                    ON question.id = option.question_id
                    AND question.community_id = option.community_id
                WHERE question.id IS NULL

                UNION ALL

                SELECT
                    'realm_interaction_responses' AS table_name,
                    response.id AS row_id,
                    response.community_id,
                    CASE
                        WHEN interaction.id IS NULL THEN 'realm interaction response interaction belongs to another community'
                        WHEN membership.id IS NULL THEN 'realm interaction response membership belongs to another community'
                        WHEN character.id IS NULL
                            AND response.character_id IS NOT NULL
                            THEN 'realm interaction response character does not match community and membership'
                        ELSE 'realm interaction response tenant pair is invalid'
                    END AS reason
                FROM realm_interaction_responses AS response
                LEFT JOIN realm_interactions AS interaction
                    ON interaction.id = response.interaction_id
                    AND interaction.community_id = response.community_id
                LEFT JOIN community_memberships AS membership
                    ON membership.id = response.membership_id
                    AND membership.community_id = response.community_id
                LEFT JOIN characters AS character
                    ON character.id = response.character_id
                    AND character.community_id = response.community_id
                    AND character.membership_id = response.membership_id
                WHERE interaction.id IS NULL
                    OR membership.id IS NULL
                    OR (
                        response.character_id IS NOT NULL
                        AND character.id IS NULL
                    )

                UNION ALL

                SELECT
                    'realm_interaction_answers' AS table_name,
                    answer.id AS row_id,
                    answer.community_id,
                    CASE
                        WHEN response.id IS NULL THEN 'realm interaction answer response belongs to another community'
                        WHEN question.id IS NULL THEN 'realm interaction answer question does not match response interaction'
                        WHEN option.id IS NULL
                            AND answer.option_id IS NOT NULL
                            THEN 'realm interaction answer option does not match question'
                        ELSE 'realm interaction answer tenant pair is invalid'
                    END AS reason
                FROM realm_interaction_answers AS answer
                LEFT JOIN realm_interaction_responses AS response
                    ON response.id = answer.response_id
                    AND response.community_id = answer.community_id
                LEFT JOIN realm_interaction_questions AS question
                    ON question.id = answer.question_id
                    AND question.community_id = answer.community_id
                    AND question.interaction_id = response.interaction_id
                LEFT JOIN realm_interaction_options AS option
                    ON option.id = answer.option_id
                    AND option.community_id = answer.community_id
                    AND option.question_id = answer.question_id
                WHERE response.id IS NULL
                    OR question.id IS NULL
                    OR (
                        answer.option_id IS NOT NULL
                        AND option.id IS NULL
                    )

                UNION ALL

                SELECT
                    'reactions' AS table_name,
                    reaction.id AS row_id,
                    reaction.community_id,
                    CASE
                        WHEN post.id IS NULL THEN 'reaction post belongs to another community'
                        WHEN membership.id IS NULL THEN 'reaction membership belongs to another community'
                        ELSE 'reaction tenant pair is invalid'
                    END AS reason
                FROM reactions AS reaction
                LEFT JOIN posts AS post
                    ON post.id = reaction.post_id
                    AND post.community_id = reaction.community_id
                LEFT JOIN community_memberships AS membership
                    ON membership.id = reaction.membership_id
                    AND membership.community_id = reaction.community_id
                WHERE post.id IS NULL
                    OR membership.id IS NULL

                UNION ALL

                SELECT
                    'thread_participants' AS table_name,
                    participant.id AS row_id,
                    participant.community_id,
                    CASE
                        WHEN thread.id IS NULL THEN 'thread participant thread belongs to another community'
                        WHEN character.id IS NULL THEN 'thread participant character belongs to another community'
                        ELSE 'thread participant tenant pair is invalid'
                    END AS reason
                FROM thread_participants AS participant
                LEFT JOIN threads AS thread
                    ON thread.id = participant.thread_id
                    AND thread.community_id = participant.community_id
                LEFT JOIN characters AS character
                    ON character.id = participant.character_id
                    AND character.community_id = participant.community_id
                WHERE thread.id IS NULL
                    OR character.id IS NULL

                UNION ALL

                SELECT
                    'thread_reads' AS table_name,
                    read.id AS row_id,
                    read.community_id,
                    CASE
                        WHEN thread.id IS NULL THEN 'thread read thread belongs to another community'
                        WHEN membership.id IS NULL THEN 'thread read membership belongs to another community'
                        ELSE 'thread read tenant pair is invalid'
                    END AS reason
                FROM thread_reads AS read
                LEFT JOIN threads AS thread
                    ON thread.id = read.thread_id
                    AND thread.community_id = read.community_id
                LEFT JOIN community_memberships AS membership
                    ON membership.id = read.membership_id
                    AND membership.community_id = read.community_id
                WHERE thread.id IS NULL
                    OR membership.id IS NULL

                UNION ALL

                SELECT
                    'thread_watches' AS table_name,
                    watch.id AS row_id,
                    watch.community_id,
                    CASE
                        WHEN thread.id IS NULL THEN 'thread watch thread belongs to another community'
                        WHEN membership.id IS NULL THEN 'thread watch membership belongs to another community'
                        ELSE 'thread watch tenant pair is invalid'
                    END AS reason
                FROM thread_watches AS watch
                LEFT JOIN threads AS thread
                    ON thread.id = watch.thread_id
                    AND thread.community_id = watch.community_id
                LEFT JOIN community_memberships AS membership
                    ON membership.id = watch.membership_id
                    AND membership.community_id = watch.community_id
                WHERE thread.id IS NULL
                    OR membership.id IS NULL

                UNION ALL

                SELECT
                    'notifications' AS table_name,
                    notification.id AS row_id,
                    notification.community_id,
                    CASE
                        WHEN recipient.id IS NULL THEN 'notification recipient belongs to another community'
                        WHEN actor.id IS NULL THEN 'notification actor belongs to another community'
                        WHEN actor_character.id IS NULL
                            AND notification.actor_character_id IS NOT NULL
                            THEN 'notification actor character does not match community and membership'
                        WHEN target_character.id IS NULL
                            AND notification.character_id IS NOT NULL
                            THEN 'notification character target belongs to another community'
                        ELSE 'notification tenant pair is invalid'
                    END AS reason
                FROM notifications AS notification
                LEFT JOIN community_memberships AS recipient
                    ON recipient.id = notification.membership_id
                    AND recipient.community_id = notification.community_id
                LEFT JOIN community_memberships AS actor
                    ON actor.id = notification.actor_membership_id
                    AND actor.community_id = notification.community_id
                LEFT JOIN characters AS actor_character
                    ON actor_character.id = notification.actor_character_id
                    AND actor_character.community_id = notification.community_id
                    AND actor_character.membership_id = notification.actor_membership_id
                LEFT JOIN characters AS target_character
                    ON target_character.id = notification.character_id
                    AND target_character.community_id = notification.community_id
                WHERE recipient.id IS NULL
                    OR actor.id IS NULL
                    OR (
                        notification.actor_character_id IS NOT NULL
                        AND actor_character.id IS NULL
                    )
                    OR (
                        notification.character_id IS NOT NULL
                        AND target_character.id IS NULL
                    )

                UNION ALL

                SELECT
                    'plotting_rooms' AS table_name,
                    room.id AS row_id,
                    room.community_id,
                    CASE
                        WHEN owner.id IS NULL
                            THEN 'plotting room owner membership belongs to another community'
                        WHEN (
                                room.source_plot_hook_id IS NULL
                                AND room.source_plot_hook_interest_id IS NULL
                                AND room.source_wanted_ad_id IS NULL
                                AND room.source_wanted_ad_interest_id IS NULL
                            )
                            THEN 'plotting room source is missing'
                        WHEN (
                                (
                                    room.source_plot_hook_id IS NOT NULL
                                    OR room.source_plot_hook_interest_id IS NOT NULL
                                )
                                AND (
                                    room.source_wanted_ad_id IS NOT NULL
                                    OR room.source_wanted_ad_interest_id IS NOT NULL
                                )
                            )
                            THEN 'plotting room has multiple source families'
                        WHEN (
                                room.source_plot_hook_id IS NULL
                                AND room.source_plot_hook_interest_id IS NOT NULL
                            )
                            OR (
                                room.source_plot_hook_id IS NOT NULL
                                AND room.source_plot_hook_interest_id IS NULL
                            )
                            THEN 'plotting room plot source is incomplete'
                        WHEN (
                                room.source_wanted_ad_id IS NULL
                                AND room.source_wanted_ad_interest_id IS NOT NULL
                            )
                            OR (
                                room.source_wanted_ad_id IS NOT NULL
                                AND room.source_wanted_ad_interest_id IS NULL
                            )
                            THEN 'plotting room wanted source is incomplete'
                        WHEN hook.id IS NULL
                            AND room.source_plot_hook_id IS NOT NULL
                            THEN 'plotting room source plot hook belongs to another community'
                        WHEN hook_interest.id IS NULL
                            AND room.source_plot_hook_interest_id IS NOT NULL
                            THEN 'plotting room plot hook interest does not match source hook'
                        WHEN wanted.id IS NULL
                            AND room.source_wanted_ad_id IS NOT NULL
                            THEN 'plotting room source wanted hook belongs to another community'
                        WHEN wanted_interest.id IS NULL
                            AND room.source_wanted_ad_interest_id IS NOT NULL
                            THEN 'plotting room wanted interest does not match source wanted hook'
                        WHEN target_board.id IS NULL
                            AND room.target_board_id IS NOT NULL
                            THEN 'plotting room target board belongs to another community'
                        WHEN target_thread.id IS NULL
                            AND room.target_thread_id IS NOT NULL
                            THEN 'plotting room target thread belongs to another community'
                        ELSE 'plotting room tenant pair is invalid'
                    END AS reason
                FROM plotting_rooms AS room
                LEFT JOIN community_memberships AS owner
                    ON owner.id = room.owner_membership_id
                    AND owner.community_id = room.community_id
                LEFT JOIN character_plot_hooks AS hook
                    ON hook.id = room.source_plot_hook_id
                    AND hook.community_id = room.community_id
                LEFT JOIN character_plot_hook_interests AS hook_interest
                    ON hook_interest.id = room.source_plot_hook_interest_id
                    AND hook_interest.community_id = room.community_id
                    AND hook_interest.plot_hook_id = room.source_plot_hook_id
                LEFT JOIN wanted_ads AS wanted
                    ON wanted.id = room.source_wanted_ad_id
                    AND wanted.community_id = room.community_id
                LEFT JOIN wanted_ad_interests AS wanted_interest
                    ON wanted_interest.id = room.source_wanted_ad_interest_id
                    AND wanted_interest.community_id = room.community_id
                    AND wanted_interest.wanted_ad_id = room.source_wanted_ad_id
                LEFT JOIN boards AS target_board
                    ON target_board.id = room.target_board_id
                    AND target_board.community_id = room.community_id
                LEFT JOIN threads AS target_thread
                    ON target_thread.id = room.target_thread_id
                    AND target_thread.community_id = room.community_id
                WHERE owner.id IS NULL
                    OR (
                        room.source_plot_hook_id IS NULL
                        AND room.source_plot_hook_interest_id IS NULL
                        AND room.source_wanted_ad_id IS NULL
                        AND room.source_wanted_ad_interest_id IS NULL
                    )
                    OR (
                        (
                            room.source_plot_hook_id IS NOT NULL
                            OR room.source_plot_hook_interest_id IS NOT NULL
                        )
                        AND (
                            room.source_wanted_ad_id IS NOT NULL
                            OR room.source_wanted_ad_interest_id IS NOT NULL
                        )
                    )
                    OR (
                        room.source_plot_hook_id IS NULL
                        AND room.source_plot_hook_interest_id IS NOT NULL
                    )
                    OR (
                        room.source_plot_hook_id IS NOT NULL
                        AND room.source_plot_hook_interest_id IS NULL
                    )
                    OR (
                        room.source_wanted_ad_id IS NULL
                        AND room.source_wanted_ad_interest_id IS NOT NULL
                    )
                    OR (
                        room.source_wanted_ad_id IS NOT NULL
                        AND room.source_wanted_ad_interest_id IS NULL
                    )
                    OR (
                        room.source_plot_hook_id IS NOT NULL
                        AND hook.id IS NULL
                    )
                    OR (
                        room.source_plot_hook_interest_id IS NOT NULL
                        AND hook_interest.id IS NULL
                    )
                    OR (
                        room.source_wanted_ad_id IS NOT NULL
                        AND wanted.id IS NULL
                    )
                    OR (
                        room.source_wanted_ad_interest_id IS NOT NULL
                        AND wanted_interest.id IS NULL
                    )
                    OR (
                        room.target_board_id IS NOT NULL
                        AND target_board.id IS NULL
                    )
                    OR (
                        room.target_thread_id IS NOT NULL
                        AND target_thread.id IS NULL
                    )

                UNION ALL

                SELECT
                    'plotting_room_participants' AS table_name,
                    participant.id AS row_id,
                    participant.community_id,
                    CASE
                        WHEN room.id IS NULL THEN 'plotting room participant room belongs to another community'
                        WHEN membership.id IS NULL THEN 'plotting room participant membership belongs to another community'
                        WHEN character.id IS NULL
                            AND participant.character_id IS NOT NULL
                            THEN 'plotting room participant character does not match community and membership'
                        ELSE 'plotting room participant tenant pair is invalid'
                    END AS reason
                FROM plotting_room_participants AS participant
                LEFT JOIN plotting_rooms AS room
                    ON room.id = participant.plotting_room_id
                    AND room.community_id = participant.community_id
                LEFT JOIN community_memberships AS membership
                    ON membership.id = participant.membership_id
                    AND membership.community_id = participant.community_id
                LEFT JOIN characters AS character
                    ON character.id = participant.character_id
                    AND character.community_id = participant.community_id
                    AND character.membership_id = participant.membership_id
                WHERE room.id IS NULL
                    OR membership.id IS NULL
                    OR (
                        participant.character_id IS NOT NULL
                        AND character.id IS NULL
                    )

                UNION ALL

                SELECT
                    'plotting_room_messages' AS table_name,
                    message.id AS row_id,
                    message.community_id,
                    CASE
                        WHEN room.id IS NULL THEN 'plotting room message room belongs to another community'
                        WHEN membership.id IS NULL THEN 'plotting room message author membership belongs to another community'
                        WHEN character.id IS NULL
                            AND message.author_character_id IS NOT NULL
                            THEN 'plotting room message author character does not match community and membership'
                        ELSE 'plotting room message tenant pair is invalid'
                    END AS reason
                FROM plotting_room_messages AS message
                LEFT JOIN plotting_rooms AS room
                    ON room.id = message.plotting_room_id
                    AND room.community_id = message.community_id
                LEFT JOIN community_memberships AS membership
                    ON membership.id = message.author_membership_id
                    AND membership.community_id = message.community_id
                LEFT JOIN characters AS character
                    ON character.id = message.author_character_id
                    AND character.community_id = message.community_id
                    AND character.membership_id = message.author_membership_id
                WHERE room.id IS NULL
                    OR membership.id IS NULL
                    OR (
                        message.author_character_id IS NOT NULL
                        AND character.id IS NULL
                    )
            )
            ORDER BY table_name, community_id, row_id
            """
        ).fetchall()
        return [
            TenantPairIntegrityIssue(
                table_name=row["table_name"],
                row_id=row["row_id"],
                community_id=row["community_id"],
                reason=row["reason"],
            )
            for row in rows
        ]

    def get_command_submission(
        self,
        community_id: int,
        membership_id: int,
        *,
        command_key: str,
        token: str,
    ) -> CommandSubmission | None:
        row = self.connection.execute(
            """
            SELECT id, community_id, membership_id, command_key, result_path
            FROM command_submissions
            WHERE community_id = ?
                AND membership_id = ?
                AND command_key = ?
                AND token_hash = ?
            """,
            (community_id, membership_id, command_key, _command_token_hash(token)),
        ).fetchone()
        if row is None:
            return None
        return CommandSubmission(
            id=row["id"],
            community_id=row["community_id"],
            membership_id=row["membership_id"],
            command_key=row["command_key"],
            result_path=row["result_path"],
        )

    def reserve_command_submission(
        self,
        community_id: int,
        membership_id: int,
        *,
        command_key: str,
        token: str,
    ) -> bool:
        self.get_membership(community_id, membership_id)
        try:
            self.connection.execute(
                """
                INSERT INTO command_submissions (
                    community_id,
                    membership_id,
                    command_key,
                    token_hash,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    community_id,
                    membership_id,
                    command_key,
                    _command_token_hash(token),
                    _utc_now(),
                ),
            )
        except sqlite3.IntegrityError:
            return False
        self._commit()
        return True

    def complete_command_submission(
        self,
        community_id: int,
        membership_id: int,
        *,
        command_key: str,
        token: str,
        result_path: str,
    ) -> None:
        self.connection.execute(
            """
            UPDATE command_submissions
            SET result_path = ?,
                completed_at = ?
            WHERE community_id = ?
                AND membership_id = ?
                AND command_key = ?
                AND token_hash = ?
            """,
            (
                result_path,
                _utc_now(),
                community_id,
                membership_id,
                command_key,
                _command_token_hash(token),
            ),
        )
        self._commit()

    def discard_command_submission(
        self,
        community_id: int,
        membership_id: int,
        *,
        command_key: str,
        token: str,
    ) -> bool:
        self.get_membership(community_id, membership_id)
        cursor = self.connection.execute(
            """
            DELETE FROM command_submissions
            WHERE community_id = ?
                AND membership_id = ?
                AND command_key = ?
                AND token_hash = ?
                AND result_path IS NULL
            """,
            (community_id, membership_id, command_key, _command_token_hash(token)),
        )
        self._commit()
        return cursor.rowcount > 0

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


def _session_identity_integrity_reason(row: Any) -> str:
    if row["membership_id"] is None:
        return "selected membership is missing"
    if row["membership_community_id"] != row["selected_community_id"]:
        return "selected membership belongs to another community"
    if row["membership_user_id"] != row["user_id"]:
        return "selected membership belongs to another user"
    if row["membership_is_active"] == 0:
        return "selected membership is inactive"
    return "selected identity is invalid"


def _command_token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
