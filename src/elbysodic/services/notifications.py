"""Notification inbox, targeting, and delivery helpers."""

from __future__ import annotations

import re
from typing import Protocol

from elbysodic.domain.models import (
    Board,
    Character,
    CharacterPlotHook,
    CommunityMembership,
    Notification,
    PlottingRoom,
    PlottingRoomParticipant,
    Post,
    Role,
    Thread,
    WantedAd,
    WantedAdInterest,
)
from elbysodic.services import policies
from elbysodic.services.posts import PostViewRepository, post_view
from elbysodic.services.read_models import ForumView, NotificationInbox, NotificationItem
from elbysodic.services.timestamps import timestamp_label


class NotificationRepository(PostViewRepository, Protocol):
    def get_board(self, community_id: int, board_id: int) -> Board: ...

    def get_thread(self, community_id: int, thread_id: int) -> Thread: ...

    def get_post(self, community_id: int, post_id: int) -> Post: ...

    def get_wanted_ad(self, community_id: int, wanted_ad_id: int) -> WantedAd: ...

    def get_wanted_ad_interest(
        self,
        community_id: int,
        interest_id: int,
    ) -> WantedAdInterest: ...

    def get_character_plot_hook(
        self,
        community_id: int,
        plot_hook_id: int,
    ) -> CharacterPlotHook: ...

    def get_plotting_room(self, community_id: int, plotting_room_id: int) -> PlottingRoom: ...

    def list_plotting_room_participants(
        self,
        community_id: int,
        plotting_room_id: int,
    ) -> list[PlottingRoomParticipant]: ...

    def get_notification(self, community_id: int, notification_id: int) -> Notification: ...

    def list_notifications(
        self,
        community_id: int,
        membership_id: int,
        *,
        limit: int = 50,
    ) -> list[Notification]: ...

    def count_unread_notifications(self, community_id: int, membership_id: int) -> int: ...

    def mark_notification_read(self, community_id: int, notification_id: int) -> Notification: ...

    def mark_all_notifications_read(self, community_id: int, membership_id: int) -> None: ...

    def list_thread_watch_membership_ids(
        self,
        community_id: int,
        thread_id: int,
    ) -> list[int]: ...

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
    ) -> Notification: ...


def notification_inbox(
    repo: NotificationRepository,
    viewer: ForumView,
    *,
    limit: int = 50,
) -> NotificationInbox:
    items: list[NotificationItem] = []
    for notification in repo.list_notifications(
        viewer.community.id,
        viewer.membership.id,
        limit=limit,
    ):
        item = notification_item(repo, viewer, notification)
        if item is not None:
            items.append(item)
    return NotificationInbox(
        items=items,
        unread_count=count_visible_unread_notifications(
            repo,
            viewer.community.id,
            viewer.membership,
            viewer.role,
        ),
    )


def count_visible_unread_notifications(
    repo: NotificationRepository,
    community_id: int,
    membership: CommunityMembership,
    role: Role | None,
) -> int:
    return sum(
        1
        for notification in repo.list_notifications(community_id, membership.id, limit=1000)
        if notification.read_at is None
        and _can_view_notification_target(repo, community_id, membership, role, notification)
    )


def open_notification(
    repo: NotificationRepository,
    viewer: ForumView,
    notification_id: int,
) -> str:
    notification = repo.get_notification(viewer.community.id, notification_id)
    if notification.membership_id != viewer.membership.id:
        raise PermissionError(
            f"membership {viewer.membership.id} cannot read notification {notification.id}"
        )
    item = notification_item(repo, viewer, notification)
    if item is None:
        raise LookupError(f"notification target not found: {notification.id}")
    repo.mark_notification_read(viewer.community.id, notification.id)
    return item.href


def mark_all_notifications_read(repo: NotificationRepository, viewer: ForumView) -> None:
    repo.mark_all_notifications_read(viewer.community.id, viewer.membership.id)


def notify_post_created(
    repo: NotificationRepository,
    viewer: ForumView,
    thread: Thread,
    post: Post,
) -> None:
    mentioned_memberships = mentioned_membership_ids(repo, viewer.community.id, post.body)
    watch_memberships = set(repo.list_thread_watch_membership_ids(viewer.community.id, thread.id))
    actor_membership_id = viewer.membership.id
    for membership_id in mentioned_memberships:
        if membership_id != actor_membership_id:
            repo.create_notification(
                viewer.community.id,
                membership_id,
                kind="mention",
                thread_id=thread.id,
                post_id=post.id,
                actor_membership_id=actor_membership_id,
                actor_character_id=post.author_character_id,
            )
    for membership_id in watch_memberships - mentioned_memberships:
        if membership_id != actor_membership_id:
            repo.create_notification(
                viewer.community.id,
                membership_id,
                kind="thread_reply",
                thread_id=thread.id,
                post_id=post.id,
                actor_membership_id=actor_membership_id,
                actor_character_id=post.author_character_id,
            )


