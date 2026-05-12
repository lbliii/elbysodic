"""Board and location repository methods."""

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
    _community_from_row,
    _sidebar_section_config_from_row,
)
from elbysodic.domain.boards import (
    BOARD_SIDEBAR_SECTION_REALMS,
    DEFAULT_SIDEBAR_SECTION_CONFIGS,
    normalize_board_kind,
    normalize_board_sidebar_section,
)
from elbysodic.domain.models import Board, Community, SidebarSectionConfig


class BoardRepositoryMixin(NotificationRepositoryMixin):
    def ensure_sidebar_section_defaults(self, community_id: int) -> None:
        self.get_community(community_id)
        now = _utc_now()
        for (
            realm,
            section_key,
            label,
            description,
            sort_order,
            show_label,
        ) in DEFAULT_SIDEBAR_SECTION_CONFIGS:
            self.connection.execute(
                """
                INSERT OR IGNORE INTO sidebar_sections (
                    community_id,
                    realm,
                    section_key,
                    label,
                    description,
                    sort_order,
                    show_label,
                    is_system,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (
                    community_id,
                    realm,
                    section_key,
                    label,
                    description,
                    sort_order,
                    int(show_label),
                    now,
                    now,
                ),
            )
        self._commit()

    def list_sidebar_sections(self, community_id: int) -> list[SidebarSectionConfig]:
        self.ensure_sidebar_section_defaults(community_id)
        rows = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                realm,
                section_key,
                label,
                description,
                sort_order,
                show_label,
                is_system,
                created_at,
                updated_at
            FROM sidebar_sections
            WHERE community_id = ?
            ORDER BY
                CASE realm
                    WHEN 'world' THEN 10
                    WHEN 'desk' THEN 20
                    WHEN 'studio' THEN 30
                    ELSE 99
                END,
                sort_order,
                label
            """,
            (community_id,),
        ).fetchall()
        return [_sidebar_section_config_from_row(row) for row in rows]

    def get_sidebar_section(
        self,
        community_id: int,
        section_key: str,
    ) -> SidebarSectionConfig:
        normalized_key = normalize_board_sidebar_section(section_key)
        self.ensure_sidebar_section_defaults(community_id)
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                realm,
                section_key,
                label,
                description,
                sort_order,
                show_label,
                is_system,
                created_at,
                updated_at
            FROM sidebar_sections
            WHERE community_id = ? AND realm = ? AND section_key = ?
            """,
            (community_id, BOARD_SIDEBAR_SECTION_REALMS[normalized_key], normalized_key),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"sidebar section not found in community {community_id}: {section_key}"
            )
        return _sidebar_section_config_from_row(row)

    def update_sidebar_section(
        self,
        community_id: int,
        section_key: str,
        *,
        label: str,
        description: str,
        sort_order: int,
        show_label: bool,
    ) -> SidebarSectionConfig:
        section = self.get_sidebar_section(community_id, section_key)
        cleaned_label = label.strip()
        if not cleaned_label:
            raise ValueError("sidebar section label is required")
        self.connection.execute(
            """
            UPDATE sidebar_sections
            SET label = ?,
                description = ?,
                sort_order = ?,
                show_label = ?,
                updated_at = ?
            WHERE community_id = ? AND id = ?
            """,
            (
                cleaned_label,
                description.strip(),
                sort_order,
                int(show_label),
                _next_update_stamp(section.updated_at),
                community_id,
                section.id,
            ),
        )
        self._commit()
        return self.get_sidebar_section(community_id, section.section_key)

    def create_board(
        self,
        community_id: int,
        slug: str,
        name: str,
        description: str = "",
        *,
        parent_board_id: int | None = None,
        board_kind: str = "location",
        sidebar_section: str | None = None,
        tagline: str = "",
        image_url: str | None = None,
        image_alt: str = "",
        image_treatment: str = "poster",
        image_focal_point: str = "center",
        image_overlay: str = "medium",
        sort_order: int = 0,
        navigation_order: int | None = None,
        show_in_navigation: bool = True,
        is_private: bool = False,
    ) -> Board:
        if parent_board_id is not None:
            self.get_board(community_id, parent_board_id)
        normalized_board_kind = normalize_board_kind(board_kind)
        normalized_sidebar_section = normalize_board_sidebar_section(
            sidebar_section,
            normalized_board_kind,
        )
        now = _utc_now()
        cursor = self.connection.execute(
            """
            INSERT INTO boards (
                community_id,
                parent_board_id,
                slug,
                name,
                board_kind,
                sidebar_section,
                tagline,
                description,
                image_url,
                image_alt,
                image_treatment,
                image_focal_point,
                image_overlay,
                sort_order,
                navigation_order,
                show_in_navigation,
                is_private,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                community_id,
                parent_board_id,
                slug,
                name,
                normalized_board_kind,
                normalized_sidebar_section,
                tagline,
                description,
                image_url,
                image_alt,
                image_treatment,
                image_focal_point,
                image_overlay,
                sort_order,
                sort_order if navigation_order is None else navigation_order,
                int(show_in_navigation),
                int(is_private),
                now,
                now,
            ),
        )
        self._commit()
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
        sidebar_section: str | None = None,
        tagline: str = "",
        image_url: str | None = None,
        image_alt: str = "",
        image_treatment: str | None = None,
        image_focal_point: str | None = None,
        image_overlay: str | None = None,
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
        normalized_sidebar_section = normalize_board_sidebar_section(
            board.sidebar_section if sidebar_section is None else sidebar_section,
            normalized_board_kind,
        )
        self.connection.execute(
            """
            UPDATE boards
            SET
                parent_board_id = ?,
                name = ?,
                board_kind = ?,
                sidebar_section = ?,
                tagline = ?,
                description = ?,
                image_url = ?,
                image_alt = ?,
                image_treatment = ?,
                image_focal_point = ?,
                image_overlay = ?,
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
                normalized_sidebar_section,
                tagline,
                description,
                image_url,
                image_alt,
                board.image_treatment if image_treatment is None else image_treatment,
                board.image_focal_point if image_focal_point is None else image_focal_point,
                board.image_overlay if image_overlay is None else image_overlay,
                sort_order,
                board.navigation_order if navigation_order is None else navigation_order,
                int(board.show_in_navigation if show_in_navigation is None else show_in_navigation),
                int(is_private),
                _next_update_stamp(board.updated_at),
                community_id,
                board_id,
            ),
        )
        self._commit()
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
                sidebar_section,
                tagline,
                description,
                image_url,
                image_alt,
                image_treatment,
                image_focal_point,
                image_overlay,
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
                sidebar_section,
                tagline,
                description,
                image_url,
                image_alt,
                image_treatment,
                image_focal_point,
                image_overlay,
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

    def list_board_communities_by_slug(self, slug: str) -> list[Community]:
        rows = self.connection.execute(
            """
            SELECT DISTINCT
                communities.id,
                communities.name,
                communities.slug,
                communities.host,
                communities.launch_status,
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
            JOIN boards ON boards.community_id = communities.id
            WHERE boards.slug = ? AND boards.is_private = 0
            ORDER BY communities.name, communities.id
            """,
            (slug,),
        ).fetchall()
        return [_community_from_row(row) for row in rows]

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
                sidebar_section,
                tagline,
                description,
                image_url,
                image_alt,
                image_treatment,
                image_focal_point,
                image_overlay,
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
                    sidebar_section,
                    tagline,
                    description,
                    image_url,
                    image_alt,
                    image_treatment,
                    image_focal_point,
                    image_overlay,
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
                    sidebar_section,
                    tagline,
                    description,
                    image_url,
                    image_alt,
                    image_treatment,
                    image_focal_point,
                    image_overlay,
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
