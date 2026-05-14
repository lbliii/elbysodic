"""Notification repository methods."""

from __future__ import annotations

import json
from collections import defaultdict

from elbysodic.db.repositories.base import TenantBoundaryError, _utc_now
from elbysodic.db.repositories.characters import CharacterRepositoryMixin
from elbysodic.db.repositories.rows import _notification_from_row
from elbysodic.domain.models import (
    CharacterPlotHook,
    Notification,
    PlottingRoom,
    Post,
    Thread,
    WantedAd,
    WantedAdInterest,
)


class NotificationRepositoryMixin(CharacterRepositoryMixin):
    def get_thread(self, community_id: int, thread_id: int) -> Thread:
        raise NotImplementedError

    def get_post(self, community_id: int, post_id: int) -> Post:
        raise NotImplementedError

    def get_wanted_ad(self, community_id: int, wanted_ad_id: int) -> WantedAd:
        raise NotImplementedError

    def get_wanted_ad_interest(
        self,
        community_id: int,
        interest_id: int,
    ) -> WantedAdInterest:
        raise NotImplementedError

    def get_character_plot_hook(
        self,
        community_id: int,
        plot_hook_id: int,
    ) -> CharacterPlotHook:
        raise NotImplementedError

    def get_plotting_room(self, community_id: int, plotting_room_id: int) -> PlottingRoom:
        raise NotImplementedError

    def create_notification(
        self,
        community_id: int,
        membership_id: int,
        *,
        kind: str,
        thread_id: int | None = None,
        post_id: int | None = None,
        wanted_ad_id: int | None = None,
        wanted_ad_interest_id: int | None = None,
        character_plot_hook_id: int | None = None,
        plotting_room_id: int | None = None,
        character_id: int | None = None,
        actor_membership_id: int,
        actor_character_id: int | None,
    ) -> Notification:
        self.get_membership(community_id, membership_id)
        self.get_membership(community_id, actor_membership_id)
        if actor_character_id is not None:
            actor = self.get_character(community_id, actor_character_id)
            if actor.membership_id != actor_membership_id:
                raise TenantBoundaryError(
                    f"character {actor_character_id} does not belong to membership {actor_membership_id}"
                )
        post_target_id: int | None = None
        wanted_interest_target_id: int | None = None
        plot_hook_target_id: int | None = None
        plotting_room_target_id: int | None = None
        character_target_id: int | None = None
        has_post_target = thread_id is not None and post_id is not None
        has_wanted_target = wanted_ad_id is not None and wanted_ad_interest_id is not None
        has_plot_hook_target = character_plot_hook_id is not None
        has_plotting_room_target = plotting_room_id is not None
        has_character_target = character_id is not None
        if (
            sum(
                (
                    has_post_target,
                    has_wanted_target,
                    has_plot_hook_target,
                    has_plotting_room_target,
                    has_character_target,
                )
            )
            != 1
        ):
            raise ValueError(
                "notification must target exactly one post, wanted interest, plot hook, plotting room, or character"
            )
        if thread_id is not None and post_id is not None:
            post_target_id = post_id
            thread = self.get_thread(community_id, thread_id)
            post = self.get_post(community_id, post_target_id)
            if post.thread_id != thread.id:
                raise TenantBoundaryError(f"post {post_id} does not belong to thread {thread_id}")
        elif wanted_ad_id is not None and wanted_ad_interest_id is not None:
            wanted_interest_target_id = wanted_ad_interest_id
            wanted_ad = self.get_wanted_ad(community_id, wanted_ad_id)
            interest = self.get_wanted_ad_interest(community_id, wanted_interest_target_id)
            if interest.wanted_ad_id != wanted_ad.id:
                raise TenantBoundaryError(
                    f"wanted interest {wanted_ad_interest_id} does not belong to wanted ad {wanted_ad_id}"
                )
        elif character_plot_hook_id is not None:
            plot_hook_target_id = character_plot_hook_id
            self.get_character_plot_hook(community_id, plot_hook_target_id)
        elif plotting_room_id is not None:
            plotting_room_target_id = plotting_room_id
            self.get_plotting_room(community_id, plotting_room_target_id)
        elif character_id is not None:
            character_target_id = character_id
            self.get_character(community_id, character_target_id)
        now = _utc_now()
        self.connection.execute(
            """
            INSERT OR IGNORE INTO notifications (
                community_id,
                membership_id,
                kind,
                thread_id,
                post_id,
                wanted_ad_id,
                wanted_ad_interest_id,
                character_plot_hook_id,
                plotting_room_id,
                character_id,
                actor_membership_id,
                actor_character_id,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                community_id,
                membership_id,
                kind,
                thread_id,
                post_id,
                wanted_ad_id,
                wanted_ad_interest_id,
                character_plot_hook_id,
                plotting_room_id,
                character_id,
                actor_membership_id,
                actor_character_id,
                now,
            ),
        )
        self._commit()
        if post_target_id is not None:
            return self.get_notification_for_post(community_id, membership_id, kind, post_target_id)
        if wanted_interest_target_id is not None:
            return self.get_notification_for_wanted_interest(
                community_id,
                membership_id,
                kind,
                wanted_interest_target_id,
            )
        if plot_hook_target_id is not None:
            return self.get_notification_for_plot_hook(
                community_id,
                membership_id,
                kind,
                plot_hook_target_id,
            )
        if plotting_room_target_id is not None:
            return self.get_notification_for_plotting_room(
                community_id,
                membership_id,
                kind,
                plotting_room_target_id,
            )
        if character_target_id is None:
            raise ValueError(
                "notification must target exactly one post, wanted interest, plot hook, plotting room, or character"
            )
        return self.get_notification_for_character(
            community_id,
            membership_id,
            kind,
            character_target_id,
        )

    def get_notification(self, community_id: int, notification_id: int) -> Notification:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                membership_id,
                kind,
                thread_id,
                post_id,
                wanted_ad_id,
                wanted_ad_interest_id,
                character_plot_hook_id,
                plotting_room_id,
                character_id,
                actor_membership_id,
                actor_character_id,
                read_at,
                created_at
            FROM notifications
            WHERE community_id = ? AND id = ?
            """,
            (community_id, notification_id),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"notification not found in community {community_id}: {notification_id}"
            )
        return _notification_from_row(row)

    def get_notification_for_post(
        self,
        community_id: int,
        membership_id: int,
        kind: str,
        post_id: int,
    ) -> Notification:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                membership_id,
                kind,
                thread_id,
                post_id,
                wanted_ad_id,
                wanted_ad_interest_id,
                character_plot_hook_id,
                plotting_room_id,
                character_id,
                actor_membership_id,
                actor_character_id,
                read_at,
                created_at
            FROM notifications
            WHERE community_id = ? AND membership_id = ? AND kind = ? AND post_id = ?
            """,
            (community_id, membership_id, kind, post_id),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"notification not found in community {community_id}: {membership_id}/{kind}/{post_id}"
            )
        return _notification_from_row(row)

    def get_notification_for_wanted_interest(
        self,
        community_id: int,
        membership_id: int,
        kind: str,
        wanted_ad_interest_id: int,
    ) -> Notification:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                membership_id,
                kind,
                thread_id,
                post_id,
                wanted_ad_id,
                wanted_ad_interest_id,
                character_plot_hook_id,
                plotting_room_id,
                character_id,
                actor_membership_id,
                actor_character_id,
                read_at,
                created_at
            FROM notifications
            WHERE community_id = ?
              AND membership_id = ?
              AND kind = ?
              AND wanted_ad_interest_id = ?
            """,
            (community_id, membership_id, kind, wanted_ad_interest_id),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"notification not found in community {community_id}: {membership_id}/{kind}/{wanted_ad_interest_id}"
            )
        return _notification_from_row(row)

    def get_notification_for_plot_hook(
        self,
        community_id: int,
        membership_id: int,
        kind: str,
        plot_hook_id: int,
    ) -> Notification:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                membership_id,
                kind,
                thread_id,
                post_id,
                wanted_ad_id,
                wanted_ad_interest_id,
                character_plot_hook_id,
                plotting_room_id,
                character_id,
                actor_membership_id,
                actor_character_id,
                read_at,
                created_at
            FROM notifications
            WHERE community_id = ?
              AND membership_id = ?
              AND kind = ?
              AND character_plot_hook_id = ?
            """,
            (community_id, membership_id, kind, plot_hook_id),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"notification not found in community {community_id}: {membership_id}/{kind}/{plot_hook_id}"
            )
        return _notification_from_row(row)

    def get_notification_for_plotting_room(
        self,
        community_id: int,
        membership_id: int,
        kind: str,
        plotting_room_id: int,
    ) -> Notification:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                membership_id,
                kind,
                thread_id,
                post_id,
                wanted_ad_id,
                wanted_ad_interest_id,
                character_plot_hook_id,
                plotting_room_id,
                character_id,
                actor_membership_id,
                actor_character_id,
                read_at,
                created_at
            FROM notifications
            WHERE community_id = ?
              AND membership_id = ?
              AND kind = ?
              AND plotting_room_id = ?
            """,
            (community_id, membership_id, kind, plotting_room_id),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"notification not found in community {community_id}: {membership_id}/{kind}/{plotting_room_id}"
            )
        return _notification_from_row(row)

    def get_notification_for_character(
        self,
        community_id: int,
        membership_id: int,
        kind: str,
        character_id: int,
    ) -> Notification:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                membership_id,
                kind,
                thread_id,
                post_id,
                wanted_ad_id,
                wanted_ad_interest_id,
                character_plot_hook_id,
                plotting_room_id,
                character_id,
                actor_membership_id,
                actor_character_id,
                read_at,
                created_at
            FROM notifications
            WHERE community_id = ?
              AND membership_id = ?
              AND kind = ?
              AND character_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (community_id, membership_id, kind, character_id),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"notification not found in community {community_id}: {membership_id}/{kind}/{character_id}"
            )
        return _notification_from_row(row)

    def list_notifications(
        self,
        community_id: int,
        membership_id: int,
        *,
        limit: int = 50,
    ) -> list[Notification]:
        self.get_membership(community_id, membership_id)
        rows = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                membership_id,
                kind,
                thread_id,
                post_id,
                wanted_ad_id,
                wanted_ad_interest_id,
                character_plot_hook_id,
                plotting_room_id,
                character_id,
                actor_membership_id,
                actor_character_id,
                read_at,
                created_at
            FROM notifications
            WHERE community_id = ? AND membership_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (community_id, membership_id, limit),
        ).fetchall()
        return [_notification_from_row(row) for row in rows]

    def list_unread_notifications_for_memberships(
        self,
        membership_pairs: list[tuple[int, int]],
    ) -> dict[tuple[int, int], list[Notification]]:
        if not membership_pairs:
            return {}
        requested_json = json.dumps(
            [
                {"community_id": community_id, "membership_id": membership_id}
                for community_id, membership_id in membership_pairs
            ]
        )
        rows = self.connection.execute(
            """
            WITH requested AS (
                SELECT
                    CAST(json_extract(value, '$.community_id') AS INTEGER) AS community_id,
                    CAST(json_extract(value, '$.membership_id') AS INTEGER) AS membership_id
                FROM json_each(?)
            )
            SELECT
                notifications.id,
                notifications.community_id,
                notifications.membership_id,
                notifications.kind,
                notifications.thread_id,
                notifications.post_id,
                notifications.wanted_ad_id,
                notifications.wanted_ad_interest_id,
                notifications.character_plot_hook_id,
                notifications.plotting_room_id,
                notifications.character_id,
                notifications.actor_membership_id,
                notifications.actor_character_id,
                notifications.read_at,
                notifications.created_at
            FROM notifications
            JOIN requested
              ON requested.community_id = notifications.community_id
             AND requested.membership_id = notifications.membership_id
            WHERE notifications.read_at IS NULL
            ORDER BY notifications.community_id,
                     notifications.membership_id,
                     notifications.created_at DESC,
                     notifications.id DESC
            """,
            (requested_json,),
        ).fetchall()
        notifications_by_membership: dict[tuple[int, int], list[Notification]] = defaultdict(list)
        for row in rows:
            notification = _notification_from_row(row)
            notifications_by_membership[
                (notification.community_id, notification.membership_id)
            ].append(notification)
        return dict(notifications_by_membership)

    def count_unread_notifications(self, community_id: int, membership_id: int) -> int:
        self.get_membership(community_id, membership_id)
        row = self.connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM notifications
            WHERE community_id = ? AND membership_id = ? AND read_at IS NULL
            """,
            (community_id, membership_id),
        ).fetchone()
        return int(row["count"] if row is not None else 0)

    def mark_notification_read(self, community_id: int, notification_id: int) -> Notification:
        notification = self.get_notification(community_id, notification_id)
        if notification.read_at is None:
            self.connection.execute(
                """
                UPDATE notifications
                SET read_at = ?
                WHERE community_id = ? AND id = ?
                """,
                (_utc_now(), community_id, notification_id),
            )
            self._commit()
        return self.get_notification(community_id, notification_id)

    def mark_all_notifications_read(self, community_id: int, membership_id: int) -> None:
        self.get_membership(community_id, membership_id)
        self.connection.execute(
            """
            UPDATE notifications
            SET read_at = COALESCE(read_at, ?)
            WHERE community_id = ? AND membership_id = ?
            """,
            (_utc_now(), community_id, membership_id),
        )
        self._commit()
