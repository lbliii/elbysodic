"""Community, user, role, and membership repository methods."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from typing import Any, Protocol, cast

from elbysodic.db.repositories.base import RepositoryBase, _last_id, _utc_now
from elbysodic.db.repositories.rows import (
    _community_from_row,
    _community_invitation_from_row,
    _community_theme_from_row,
    _membership_from_row,
    _role_from_row,
    _user_from_row,
    _user_session_from_row,
)
from elbysodic.domain.context import DEFAULT_COMMUNITY_ID, DEFAULT_COMMUNITY_SLUG
from elbysodic.domain.models import (
    Community,
    CommunityInvitation,
    CommunityMembership,
    CommunityTheme,
    Role,
    User,
    UserSession,
)

COMMUNITY_LAUNCH_STATUSES = {"backstage", "invite-only", "public-preview"}


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

    def network_program_counts(self, community_ids: list[int]) -> dict[int, dict[str, int]]:
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
                ) AS claim_type_count
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
            SET revoked_at = COALESCE(revoked_at, ?)
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
    ) -> Role:
        now = _utc_now()
        cursor = self.connection.execute(
            """
            INSERT INTO roles (community_id, slug, name, is_admin, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (community_id, slug, name, int(is_admin), now, now),
        )
        self._commit()
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
