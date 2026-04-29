"""World material repository methods."""

from __future__ import annotations

from elbysodic.db.repositories.base import _last_id, _utc_now
from elbysodic.db.repositories.facets import FacetRepositoryMixin
from elbysodic.db.repositories.rows import _material_from_row
from elbysodic.domain.models import Material


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
        self.connection.commit()
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
