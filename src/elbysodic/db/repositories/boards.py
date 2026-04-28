"""Board and location repository methods."""

from __future__ import annotations

from elbysodic.db.repositories.base import (
    TenantBoundaryError,
    _last_id,
    _next_update_stamp,
    _utc_now,
)
from elbysodic.db.repositories.notifications import NotificationRepositoryMixin
from elbysodic.db.repositories.rows import _board_from_row
from elbysodic.domain.boards import normalize_board_kind
from elbysodic.domain.models import Board


class BoardRepositoryMixin(NotificationRepositoryMixin):
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
        navigation_order: int | None = None,
        show_in_navigation: bool = True,
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
                navigation_order,
                show_in_navigation,
                is_private,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                sort_order if navigation_order is None else navigation_order,
                int(show_in_navigation),
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
        navigation_order: int | None = None,
        show_in_navigation: bool | None = None,
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
                navigation_order = ?,
                show_in_navigation = ?,
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
                board.navigation_order if navigation_order is None else navigation_order,
                int(board.show_in_navigation if show_in_navigation is None else show_in_navigation),
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
                navigation_order,
                show_in_navigation,
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
                navigation_order,
                show_in_navigation,
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
                navigation_order,
                show_in_navigation,
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
                    navigation_order,
                    show_in_navigation,
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
                    navigation_order,
                    show_in_navigation,
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
