"""Tenant-aware SQLite repository for forum-domain operations."""

from __future__ import annotations

from elbysodic.db.repositories.base import (
    TenantBoundaryError,
    _last_id,
    _next_update_stamp,
    _utc_now,
)
from elbysodic.db.repositories.rows import (
    _character_from_row,
    _character_plot_hook_from_row,
    _character_plot_hook_interest_from_row,
    _character_reserve_from_row,
    _plotting_room_from_row,
    _plotting_room_participant_from_row,
    _post_from_row,
    _post_revision_from_row,
    _thread_from_row,
    _thread_participant_from_row,
    _thread_watch_from_row,
)
from elbysodic.db.repositories.wanted import WantedRepositoryMixin
from elbysodic.domain.models import (
    Character,
    CharacterPlotHook,
    CharacterPlotHookInterest,
    CharacterReserve,
    PlottingRoom,
    PlottingRoomParticipant,
    Post,
    PostRevision,
    Thread,
    ThreadParticipant,
    ThreadWatch,
)


class ForumRepository(
    WantedRepositoryMixin,
):
    """Small repository layer that keeps community scope explicit."""

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
        self.connection.commit()
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
        self.connection.commit()
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
        self.connection.commit()
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
        self.connection.commit()
        return self.get_character_plot_hook_interest(community_id, interest_id)

    def create_plotting_room(
        self,
        community_id: int,
        owner_membership_id: int,
        title: str,
        *,
        source_plot_hook_id: int | None = None,
        source_plot_hook_interest_id: int | None = None,
        source_wanted_ad_id: int | None = None,
        source_wanted_ad_interest_id: int | None = None,
        summary: str = "",
        status: str = "brainstorming",
    ) -> PlottingRoom:
        self.get_membership(community_id, owner_membership_id)
        has_plot_source = (
            source_plot_hook_id is not None or source_plot_hook_interest_id is not None
        )
        has_wanted_source = (
            source_wanted_ad_id is not None or source_wanted_ad_interest_id is not None
        )
        if has_plot_source == has_wanted_source:
            raise ValueError("plotting room must have exactly one source")
        if source_plot_hook_id is not None and source_plot_hook_interest_id is not None:
            hook = self.get_character_plot_hook(community_id, source_plot_hook_id)
            interest = self.get_character_plot_hook_interest(
                community_id,
                source_plot_hook_interest_id,
            )
            if interest.plot_hook_id != hook.id:
                raise TenantBoundaryError(
                    f"plot hook interest {interest.id} does not belong to hook {hook.id}"
                )
        elif has_plot_source:
            raise ValueError("plotting room plot source requires hook and interest")
        if source_wanted_ad_id is not None and source_wanted_ad_interest_id is not None:
            wanted_ad = self.get_wanted_ad(community_id, source_wanted_ad_id)
            interest = self.get_wanted_ad_interest(community_id, source_wanted_ad_interest_id)
            if interest.wanted_ad_id != wanted_ad.id:
                raise TenantBoundaryError(
                    f"wanted interest {interest.id} does not belong to wanted hook {wanted_ad.id}"
                )
        elif has_wanted_source:
            raise ValueError("plotting room wanted source requires hook and interest")
        now = _utc_now()
        cursor = self.connection.execute(
            """
            INSERT OR IGNORE INTO plotting_rooms (
                community_id,
                owner_membership_id,
                source_plot_hook_id,
                source_plot_hook_interest_id,
                source_wanted_ad_id,
                source_wanted_ad_interest_id,
                title,
                summary,
                status,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                community_id,
                owner_membership_id,
                source_plot_hook_id,
                source_plot_hook_interest_id,
                source_wanted_ad_id,
                source_wanted_ad_interest_id,
                title,
                summary,
                status,
                now,
                now,
            ),
        )
        self.connection.commit()
        if source_plot_hook_interest_id is not None:
            return self.get_plotting_room_for_plot_hook_interest(
                community_id,
                source_plot_hook_interest_id,
            )
        if source_wanted_ad_interest_id is not None:
            return self.get_plotting_room_for_wanted_interest(
                community_id,
                source_wanted_ad_interest_id,
            )
        return self.get_plotting_room(community_id, _last_id(cursor))

    def get_plotting_room(self, community_id: int, plotting_room_id: int) -> PlottingRoom:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                owner_membership_id,
                source_plot_hook_id,
                source_plot_hook_interest_id,
                source_wanted_ad_id,
                source_wanted_ad_interest_id,
                title,
                summary,
                status,
                created_at,
                updated_at
            FROM plotting_rooms
            WHERE community_id = ? AND id = ?
            """,
            (community_id, plotting_room_id),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"plotting room not found in community {community_id}: {plotting_room_id}"
            )
        return _plotting_room_from_row(row)

    def get_plotting_room_for_plot_hook_interest(
        self,
        community_id: int,
        interest_id: int,
    ) -> PlottingRoom:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                owner_membership_id,
                source_plot_hook_id,
                source_plot_hook_interest_id,
                source_wanted_ad_id,
                source_wanted_ad_interest_id,
                title,
                summary,
                status,
                created_at,
                updated_at
            FROM plotting_rooms
            WHERE community_id = ? AND source_plot_hook_interest_id = ?
            """,
            (community_id, interest_id),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"plotting room not found in community {community_id}: plot hook interest {interest_id}"
            )
        return _plotting_room_from_row(row)

    def get_plotting_room_for_wanted_interest(
        self,
        community_id: int,
        interest_id: int,
    ) -> PlottingRoom:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                owner_membership_id,
                source_plot_hook_id,
                source_plot_hook_interest_id,
                source_wanted_ad_id,
                source_wanted_ad_interest_id,
                title,
                summary,
                status,
                created_at,
                updated_at
            FROM plotting_rooms
            WHERE community_id = ? AND source_wanted_ad_interest_id = ?
            """,
            (community_id, interest_id),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"plotting room not found in community {community_id}: wanted interest {interest_id}"
            )
        return _plotting_room_from_row(row)

    def list_plotting_rooms(
        self,
        community_id: int,
        *,
        status: str | None = None,
    ) -> list[PlottingRoom]:
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
                owner_membership_id,
                source_plot_hook_id,
                source_plot_hook_interest_id,
                source_wanted_ad_id,
                source_wanted_ad_interest_id,
                title,
                summary,
                status,
                created_at,
                updated_at
            FROM plotting_rooms
            {where}
            ORDER BY updated_at DESC, id DESC
            """,
            params,
        ).fetchall()
        return [_plotting_room_from_row(row) for row in rows]

    def list_plotting_rooms_for_membership(
        self,
        community_id: int,
        membership_id: int,
        *,
        status: str | None = None,
    ) -> list[PlottingRoom]:
        self.get_membership(community_id, membership_id)
        where = "WHERE rooms.community_id = ? AND participants.membership_id = ?"
        params: tuple[object, ...] = (community_id, membership_id)
        if status is not None:
            where = f"{where} AND rooms.status = ?"
            params = (*params, status)
        rows = self.connection.execute(
            f"""
            SELECT DISTINCT
                rooms.id,
                rooms.community_id,
                rooms.owner_membership_id,
                rooms.source_plot_hook_id,
                rooms.source_plot_hook_interest_id,
                rooms.source_wanted_ad_id,
                rooms.source_wanted_ad_interest_id,
                rooms.title,
                rooms.summary,
                rooms.status,
                rooms.created_at,
                rooms.updated_at
            FROM plotting_rooms AS rooms
            JOIN plotting_room_participants AS participants
              ON participants.community_id = rooms.community_id
             AND participants.plotting_room_id = rooms.id
            {where}
            ORDER BY rooms.updated_at DESC, rooms.id DESC
            """,
            params,
        ).fetchall()
        return [_plotting_room_from_row(row) for row in rows]

    def list_plotting_rooms_for_character(
        self,
        community_id: int,
        character_id: int,
        *,
        status: str | None = None,
    ) -> list[PlottingRoom]:
        self.get_character(community_id, character_id)
        where = "WHERE rooms.community_id = ? AND participants.character_id = ?"
        params: tuple[object, ...] = (community_id, character_id)
        if status is not None:
            where = f"{where} AND rooms.status = ?"
            params = (*params, status)
        rows = self.connection.execute(
            f"""
            SELECT DISTINCT
                rooms.id,
                rooms.community_id,
                rooms.owner_membership_id,
                rooms.source_plot_hook_id,
                rooms.source_plot_hook_interest_id,
                rooms.source_wanted_ad_id,
                rooms.source_wanted_ad_interest_id,
                rooms.title,
                rooms.summary,
                rooms.status,
                rooms.created_at,
                rooms.updated_at
            FROM plotting_rooms AS rooms
            JOIN plotting_room_participants AS participants
              ON participants.community_id = rooms.community_id
             AND participants.plotting_room_id = rooms.id
            {where}
            ORDER BY rooms.updated_at DESC, rooms.id DESC
            """,
            params,
        ).fetchall()
        return [_plotting_room_from_row(row) for row in rows]

    def create_plotting_room_participant(
        self,
        community_id: int,
        plotting_room_id: int,
        membership_id: int,
        *,
        character_id: int | None = None,
        prospective_character_name: str = "",
        participant_role: str = "participant",
    ) -> PlottingRoomParticipant:
        self.get_plotting_room(community_id, plotting_room_id)
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
            INSERT OR IGNORE INTO plotting_room_participants (
                community_id,
                plotting_room_id,
                membership_id,
                character_id,
                prospective_character_name,
                participant_role,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                community_id,
                plotting_room_id,
                membership_id,
                character_id,
                prospective_character_name,
                participant_role,
                now,
            ),
        )
        self.connection.commit()
        return self.get_plotting_room_participant_for_identity(
            community_id,
            plotting_room_id,
            membership_id,
            character_id=character_id,
            prospective_character_name=prospective_character_name,
        )

    def get_plotting_room_participant_for_identity(
        self,
        community_id: int,
        plotting_room_id: int,
        membership_id: int,
        *,
        character_id: int | None = None,
        prospective_character_name: str = "",
    ) -> PlottingRoomParticipant:
        if character_id is not None:
            identity_clause = "character_id = ?"
            identity_params: tuple[object, ...] = (character_id,)
        else:
            identity_clause = "character_id IS NULL AND prospective_character_name = ?"
            identity_params = (prospective_character_name,)
        row = self.connection.execute(
            f"""
            SELECT
                id,
                community_id,
                plotting_room_id,
                membership_id,
                character_id,
                prospective_character_name,
                participant_role,
                created_at
            FROM plotting_room_participants
            WHERE community_id = ?
              AND plotting_room_id = ?
              AND membership_id = ?
              AND {identity_clause}
            ORDER BY id
            LIMIT 1
            """,
            (community_id, plotting_room_id, membership_id, *identity_params),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"plotting room participant not found in community {community_id}: "
                f"{plotting_room_id}/{membership_id}"
            )
        return _plotting_room_participant_from_row(row)

    def get_plotting_room_participant(
        self,
        community_id: int,
        participant_id: int,
    ) -> PlottingRoomParticipant:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                plotting_room_id,
                membership_id,
                character_id,
                prospective_character_name,
                participant_role,
                created_at
            FROM plotting_room_participants
            WHERE community_id = ? AND id = ?
            """,
            (community_id, participant_id),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"plotting room participant not found in community {community_id}: {participant_id}"
            )
        return _plotting_room_participant_from_row(row)

    def list_plotting_room_participants(
        self,
        community_id: int,
        plotting_room_id: int,
    ) -> list[PlottingRoomParticipant]:
        self.get_plotting_room(community_id, plotting_room_id)
        rows = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                plotting_room_id,
                membership_id,
                character_id,
                prospective_character_name,
                participant_role,
                created_at
            FROM plotting_room_participants
            WHERE community_id = ? AND plotting_room_id = ?
            ORDER BY participant_role, id
            """,
            (community_id, plotting_room_id),
        ).fetchall()
        return [_plotting_room_participant_from_row(row) for row in rows]

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
            if interest.character_id is None:
                raise TenantBoundaryError(
                    f"wanted interest {wanted_ad_interest_id} has no reserved character yet"
                )
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
