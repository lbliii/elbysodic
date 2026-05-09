"""Character plot hook and plot hook interest repository methods."""

from __future__ import annotations

from elbysodic.db.repositories.base import TenantBoundaryError, _last_id, _utc_now
from elbysodic.db.repositories.rows import (
    _character_plot_hook_from_row,
    _character_plot_hook_interest_from_row,
)
from elbysodic.db.repositories.wanted import WantedRepositoryMixin
from elbysodic.domain.models import CharacterPlotHook, CharacterPlotHookInterest
from elbysodic.domain.vocabulary import PLOT_HOOK_TYPES


class PlotHookRepositoryMixin(WantedRepositoryMixin):
    def create_character_plot_hook(
        self,
        community_id: int,
        author_membership_id: int,
        character_id: int,
        slug: str,
        title: str,
        *,
        related_material_id: int | None = None,
        hook_type: str = "scene",
        summary: str = "",
        body: str = "",
        status: str = "open",
    ) -> CharacterPlotHook:
        self.get_membership(community_id, author_membership_id)
        _require_plot_hook_type(hook_type)
        character = self.get_character(community_id, character_id)
        if character.membership_id != author_membership_id:
            raise TenantBoundaryError("plot hook character must belong to author membership")
        if related_material_id is not None:
            self.get_material(community_id, related_material_id)
        now = _utc_now()
        cursor = self.connection.execute(
            """
            INSERT INTO character_plot_hooks (
                community_id,
                author_membership_id,
                character_id,
                related_material_id,
                slug,
                title,
                hook_type,
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
                author_membership_id,
                character_id,
                related_material_id,
                slug,
                title,
                hook_type,
                summary,
                body,
                status,
                now,
                now,
            ),
        )
        self._commit()
        return self.get_character_plot_hook(community_id, _last_id(cursor))

    def update_character_plot_hook(
        self,
        community_id: int,
        plot_hook_id: int,
        *,
        title: str,
        hook_type: str,
        summary: str,
        body: str,
        status: str,
        related_material_id: int | None = None,
    ) -> CharacterPlotHook:
        self.get_character_plot_hook(community_id, plot_hook_id)
        _require_plot_hook_type(hook_type)
        if related_material_id is not None:
            self.get_material(community_id, related_material_id)
        self.connection.execute(
            """
            UPDATE character_plot_hooks
            SET
                title = ?,
                hook_type = ?,
                summary = ?,
                body = ?,
                status = ?,
                related_material_id = ?,
                updated_at = ?
            WHERE community_id = ? AND id = ?
            """,
            (
                title,
                hook_type,
                summary,
                body,
                status,
                related_material_id,
                _utc_now(),
                community_id,
                plot_hook_id,
            ),
        )
        self._commit()
        return self.get_character_plot_hook(community_id, plot_hook_id)

    def get_character_plot_hook(
        self,
        community_id: int,
        plot_hook_id: int,
    ) -> CharacterPlotHook:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                author_membership_id,
                character_id,
                related_material_id,
                slug,
                title,
                hook_type,
                summary,
                body,
                status,
                created_at,
                updated_at
            FROM character_plot_hooks
            WHERE community_id = ? AND id = ?
            """,
            (community_id, plot_hook_id),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"character plot hook not found in community {community_id}: {plot_hook_id}"
            )
        return _character_plot_hook_from_row(row)

    def get_character_plot_hook_by_slug(
        self,
        community_id: int,
        character_id: int,
        slug: str,
    ) -> CharacterPlotHook:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                author_membership_id,
                character_id,
                related_material_id,
                slug,
                title,
                hook_type,
                summary,
                body,
                status,
                created_at,
                updated_at
            FROM character_plot_hooks
            WHERE community_id = ? AND character_id = ? AND slug = ?
            """,
            (community_id, character_id, slug),
        ).fetchone()
        if row is None:
            raise LookupError(f"character plot hook not found in community {community_id}: {slug}")
        return _character_plot_hook_from_row(row)

    def list_character_plot_hooks(
        self,
        community_id: int,
        *,
        status: str | None = "open",
    ) -> list[CharacterPlotHook]:
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
                author_membership_id,
                character_id,
                related_material_id,
                slug,
                title,
                hook_type,
                summary,
                body,
                status,
                created_at,
                updated_at
            FROM character_plot_hooks
            {where}
            ORDER BY updated_at DESC, title, id
            """,
            params,
        ).fetchall()
        return [_character_plot_hook_from_row(row) for row in rows]

    def list_character_plot_hooks_for_character(
        self,
        community_id: int,
        character_id: int,
        *,
        status: str | None = "open",
    ) -> list[CharacterPlotHook]:
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
                author_membership_id,
                character_id,
                related_material_id,
                slug,
                title,
                hook_type,
                summary,
                body,
                status,
                created_at,
                updated_at
            FROM character_plot_hooks
            {where}
            ORDER BY updated_at DESC, title, id
            """,
            params,
        ).fetchall()
        return [_character_plot_hook_from_row(row) for row in rows]

    def create_character_plot_hook_interest(
        self,
        community_id: int,
        plot_hook_id: int,
        membership_id: int,
        character_id: int,
        *,
        note: str = "",
        status: str = "interested",
    ) -> CharacterPlotHookInterest:
        self.get_character_plot_hook(community_id, plot_hook_id)
        self.get_membership(community_id, membership_id)
        character = self.get_character(community_id, character_id)
        if character.membership_id != membership_id:
            raise TenantBoundaryError(
                f"character {character_id} does not belong to membership {membership_id}"
            )
        now = _utc_now()
        self.connection.execute(
            """
            INSERT OR IGNORE INTO character_plot_hook_interests (
                community_id,
                plot_hook_id,
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
                plot_hook_id,
                membership_id,
                character_id,
                note,
                status,
                now,
                now,
            ),
        )
        self._commit()
        return self.get_character_plot_hook_interest_for_character(
            community_id,
            plot_hook_id,
            character_id,
        )

    def get_character_plot_hook_interest(
        self,
        community_id: int,
        interest_id: int,
    ) -> CharacterPlotHookInterest:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                plot_hook_id,
                membership_id,
                character_id,
                note,
                status,
                created_at,
                updated_at
            FROM character_plot_hook_interests
            WHERE community_id = ? AND id = ?
            """,
            (community_id, interest_id),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"plot hook interest not found in community {community_id}: {interest_id}"
            )
        return _character_plot_hook_interest_from_row(row)

    def get_character_plot_hook_interest_for_character(
        self,
        community_id: int,
        plot_hook_id: int,
        character_id: int,
    ) -> CharacterPlotHookInterest:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                plot_hook_id,
                membership_id,
                character_id,
                note,
                status,
                created_at,
                updated_at
            FROM character_plot_hook_interests
            WHERE community_id = ? AND plot_hook_id = ? AND character_id = ?
            """,
            (community_id, plot_hook_id, character_id),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"plot hook interest not found in community {community_id}: {plot_hook_id}/{character_id}"
            )
        return _character_plot_hook_interest_from_row(row)

    def list_character_plot_hook_interests(
        self,
        community_id: int,
        plot_hook_id: int,
        *,
        status: str | None = None,
    ) -> list[CharacterPlotHookInterest]:
        self.get_character_plot_hook(community_id, plot_hook_id)
        where = "WHERE community_id = ? AND plot_hook_id = ?"
        params: tuple[object, ...] = (community_id, plot_hook_id)
        if status is not None:
            where = f"{where} AND status = ?"
            params = (*params, status)
        rows = self.connection.execute(
            f"""
            SELECT
                id,
                community_id,
                plot_hook_id,
                membership_id,
                character_id,
                note,
                status,
                created_at,
                updated_at
            FROM character_plot_hook_interests
            {where}
            ORDER BY created_at DESC, id DESC
            """,
            params,
        ).fetchall()
        return [_character_plot_hook_interest_from_row(row) for row in rows]

    def update_character_plot_hook_interest_status(
        self,
        community_id: int,
        interest_id: int,
        status: str,
    ) -> CharacterPlotHookInterest:
        self.get_character_plot_hook_interest(community_id, interest_id)
        self.connection.execute(
            """
            UPDATE character_plot_hook_interests
            SET status = ?, updated_at = ?
            WHERE community_id = ? AND id = ?
            """,
            (status, _utc_now(), community_id, interest_id),
        )
        self._commit()
        return self.get_character_plot_hook_interest(community_id, interest_id)


def _require_plot_hook_type(hook_type: str) -> None:
    if hook_type not in PLOT_HOOK_TYPES:
        allowed = ", ".join(sorted(PLOT_HOOK_TYPES))
        raise ValueError(f"hook_type must be one of: {allowed}")
