"""Wanted hook and wanted interest repository methods."""

from __future__ import annotations

from elbysodic.db.repositories.base import TenantBoundaryError, _last_id, _utc_now
from elbysodic.db.repositories.materials import MaterialRepositoryMixin
from elbysodic.db.repositories.rows import (
    _character_from_row,
    _community_from_row,
    _wanted_ad_from_row,
    _wanted_ad_interest_from_row,
)
from elbysodic.domain.models import Character, Community, WantedAd, WantedAdInterest


class WantedRepositoryMixin(MaterialRepositoryMixin):
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

    def list_wanted_ad_communities_by_slug(self, slug: str) -> list[Community]:
        rows = self.connection.execute(
            """
            SELECT DISTINCT
                communities.id,
                communities.name,
                communities.slug,
                communities.host,
                communities.default_theme_id,
                communities.identity_accent_facet_group_id,
                communities.community_mark_url,
                communities.community_mark_alt,
                communities.world_hero_image_url,
                communities.world_hero_image_alt,
                communities.enabled_post_profile_variants,
                communities.enabled_post_accent_styles,
                communities.enabled_post_border_styles,
                communities.enabled_post_title_styles,
                communities.enabled_post_densities,
                communities.created_at,
                communities.updated_at
            FROM communities
            JOIN wanted_ads ON wanted_ads.community_id = communities.id
            WHERE wanted_ads.slug = ?
            ORDER BY communities.name, communities.id
            """,
            (slug,),
        ).fetchall()
        return [_community_from_row(row) for row in rows]

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
                characters.poster_url,
                characters.poster_alt,
                characters.tagline,
                characters.accent_color,
                characters.summary,
                characters.post_profile_variant,
                characters.post_accent_style,
                characters.post_border_style,
                characters.post_title_style,
                characters.post_density,
                characters.application_status,
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
        character_id: int | None = None,
        *,
        prospective_character_name: str = "",
        note: str = "",
        status: str = "interested",
    ) -> WantedAdInterest:
        self.get_wanted_ad(community_id, wanted_ad_id)
        self.get_membership(community_id, membership_id)
        if character_id is not None:
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
                prospective_character_name,
                note,
                status,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                community_id,
                wanted_ad_id,
                membership_id,
                character_id,
                prospective_character_name,
                note,
                status,
                now,
                now,
            ),
        )
        self.connection.commit()
        if character_id is not None:
            return self.get_wanted_ad_interest_for_character(
                community_id,
                wanted_ad_id,
                character_id,
            )
        return self.get_prospective_wanted_ad_interest_for_membership(
            community_id,
            wanted_ad_id,
            membership_id,
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
                prospective_character_name,
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
                prospective_character_name,
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

    def get_prospective_wanted_ad_interest_for_membership(
        self,
        community_id: int,
        wanted_ad_id: int,
        membership_id: int,
    ) -> WantedAdInterest:
        row = self.connection.execute(
            """
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
            WHERE community_id = ?
              AND wanted_ad_id = ?
              AND membership_id = ?
              AND character_id IS NULL
            """,
            (community_id, wanted_ad_id, membership_id),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"prospective wanted interest not found in community {community_id}: {wanted_ad_id}/{membership_id}"
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
                prospective_character_name,
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
