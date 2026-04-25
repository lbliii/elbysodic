"""Tenant-aware SQLite repository for forum-domain operations."""

from __future__ import annotations

from elbysodic.db.repositories.base import (
    TenantBoundaryError,
    _last_id,
    _next_update_stamp,
    _utc_now,
)
from elbysodic.db.repositories.notifications import NotificationRepositoryMixin
from elbysodic.db.repositories.rows import (
    _board_from_row,
    _character_from_row,
    _character_reserve_from_row,
    _facet_from_row,
    _facet_group_from_row,
    _material_from_row,
    _post_from_row,
    _post_revision_from_row,
    _thread_from_row,
    _thread_participant_from_row,
    _thread_watch_from_row,
    _wanted_ad_from_row,
    _wanted_ad_interest_from_row,
)
from elbysodic.domain.boards import normalize_board_kind
from elbysodic.domain.models import (
    Board,
    Character,
    CharacterReserve,
    Facet,
    FacetGroup,
    Material,
    Post,
    PostRevision,
    Thread,
    ThreadParticipant,
    ThreadWatch,
    WantedAd,
    WantedAdInterest,
)


class ForumRepository(
    NotificationRepositoryMixin,
):
    """Small repository layer that keeps community scope explicit."""

    def create_board(
        self,
        community_id: int,
        slug: str,
        name: str,
        description: str = "",
        *,
        parent_board_id: int | None = None,
        board_kind: str = "location",
        tagline: str = "",
        image_url: str | None = None,
        image_alt: str = "",
        sort_order: int = 0,
        is_private: bool = False,
    ) -> Board:
        if parent_board_id is not None:
            self.get_board(community_id, parent_board_id)
        normalized_board_kind = normalize_board_kind(board_kind)
        now = _utc_now()
        cursor = self.connection.execute(
            """
            INSERT INTO boards (
                community_id,
                parent_board_id,
                slug,
                name,
                board_kind,
                tagline,
                description,
                image_url,
                image_alt,
                sort_order,
                is_private,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                community_id,
                parent_board_id,
                slug,
                name,
                normalized_board_kind,
                tagline,
                description,
                image_url,
                image_alt,
                sort_order,
                int(is_private),
                now,
                now,
            ),
        )
        self.connection.commit()
        return self.get_board(community_id, _last_id(cursor))

    def update_board(
        self,
        community_id: int,
        board_id: int,
        *,
        name: str,
        description: str,
        sort_order: int,
        parent_board_id: int | None = None,
        board_kind: str = "location",
        tagline: str = "",
        image_url: str | None = None,
        image_alt: str = "",
        is_private: bool = False,
    ) -> Board:
        board = self.get_board(community_id, board_id)
        if parent_board_id is not None:
            parent = self.get_board(community_id, parent_board_id)
            if parent.id == board.id:
                raise TenantBoundaryError("board cannot be its own parent")
        normalized_board_kind = normalize_board_kind(board_kind)
        self.connection.execute(
            """
            UPDATE boards
            SET
                parent_board_id = ?,
                name = ?,
                board_kind = ?,
                tagline = ?,
                description = ?,
                image_url = ?,
                image_alt = ?,
                sort_order = ?,
                is_private = ?,
                updated_at = ?
            WHERE community_id = ? AND id = ?
            """,
            (
                parent_board_id,
                name,
                normalized_board_kind,
                tagline,
                description,
                image_url,
                image_alt,
                sort_order,
                int(is_private),
                _next_update_stamp(board.updated_at),
                community_id,
                board_id,
            ),
        )
        self.connection.commit()
        return self.get_board(community_id, board_id)

    def get_board(self, community_id: int, board_id: int) -> Board:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                parent_board_id,
                slug,
                name,
                board_kind,
                tagline,
                description,
                image_url,
                image_alt,
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
                parent_board_id,
                slug,
                name,
                board_kind,
                tagline,
                description,
                image_url,
                image_alt,
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
                parent_board_id,
                slug,
                name,
                board_kind,
                tagline,
                description,
                image_url,
                image_alt,
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

    def list_child_boards(self, community_id: int, parent_board_id: int | None) -> list[Board]:
        if parent_board_id is not None:
            self.get_board(community_id, parent_board_id)
        if parent_board_id is None:
            rows = self.connection.execute(
                """
                SELECT
                    id,
                    community_id,
                    parent_board_id,
                    slug,
                    name,
                    board_kind,
                    tagline,
                    description,
                    image_url,
                    image_alt,
                    sort_order,
                    is_private,
                    created_at,
                    updated_at
                FROM boards
                WHERE community_id = ? AND parent_board_id IS NULL
                ORDER BY sort_order, name
                """,
                (community_id,),
            ).fetchall()
        else:
            rows = self.connection.execute(
                """
                SELECT
                    id,
                    community_id,
                    parent_board_id,
                    slug,
                    name,
                    board_kind,
                    tagline,
                    description,
                    image_url,
                    image_alt,
                    sort_order,
                    is_private,
                    created_at,
                    updated_at
                FROM boards
                WHERE community_id = ? AND parent_board_id = ?
                ORDER BY sort_order, name
                """,
                (community_id, parent_board_id),
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

    def create_character_reserve(
        self,
        community_id: int,
        membership_id: int,
        character_id: int,
        title: str,
        *,
        wanted_ad_id: int | None = None,
        wanted_ad_interest_id: int | None = None,
        reserve_type: str = "wanted",
        notes: str = "",
        status: str = "active",
    ) -> CharacterReserve:
        self.get_membership(community_id, membership_id)
        character = self.get_character(community_id, character_id)
        if character.membership_id != membership_id:
            raise TenantBoundaryError(
                f"character {character_id} does not belong to membership {membership_id}"
            )
        if wanted_ad_id is not None:
            self.get_wanted_ad(community_id, wanted_ad_id)
        if wanted_ad_interest_id is not None:
            interest = self.get_wanted_ad_interest(community_id, wanted_ad_interest_id)
            if interest.membership_id != membership_id or interest.character_id != character_id:
                raise TenantBoundaryError(
                    f"wanted interest {wanted_ad_interest_id} does not belong to reserve owner"
                )
            if wanted_ad_id is not None and interest.wanted_ad_id != wanted_ad_id:
                raise TenantBoundaryError(
                    f"wanted interest {wanted_ad_interest_id} does not belong to wanted ad {wanted_ad_id}"
                )
        now = _utc_now()
        self.connection.execute(
            """
            INSERT OR IGNORE INTO character_reserves (
                community_id,
                membership_id,
                character_id,
                wanted_ad_id,
                wanted_ad_interest_id,
                reserve_type,
                title,
                notes,
                status,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                community_id,
                membership_id,
                character_id,
                wanted_ad_id,
                wanted_ad_interest_id,
                reserve_type,
                title,
                notes,
                status,
                now,
                now,
            ),
        )
        self.connection.commit()
        if wanted_ad_interest_id is not None:
            return self.get_character_reserve_for_wanted_interest(
                community_id,
                wanted_ad_interest_id,
            )
        row = self.connection.execute(
            """
            SELECT MAX(id) AS id
            FROM character_reserves
            WHERE community_id = ? AND membership_id = ? AND character_id = ?
            """,
            (community_id, membership_id, character_id),
        ).fetchone()
        return self.get_character_reserve(community_id, int(row["id"]))

    def get_character_reserve(
        self,
        community_id: int,
        reserve_id: int,
    ) -> CharacterReserve:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                membership_id,
                character_id,
                wanted_ad_id,
                wanted_ad_interest_id,
                reserve_type,
                title,
                notes,
                status,
                created_at,
                updated_at
            FROM character_reserves
            WHERE community_id = ? AND id = ?
            """,
            (community_id, reserve_id),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"character reserve not found in community {community_id}: {reserve_id}"
            )
        return _character_reserve_from_row(row)

    def get_character_reserve_for_wanted_interest(
        self,
        community_id: int,
        wanted_ad_interest_id: int,
    ) -> CharacterReserve:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                membership_id,
                character_id,
                wanted_ad_id,
                wanted_ad_interest_id,
                reserve_type,
                title,
                notes,
                status,
                created_at,
                updated_at
            FROM character_reserves
            WHERE community_id = ? AND wanted_ad_interest_id = ?
            """,
            (community_id, wanted_ad_interest_id),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"character reserve not found in community {community_id}: {wanted_ad_interest_id}"
            )
        return _character_reserve_from_row(row)

    def list_character_reserves(
        self,
        community_id: int,
        character_id: int,
        *,
        status: str | None = "active",
    ) -> list[CharacterReserve]:
        self.get_character(community_id, character_id)
        where = "WHERE community_id = ? AND character_id = ?"
        params: tuple[object, ...] = (community_id, character_id)
        if status is not None:
            where = f"{where} AND status = ?"
            params = (*params, status)
        rows = self.connection.execute(
            f"""
            SELECT
                id,
                community_id,
                membership_id,
                character_id,
                wanted_ad_id,
                wanted_ad_interest_id,
                reserve_type,
                title,
                notes,
                status,
                created_at,
                updated_at
            FROM character_reserves
            {where}
            ORDER BY created_at DESC, id DESC
            """,
            params,
        ).fetchall()
        return [_character_reserve_from_row(row) for row in rows]

    def list_character_reserves_for_wanted_ad(
        self,
        community_id: int,
        wanted_ad_id: int,
        *,
        status: str | None = "active",
    ) -> list[CharacterReserve]:
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
                membership_id,
                character_id,
                wanted_ad_id,
                wanted_ad_interest_id,
                reserve_type,
                title,
                notes,
                status,
                created_at,
                updated_at
            FROM character_reserves
            {where}
            ORDER BY created_at DESC, id DESC
            """,
            params,
        ).fetchall()
        return [_character_reserve_from_row(row) for row in rows]

    def list_character_reserves_for_community(
        self,
        community_id: int,
        *,
        status: str | None = "active",
    ) -> list[CharacterReserve]:
        self.get_community(community_id)
        where = "WHERE community_id = ?"
        params: tuple[object, ...] = (community_id,)
        if status is not None:
            where = f"{where} AND status = ?"
            params = (*params, status)
        rows = self.connection.execute(
            f"""
            SELECT
                id,
                community_id,
                membership_id,
                character_id,
                wanted_ad_id,
                wanted_ad_interest_id,
                reserve_type,
                title,
                notes,
                status,
                created_at,
                updated_at
            FROM character_reserves
            {where}
            ORDER BY updated_at DESC, created_at DESC, id DESC
            """,
            params,
        ).fetchall()
        return [_character_reserve_from_row(row) for row in rows]

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
                characters.application_status,
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
