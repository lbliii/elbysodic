"""Plotting room and participant repository methods."""

from __future__ import annotations

from elbysodic.db.repositories.base import TenantBoundaryError, _last_id, _utc_now
from elbysodic.db.repositories.plot_hooks import PlotHookRepositoryMixin
from elbysodic.db.repositories.rows import (
    _plotting_room_from_row,
    _plotting_room_message_from_row,
    _plotting_room_participant_from_row,
)
from elbysodic.domain.models import PlottingRoom, PlottingRoomMessage, PlottingRoomParticipant


class PlottingRepositoryMixin(PlotHookRepositoryMixin):
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
        self._commit()
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
                notes,
                next_step,
                target_board_id,
                target_thread_id,
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

    def update_plotting_room_plan(
        self,
        community_id: int,
        plotting_room_id: int,
        *,
        notes: str,
        next_step: str,
        target_board_id: int | None,
        status: str,
    ) -> PlottingRoom:
        self.get_plotting_room(community_id, plotting_room_id)
        if target_board_id is not None:
            self.get_board(community_id, target_board_id)
        self.connection.execute(
            """
            UPDATE plotting_rooms
            SET notes = ?,
                next_step = ?,
                target_board_id = ?,
                status = ?,
                updated_at = ?
            WHERE community_id = ? AND id = ?
            """,
            (
                notes,
                next_step,
                target_board_id,
                status,
                _utc_now(),
                community_id,
                plotting_room_id,
            ),
        )
        self._commit()
        return self.get_plotting_room(community_id, plotting_room_id)

    def attach_plotting_room_thread(
        self,
        community_id: int,
        plotting_room_id: int,
        thread_id: int,
    ) -> PlottingRoom:
        self.get_plotting_room(community_id, plotting_room_id)
        thread = self.get_thread(community_id, thread_id)
        self.connection.execute(
            """
            UPDATE plotting_rooms
            SET target_board_id = ?,
                target_thread_id = ?,
                status = 'threaded',
                updated_at = ?
            WHERE community_id = ? AND id = ?
            """,
            (
                thread.board_id,
                thread.id,
                _utc_now(),
                community_id,
                plotting_room_id,
            ),
        )
        self._commit()
        return self.get_plotting_room(community_id, plotting_room_id)

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
                notes,
                next_step,
                target_board_id,
                target_thread_id,
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
                notes,
                next_step,
                target_board_id,
                target_thread_id,
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
                notes,
                next_step,
                target_board_id,
                target_thread_id,
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
                rooms.notes,
                rooms.next_step,
                rooms.target_board_id,
                rooms.target_thread_id,
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
                rooms.notes,
                rooms.next_step,
                rooms.target_board_id,
                rooms.target_thread_id,
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
        self._commit()
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

    def create_plotting_room_message(
        self,
        community_id: int,
        plotting_room_id: int,
        author_membership_id: int,
        body: str,
        *,
        author_character_id: int | None = None,
    ) -> PlottingRoomMessage:
        self.get_plotting_room(community_id, plotting_room_id)
        self.get_membership(community_id, author_membership_id)
        if author_character_id is not None:
            character = self.get_character(community_id, author_character_id)
            if character.membership_id != author_membership_id:
                raise TenantBoundaryError(
                    f"character {author_character_id} does not belong to membership {author_membership_id}"
                )
        cursor = self.connection.execute(
            """
            INSERT INTO plotting_room_messages (
                community_id,
                plotting_room_id,
                author_membership_id,
                author_character_id,
                body,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                community_id,
                plotting_room_id,
                author_membership_id,
                author_character_id,
                body,
                _utc_now(),
            ),
        )
        self.connection.execute(
            """
            UPDATE plotting_rooms
            SET updated_at = ?
            WHERE community_id = ? AND id = ?
            """,
            (_utc_now(), community_id, plotting_room_id),
        )
        self._commit()
        return self.get_plotting_room_message(community_id, _last_id(cursor))

    def get_plotting_room_message(
        self,
        community_id: int,
        message_id: int,
    ) -> PlottingRoomMessage:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                plotting_room_id,
                author_membership_id,
                author_character_id,
                body,
                created_at
            FROM plotting_room_messages
            WHERE community_id = ? AND id = ?
            """,
            (community_id, message_id),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"plotting room message not found in community {community_id}: {message_id}"
            )
        return _plotting_room_message_from_row(row)

    def list_plotting_room_messages(
        self,
        community_id: int,
        plotting_room_id: int,
        *,
        after_id: int | None = None,
        limit: int = 100,
    ) -> list[PlottingRoomMessage]:
        self.get_plotting_room(community_id, plotting_room_id)
        where = "WHERE community_id = ? AND plotting_room_id = ?"
        params: tuple[object, ...] = (community_id, plotting_room_id)
        if after_id is not None:
            where = f"{where} AND id > ?"
            params = (*params, after_id)
        rows = self.connection.execute(
            f"""
            SELECT
                id,
                community_id,
                plotting_room_id,
                author_membership_id,
                author_character_id,
                body,
                created_at
            FROM plotting_room_messages
            {where}
            ORDER BY id
            LIMIT ?
            """,
            (*params, limit),
        ).fetchall()
        return [_plotting_room_message_from_row(row) for row in rows]