def notification_item(
    repo: NotificationRepository,
    viewer: ForumView,
    notification: Notification,
) -> NotificationItem | None:
    actor_membership = repo.get_membership(
        viewer.community.id,
        notification.actor_membership_id,
    )
    actor = (
        repo.get_character(viewer.community.id, notification.actor_character_id)
        if notification.actor_character_id is not None
        else None
    )
    actor_label = actor.name if actor is not None else actor_membership.display_name
    if notification.character_id is not None:
        character = repo.get_character(viewer.community.id, notification.character_id)
        if character.membership_id != viewer.membership.id and not policies.can_manage_casting(
            viewer.membership, viewer.role
        ):
            return None
        match notification.kind:
            case "application_submitted":
                snippet = f"{actor_label} submitted this character for review."
            case "application_accepted":
                snippet = f"{actor_label} accepted this character application."
            case "application_revision_requested":
                snippet = f"{actor_label} requested revisions for this character application."
            case _:
                snippet = f"{actor_label} updated this character application."
        return NotificationItem(
            notification=notification,
            board=None,
            thread=None,
            post=None,
            wanted_ad=None,
            plot_hook=None,
            plotting_room=None,
            actor=actor,
            actor_membership=actor_membership,
            label=notification_label(notification.kind),
            title=character.name,
            created_at_label=timestamp_label(notification.created_at),
            snippet=snippet,
            href=f"/applications/{character.slug}",
        )
    if notification.wanted_ad_id is not None:
        wanted_ad = repo.get_wanted_ad(viewer.community.id, notification.wanted_ad_id)
        interest = (
            repo.get_wanted_ad_interest(
                viewer.community.id,
                notification.wanted_ad_interest_id,
            )
            if notification.wanted_ad_interest_id is not None
            else None
        )
        if interest is not None and not _can_view_wanted_interest_notification(
            viewer.membership,
            viewer.role,
            wanted_ad,
            interest,
        ):
            return None
        if notification.kind == "wanted_reserved":
            snippet = f"{actor_label} reserved this wanted hook."
        elif notification.kind == "reserve_created":
            snippet = f"{actor_label} created a reserve from this wanted hook."
        else:
            snippet = f"{actor_label} is interested in this wanted hook."
        if interest is not None and interest.character_id is None:
            snippet = (
                f"{actor_membership.display_name} would create "
                f"{interest.prospective_character_name} for this hook."
            )
        if interest is not None and interest.note:
            snippet = interest.note
        return NotificationItem(
            notification=notification,
            board=None,
            thread=None,
            post=None,
            wanted_ad=wanted_ad,
            plot_hook=None,
            plotting_room=None,
            actor=actor,
            actor_membership=actor_membership,
            label=notification_label(notification.kind),
            title=wanted_ad.title,
            created_at_label=timestamp_label(notification.created_at),
            snippet=snippet,
            href=f"/wanted/{wanted_ad.slug}",
        )
    if notification.character_plot_hook_id is not None:
        plot_hook = repo.get_character_plot_hook(
            viewer.community.id,
            notification.character_plot_hook_id,
        )
        character = repo.get_character(viewer.community.id, plot_hook.character_id)
        return NotificationItem(
            notification=notification,
            board=None,
            thread=None,
            post=None,
            wanted_ad=None,
            plot_hook=plot_hook,
            plotting_room=None,
            actor=actor,
            actor_membership=actor_membership,
            label=notification_label(notification.kind),
            title=plot_hook.title,
            created_at_label=timestamp_label(notification.created_at),
            snippet=f"{actor_label} is interested in this plot hook.",
            href=f"/characters/{character.slug}/hooks/{plot_hook.slug}",
        )
    if notification.plotting_room_id is not None:
        room = repo.get_plotting_room(viewer.community.id, notification.plotting_room_id)
        if not _can_view_plotting_room_notification(
            repo,
            viewer.community.id,
            viewer.membership,
            viewer.role,
            room,
        ):
            return None
        if notification.kind == "plotting_room_threaded":
            snippet = f"{actor_label} started a scene from this plotting room."
        else:
            snippet = f"{actor_label} started a plotting room with you."
        return NotificationItem(
            notification=notification,
            board=None,
            thread=None,
            post=None,
            wanted_ad=None,
            plot_hook=None,
            plotting_room=room,
            actor=actor,
            actor_membership=actor_membership,
            label=notification_label(notification.kind),
            title=room.title,
            created_at_label=timestamp_label(notification.created_at),
            snippet=snippet,
            href=f"/plotting/{room.id}",
        )
    if notification.thread_id is None or notification.post_id is None:
        return None
    thread = repo.get_thread(viewer.community.id, notification.thread_id)
    board = repo.get_board(viewer.community.id, thread.board_id)
    if not policies.can_view_board(viewer.membership, board, viewer.role):
        return None
    post = repo.get_post(viewer.community.id, notification.post_id)
    rendered_post = post_view(repo, viewer.community.id, post)
    return NotificationItem(
        notification=notification,
        board=board,
        thread=thread,
        post=rendered_post,
        wanted_ad=None,
        plot_hook=None,
        plotting_room=None,
        actor=actor,
        actor_membership=actor_membership,
        label=notification_label(notification.kind),
        title=thread.title,
        created_at_label=rendered_post.created_at_label,
        snippet=rendered_post.snippet,
        href=f"/boards/{board.slug}/threads/{thread.slug}#{rendered_post.anchor}",
    )


