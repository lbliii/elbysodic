"""Facet repository methods for world lenses and discovery."""

from __future__ import annotations

import json
from collections import defaultdict

from elbysodic.db.repositories.base import _last_id, _utc_now
from elbysodic.db.repositories.boards import BoardRepositoryMixin
from elbysodic.db.repositories.rows import _facet_from_row, _facet_group_from_row
from elbysodic.domain.models import CharacterPlotHook, Facet, FacetGroup, Material, Thread, WantedAd


class FacetRepositoryMixin(BoardRepositoryMixin):
    def get_thread(self, community_id: int, thread_id: int) -> Thread:
        raise NotImplementedError

    def get_material(self, community_id: int, material_id: int) -> Material:
        raise NotImplementedError

    def get_wanted_ad(self, community_id: int, wanted_ad_id: int) -> WantedAd:
        raise NotImplementedError

    def get_character_plot_hook(
        self,
        community_id: int,
        plot_hook_id: int,
    ) -> CharacterPlotHook:
        raise NotImplementedError

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
        self._commit()
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

    def list_facet_groups_for_communities(
        self,
        community_ids: list[int],
    ) -> dict[int, list[FacetGroup]]:
        if not community_ids:
            return {}
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
            WHERE community_id IN (SELECT value FROM json_each(?))
            ORDER BY community_id, sort_order, name, id
            """,
            (json.dumps(community_ids),),
        ).fetchall()
        groups_by_community: dict[int, list[FacetGroup]] = defaultdict(list)
        for row in rows:
            group = _facet_group_from_row(row)
            groups_by_community[group.community_id].append(group)
        return dict(groups_by_community)

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
        self._commit()
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

    def list_board_facets_for_boards(
        self,
        community_id: int,
        board_ids: list[int],
    ) -> dict[int, list[Facet]]:
        if not board_ids:
            return {}
        rows = self.connection.execute(
            """
            SELECT
                board_facets.board_id,
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
            FROM board_facets
            JOIN facets
              ON facets.community_id = board_facets.community_id
             AND facets.id = board_facets.facet_id
            JOIN facet_groups
              ON facet_groups.community_id = facets.community_id
             AND facet_groups.id = facets.facet_group_id
            WHERE board_facets.community_id = ?
              AND board_facets.board_id IN (SELECT value FROM json_each(?))
            ORDER BY board_facets.board_id,
                     facet_groups.sort_order,
                     facet_groups.name,
                     facets.sort_order,
                     facets.name
            """,
            (community_id, json.dumps(board_ids)),
        ).fetchall()
        facets_by_board: dict[int, list[Facet]] = defaultdict(list)
        for row in rows:
            facets_by_board[int(row["board_id"])].append(_facet_from_row(row))
        return dict(facets_by_board)

    def list_thread_facets(self, community_id: int, thread_id: int) -> list[Facet]:
        self.get_thread(community_id, thread_id)
        return self._list_facets_for_assignment(
            "thread_facets",
            "thread_id",
            community_id,
            thread_id,
        )

    def list_thread_facets_for_threads(
        self,
        community_id: int,
        thread_ids: list[int],
    ) -> dict[int, list[Facet]]:
        if not thread_ids:
            return {}
        rows = self.connection.execute(
            """
            SELECT
                thread_facets.thread_id,
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
            FROM thread_facets
            JOIN facets
              ON facets.community_id = thread_facets.community_id
             AND facets.id = thread_facets.facet_id
            JOIN facet_groups
              ON facet_groups.community_id = facets.community_id
             AND facet_groups.id = facets.facet_group_id
            WHERE thread_facets.community_id = ?
              AND thread_facets.thread_id IN (SELECT value FROM json_each(?))
            ORDER BY thread_facets.thread_id,
                     facet_groups.sort_order,
                     facet_groups.name,
                     facets.sort_order,
                     facets.name
            """,
            (community_id, json.dumps(thread_ids)),
        ).fetchall()
        facets_by_thread: dict[int, list[Facet]] = defaultdict(list)
        for row in rows:
            facets_by_thread[int(row["thread_id"])].append(_facet_from_row(row))
        return dict(facets_by_thread)

    def list_material_facets(self, community_id: int, material_id: int) -> list[Facet]:
        self.get_material(community_id, material_id)
        return self._list_facets_for_assignment(
            "material_facets",
            "material_id",
            community_id,
            material_id,
        )

    def list_material_facets_for_materials(
        self,
        community_ids: list[int],
        material_ids: list[int],
    ) -> dict[tuple[int, int], list[Facet]]:
        if not community_ids or not material_ids:
            return {}
        rows = self.connection.execute(
            """
            SELECT
                material_facets.community_id AS assignment_community_id,
                material_facets.material_id,
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
            FROM material_facets
            JOIN facets
              ON facets.community_id = material_facets.community_id
             AND facets.id = material_facets.facet_id
            JOIN facet_groups
              ON facet_groups.community_id = facets.community_id
             AND facet_groups.id = facets.facet_group_id
            WHERE material_facets.community_id IN (SELECT value FROM json_each(?))
              AND material_facets.material_id IN (SELECT value FROM json_each(?))
            ORDER BY material_facets.community_id,
                     material_facets.material_id,
                     facet_groups.sort_order,
                     facet_groups.name,
                     facets.sort_order,
                     facets.name
            """,
            (json.dumps(community_ids), json.dumps(material_ids)),
        ).fetchall()
        facets_by_material: dict[tuple[int, int], list[Facet]] = defaultdict(list)
        for row in rows:
            key = (int(row["assignment_community_id"]), int(row["material_id"]))
            facets_by_material[key].append(_facet_from_row(row))
        return dict(facets_by_material)

    def list_wanted_ad_facets(self, community_id: int, wanted_ad_id: int) -> list[Facet]:
        self.get_wanted_ad(community_id, wanted_ad_id)
        return self._list_facets_for_assignment(
            "wanted_ad_facets",
            "wanted_ad_id",
            community_id,
            wanted_ad_id,
        )

    def list_character_plot_hook_facets(
        self,
        community_id: int,
        plot_hook_id: int,
    ) -> list[Facet]:
        self.get_character_plot_hook(community_id, plot_hook_id)
        return self._list_facets_for_assignment(
            "character_plot_hook_facets",
            "plot_hook_id",
            community_id,
            plot_hook_id,
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

    def list_character_plot_hook_ids_for_facets(
        self,
        community_id: int,
        facet_ids: list[int],
    ) -> set[int]:
        return self._list_entity_ids_for_facets(
            "character_plot_hook_facets",
            "plot_hook_id",
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

    def assign_character_plot_hook_facet(
        self,
        community_id: int,
        plot_hook_id: int,
        facet_id: int,
    ) -> None:
        self.get_character_plot_hook(community_id, plot_hook_id)
        self.get_facet(community_id, facet_id)
        self._assign_facet(
            "character_plot_hook_facets",
            "plot_hook_id",
            community_id,
            plot_hook_id,
            facet_id,
        )

    def set_character_plot_hook_facets(
        self,
        community_id: int,
        plot_hook_id: int,
        facet_ids: list[int],
    ) -> None:
        self.get_character_plot_hook(community_id, plot_hook_id)
        cleaned_facet_ids = list(dict.fromkeys(facet_ids))
        for facet_id in cleaned_facet_ids:
            self.get_facet(community_id, facet_id)
        self.connection.execute(
            """
            DELETE FROM character_plot_hook_facets
            WHERE community_id = ? AND plot_hook_id = ?
            """,
            (community_id, plot_hook_id),
        )
        for facet_id in cleaned_facet_ids:
            self._assign_facet(
                "character_plot_hook_facets",
                "plot_hook_id",
                community_id,
                plot_hook_id,
                facet_id,
            )
        if not cleaned_facet_ids:
            self._commit()

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
        self._commit()
