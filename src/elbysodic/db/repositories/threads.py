"""Thread, participant, read-state, and watch repository methods."""

from __future__ import annotations

from elbysodic.db.repositories.base import _last_id, _utc_now
from elbysodic.db.repositories.reserves import ReserveRepositoryMixin
from elbysodic.db.repositories.rows import (
    _character_from_row,
    _thread_from_row,
    _thread_participant_from_row,
    _thread_watch_from_row,
)
from elbysodic.domain.models import Character, Thread, ThreadParticipant, ThreadWatch


class ThreadRepositoryMixin(ReserveRepositoryMixin):
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
        self._commit()
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
        self._commit()
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
        self._commit()
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
        self._commit()
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
        self._commit()
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
        self._commit()
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
        self._commit()

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
        self._commit()
        return self.get_thread_watch(community_id, thread_id, membership_id)

    def unwatch_thread(self, community_id: int, thread_id: int, membership_id: int) -> None:
        self.connection.execute(
            """
            DELETE FROM thread_watches
            WHERE community_id = ? AND thread_id = ? AND membership_id = ?
            """,
            (community_id, thread_id, membership_id),
        )
        self._commit()

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
