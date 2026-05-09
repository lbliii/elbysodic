"""World material repository methods."""

from __future__ import annotations

from elbysodic.db.repositories.base import _last_id, _utc_now
from elbysodic.db.repositories.facets import FacetRepositoryMixin
from elbysodic.db.repositories.rows import _community_from_row, _material_from_row
from elbysodic.domain.models import Community, Material
from elbysodic.domain.vocabulary import MATERIAL_TYPES


class MaterialRepositoryMixin(FacetRepositoryMixin):
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
        _require_material_type(material_type)
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
        self._commit()
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

    def list_published_material_communities_by_slug(self, slug: str) -> list[Community]:
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
                communities.world_hero_treatment,
                communities.world_hero_focal_point,
                communities.world_hero_overlay,
                communities.world_hero_height,
                communities.enabled_post_profile_variants,
                communities.enabled_post_accent_styles,
                communities.enabled_post_border_styles,
                communities.enabled_post_title_styles,
                communities.enabled_post_densities,
                communities.created_at,
                communities.updated_at
            FROM communities
            JOIN materials ON materials.community_id = communities.id
            WHERE materials.slug = ? AND materials.status = 'published'
            ORDER BY communities.name, communities.id
            """,
            (slug,),
        ).fetchall()
        return [_community_from_row(row) for row in rows]

    def update_material(
        self,
        community_id: int,
        material_id: int,
        *,
        title: str,
        material_type: str,
        summary: str,
        body: str,
        status: str = "published",
        sort_order: int = 0,
        is_featured: bool = False,
    ) -> Material:
        self.get_material(community_id, material_id)
        _require_material_type(material_type)
        self.connection.execute(
            """
            UPDATE materials
            SET
                title = ?,
                material_type = ?,
                summary = ?,
                body = ?,
                status = ?,
                sort_order = ?,
                is_featured = ?,
                updated_at = ?
            WHERE community_id = ? AND id = ?
            """,
            (
                title,
                material_type,
                summary,
                body,
                status,
                sort_order,
                int(is_featured),
                _utc_now(),
                community_id,
                material_id,
            ),
        )
        self._commit()
        return self.get_material(community_id, material_id)

    def list_materials(
        self,
        community_id: int,
        *,
        status: str | None = "published",
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


def _require_material_type(material_type: str) -> None:
    if material_type not in MATERIAL_TYPES:
        allowed = ", ".join(sorted(MATERIAL_TYPES))
        raise ValueError(f"material_type must be one of: {allowed}")
