"""Service-layer commands and read models for the forum slice."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal, cast

from elbysodic.db import ForumRepository, connect, create_schema
from elbysodic.db.seed import DemoSeed, seed_demo_forum
from elbysodic.domain.models import (
    Board,
    Character,
    Community,
    CommunityMembership,
    Notification,
    Post,
    PostRevision,
    Role,
    Thread,
)
from elbysodic.services import policies
from elbysodic.services.markup import post_snippet, render_post_body

DEFAULT_DATABASE_PATH = Path("var/elbysodic.sqlite3")
DATABASE_PATH_ENV = "ELBYSODIC_DB_PATH"
type BoardThreadFilter = Literal["all", "unread", "attention", "mine", "pinned", "locked"]
type ThreadStatus = Literal["open", "active", "paused", "complete", "private", "archived"]
type PostingMode = Literal["freeform", "posting_order"]
type MentionableKind = Literal["character", "writer"]
type MentionableScope = Literal["all", "cast", "characters", "writers", "ooc"]

THREAD_STATUSES: tuple[ThreadStatus, ...] = (
    "open",
    "active",
    "paused",
    "complete",
    "private",
    "archived",
)
POSTING_MODES: tuple[PostingMode, ...] = ("freeform", "posting_order")


@dataclass(frozen=True, slots=True)
class BoardSummary:
    board: Board
    thread_count: int
    post_count: int
    unread_thread_count: int
    latest_thread: Thread | None
    latest_post: PostView | None


@dataclass(frozen=True, slots=True)
class BoardNavigationItem:
    board: Board
    unread_thread_count: int


@dataclass(frozen=True, slots=True)
class ThreadCardBadge:
    label: str
    variant: str


@dataclass(frozen=True, slots=True)
class ThreadSummary:
    thread: Thread
    author: Character
    author_membership: CommunityMembership
    participants: list[Character]
    reply_count: int
    latest_post: PostView | None
    first_unread_post: PostView | None
    is_unread: bool
    is_mine: bool
    needs_attention: bool

    @property
    def badges(self) -> tuple[ThreadCardBadge, ...]:
        badges: list[ThreadCardBadge] = []
        if self.needs_attention:
            badges.append(ThreadCardBadge("needs reply", "warning"))
        elif self.is_unread:
            badges.append(ThreadCardBadge("new replies", "info"))
        if self.is_mine:
            badges.append(ThreadCardBadge("mine", "success"))
        badges.extend(_thread_state_badges(self.thread))
        return tuple(badges)

    @property
    def jump_post(self) -> PostView | None:
        return self.first_unread_post or self.latest_post

    @property
    def jump_label(self) -> str:
        if self.first_unread_post is not None:
            return "First unread"
        return "Jump to latest"


@dataclass(frozen=True, slots=True)
class PostView:
    post: Post
    author: Character
    author_membership: CommunityMembership
    rendered_body: str
    snippet: str
    can_edit: bool
    is_edited: bool
    created_at_label: str
    updated_at_label: str
    anchor: str


@dataclass(frozen=True, slots=True)
class ActivityItem:
    board: Board
    thread: Thread
    post: PostView
    snippet: str
    is_unread: bool


@dataclass(frozen=True, slots=True)
class AttentionItem:
    board: Board
    thread: Thread
    latest_post: PostView
    reply_count: int
    snippet: str


@dataclass(frozen=True, slots=True)
class NotificationItem:
    notification: Notification
    board: Board
    thread: Thread
    post: PostView
    actor: Character
    actor_membership: CommunityMembership
    label: str
    snippet: str
    href: str

    @property
    def is_unread(self) -> bool:
        return self.notification.read_at is None


@dataclass(frozen=True, slots=True)
class NotificationInbox:
    items: list[NotificationItem]
    unread_count: int


@dataclass(frozen=True, slots=True)
class Mentionable:
    kind: MentionableKind
    id: int
    handle: str
    label: str
    detail: str
    avatar_url: str | None
    href: str

    @property
    def tag(self) -> str:
        return f"@{self.handle}"

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "id": self.id,
            "handle": self.handle,
            "tag": self.tag,
            "label": self.label,
            "detail": self.detail,
            "avatar_url": self.avatar_url,
            "href": self.href,
            "initial": self.label[:1],
        }


@dataclass(frozen=True, slots=True)
class CreatedThread:
    thread: Thread
    post: Post


@dataclass(frozen=True, slots=True)
class EditablePostView:
    board: Board
    thread: Thread
    post: PostView


@dataclass(frozen=True, slots=True)
class PostRevisionView:
    revision: PostRevision
    editor_membership: CommunityMembership
    created_at_label: str


@dataclass(frozen=True, slots=True)
class PostRevisionHistory:
    board: Board
    thread: Thread
    post: PostView
    revisions: list[PostRevisionView]


@dataclass(frozen=True, slots=True)
class ThreadObligationItem:
    board: Board
    thread: Thread
    author: Character
    author_membership: CommunityMembership
    participants: list[Character]
    latest_post: PostView | None
    first_unread_post: PostView | None
    last_own_post: PostView | None
    reply_count: int
    is_unread: bool
    is_started_by_roster: bool
    needs_reply: bool
    waiting_on_others: bool

    @property
    def badges(self) -> tuple[ThreadCardBadge, ...]:
        badges: list[ThreadCardBadge] = []
        if self.needs_reply:
            badges.append(ThreadCardBadge("needs reply", "warning"))
        if self.waiting_on_others:
            badges.append(ThreadCardBadge("waiting", "info"))
        if self.is_started_by_roster:
            badges.append(ThreadCardBadge("started by me", "success"))
        if self.is_unread and not self.needs_reply:
            badges.append(ThreadCardBadge("new replies", "info"))
        badges.extend(_thread_state_badges(self.thread))
        return tuple(badges)

    @property
    def jump_post(self) -> PostView | None:
        return self.first_unread_post or self.latest_post

    @property
    def jump_label(self) -> str:
        if self.first_unread_post is not None:
            return "First unread"
        return "Jump to latest"


@dataclass(frozen=True, slots=True)
class CharacterThreadActivity:
    character: Character
    needs_reply: list[ThreadObligationItem]
    waiting_on_others: list[ThreadObligationItem]
    started_by_character: list[ThreadObligationItem]
    participated: list[ThreadObligationItem]


@dataclass(frozen=True, slots=True)
class CharacterRosterCard:
    character: Character
    is_default: bool
    activity: CharacterThreadActivity


@dataclass(frozen=True, slots=True)
class CharacterRosterDashboard:
    cards: list[CharacterRosterCard]


@dataclass(frozen=True, slots=True)
class MemberDirectoryCard:
    membership: CommunityMembership
    role: Role
    roster: list[Character]
    default_character: Character | None
    visible_post_count: int
    active_thread_count: int
    latest_post: CharacterAppearance | None
    is_current_member: bool


@dataclass(frozen=True, slots=True)
class MemberDirectory:
    cards: list[MemberDirectoryCard]


@dataclass(frozen=True, slots=True)
class MemberProfile:
    membership: CommunityMembership
    role: Role
    roster: list[Character]
    default_character: Character | None
    visible_post_count: int
    visible_thread_count: int
    active_threads: list[ThreadObligationItem]
    started_threads: list[ThreadObligationItem]
    recent_posts: list[CharacterAppearance]
    is_current_member: bool


@dataclass(frozen=True, slots=True)
class MyThreadsDashboard:
    needs_reply: list[ThreadObligationItem]
    waiting_on_others: list[ThreadObligationItem]
    started_by_me: list[ThreadObligationItem]
    participated: list[ThreadObligationItem]
    selected_character: Character | None
    roster_activity: list[CharacterThreadActivity]


@dataclass(frozen=True, slots=True)
class CharacterAppearance:
    post: PostView
    thread: Thread
    board: Board


@dataclass(frozen=True, slots=True)
class CharacterProfile:
    character: Character
    owner_membership: CommunityMembership
    is_default: bool
    can_manage: bool
    post_count: int
    thread_count: int
    activity: CharacterThreadActivity
    recent_posts: list[CharacterAppearance]


@dataclass(frozen=True, slots=True)
class ThreadNavigationItem:
    board: Board
    thread: Thread
    jump_post: PostView | None


@dataclass(frozen=True, slots=True)
class ThreadView:
    board: Board
    thread: Thread
    participants: list[Character]
    taggable_characters: list[Character]
    tagged_character_ids: set[int]
    posts: list[PostView]
    can_reply: bool
    can_moderate: bool
    can_manage_scene: bool
    moderation_boards: list[Board]
    is_unread: bool
    previous_thread: ThreadNavigationItem | None
    next_thread: ThreadNavigationItem | None
    next_unread_thread: ThreadNavigationItem | None
    is_watched: bool


@dataclass(frozen=True, slots=True)
class ForumView:
    community: Community
    membership: CommunityMembership
    role: Role
    current_character: Character | None
    roster: list[Character]
    navigation_boards: list[BoardNavigationItem]
    unread_notification_count: int


class AppServices:
    """Small application service facade for the dev forum."""

    def __init__(self, repo: ForumRepository, seed: DemoSeed) -> None:
        self.repo = repo
        self.seed = seed

    def viewer(self) -> ForumView:
        community = self.seed.community
        membership = self.repo.get_membership(community.id, self.seed.membership.id)
        role = self.repo.get_role(community.id, membership.role_id)
        roster = self.repo.list_characters(community.id, membership.id)
        current_character = _resolve_current_character(self.repo, membership, roster)
        return ForumView(
            community=community,
            membership=membership,
            role=role,
            current_character=current_character,
            roster=roster,
            navigation_boards=_board_navigation(self.repo, community.id, membership, role),
            unread_notification_count=self.repo.count_unread_notifications(
                community.id, membership.id
            ),
        )

    def list_boards(self) -> list[BoardSummary]:
        viewer = self.viewer()
        summaries: list[BoardSummary] = []
        for board in self.repo.list_boards(viewer.community.id):
            if not policies.can_view_board(viewer.membership, board, viewer.role):
                continue
            threads = self.repo.list_threads(viewer.community.id, board.id)
            posts_by_thread = {
                thread.id: self.repo.list_posts(viewer.community.id, thread.id)
                for thread in threads
            }
            latest_thread = _latest_thread(threads)
            latest_thread_posts = posts_by_thread.get(latest_thread.id, []) if latest_thread else []
            latest_post = (
                _post_view(self.repo, viewer.community.id, latest_thread_posts[-1])
                if latest_thread_posts
                else None
            )
            summaries.append(
                BoardSummary(
                    board=board,
                    thread_count=len(threads),
                    post_count=sum(len(posts) for posts in posts_by_thread.values()),
                    unread_thread_count=sum(
                        1
                        for thread in threads
                        if _is_unread(
                            self.repo,
                            viewer.community.id,
                            viewer.membership.id,
                            thread,
                        )
                    ),
                    latest_thread=latest_thread,
                    latest_post=latest_post,
                )
            )
        return summaries

    def recent_activity(self, *, limit: int = 6) -> list[ActivityItem]:
        viewer = self.viewer()
        visible_boards = {
            board.id: board
            for board in self.repo.list_boards(viewer.community.id)
            if policies.can_view_board(viewer.membership, board, viewer.role)
        }
        items: list[ActivityItem] = []
        for thread in self.repo.list_threads(viewer.community.id):
            board = visible_boards.get(thread.board_id)
            if board is None:
                continue
            for post in self.repo.list_posts(viewer.community.id, thread.id):
                post_view = _post_view(self.repo, viewer.community.id, post)
                items.append(
                    ActivityItem(
                        board=board,
                        thread=thread,
                        post=post_view,
                        snippet=post_view.snippet,
                        is_unread=_is_unread(
                            self.repo,
                            viewer.community.id,
                            viewer.membership.id,
                            thread,
                        ),
                    )
                )
        return sorted(
            items,
            key=lambda item: (_timestamp_key(item.post.post.created_at), item.post.post.id),
            reverse=True,
        )[:limit]

    def needs_attention(self, *, limit: int = 5) -> list[AttentionItem]:
        viewer = self.viewer()
        roster_character_ids = {character.id for character in viewer.roster}
        visible_boards = {
            board.id: board
            for board in self.repo.list_boards(viewer.community.id)
            if policies.can_view_board(viewer.membership, board, viewer.role)
        }
        items: list[AttentionItem] = []
        for thread in self.repo.list_threads(viewer.community.id):
            board = visible_boards.get(thread.board_id)
            if board is None:
                continue
            if not _is_live_queue_thread(thread):
                continue
            posts = self.repo.list_posts(viewer.community.id, thread.id)
            latest_post = posts[-1] if posts else None
            if latest_post is None:
                continue
            if not _thread_needs_attention(
                self.repo,
                viewer.community.id,
                viewer.membership.id,
                thread,
                latest_post,
                roster_character_ids,
            ):
                continue
            items.append(
                AttentionItem(
                    board=board,
                    thread=thread,
                    latest_post=_post_view(self.repo, viewer.community.id, latest_post),
                    reply_count=max(0, len(posts) - 1),
                    snippet=post_snippet(latest_post.body),
                )
            )
        return sorted(
            items,
            key=lambda item: (
                _timestamp_key(item.latest_post.post.created_at),
                item.latest_post.post.id,
            ),
            reverse=True,
        )[:limit]

    def my_threads(self, *, character_slug: str | None = None) -> MyThreadsDashboard:
        viewer = self.viewer()
        selected_character = self._selected_character(viewer, character_slug)
        target_ids = (
            {selected_character.id}
            if selected_character is not None
            else {character.id for character in viewer.roster}
        )
        sorted_items = self._thread_obligations(viewer, target_ids)
        return MyThreadsDashboard(
            needs_reply=[item for item in sorted_items if item.needs_reply],
            waiting_on_others=[item for item in sorted_items if item.waiting_on_others],
            started_by_me=[item for item in sorted_items if item.is_started_by_roster],
            participated=sorted_items,
            selected_character=selected_character,
            roster_activity=self._roster_activity(viewer),
        )

    def character_roster(self) -> CharacterRosterDashboard:
        viewer = self.viewer()
        return CharacterRosterDashboard(
            cards=[
                CharacterRosterCard(
                    character=character,
                    is_default=viewer.membership.default_character_id == character.id,
                    activity=self._character_activity(viewer, character),
                )
                for character in viewer.roster
            ]
        )

    def members_directory(self) -> MemberDirectory:
        viewer = self.viewer()
        cards = [
            self._member_directory_card(viewer, membership)
            for membership in self.repo.list_memberships(viewer.community.id)
            if membership.is_active
        ]
        return MemberDirectory(cards=cards)

    def read_member(self, username: str) -> MemberProfile:
        viewer = self.viewer()
        membership = self.repo.get_membership_by_username(viewer.community.id, username)
        if not membership.is_active:
            raise LookupError(
                f"membership not found in community {viewer.community.id}: {username}"
            )
        roster = self.repo.list_characters(viewer.community.id, membership.id)
        roster_ids = {character.id for character in roster}
        active_threads = self._thread_obligations(viewer, roster_ids)
        recent_posts = _recent_character_posts(
            self.repo,
            viewer,
            roster_ids,
            limit=8,
        )
        return MemberProfile(
            membership=membership,
            role=self.repo.get_role(viewer.community.id, membership.role_id),
            roster=roster,
            default_character=_default_character(roster, membership.default_character_id),
            visible_post_count=len(_visible_character_posts(self.repo, viewer, roster_ids)),
            visible_thread_count=len(active_threads),
            active_threads=active_threads,
            started_threads=[item for item in active_threads if item.is_started_by_roster],
            recent_posts=recent_posts,
            is_current_member=membership.id == viewer.membership.id,
        )

    def board_threads(
        self,
        board_slug: str,
        *,
        filter_by: BoardThreadFilter = "all",
    ) -> tuple[Board, list[ThreadSummary]]:
        viewer = self.viewer()
        board = self.repo.get_board_by_slug(viewer.community.id, board_slug)
        if not policies.can_view_board(viewer.membership, board, viewer.role):
            raise PermissionError(f"membership {viewer.membership.id} cannot view board {board.id}")

        summaries = []
        roster_character_ids = {character.id for character in viewer.roster}
        for thread in self.repo.list_threads(viewer.community.id, board.id):
            posts = self.repo.list_posts(viewer.community.id, thread.id)
            participants = self.repo.list_thread_participants(viewer.community.id, thread.id)
            participant_ids = {character.id for character in participants}
            is_unread = _is_unread(
                self.repo,
                viewer.community.id,
                viewer.membership.id,
                thread,
            )
            is_mine = _thread_belongs_to_roster(
                thread,
                posts,
                roster_character_ids,
                participant_ids,
            )
            latest_post = posts[-1] if posts else None
            first_unread_post = _first_unread_post(
                self.repo,
                viewer.community.id,
                viewer.membership.id,
                thread,
                posts,
            )
            summary = ThreadSummary(
                thread=thread,
                author=self.repo.get_character(viewer.community.id, thread.author_character_id),
                author_membership=self.repo.get_membership(
                    viewer.community.id,
                    thread.author_membership_id,
                ),
                participants=participants,
                reply_count=max(0, len(posts) - 1),
                latest_post=(
                    _post_view(self.repo, viewer.community.id, latest_post) if latest_post else None
                ),
                first_unread_post=(
                    _post_view(self.repo, viewer.community.id, first_unread_post)
                    if first_unread_post
                    else None
                ),
                is_unread=is_unread,
                is_mine=is_mine,
                needs_attention=(
                    latest_post is not None
                    and _is_live_queue_thread(thread)
                    and _thread_needs_attention(
                        self.repo,
                        viewer.community.id,
                        viewer.membership.id,
                        thread,
                        latest_post,
                        roster_character_ids,
                    )
                ),
            )
            if _thread_matches_filter(summary, filter_by):
                summaries.append(summary)
        return board, summaries

    def next_unread_thread(self, board_slug: str) -> ThreadNavigationItem | None:
        viewer = self.viewer()
        board = self.repo.get_board_by_slug(viewer.community.id, board_slug)
        if not policies.can_view_board(viewer.membership, board, viewer.role):
            raise PermissionError(f"membership {viewer.membership.id} cannot view board {board.id}")
        for thread in self.repo.list_threads(viewer.community.id, board.id):
            if _is_unread(self.repo, viewer.community.id, viewer.membership.id, thread):
                return _thread_navigation_item(
                    self.repo,
                    viewer.community.id,
                    viewer.membership.id,
                    board,
                    thread,
                )
        return None

    def can_start_thread(self, board: Board) -> bool:
        viewer = self.viewer()
        return policies.can_start_thread(viewer.membership, board, viewer.role)

    def read_thread(self, board_slug: str, thread_slug: str) -> ThreadView:
        viewer = self.viewer()
        board = self.repo.get_board_by_slug(viewer.community.id, board_slug)
        if not policies.can_view_board(viewer.membership, board, viewer.role):
            raise PermissionError(f"membership {viewer.membership.id} cannot view board {board.id}")
        thread = self.repo.get_thread_by_slug(viewer.community.id, board.id, thread_slug)
        board_threads = self.repo.list_threads(viewer.community.id, board.id)
        previous_thread, next_thread, next_unread_thread = _thread_navigation(
            self.repo,
            viewer.community.id,
            viewer.membership.id,
            board,
            board_threads,
            thread,
        )
        is_unread = _is_unread(self.repo, viewer.community.id, viewer.membership.id, thread)
        posts = [
            _post_view(
                self.repo,
                viewer.community.id,
                post,
                viewer_membership=viewer.membership,
                viewer_role=viewer.role,
            )
            for post in self.repo.list_posts(viewer.community.id, thread.id)
        ]
        self.repo.mark_thread_read(viewer.community.id, thread.id, viewer.membership.id)
        can_moderate = policies.can_moderate_thread(
            viewer.membership,
            thread,
            viewer.role,
        )
        can_manage_scene = can_moderate or thread.author_membership_id == viewer.membership.id
        posted_character_ids = {post.post.author_character_id for post in posts}
        return ThreadView(
            board=board,
            thread=thread,
            participants=self.repo.list_thread_participants(viewer.community.id, thread.id),
            taggable_characters=taggable_characters(
                self.repo.list_community_characters(viewer.community.id),
                viewer.roster,
            ),
            tagged_character_ids=self.repo.list_thread_participant_ids(
                viewer.community.id,
                thread.id,
            )
            - posted_character_ids
            - {thread.author_character_id},
            posts=posts,
            can_reply=policies.can_reply(viewer.membership, thread, viewer.role),
            can_moderate=can_moderate,
            can_manage_scene=can_manage_scene,
            moderation_boards=(
                [
                    board
                    for board in self.repo.list_boards(viewer.community.id)
                    if policies.can_view_board(viewer.membership, board, viewer.role)
                ]
                if can_moderate
                else []
            ),
            is_unread=is_unread,
            previous_thread=previous_thread,
            next_thread=next_thread,
            next_unread_thread=next_unread_thread,
            is_watched=self.repo.is_thread_watched(
                viewer.community.id,
                thread.id,
                viewer.membership.id,
            ),
        )

    def watch_thread(self, board_slug: str, thread_slug: str) -> None:
        viewer = self.viewer()
        _board, thread = self._visible_thread(viewer, board_slug, thread_slug)
        self.repo.watch_thread(viewer.community.id, thread.id, viewer.membership.id)

    def unwatch_thread(self, board_slug: str, thread_slug: str) -> None:
        viewer = self.viewer()
        _board, thread = self._visible_thread(viewer, board_slug, thread_slug)
        self.repo.unwatch_thread(viewer.community.id, thread.id, viewer.membership.id)

    def notifications(self, *, limit: int = 50) -> NotificationInbox:
        viewer = self.viewer()
        items: list[NotificationItem] = []
        for notification in self.repo.list_notifications(
            viewer.community.id,
            viewer.membership.id,
            limit=limit,
        ):
            item = _notification_item(self.repo, viewer, notification)
            if item is not None:
                items.append(item)
        return NotificationInbox(
            items=items,
            unread_count=self.repo.count_unread_notifications(
                viewer.community.id,
                viewer.membership.id,
            ),
        )

    def search_mentionables(
        self,
        query: str,
        *,
        scope: str = "all",
        limit: int = 8,
    ) -> list[Mentionable]:
        viewer = self.viewer()
        mention_scope = _clean_mentionable_scope(scope)
        cleaned_query = query.strip().lstrip("@")
        if not cleaned_query:
            return []

        items: list[Mentionable] = []
        if mention_scope in {"all", "cast", "characters"}:
            excluded_memberships = [viewer.membership.id] if mention_scope == "cast" else []
            characters = self.repo.search_characters(
                viewer.community.id,
                cleaned_query,
                limit=limit,
                exclude_membership_ids=excluded_memberships,
            )
            items.extend(_character_mentionable(character) for character in characters)

        remaining = max(0, limit - len(items))
        if remaining and mention_scope in {"all", "writers", "ooc"}:
            memberships = self.repo.search_memberships(
                viewer.community.id,
                cleaned_query,
                limit=remaining,
            )
            items.extend(_membership_mentionable(membership) for membership in memberships)

        return items[:limit]

    def open_notification(self, notification_id: int) -> str:
        viewer = self.viewer()
        notification = self.repo.get_notification(viewer.community.id, notification_id)
        if notification.membership_id != viewer.membership.id:
            raise PermissionError(
                f"membership {viewer.membership.id} cannot read notification {notification.id}"
            )
        item = _notification_item(self.repo, viewer, notification)
        if item is None:
            raise LookupError(f"notification target not found: {notification.id}")
        self.repo.mark_notification_read(viewer.community.id, notification.id)
        return item.href

    def mark_all_notifications_read(self) -> None:
        viewer = self.viewer()
        self.repo.mark_all_notifications_read(viewer.community.id, viewer.membership.id)

    def set_default_character(self, character_id: int) -> ForumView:
        viewer = self.viewer()
        character = self.repo.get_character(viewer.community.id, character_id)
        if not policies.can_post_as(viewer.membership, character):
            raise PermissionError(
                f"membership {viewer.membership.id} cannot use character {character_id}"
            )
        self.repo.set_default_character(viewer.community.id, viewer.membership.id, character_id)
        return self.viewer()

    def read_character(self, character_slug: str) -> CharacterProfile:
        viewer = self.viewer()
        character = self.repo.get_character_by_slug(viewer.community.id, character_slug)
        owner_membership = self.repo.get_membership(viewer.community.id, character.membership_id)
        can_manage = character.membership_id == viewer.membership.id
        recent_posts = _recent_character_posts(
            self.repo,
            viewer,
            {character.id},
            limit=5,
        )
        activity = self._character_activity(viewer, character)
        return CharacterProfile(
            character=character,
            owner_membership=owner_membership,
            is_default=can_manage and viewer.membership.default_character_id == character.id,
            can_manage=can_manage,
            post_count=len(_visible_character_posts(self.repo, viewer, {character.id})),
            thread_count=len(activity.started_by_character),
            activity=activity,
            recent_posts=recent_posts,
        )

    def read_post_editor(self, board_slug: str, thread_slug: str, post_id: int) -> EditablePostView:
        viewer = self.viewer()
        board, thread, post = self._editable_post(viewer, board_slug, thread_slug, post_id)
        return EditablePostView(
            board=board,
            thread=thread,
            post=_post_view(
                self.repo,
                viewer.community.id,
                post,
                viewer_membership=viewer.membership,
                viewer_role=viewer.role,
            ),
        )

    def read_post_revisions(
        self,
        board_slug: str,
        thread_slug: str,
        post_id: int,
    ) -> PostRevisionHistory:
        viewer = self.viewer()
        board, thread, post = self._editable_post(viewer, board_slug, thread_slug, post_id)
        revisions = [
            _post_revision_view(self.repo, viewer.community.id, revision)
            for revision in self.repo.list_post_revisions(viewer.community.id, post.id)
        ]
        return PostRevisionHistory(
            board=board,
            thread=thread,
            post=_post_view(
                self.repo,
                viewer.community.id,
                post,
                viewer_membership=viewer.membership,
                viewer_role=viewer.role,
            ),
            revisions=revisions,
        )

    def create_character(
        self,
        *,
        name: str,
        summary: str = "",
        avatar_url: str | None = None,
        make_default: bool = False,
    ) -> Character:
        viewer = self.viewer()
        cleaned_name = name.strip()
        if not cleaned_name:
            raise ValueError("character name is required")
        cleaned_summary = summary.strip()
        cleaned_avatar_url = (avatar_url or "").strip() or None
        slug = _unique_character_slug(self.repo, viewer.community.id, cleaned_name)
        return self.repo.create_character(
            viewer.community.id,
            viewer.membership.id,
            slug,
            cleaned_name,
            avatar_url=cleaned_avatar_url,
            summary=cleaned_summary,
            make_default=make_default,
        )

    def update_character(
        self,
        character_slug: str,
        *,
        name: str,
        summary: str = "",
        avatar_url: str | None = None,
    ) -> Character:
        viewer = self.viewer()
        character = self.repo.get_character_by_slug(viewer.community.id, character_slug)
        if not policies.can_post_as(viewer.membership, character):
            raise PermissionError(
                f"membership {viewer.membership.id} cannot update character {character.id}"
            )
        cleaned_name = name.strip()
        if not cleaned_name:
            raise ValueError("character name is required")
        cleaned_summary = summary.strip()
        cleaned_avatar_url = (avatar_url or "").strip() or None
        slug = character.slug
        if cleaned_name != character.name:
            slug = _unique_character_slug(
                self.repo,
                viewer.community.id,
                cleaned_name,
                current_character_id=character.id,
            )
        return self.repo.update_character(
            viewer.community.id,
            character.id,
            slug=slug,
            name=cleaned_name,
            avatar_url=cleaned_avatar_url,
            summary=cleaned_summary,
        )

    def update_post(self, board_slug: str, thread_slug: str, post_id: int, body: str) -> Post:
        viewer = self.viewer()
        _board, _thread, post = self._editable_post(viewer, board_slug, thread_slug, post_id)
        cleaned = body.strip()
        if not cleaned:
            raise ValueError("post body is required")
        if cleaned == post.body:
            return post
        self.repo.create_post_revision(
            viewer.community.id,
            post.id,
            viewer.membership.id,
            post.body,
            cleaned,
        )
        return self.repo.update_post_body(viewer.community.id, post_id, cleaned)

    def update_thread_state(
        self,
        board_slug: str,
        thread_slug: str,
        *,
        is_locked: bool | None = None,
        is_pinned: bool | None = None,
    ) -> Thread:
        viewer = self.viewer()
        board = self.repo.get_board_by_slug(viewer.community.id, board_slug)
        if not policies.can_view_board(viewer.membership, board, viewer.role):
            raise PermissionError(f"membership {viewer.membership.id} cannot view board {board.id}")
        thread = self.repo.get_thread_by_slug(viewer.community.id, board.id, thread_slug)
        if not policies.can_moderate_thread(viewer.membership, thread, viewer.role):
            raise PermissionError(
                f"membership {viewer.membership.id} cannot moderate thread {thread.id}"
            )
        return self.repo.update_thread_flags(
            viewer.community.id,
            thread.id,
            is_locked=is_locked,
            is_pinned=is_pinned,
        )

    def update_thread_scene(
        self,
        board_slug: str,
        thread_slug: str,
        *,
        status: str,
        location: str = "",
        timeline: str = "",
        summary: str = "",
        posting_mode: str = "freeform",
        participant_ids: list[int] | None = None,
    ) -> Thread:
        viewer = self.viewer()
        _board, thread = self._visible_thread(viewer, board_slug, thread_slug)
        if not self._can_manage_scene(viewer, thread):
            raise PermissionError(
                f"membership {viewer.membership.id} cannot manage scene {thread.id}"
            )
        cleaned_status = _clean_thread_status(status)
        cleaned_posting_mode = _clean_posting_mode(posting_mode)
        self.repo.update_thread_scene(
            viewer.community.id,
            thread.id,
            status=cleaned_status,
            location=location.strip(),
            timeline=timeline.strip(),
            summary=summary.strip(),
            posting_mode=cleaned_posting_mode,
        )
        posted_character_ids = {
            post.author_character_id
            for post in self.repo.list_posts(viewer.community.id, thread.id)
        }
        required_ids = [thread.author_character_id, *posted_character_ids]
        taggable_ids = {
            character.id
            for character in taggable_characters(
                self.repo.list_community_characters(viewer.community.id),
                viewer.roster,
            )
        }
        tag_ids = [
            character_id
            for character_id in _clean_participant_ids(participant_ids or [])
            if character_id in taggable_ids
        ]
        self.repo.set_thread_participants(
            viewer.community.id,
            thread.id,
            _clean_participant_ids([*required_ids, *tag_ids]),
        )
        return self.repo.get_thread(viewer.community.id, thread.id)

    def move_thread(
        self,
        board_slug: str,
        thread_slug: str,
        target_board_id: int,
    ) -> tuple[Board, Thread]:
        viewer = self.viewer()
        board = self.repo.get_board_by_slug(viewer.community.id, board_slug)
        if not policies.can_view_board(viewer.membership, board, viewer.role):
            raise PermissionError(f"membership {viewer.membership.id} cannot view board {board.id}")
        thread = self.repo.get_thread_by_slug(viewer.community.id, board.id, thread_slug)
        if not policies.can_moderate_thread(viewer.membership, thread, viewer.role):
            raise PermissionError(
                f"membership {viewer.membership.id} cannot moderate thread {thread.id}"
            )
        target_board = self.repo.get_board(viewer.community.id, target_board_id)
        if not policies.can_view_board(viewer.membership, target_board, viewer.role):
            raise PermissionError(
                f"membership {viewer.membership.id} cannot move thread into board {target_board.id}"
            )
        if target_board.id == board.id:
            return target_board, thread
        try:
            conflicting = self.repo.get_thread_by_slug(
                viewer.community.id,
                target_board.id,
                thread.slug,
            )
        except LookupError:
            conflicting = None
        if conflicting is not None and conflicting.id != thread.id:
            raise ValueError(
                f"board {target_board.slug} already has a thread at slug {thread.slug}"
            )
        moved = self.repo.move_thread(viewer.community.id, thread.id, target_board.id)
        return target_board, moved

    def reply_to_thread(
        self, board_slug: str, thread_slug: str, character_id: int, body: str
    ) -> Post:
        viewer = self.viewer()
        character = self.repo.get_character(viewer.community.id, character_id)
        if not policies.can_post_as(viewer.membership, character):
            raise PermissionError(
                f"membership {viewer.membership.id} cannot use character {character_id}"
            )
        board = self.repo.get_board_by_slug(viewer.community.id, board_slug)
        thread = self.repo.get_thread_by_slug(viewer.community.id, board.id, thread_slug)
        if not policies.can_view_board(viewer.membership, board, viewer.role):
            raise PermissionError(f"membership {viewer.membership.id} cannot view board {board.id}")
        if not policies.can_reply(viewer.membership, thread, viewer.role):
            raise PermissionError(
                f"membership {viewer.membership.id} cannot reply to thread {thread.id}"
            )
        cleaned = body.strip()
        if not cleaned:
            raise ValueError("reply body is required")
        post = self.repo.create_post(viewer.community.id, thread.id, character.id, cleaned)
        self._notify_post_created(viewer, thread, post)
        self.repo.watch_thread(viewer.community.id, thread.id, viewer.membership.id)
        self.repo.mark_thread_read(viewer.community.id, thread.id, viewer.membership.id)
        return post

    def start_thread(
        self,
        *,
        board_slug: str,
        character_id: int,
        title: str,
        body: str,
        status: str = "active",
        location: str = "",
        timeline: str = "",
        summary: str = "",
        posting_mode: str = "freeform",
        participant_ids: list[int] | None = None,
    ) -> Thread:
        return self.start_thread_with_post(
            board_slug=board_slug,
            character_id=character_id,
            title=title,
            body=body,
            status=status,
            location=location,
            timeline=timeline,
            summary=summary,
            posting_mode=posting_mode,
            participant_ids=participant_ids,
        ).thread

    def start_thread_with_post(
        self,
        *,
        board_slug: str,
        character_id: int,
        title: str,
        body: str,
        status: str = "active",
        location: str = "",
        timeline: str = "",
        summary: str = "",
        posting_mode: str = "freeform",
        participant_ids: list[int] | None = None,
    ) -> CreatedThread:
        viewer = self.viewer()
        character = self.repo.get_character(viewer.community.id, character_id)
        if not policies.can_post_as(viewer.membership, character):
            raise PermissionError(
                f"membership {viewer.membership.id} cannot use character {character_id}"
            )
        board = self.repo.get_board_by_slug(viewer.community.id, board_slug)
        if not policies.can_start_thread(viewer.membership, board, viewer.role):
            raise PermissionError(
                f"membership {viewer.membership.id} cannot start threads in board {board.id}"
            )
        cleaned_title = title.strip()
        if not cleaned_title:
            raise ValueError("thread title is required")
        cleaned_body = body.strip()
        if not cleaned_body:
            raise ValueError("opening post is required")
        cleaned_status = _clean_thread_status(status)
        cleaned_posting_mode = _clean_posting_mode(posting_mode)
        cleaned_location = location.strip()
        cleaned_timeline = timeline.strip()
        cleaned_summary = summary.strip()
        cleaned_participant_ids = _clean_participant_ids([character.id, *(participant_ids or [])])
        for participant_id in cleaned_participant_ids:
            self.repo.get_character(viewer.community.id, participant_id)
        slug = _unique_thread_slug(self.repo, viewer.community.id, board.id, cleaned_title)
        thread = self.repo.create_thread(
            viewer.community.id,
            board.id,
            character.id,
            slug,
            cleaned_title,
            status=cleaned_status,
            location=cleaned_location,
            timeline=cleaned_timeline,
            summary=cleaned_summary,
            posting_mode=cleaned_posting_mode,
        )
        self.repo.set_thread_participants(
            viewer.community.id,
            thread.id,
            cleaned_participant_ids,
        )
        post = self.repo.create_post(viewer.community.id, thread.id, character.id, cleaned_body)
        thread = self.repo.get_thread(viewer.community.id, thread.id)
        self.repo.watch_thread(viewer.community.id, thread.id, viewer.membership.id)
        self.repo.mark_thread_read(viewer.community.id, thread.id, viewer.membership.id)
        return CreatedThread(thread=thread, post=post)

    def _visible_thread(
        self,
        viewer: ForumView,
        board_slug: str,
        thread_slug: str,
    ) -> tuple[Board, Thread]:
        board = self.repo.get_board_by_slug(viewer.community.id, board_slug)
        if not policies.can_view_board(viewer.membership, board, viewer.role):
            raise PermissionError(f"membership {viewer.membership.id} cannot view board {board.id}")
        thread = self.repo.get_thread_by_slug(viewer.community.id, board.id, thread_slug)
        return board, thread

    def _can_manage_scene(self, viewer: ForumView, thread: Thread) -> bool:
        return thread.author_membership_id == viewer.membership.id or policies.can_moderate_thread(
            viewer.membership,
            thread,
            viewer.role,
        )

    def _notify_post_created(
        self,
        viewer: ForumView,
        thread: Thread,
        post: Post,
    ) -> None:
        mentioned_memberships = _mentioned_membership_ids(
            self.repo,
            viewer.community.id,
            post.body,
        )
        watch_memberships = set(
            self.repo.list_thread_watch_membership_ids(viewer.community.id, thread.id)
        )
        actor_membership_id = viewer.membership.id
        for membership_id in mentioned_memberships:
            if membership_id != actor_membership_id:
                self.repo.create_notification(
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
                self.repo.create_notification(
                    viewer.community.id,
                    membership_id,
                    kind="thread_reply",
                    thread_id=thread.id,
                    post_id=post.id,
                    actor_membership_id=actor_membership_id,
                    actor_character_id=post.author_character_id,
                )

    def _editable_post(
        self,
        viewer: ForumView,
        board_slug: str,
        thread_slug: str,
        post_id: int,
    ) -> tuple[Board, Thread, Post]:
        board = self.repo.get_board_by_slug(viewer.community.id, board_slug)
        if not policies.can_view_board(viewer.membership, board, viewer.role):
            raise PermissionError(f"membership {viewer.membership.id} cannot view board {board.id}")
        thread = self.repo.get_thread_by_slug(viewer.community.id, board.id, thread_slug)
        post = self.repo.get_post(viewer.community.id, post_id)
        if post.thread_id != thread.id:
            raise LookupError(f"post {post_id} does not belong to thread {thread.id}")
        if not policies.can_edit_post(viewer.membership, post, viewer.role):
            raise PermissionError(f"membership {viewer.membership.id} cannot edit post {post.id}")
        return board, thread, post

    def _selected_character(
        self,
        viewer: ForumView,
        character_slug: str | None,
    ) -> Character | None:
        if not character_slug:
            return None
        character = self.repo.get_character_by_slug(viewer.community.id, character_slug)
        if character.membership_id != viewer.membership.id:
            raise PermissionError(
                f"membership {viewer.membership.id} cannot filter by character {character.id}"
            )
        return character

    def _character_activity(
        self,
        viewer: ForumView,
        character: Character,
    ) -> CharacterThreadActivity:
        items = self._thread_obligations(viewer, {character.id})
        return CharacterThreadActivity(
            character=character,
            needs_reply=[item for item in items if item.needs_reply],
            waiting_on_others=[item for item in items if item.waiting_on_others],
            started_by_character=[item for item in items if item.is_started_by_roster],
            participated=items,
        )

    def _roster_activity(self, viewer: ForumView) -> list[CharacterThreadActivity]:
        return [self._character_activity(viewer, character) for character in viewer.roster]

    def _member_directory_card(
        self,
        viewer: ForumView,
        membership: CommunityMembership,
    ) -> MemberDirectoryCard:
        roster = self.repo.list_characters(viewer.community.id, membership.id)
        roster_ids = {character.id for character in roster}
        active_threads = self._thread_obligations(viewer, roster_ids)
        latest_posts = _recent_character_posts(self.repo, viewer, roster_ids, limit=1)
        return MemberDirectoryCard(
            membership=membership,
            role=self.repo.get_role(viewer.community.id, membership.role_id),
            roster=roster,
            default_character=_default_character(roster, membership.default_character_id),
            visible_post_count=len(_visible_character_posts(self.repo, viewer, roster_ids)),
            active_thread_count=len(active_threads),
            latest_post=latest_posts[0] if latest_posts else None,
            is_current_member=membership.id == viewer.membership.id,
        )

    def _thread_obligations(
        self,
        viewer: ForumView,
        target_character_ids: set[int],
    ) -> list[ThreadObligationItem]:
        if not target_character_ids:
            return []
        visible_boards = {
            board.id: board
            for board in self.repo.list_boards(viewer.community.id)
            if policies.can_view_board(viewer.membership, board, viewer.role)
        }
        items = []
        for thread in self.repo.list_threads(viewer.community.id):
            board = visible_boards.get(thread.board_id)
            if board is None:
                continue
            if not _is_live_queue_thread(thread):
                continue
            posts = self.repo.list_posts(viewer.community.id, thread.id)
            participants = self.repo.list_thread_participants(viewer.community.id, thread.id)
            participant_ids = {character.id for character in participants}
            if not _thread_belongs_to_roster(
                thread,
                posts,
                target_character_ids,
                participant_ids,
            ):
                continue
            latest_post = posts[-1] if posts else None
            first_unread_post = _first_unread_post(
                self.repo,
                viewer.community.id,
                viewer.membership.id,
                thread,
                posts,
            )
            last_own_post = _last_roster_post(posts, target_character_ids)
            needs_reply = (
                latest_post is not None
                and latest_post.author_character_id not in target_character_ids
                and _is_reply_obligation_thread(thread)
            )
            waiting_on_others = (
                latest_post is not None
                and latest_post.author_character_id in target_character_ids
                and _is_reply_obligation_thread(thread)
            )
            items.append(
                ThreadObligationItem(
                    board=board,
                    thread=thread,
                    author=self.repo.get_character(
                        viewer.community.id,
                        thread.author_character_id,
                    ),
                    author_membership=self.repo.get_membership(
                        viewer.community.id,
                        thread.author_membership_id,
                    ),
                    participants=participants,
                    latest_post=(
                        _post_view(self.repo, viewer.community.id, latest_post)
                        if latest_post
                        else None
                    ),
                    first_unread_post=(
                        _post_view(self.repo, viewer.community.id, first_unread_post)
                        if first_unread_post
                        else None
                    ),
                    last_own_post=(
                        _post_view(self.repo, viewer.community.id, last_own_post)
                        if last_own_post
                        else None
                    ),
                    reply_count=max(0, len(posts) - 1),
                    is_unread=_is_unread(
                        self.repo,
                        viewer.community.id,
                        viewer.membership.id,
                        thread,
                    ),
                    is_started_by_roster=thread.author_character_id in target_character_ids,
                    needs_reply=needs_reply,
                    waiting_on_others=waiting_on_others,
                )
            )
        return sorted(
            items,
            key=lambda item: (_timestamp_key(item.thread.updated_at), item.thread.id),
            reverse=True,
        )


def create_services(path: str | Path | None = None) -> AppServices:
    database_path = _resolve_database_path(path)
    if database_path != ":memory:":
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
    connection = connect(database_path, check_same_thread=False)
    create_schema(connection)
    repo = ForumRepository(connection)
    seed = seed_demo_forum(repo)
    return AppServices(repo, seed)


def initialize_database(path: str | Path | None = None, *, seed_demo: bool = True) -> Path:
    database_path = _resolve_database_path(path)
    if database_path == ":memory:":
        raise ValueError("persistent database initialization requires a filesystem path")
    resolved_path = Path(database_path)
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    connection = connect(resolved_path)
    try:
        create_schema(connection)
        if seed_demo:
            seed_demo_forum(ForumRepository(connection))
    finally:
        connection.close()
    return resolved_path


def default_database_path() -> Path:
    configured = os.environ.get(DATABASE_PATH_ENV)
    if configured:
        return Path(configured)
    return DEFAULT_DATABASE_PATH


def _resolve_database_path(path: str | Path | None) -> str | Path:
    if path is None:
        return default_database_path()
    return path


def _resolve_current_character(
    repo: ForumRepository,
    membership: CommunityMembership,
    roster: list[Character],
) -> Character | None:
    if not roster:
        return None
    if membership.default_character_id is not None:
        return repo.get_character(membership.community_id, membership.default_character_id)
    return roster[0]


def _board_navigation(
    repo: ForumRepository,
    community_id: int,
    membership: CommunityMembership,
    role: Role,
) -> list[BoardNavigationItem]:
    items: list[BoardNavigationItem] = []
    for board in repo.list_boards(community_id):
        if not policies.can_view_board(membership, board, role):
            continue
        threads = repo.list_threads(community_id, board.id)
        unread_thread_count = sum(
            1 for thread in threads if _is_unread(repo, community_id, membership.id, thread)
        )
        items.append(BoardNavigationItem(board=board, unread_thread_count=unread_thread_count))
    return items


def _default_character(
    roster: list[Character],
    default_character_id: int | None,
) -> Character | None:
    if default_character_id is None:
        return roster[0] if roster else None
    return next(
        (character for character in roster if character.id == default_character_id),
        roster[0] if roster else None,
    )


def _visible_character_posts(
    repo: ForumRepository,
    viewer: ForumView,
    character_ids: set[int],
) -> list[CharacterAppearance]:
    if not character_ids:
        return []
    visible_boards = {
        board.id: board
        for board in repo.list_boards(viewer.community.id)
        if policies.can_view_board(viewer.membership, board, viewer.role)
    }
    items: list[CharacterAppearance] = []
    for character_id in character_ids:
        for post in repo.list_posts_by_character(viewer.community.id, character_id):
            thread = repo.get_thread(viewer.community.id, post.thread_id)
            board = visible_boards.get(thread.board_id)
            if board is None:
                continue
            items.append(
                CharacterAppearance(
                    post=_post_view(repo, viewer.community.id, post),
                    thread=thread,
                    board=board,
                )
            )
    return sorted(
        items,
        key=lambda item: (_timestamp_key(item.post.post.created_at), item.post.post.id),
        reverse=True,
    )


def _recent_character_posts(
    repo: ForumRepository,
    viewer: ForumView,
    character_ids: set[int],
    *,
    limit: int,
) -> list[CharacterAppearance]:
    return _visible_character_posts(repo, viewer, character_ids)[:limit]


def _latest_thread(threads: list[Thread]) -> Thread | None:
    if not threads:
        return None
    return max(threads, key=lambda thread: (_timestamp_key(thread.updated_at), thread.id))


def _is_unread(
    repo: ForumRepository,
    community_id: int,
    membership_id: int,
    thread: Thread,
) -> bool:
    read_at = repo.get_thread_read_at(community_id, thread.id, membership_id)
    if read_at is None:
        return True
    return _timestamp_key(read_at) < _timestamp_key(thread.updated_at)


def _first_unread_post(
    repo: ForumRepository,
    community_id: int,
    membership_id: int,
    thread: Thread,
    posts: list[Post],
) -> Post | None:
    if not posts or not _is_unread(repo, community_id, membership_id, thread):
        return None
    read_at = repo.get_thread_read_at(community_id, thread.id, membership_id)
    if read_at is None:
        return posts[0]
    read_stamp = _timestamp_key(read_at)
    for post in posts:
        if _timestamp_key(post.created_at) > read_stamp:
            return post
    return posts[-1]


def _thread_navigation(
    repo: ForumRepository,
    community_id: int,
    membership_id: int,
    board: Board,
    threads: list[Thread],
    current: Thread,
) -> tuple[ThreadNavigationItem | None, ThreadNavigationItem | None, ThreadNavigationItem | None]:
    current_index = _thread_index(threads, current.id)
    if current_index is None:
        return None, None, None
    previous_thread = (
        _thread_navigation_item(
            repo, community_id, membership_id, board, threads[current_index - 1]
        )
        if current_index > 0
        else None
    )
    next_thread = (
        _thread_navigation_item(
            repo, community_id, membership_id, board, threads[current_index + 1]
        )
        if current_index + 1 < len(threads)
        else None
    )
    ordered_candidates = threads[current_index + 1 :] + threads[:current_index]
    next_unread_thread = None
    for thread in ordered_candidates:
        if _is_unread(repo, community_id, membership_id, thread):
            next_unread_thread = _thread_navigation_item(
                repo,
                community_id,
                membership_id,
                board,
                thread,
            )
            break
    return previous_thread, next_thread, next_unread_thread


def _thread_index(threads: list[Thread], thread_id: int) -> int | None:
    for index, thread in enumerate(threads):
        if thread.id == thread_id:
            return index
    return None


def _thread_navigation_item(
    repo: ForumRepository,
    community_id: int,
    membership_id: int,
    board: Board,
    thread: Thread,
) -> ThreadNavigationItem:
    posts = repo.list_posts(community_id, thread.id)
    jump_post = _first_unread_post(repo, community_id, membership_id, thread, posts)
    if jump_post is None and posts:
        jump_post = posts[-1]
    return ThreadNavigationItem(
        board=board,
        thread=thread,
        jump_post=_post_view(repo, community_id, jump_post) if jump_post else None,
    )


def _thread_belongs_to_roster(
    thread: Thread,
    posts: list[Post],
    roster_character_ids: set[int],
    participant_ids: set[int] | None = None,
) -> bool:
    if thread.author_character_id in roster_character_ids:
        return True
    if participant_ids and participant_ids.intersection(roster_character_ids):
        return True
    return any(post.author_character_id in roster_character_ids for post in posts)


def _last_roster_post(posts: list[Post], roster_character_ids: set[int]) -> Post | None:
    for post in reversed(posts):
        if post.author_character_id in roster_character_ids:
            return post
    return None


def _thread_needs_attention(
    repo: ForumRepository,
    community_id: int,
    membership_id: int,
    thread: Thread,
    latest_post: Post,
    roster_character_ids: set[int],
) -> bool:
    return (
        _is_unread(repo, community_id, membership_id, thread)
        and latest_post.author_character_id not in roster_character_ids
    )


def _thread_matches_filter(summary: ThreadSummary, filter_by: BoardThreadFilter) -> bool:
    match filter_by:
        case "all":
            return True
        case "unread":
            return summary.is_unread
        case "attention":
            return summary.needs_attention
        case "mine":
            return summary.is_mine
        case "pinned":
            return summary.thread.is_pinned
        case "locked":
            return summary.thread.is_locked


def _thread_state_badges(thread: Thread) -> tuple[ThreadCardBadge, ...]:
    badges: list[ThreadCardBadge] = []
    status_badge = _thread_status_badge(thread.status)
    if status_badge is not None:
        badges.append(status_badge)
    if thread.is_pinned:
        badges.append(ThreadCardBadge("pinned", "warning"))
    if thread.is_locked:
        badges.append(ThreadCardBadge("locked", "muted"))
    return tuple(badges)


def _thread_status_badge(status: str) -> ThreadCardBadge | None:
    match status:
        case "open":
            return ThreadCardBadge("open to join", "info")
        case "paused":
            return ThreadCardBadge("paused", "warning")
        case "complete":
            return ThreadCardBadge("complete", "muted")
        case "private":
            return ThreadCardBadge("private scene", "muted")
        case "archived":
            return ThreadCardBadge("archived", "muted")
        case _:
            return None


def _is_live_queue_thread(thread: Thread) -> bool:
    return thread.status in {"open", "active"} and not thread.is_locked


def _is_reply_obligation_thread(thread: Thread) -> bool:
    return _is_live_queue_thread(thread)


def _clean_thread_status(value: str) -> ThreadStatus:
    status = value.strip().lower().replace("-", "_")
    if status not in THREAD_STATUSES:
        raise ValueError("choose a valid thread status")
    return cast(ThreadStatus, status)


def _clean_posting_mode(value: str) -> PostingMode:
    mode = value.strip().lower().replace("-", "_")
    if mode not in POSTING_MODES:
        raise ValueError("choose a valid posting mode")
    return cast(PostingMode, mode)


def _clean_participant_ids(character_ids: list[int]) -> list[int]:
    cleaned: list[int] = []
    for character_id in character_ids:
        if character_id not in cleaned:
            cleaned.append(character_id)
    return cleaned


def _clean_mentionable_scope(value: str) -> MentionableScope:
    scope = value.strip().lower().replace("-", "_")
    if scope not in {"all", "cast", "characters", "writers", "ooc"}:
        return "all"
    return cast(MentionableScope, scope)


def _character_mentionable(character: Character) -> Mentionable:
    return Mentionable(
        kind="character",
        id=character.id,
        handle=character.slug,
        label=character.name,
        detail="Character",
        avatar_url=character.avatar_url,
        href=f"/characters/{character.slug}",
    )


def _membership_mentionable(membership: CommunityMembership) -> Mentionable:
    return Mentionable(
        kind="writer",
        id=membership.id,
        handle=membership.username,
        label=membership.display_name,
        detail=f"Writer @{membership.username}",
        avatar_url=membership.avatar_url,
        href=f"/members/{membership.username}",
    )


def taggable_characters(characters: list[Character], roster: list[Character]) -> list[Character]:
    own_membership_ids = {character.membership_id for character in roster}
    return [
        character for character in characters if character.membership_id not in own_membership_ids
    ]


def _notification_item(
    repo: ForumRepository,
    viewer: ForumView,
    notification: Notification,
) -> NotificationItem | None:
    thread = repo.get_thread(viewer.community.id, notification.thread_id)
    board = repo.get_board(viewer.community.id, thread.board_id)
    if not policies.can_view_board(viewer.membership, board, viewer.role):
        return None
    post = repo.get_post(viewer.community.id, notification.post_id)
    post_view = _post_view(repo, viewer.community.id, post)
    actor = repo.get_character(viewer.community.id, notification.actor_character_id)
    actor_membership = repo.get_membership(
        viewer.community.id,
        notification.actor_membership_id,
    )
    return NotificationItem(
        notification=notification,
        board=board,
        thread=thread,
        post=post_view,
        actor=actor,
        actor_membership=actor_membership,
        label=_notification_label(notification.kind),
        snippet=post_view.snippet,
        href=f"/boards/{board.slug}/threads/{thread.slug}#{post_view.anchor}",
    )


def _notification_label(kind: str) -> str:
    match kind:
        case "mention":
            return "Mention"
        case "thread_reply":
            return "Watched thread"
        case _:
            return "Notification"


def _mentioned_membership_ids(
    repo: ForumRepository,
    community_id: int,
    body: str,
) -> set[int]:
    mentioned: set[int] = set()
    for character in repo.list_community_characters(community_id):
        if _mentions_character(body, character):
            mentioned.add(character.membership_id)
    for membership in repo.list_memberships(community_id):
        if membership.is_active and _mentions_membership(body, membership):
            mentioned.add(membership.id)
    return mentioned


def _mentions_character(body: str, character: Character) -> bool:
    for label in {character.slug, character.name}:
        if re.search(rf"(?<![\w-])@{re.escape(label)}(?![\w-])", body, re.IGNORECASE):
            return True
    return False


def _mentions_membership(body: str, membership: CommunityMembership) -> bool:
    return bool(
        re.search(
            rf"(?<![\w-])@{re.escape(membership.username)}(?![\w-])",
            body,
            re.IGNORECASE,
        )
    )


def _post_view(
    repo: ForumRepository,
    community_id: int,
    post: Post,
    *,
    viewer_membership: CommunityMembership | None = None,
    viewer_role: Role | None = None,
) -> PostView:
    return PostView(
        post=post,
        author=repo.get_character(community_id, post.author_character_id),
        author_membership=repo.get_membership(
            community_id,
            post.author_membership_id,
        ),
        rendered_body=render_post_body(post.body),
        snippet=post_snippet(post.body),
        can_edit=(
            viewer_membership is not None
            and policies.can_edit_post(viewer_membership, post, viewer_role)
        ),
        is_edited=_timestamp_key(post.updated_at) > _timestamp_key(post.created_at),
        created_at_label=_timestamp_label(post.created_at),
        updated_at_label=_timestamp_label(post.updated_at),
        anchor=f"post-{post.id}",
    )


def _post_revision_view(
    repo: ForumRepository,
    community_id: int,
    revision: PostRevision,
) -> PostRevisionView:
    return PostRevisionView(
        revision=revision,
        editor_membership=repo.get_membership(community_id, revision.editor_membership_id),
        created_at_label=_timestamp_label(revision.created_at),
    )


def _timestamp_key(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return datetime.min


def _timestamp_label(value: str) -> str:
    try:
        stamp = datetime.fromisoformat(value)
    except ValueError:
        return value
    hour = stamp.hour % 12 or 12
    meridiem = "AM" if stamp.hour < 12 else "PM"
    zone = stamp.tzname() or "UTC"
    return f"{stamp:%b} {stamp.day}, {stamp.year} {hour}:{stamp.minute:02d} {meridiem} {zone}"


def _unique_character_slug(
    repo: ForumRepository,
    community_id: int,
    name: str,
    *,
    current_character_id: int | None = None,
) -> str:
    base = _slugify(name)
    slug = base
    suffix = 2
    while True:
        try:
            existing = repo.get_character_by_slug(community_id, slug)
        except LookupError:
            return slug
        if existing.id == current_character_id:
            return slug
        slug = f"{base}-{suffix}"
        suffix += 1


def _unique_thread_slug(
    repo: ForumRepository,
    community_id: int,
    board_id: int,
    title: str,
) -> str:
    base = _slugify(title)
    slug = base
    suffix = 2
    while True:
        try:
            repo.get_thread_by_slug(community_id, board_id, slug)
        except LookupError:
            return slug
        slug = f"{base}-{suffix}"
        suffix += 1


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "character"
