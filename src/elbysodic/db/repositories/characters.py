"""Character and application-status repository methods."""

from __future__ import annotations

from elbysodic.db.repositories.base import _last_id, _utc_now
from elbysodic.db.repositories.identity import IdentityRepositoryMixin
from elbysodic.db.repositories.rows import _character_from_row
from elbysodic.domain.models import Character, CommunityMembership


class CharacterRepositoryMixin(IdentityRepositoryMixin):
    def create_character(
        self,
        community_id: int,
        membership_id: int,
        slug: str,
        name: str,
        avatar_url: str | None = None,
        poster_url: str | None = None,
        poster_alt: str = "",
        tagline: str = "",
        accent_color: str = "",
        summary: str = "",
        post_profile_variant: str = "bio",
        *,
        application_status: str = "accepted",
        make_default: bool = False,
    ) -> Character:
        self.get_membership(community_id, membership_id)
        now = _utc_now()
        cursor = self.connection.execute(
            """
            INSERT INTO characters (
                community_id,
                membership_id,
                slug,
                name,
                avatar_url,
                poster_url,
                poster_alt,
                tagline,
                accent_color,
                summary,
                post_profile_variant,
                application_status,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                community_id,
                membership_id,
                slug,
                name,
                avatar_url,
                poster_url,
                poster_alt,
                tagline,
                accent_color,
                summary,
                post_profile_variant,
                application_status,
                now,
                now,
            ),
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
                poster_url,
                poster_alt,
                tagline,
                accent_color,
                summary,
                post_profile_variant,
                application_status,
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
                poster_url,
                poster_alt,
                tagline,
                accent_color,
                summary,
                post_profile_variant,
                application_status,
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
        poster_url: str | None = None,
        poster_alt: str = "",
        tagline: str = "",
        accent_color: str = "",
        summary: str = "",
        post_profile_variant: str = "bio",
    ) -> Character:
        self.get_character(community_id, character_id)
        self.connection.execute(
            """
            UPDATE characters
            SET
                slug = ?,
                name = ?,
                avatar_url = ?,
                poster_url = ?,
                poster_alt = ?,
                tagline = ?,
                accent_color = ?,
                summary = ?,
                post_profile_variant = ?,
                updated_at = ?
            WHERE community_id = ? AND id = ?
            """,
            (
                slug,
                name,
                avatar_url,
                poster_url,
                poster_alt,
                tagline,
                accent_color,
                summary,
                post_profile_variant,
                _utc_now(),
                community_id,
                character_id,
            ),
        )
        self.connection.commit()
        return self.get_character(community_id, character_id)

    def update_character_application_status(
        self,
        community_id: int,
        character_id: int,
        application_status: str,
    ) -> Character:
        self.get_character(community_id, character_id)
        self.connection.execute(
            """
            UPDATE characters
            SET application_status = ?, updated_at = ?
            WHERE community_id = ? AND id = ?
            """,
            (application_status, _utc_now(), community_id, character_id),
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
                poster_url,
                poster_alt,
                tagline,
                accent_color,
                summary,
                post_profile_variant,
                application_status,
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
                poster_url,
                poster_alt,
                tagline,
                accent_color,
                summary,
                post_profile_variant,
                application_status,
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
        fetch_limit = limit + len(excluded_ids) + 16
        rows = self.connection.execute(
            """
            SELECT
                characters.id,
                characters.community_id,
                characters.membership_id,
                characters.name,
                characters.slug,
                characters.avatar_url,
                characters.poster_url,
                characters.poster_alt,
                characters.tagline,
                characters.accent_color,
                characters.summary,
                characters.post_profile_variant,
                characters.application_status,
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
            (community_id, like, like, normalized, prefix, prefix, fetch_limit),
        ).fetchall()
        excluded_id_set = set(excluded_ids)
        return [
            _character_from_row(row) for row in rows if row["membership_id"] not in excluded_id_set
        ][:limit]

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
