"""Community, user, role, and membership repository methods."""

from __future__ import annotations

from elbysodic.db.repositories.base import RepositoryBase, _last_id, _utc_now
from elbysodic.db.repositories.rows import (
    _community_from_row,
    _community_theme_from_row,
    _membership_from_row,
    _role_from_row,
    _user_from_row,
    _user_session_from_row,
)
from elbysodic.domain.context import DEFAULT_COMMUNITY_ID, DEFAULT_COMMUNITY_SLUG
from elbysodic.domain.models import (
    Community,
    CommunityMembership,
    CommunityTheme,
    Role,
    User,
    UserSession,
)


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
        self._commit()
        return self.get_community(_last_id(cursor))

    def get_community(self, community_id: int) -> Community:
        row = self.connection.execute(
            """
            SELECT
                id,
                name,
                slug,
                host,
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

    def get_community_by_name(self, name: str) -> Community:
        row = self.connection.execute(
            """
            SELECT
                id,
                name,
                slug,
                host,
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
            WHERE lower(name) = lower(?)
            """,
            (name,),
        ).fetchone()
        if row is None:
            raise LookupError(f"community not found for name: {name}")
        return _community_from_row(row)

    def get_community_by_host(self, host: str) -> Community:
        row = self.connection.execute(
            """
            SELECT
                id,
                name,
                slug,
                host,
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

    def update_user_password(self, user_id: int, password_hash: str) -> User:
        self.get_user(user_id)
        self.connection.execute(
            """
            UPDATE users
            SET password_hash = ?
            WHERE id = ?
            """,
            (password_hash, user_id),
        )
        self._commit()
        return self.get_user(user_id)

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

    def update_role_admin(self, community_id: int, role_id: int, *, is_admin: bool) -> Role:
        self.get_role(community_id, role_id)
        self.connection.execute(
            """
            UPDATE roles
            SET is_admin = ?,
                updated_at = ?
            WHERE community_id = ? AND id = ?
            """,
            (int(is_admin), _utc_now(), community_id, role_id),
        )
        self._commit()
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

    def update_membership_role(
        self,
        community_id: int,
        membership_id: int,
        role_id: int,
    ) -> CommunityMembership:
        self.get_membership(community_id, membership_id)
        self.get_role(community_id, role_id)
        self.connection.execute(
            """
            UPDATE community_memberships
            SET role_id = ?
            WHERE community_id = ? AND id = ?
            """,
            (role_id, community_id, membership_id),
        )
        self._commit()
        return self.get_membership(community_id, membership_id)

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