def _can_view_plotting_room_notification(
    repo: NotificationRepository,
    community_id: int,
    membership: CommunityMembership,
    role: Role | None,
    room: PlottingRoom,
) -> bool:
    if room.owner_membership_id == membership.id or policies.can_manage_casting(membership, role):
        return True
    return any(
        participant.membership_id == membership.id
        for participant in repo.list_plotting_room_participants(community_id, room.id)
    )


def _can_view_notification_target(
    repo: NotificationRepository,
    community_id: int,
    membership: CommunityMembership,
    role: Role | None,
    notification: Notification,
) -> bool:
    try:
        if notification.thread_id is not None:
            thread = repo.get_thread(community_id, notification.thread_id)
            board = repo.get_board(community_id, thread.board_id)
            return policies.can_view_board(membership, board, role)
        if notification.plotting_room_id is not None:
            room = repo.get_plotting_room(community_id, notification.plotting_room_id)
            return _can_view_plotting_room_notification(
                repo,
                community_id,
                membership,
                role,
                room,
            )
        if notification.wanted_ad_id is not None:
            wanted_ad = repo.get_wanted_ad(community_id, notification.wanted_ad_id)
            if notification.wanted_ad_interest_id is None:
                return True
            interest = repo.get_wanted_ad_interest(
                community_id,
                notification.wanted_ad_interest_id,
            )
            return _can_view_wanted_interest_notification(
                membership,
                role,
                wanted_ad,
                interest,
            )
        if notification.character_id is not None:
            character = repo.get_character(community_id, notification.character_id)
            return character.membership_id == membership.id or policies.can_manage_casting(
                membership, role
            )
    except LookupError:
        return False
    return True


def _can_view_wanted_interest_notification(
    membership: CommunityMembership,
    role: Role | None,
    wanted_ad: WantedAd,
    interest: WantedAdInterest,
) -> bool:
    return (
        membership.id == interest.membership_id
        or membership.id == wanted_ad.creator_membership_id
        or policies.can_manage_casting(membership, role)
    )


def notification_label(kind: str) -> str:
    match kind:
        case "mention":
            return "Mention"
        case "thread_reply":
            return "Watched thread"
        case "wanted_interest":
            return "Wanted interest"
        case "plot_hook_interest":
            return "Plot hook interest"
        case "plotting_room_created":
            return "Plotting room"
        case "plotting_room_threaded":
            return "Scene started"
        case "wanted_reserved":
            return "Wanted reserved"
        case "reserve_created":
            return "Reserve created"
        case "application_submitted":
            return "Application submitted"
        case "application_accepted":
            return "Application accepted"
        case "application_revision_requested":
            return "Revisions requested"
        case _:
            return "Notification"


def mentioned_membership_ids(
    repo: NotificationRepository,
    community_id: int,
    body: str,
) -> set[int]:
    mentioned: set[int] = set()
    for character in repo.list_community_characters(community_id):
        if mentions_character(body, character):
            mentioned.add(character.membership_id)
    for membership in repo.list_memberships(community_id):
        if membership.is_active and mentions_membership(body, membership):
            mentioned.add(membership.id)
    return mentioned


def mentions_character(body: str, character: Character) -> bool:
    for label in {character.slug, character.name}:
        if re.search(rf"(?<![\w-])@{re.escape(label)}(?![\w-])", body, re.IGNORECASE):
            return True
    return False


def mentions_membership(body: str, membership: CommunityMembership) -> bool:
    return bool(
        re.search(
            rf"(?<![\w-])@{re.escape(membership.username)}(?![\w-])",
            body,
            re.IGNORECASE,
        )
    )
