"""Post and post-revision repository methods."""

from __future__ import annotations

from elbysodic.db.repositories.base import (
    _last_id,
    _next_update_stamp,
    _utc_now,
)
from elbysodic.db.repositories.claims import ClaimRepositoryMixin
from elbysodic.db.repositories.rows import (
    _post_from_row,
    _post_revision_from_row,
)
from elbysodic.domain.models import Post, PostRevision


class PostRepositoryMixin(ClaimRepositoryMixin):
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
        post_number = self._next_post_number(community_id, thread_id)
        cursor = self.connection.execute(
            """
            INSERT INTO posts (
                community_id,
                thread_id,
                post_number,
                author_membership_id,
                author_character_id,
                body,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                community_id,
                thread_id,
                post_number,
                character.membership_id,
                author_character_id,
                body,
                now,
                now,
            ),
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

    def _next_post_number(self, community_id: int, thread_id: int) -> int:
        row = self.connection.execute(
            """
            SELECT COALESCE(MAX(post_number), 0) + 1 AS next_post_number
            FROM posts
            WHERE community_id = ? AND thread_id = ?
            """,
            (community_id, thread_id),
        ).fetchone()
        return int(row["next_post_number"])

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
                post_number,
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

    def get_post_by_number(self, community_id: int, thread_id: int, post_number: int) -> Post:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                thread_id,
                post_number,
                author_membership_id,
                author_character_id,
                body,
                created_at,
                updated_at
            FROM posts
            WHERE community_id = ? AND thread_id = ? AND post_number = ?
            """,
            (community_id, thread_id, post_number),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"post number {post_number} not found in community {community_id} "
                f"thread {thread_id}"
            )
        return _post_from_row(row)

    def list_posts(self, community_id: int, thread_id: int) -> list[Post]:
        rows = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                thread_id,
                post_number,
                author_membership_id,
                author_character_id,
                body,
                created_at,
                updated_at
            FROM posts
            WHERE community_id = ? AND thread_id = ?
            ORDER BY post_number
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
                post_number,
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
