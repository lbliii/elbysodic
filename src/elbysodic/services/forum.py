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
from elbysodic.domain.boards import is_community_board, is_location_board
from elbysodic.domain.models import (
    Board,
    Character,
    CharacterReserve,
    Community,
    CommunityMembership,
    Facet,
    FacetGroup,
    Material,
    Notification,
    Post,
    PostRevision,
    Role,
    Thread,
    WantedAd,
    WantedAdInterest,
)
from elbysodic.services import policies
from elbysodic.services.markup import MentionLink, post_snippet, render_post_body

DEFAULT_DATABASE_PATH = Path("var/elbysodic.sqlite3")
DATABASE_PATH_ENV = "ELBYSODIC_DB_PATH"
type BoardThreadFilter = Literal["all", "unread", "attention", "mine", "pinned", "locked"]
type ThreadStatus = Literal["open", "active", "paused", "complete", "private", "archived"]
type PostingMode = Literal["freeform", "posting_order"]
type MentionableKind = Literal["character", "writer"]
type MentionableScope = Literal["all", "cast", "characters", "writers", "ooc"]
type ApplicationStatus = Literal[
    "draft",
    "submitted",
    "accepted",
    "revision_requested",
    "rejected",
]

THREAD_STATUSES: tuple[ThreadStatus, ...] = (
    "open",
    "active",
    "paused",
    "complete",
    "private",
    "archived",
)
POSTING_MODES: tuple[PostingMode, ...] = ("freeform", "posting_order")
APPLICATION_STATUS_LABELS: dict[str, str] = {
    "draft": "Draft",
    "submitted": "Submitted",
    "accepted": "Accepted",
    "revision_requested": "Revision requested",
    "rejected": "Rejected",
}
APPLICATION_STATUS_VARIANTS: dict[str, str] = {
    "draft": "muted",
    "submitted": "info",
    "accepted": "success",
    "revision_requested": "warning",
    "rejected": "muted",
}


@dataclass(frozen=True, slots=True)
class BoardSummary:
    board: Board
    child_boards: list[Board]
    thread_count: int
    post_count: int
    unread_thread_count: int
    latest_thread: Thread | None
    latest_board: Board | None
    latest_post: PostView | None
    facets: list[FacetTag]
    is_relevant_to_current_face: bool

    @property
    def href(self) -> str:
        return f"/boards/{self.board.slug}"

    @property
    def latest_href(self) -> str | None:
        if self.latest_thread is None:
            return None
        board = self.latest_board or self.board
        anchor = f"#{self.latest_post.anchor}" if self.latest_post else ""
        return f"/boards/{board.slug}/threads/{self.latest_thread.slug}{anchor}"

    @property
    def display_tagline(self) -> str:
        return self.board.tagline or self.board.board_kind

    @property
    def has_children(self) -> bool:
        return bool(self.child_boards)


@dataclass(frozen=True, slots=True)
class BoardNavigationItem:
    board: Board
    unread_thread_count: int


@dataclass(frozen=True, slots=True)
class LocationNavigationGroup:
    parent: BoardNavigationItem
    children: list[BoardNavigationItem]

    @property
    def unread_thread_count(self) -> int:
        return self.parent.unread_thread_count + sum(
            child.unread_thread_count for child in self.children
        )


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
    facets: list[FacetTag]
    is_relevant_to_current_face: bool
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
    board: Board | None
    thread: Thread | None
    post: PostView | None
    wanted_ad: WantedAd | None
    actor: Character
    actor_membership: CommunityMembership
    label: str
    title: str
    created_at_label: str
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
    application_status_label: str
    application_status_variant: str


@dataclass(frozen=True, slots=True)
class CharacterRosterDashboard:
    cards: list[CharacterRosterCard]


@dataclass(frozen=True, slots=True)
class ApplicationCharacterView:
    character: Character
    membership: CommunityMembership
    facets: list[FacetTag]
    reserves: list[CharacterReserveView]
    status_label: str
    status_variant: str
    is_owned_by_viewer: bool


@dataclass(frozen=True, slots=True)
class ApplicationsDesk:
    my_applications: list[ApplicationCharacterView]
    review_queue: list[ApplicationCharacterView]
    accepted_characters: list[ApplicationCharacterView]
    application_materials: list[MaterialSummary]
    can_review: bool


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
class FacetTag:
    group: FacetGroup
    facet: Facet

    @property
    def label(self) -> str:
        return self.facet.name

    @property
    def group_label(self) -> str:
        return self.group.name


@dataclass(frozen=True, slots=True)
class FacetFilterOption:
    tag: FacetTag
    href: str
    is_selected: bool


@dataclass(frozen=True, slots=True)
class FacetFilterGroup:
    group: FacetGroup
    options: list[FacetFilterOption]


@dataclass(frozen=True, slots=True)
class DiscoveryCharacterResult:
    character: Character
    owner_membership: CommunityMembership
    facets: list[FacetTag]
    matching_facets: list[FacetTag]


@dataclass(frozen=True, slots=True)
class DiscoveryThreadResult:
    board: Board
    thread: Thread
    author: Character
    participants: list[Character]
    facets: list[FacetTag]
    matching_facets: list[FacetTag]
    reply_count: int


@dataclass(frozen=True, slots=True)
class PlotDiscovery:
    selected_facets: list[FacetTag]
    active_face_facets: list[FacetTag]
    filter_groups: list[FacetFilterGroup]
    characters: list[DiscoveryCharacterResult]
    open_threads: list[DiscoveryThreadResult]
    used_active_face_lens: bool


@dataclass(frozen=True, slots=True)
class MaterialSummary:
    material: Material
    facets: list[FacetTag]
    rendered_summary: str
    type_label: str


@dataclass(frozen=True, slots=True)
class MaterialDetail:
    material: Material
    facets: list[FacetTag]
    rendered_body: object
    type_label: str
    related_materials: list[MaterialSummary]


@dataclass(frozen=True, slots=True)
class WorldHub:
    featured: list[MaterialSummary]
    guides: list[MaterialSummary]
    events: list[MaterialSummary]
    application_materials: list[MaterialSummary]


@dataclass(frozen=True, slots=True)
class WantedAdSummary:
    wanted_ad: WantedAd
    creator_membership: CommunityMembership
    creator_character: Character | None
    related_material: Material | None
    related_characters: list[Character]
    facets: list[FacetTag]
    type_label: str


@dataclass(frozen=True, slots=True)
class WantedAdInterestView:
    interest: WantedAdInterest
    membership: CommunityMembership
    character: Character
    created_at_label: str


@dataclass(frozen=True, slots=True)
class CharacterReserveView:
    reserve: CharacterReserve
    membership: CommunityMembership
    character: Character
    wanted_ad: WantedAd | None
    created_at_label: str


@dataclass(frozen=True, slots=True)
class WantedAdDetail:
    wanted_ad: WantedAd
    creator_membership: CommunityMembership
    creator_character: Character | None
    related_material: Material | None
    related_characters: list[Character]
    facets: list[FacetTag]
    interests: list[WantedAdInterestView]
    reserves: list[CharacterReserveView]
    reserve_interest_ids: set[int]
    viewer_interest: WantedAdInterestView | None
    can_express_interest: bool
    is_created_by_viewer: bool
    can_manage: bool
    rendered_body: object
    type_label: str
    related_ads: list[WantedAdSummary]


@dataclass(frozen=True, slots=True)
class WantedBoard:
    open_ads: list[WantedAdSummary]


@dataclass(frozen=True, slots=True)
class CastingWantedItem:
    wanted_ad: WantedAdSummary
    interests: list[WantedAdInterestView]
    reserves: list[CharacterReserveView]
    is_created_by_viewer: bool


@dataclass(frozen=True, slots=True)
class CastingDesk:
    active_face: Character | None
    active_face_reserves: list[CharacterReserveView]
    my_reserves: list[CharacterReserveView]
    active_reserves: list[CharacterReserveView]
    wanted_with_interest: list[CastingWantedItem]


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
    facets: list[FacetTag]
    wanted_ads: list[WantedAdSummary]
    reserves: list[CharacterReserveView]
    application_status_label: str
    application_status_variant: str
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
    board_facets: list[FacetTag]
    thread_facets: list[FacetTag]
    taggable_characters: list[Character]
    tagged_character_ids: set[int]
    posts: list[PostView]
    can_reply: bool
    can_join_scene: bool
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
    location_navigation_boards: list[BoardNavigationItem]
    location_navigation_groups: list[LocationNavigationGroup]
    community_navigation_boards: list[BoardNavigationItem]
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
        navigation_boards = _board_navigation(self.repo, community.id, membership, role)
        return ForumView(
            community=community,
            membership=membership,
            role=role,
            current_character=current_character,
            roster=roster,
            navigation_boards=navigation_boards,
            location_navigation_boards=[
                item
                for item in navigation_boards
                if item.board.parent_board_id is None and is_location_board(item.board)
            ],
            location_navigation_groups=_location_navigation_groups(navigation_boards),
            community_navigation_boards=[
                item
                for item in navigation_boards
                if item.board.parent_board_id is None and is_community_board(item.board)
            ],
            unread_notification_count=self.repo.count_unread_notifications(
                community.id, membership.id
            ),
        )

    def list_boards(self) -> list[BoardSummary]:
        viewer = self.viewer()
        current_facet_ids = _current_character_facet_ids(self.repo, viewer)
        summaries: list[BoardSummary] = []
        for board in self.repo.list_boards(viewer.community.id):
            if not policies.can_view_board(viewer.membership, board, viewer.role):
                continue
            summaries.append(_board_summary(self.repo, viewer, board, current_facet_ids))
        return summaries

    def child_board_summaries(self, board: Board) -> list[BoardSummary]:
        viewer = self.viewer()
        current_facet_ids = _current_character_facet_ids(self.repo, viewer)
        return [
            _board_summary(self.repo, viewer, child, current_facet_ids)
            for child in self.repo.list_child_boards(viewer.community.id, board.id)
            if policies.can_view_board(viewer.membership, child, viewer.role)
        ]

    def sibling_board_summaries(self, board: Board) -> list[BoardSummary]:
        viewer = self.viewer()
        current_facet_ids = _current_character_facet_ids(self.repo, viewer)
        siblings = self.repo.list_child_boards(viewer.community.id, board.parent_board_id)
        return [
            _board_summary(self.repo, viewer, sibling, current_facet_ids)
            for sibling in siblings
            if sibling.id != board.id
            and is_location_board(sibling)
            and policies.can_view_board(viewer.membership, sibling, viewer.role)
        ]

    def parent_board(self, board: Board) -> Board | None:
        if board.parent_board_id is None:
            return None
        viewer = self.viewer()
        parent = self.repo.get_board(viewer.community.id, board.parent_board_id)
        if not policies.can_view_board(viewer.membership, parent, viewer.role):
            return None
        return parent

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
                    application_status_label=_application_status_label(
                        character.application_status
                    ),
                    application_status_variant=_application_status_variant(
                        character.application_status
                    ),
                )
                for character in viewer.roster
            ]
        )

    def applications_desk(self) -> ApplicationsDesk:
        viewer = self.viewer()
        characters = self.repo.list_community_characters(viewer.community.id)
        character_views = [
            _application_character_view(self.repo, viewer, character) for character in characters
        ]
        materials = [
            _material_summary(self.repo, viewer.community.id, material)
            for material in self.repo.list_materials(viewer.community.id)
            if material.material_type == "application"
        ]
        return ApplicationsDesk(
            my_applications=[
                item
                for item in character_views
                if item.character.membership_id == viewer.membership.id
            ],
            review_queue=(
                [
                    item
                    for item in character_views
                    if item.character.application_status == "submitted"
                ]
                if viewer.role.is_admin
                else []
            ),
            accepted_characters=[
                item for item in character_views if item.character.application_status == "accepted"
            ],
            application_materials=materials,
            can_review=viewer.role.is_admin,
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
        current_facet_ids = _current_character_facet_ids(self.repo, viewer)
        roster_character_ids = {character.id for character in viewer.roster}
        for thread in self.repo.list_threads(viewer.community.id, board.id):
            posts = self.repo.list_posts(viewer.community.id, thread.id)
            participants = self.repo.list_thread_participants(viewer.community.id, thread.id)
            participant_ids = {character.id for character in participants}
            thread_facets = _facet_tags(
                self.repo,
                viewer.community.id,
                self.repo.list_thread_facets(viewer.community.id, thread.id),
            )
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
                facets=thread_facets,
                is_relevant_to_current_face=bool(
                    current_facet_ids
                    and {tag.facet.id for tag in thread_facets}.intersection(current_facet_ids)
                ),
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

    def board_facets(self, board_slug: str) -> list[FacetTag]:
        viewer = self.viewer()
        board = self.repo.get_board_by_slug(viewer.community.id, board_slug)
        if not policies.can_view_board(viewer.membership, board, viewer.role):
            raise PermissionError(f"membership {viewer.membership.id} cannot view board {board.id}")
        return _facet_tags(
            self.repo,
            viewer.community.id,
            self.repo.list_board_facets(viewer.community.id, board.id),
        )

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
        participants = self.repo.list_thread_participants(viewer.community.id, thread.id)
        participant_ids = {character.id for character in participants}
        posted_character_ids = {post.post.author_character_id for post in posts}
        can_reply = policies.can_reply(viewer.membership, thread, viewer.role)
        return ThreadView(
            board=board,
            thread=thread,
            participants=participants,
            board_facets=_facet_tags(
                self.repo,
                viewer.community.id,
                self.repo.list_board_facets(viewer.community.id, board.id),
            ),
            thread_facets=_facet_tags(
                self.repo,
                viewer.community.id,
                self.repo.list_thread_facets(viewer.community.id, thread.id),
            ),
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
            can_reply=can_reply,
            can_join_scene=(
                viewer.current_character is not None
                and thread.status == "open"
                and not thread.is_locked
                and can_reply
                and viewer.current_character.id not in participant_ids
            ),
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

    def join_thread_as_current_character(self, board_slug: str, thread_slug: str) -> None:
        viewer = self.viewer()
        if viewer.current_character is None:
            raise ValueError("create a character before joining a scene")
        _board, thread = self._visible_thread(viewer, board_slug, thread_slug)
        if thread.status != "open" or thread.is_locked:
            raise PermissionError(f"thread {thread.id} is not open to join")
        if not policies.can_reply(viewer.membership, thread, viewer.role):
            raise PermissionError(
                f"membership {viewer.membership.id} cannot join thread {thread.id}"
            )
        if not policies.can_post_as(viewer.membership, viewer.current_character):
            raise PermissionError(
                f"membership {viewer.membership.id} cannot use character {viewer.current_character.id}"
            )
        self.repo.add_thread_participant(
            viewer.community.id,
            thread.id,
            viewer.current_character.id,
        )
        self.repo.watch_thread(viewer.community.id, thread.id, viewer.membership.id)

    def discover_plots(self, *, facet_slugs: list[str] | None = None) -> PlotDiscovery:
        viewer = self.viewer()
        active_face_facets = _current_character_facet_tags(self.repo, viewer)
        requested_slugs = _clean_facet_slugs(facet_slugs or [])
        used_active_face_lens = False
        if not requested_slugs and active_face_facets:
            requested_slugs = [
                tag.facet.slug
                for tag in active_face_facets
                if tag.group.slug in {"species", "affiliation", "location"}
            ][:3]
            used_active_face_lens = bool(requested_slugs)
        selected_facets = _resolve_facets(self.repo, viewer.community.id, requested_slugs)
        requested_slugs = [facet.slug for facet in selected_facets]
        selected_ids = [facet.id for facet in selected_facets]
        selected_tags = _facet_tags(self.repo, viewer.community.id, selected_facets)
        character_ids = (
            self.repo.list_character_ids_for_facets(viewer.community.id, selected_ids)
            if selected_ids
            else {
                character.id
                for character in self.repo.list_community_characters(viewer.community.id)
            }
        )
        thread_ids = (
            self.repo.list_thread_ids_for_facets(viewer.community.id, selected_ids)
            if selected_ids
            else {thread.id for thread in self.repo.list_threads(viewer.community.id)}
        )
        return PlotDiscovery(
            selected_facets=selected_tags,
            active_face_facets=active_face_facets,
            filter_groups=_facet_filter_groups(
                self.repo,
                viewer.community.id,
                requested_slugs,
            ),
            characters=_discovery_characters(
                self.repo,
                viewer,
                character_ids,
                selected_ids,
            ),
            open_threads=_discovery_open_threads(
                self.repo,
                viewer,
                thread_ids,
                selected_ids,
            ),
            used_active_face_lens=used_active_face_lens,
        )

    def world_hub(self) -> WorldHub:
        viewer = self.viewer()
        materials = [
            _material_summary(self.repo, viewer.community.id, material)
            for material in self.repo.list_materials(viewer.community.id)
        ]
        additional_materials = [item for item in materials if not item.material.is_featured]
        return WorldHub(
            featured=[item for item in materials if item.material.is_featured],
            guides=[
                item
                for item in additional_materials
                if item.material.material_type in {"premise", "guide", "factions"}
            ],
            events=[
                item for item in additional_materials if item.material.material_type == "event"
            ],
            application_materials=[
                item
                for item in additional_materials
                if item.material.material_type == "application"
            ],
        )

    def read_material(self, material_slug: str) -> MaterialDetail:
        viewer = self.viewer()
        material = self.repo.get_material_by_slug(viewer.community.id, material_slug)
        if material.status != "published":
            raise LookupError(
                f"material not found in community {viewer.community.id}: {material_slug}"
            )
        facets = _facet_tags(
            self.repo,
            viewer.community.id,
            self.repo.list_material_facets(viewer.community.id, material.id),
        )
        facet_ids = {tag.facet.id for tag in facets}
        related = []
        for candidate in self.repo.list_materials(viewer.community.id):
            if candidate.id == material.id:
                continue
            candidate_facets = _facet_tags(
                self.repo,
                viewer.community.id,
                self.repo.list_material_facets(viewer.community.id, candidate.id),
            )
            if facet_ids and not facet_ids.intersection({tag.facet.id for tag in candidate_facets}):
                continue
            related.append(_material_summary(self.repo, viewer.community.id, candidate))
        return MaterialDetail(
            material=material,
            facets=facets,
            rendered_body=render_post_body(
                material.body,
                mentions=_post_mention_links(self.repo, viewer.community.id),
            ),
            type_label=_material_type_label(material.material_type),
            related_materials=related[:4],
        )

    def wanted_ads(self) -> WantedBoard:
        viewer = self.viewer()
        return WantedBoard(
            open_ads=[
                _wanted_ad_summary(self.repo, viewer.community.id, wanted_ad)
                for wanted_ad in self.repo.list_wanted_ads(viewer.community.id)
            ]
        )

    def casting_desk(self) -> CastingDesk:
        viewer = self.viewer()
        active_reserves = [
            _character_reserve_view(self.repo, viewer.community.id, reserve)
            for reserve in self.repo.list_character_reserves_for_community(viewer.community.id)
        ]
        wanted_with_interest: list[CastingWantedItem] = []
        for wanted_ad in self.repo.list_wanted_ads(viewer.community.id, status=None):
            if wanted_ad.status == "archived":
                continue
            interests = [
                _wanted_ad_interest_view(self.repo, viewer.community.id, interest)
                for interest in self.repo.list_wanted_ad_interests(
                    viewer.community.id,
                    wanted_ad.id,
                )
            ]
            reserves = [
                reserve
                for reserve in active_reserves
                if reserve.reserve.wanted_ad_id == wanted_ad.id
            ]
            if not interests and not reserves:
                continue
            wanted_with_interest.append(
                CastingWantedItem(
                    wanted_ad=_wanted_ad_summary(self.repo, viewer.community.id, wanted_ad),
                    interests=interests,
                    reserves=reserves,
                    is_created_by_viewer=wanted_ad.creator_membership_id == viewer.membership.id,
                )
            )
        return CastingDesk(
            active_face=viewer.current_character,
            active_face_reserves=[
                reserve
                for reserve in active_reserves
                if viewer.current_character is not None
                and reserve.reserve.character_id == viewer.current_character.id
            ],
            my_reserves=[
                reserve
                for reserve in active_reserves
                if reserve.reserve.membership_id == viewer.membership.id
            ],
            active_reserves=active_reserves,
            wanted_with_interest=wanted_with_interest,
        )

    def read_wanted_ad(self, wanted_slug: str) -> WantedAdDetail:
        viewer = self.viewer()
        wanted_ad = self.repo.get_wanted_ad_by_slug(viewer.community.id, wanted_slug)
        if wanted_ad.status == "archived":
            raise LookupError(
                f"wanted ad not found in community {viewer.community.id}: {wanted_slug}"
            )
        facets = _facet_tags(
            self.repo,
            viewer.community.id,
            self.repo.list_wanted_ad_facets(viewer.community.id, wanted_ad.id),
        )
        facet_ids = {tag.facet.id for tag in facets}
        related = []
        for candidate in self.repo.list_wanted_ads(viewer.community.id):
            if candidate.id == wanted_ad.id:
                continue
            candidate_facets = _facet_tags(
                self.repo,
                viewer.community.id,
                self.repo.list_wanted_ad_facets(viewer.community.id, candidate.id),
            )
            if facet_ids and not facet_ids.intersection({tag.facet.id for tag in candidate_facets}):
                continue
            related.append(_wanted_ad_summary(self.repo, viewer.community.id, candidate))
        interests = [
            _wanted_ad_interest_view(self.repo, viewer.community.id, interest)
            for interest in self.repo.list_wanted_ad_interests(viewer.community.id, wanted_ad.id)
        ]
        reserves = [
            _character_reserve_view(self.repo, viewer.community.id, reserve)
            for reserve in self.repo.list_character_reserves_for_wanted_ad(
                viewer.community.id,
                wanted_ad.id,
            )
        ]
        viewer_interest = None
        if viewer.current_character is not None:
            viewer_interest = next(
                (
                    interest
                    for interest in interests
                    if interest.interest.character_id == viewer.current_character.id
                ),
                None,
            )
        is_created_by_viewer = wanted_ad.creator_membership_id == viewer.membership.id
        return WantedAdDetail(
            wanted_ad=wanted_ad,
            creator_membership=self.repo.get_membership(
                viewer.community.id,
                wanted_ad.creator_membership_id,
            ),
            creator_character=(
                self.repo.get_character(viewer.community.id, wanted_ad.creator_character_id)
                if wanted_ad.creator_character_id is not None
                else None
            ),
            related_material=(
                self.repo.get_material(viewer.community.id, wanted_ad.related_material_id)
                if wanted_ad.related_material_id is not None
                else None
            ),
            related_characters=self.repo.list_wanted_ad_related_characters(
                viewer.community.id,
                wanted_ad.id,
            ),
            facets=facets,
            interests=interests,
            reserves=reserves,
            reserve_interest_ids={
                reserve.reserve.wanted_ad_interest_id
                for reserve in reserves
                if reserve.reserve.wanted_ad_interest_id is not None
            },
            viewer_interest=viewer_interest,
            can_express_interest=(
                wanted_ad.status == "open"
                and viewer.current_character is not None
                and viewer_interest is None
                and not is_created_by_viewer
            ),
            is_created_by_viewer=is_created_by_viewer,
            can_manage=is_created_by_viewer or viewer.role.is_admin,
            rendered_body=render_post_body(
                wanted_ad.body,
                mentions=_post_mention_links(self.repo, viewer.community.id),
            ),
            type_label=_wanted_type_label(wanted_ad.wanted_type),
            related_ads=related[:4],
        )

    def express_wanted_interest(self, wanted_slug: str) -> WantedAdInterest:
        viewer = self.viewer()
        if viewer.current_character is None:
            raise ValueError("create a character before expressing interest")
        wanted_ad = self.repo.get_wanted_ad_by_slug(viewer.community.id, wanted_slug)
        if wanted_ad.status != "open":
            raise ValueError(f"wanted hook {wanted_ad.id} is not open")
        if wanted_ad.creator_membership_id == viewer.membership.id:
            raise ValueError("you cannot express interest in your own wanted hook")
        interest = self.repo.create_wanted_ad_interest(
            viewer.community.id,
            wanted_ad.id,
            viewer.membership.id,
            viewer.current_character.id,
        )
        if wanted_ad.creator_membership_id != viewer.membership.id:
            self.repo.create_notification(
                viewer.community.id,
                wanted_ad.creator_membership_id,
                kind="wanted_interest",
                wanted_ad_id=wanted_ad.id,
                wanted_ad_interest_id=interest.id,
                actor_membership_id=viewer.membership.id,
                actor_character_id=viewer.current_character.id,
            )
        return interest

    def reserve_wanted_interest(
        self,
        wanted_slug: str,
        interest_id: int,
    ) -> WantedAdInterest:
        viewer = self.viewer()
        wanted_ad = self.repo.get_wanted_ad_by_slug(viewer.community.id, wanted_slug)
        if wanted_ad.creator_membership_id != viewer.membership.id and not viewer.role.is_admin:
            raise PermissionError(
                f"membership {viewer.membership.id} cannot manage wanted hook {wanted_ad.id}"
            )
        if wanted_ad.status != "open":
            raise ValueError(f"wanted hook {wanted_ad.id} is not open")
        interest = self.repo.get_wanted_ad_interest(viewer.community.id, interest_id)
        if interest.wanted_ad_id != wanted_ad.id:
            raise LookupError(
                f"wanted interest {interest_id} not found for wanted hook {wanted_ad.id}"
            )
        if interest.status != "interested":
            raise ValueError(f"wanted interest {interest.id} is already {interest.status}")
        actor_character_id = _wanted_actor_character_id(self.repo, viewer, wanted_ad)
        reserved = self.repo.update_wanted_ad_interest_status(
            viewer.community.id,
            interest.id,
            "reserved",
        )
        self.repo.update_wanted_ad_status(viewer.community.id, wanted_ad.id, "reserved")
        if reserved.membership_id != viewer.membership.id:
            self.repo.create_notification(
                viewer.community.id,
                reserved.membership_id,
                kind="wanted_reserved",
                wanted_ad_id=wanted_ad.id,
                wanted_ad_interest_id=reserved.id,
                actor_membership_id=viewer.membership.id,
                actor_character_id=actor_character_id,
            )
        return reserved

    def create_reserve_for_wanted_interest(
        self,
        wanted_slug: str,
        interest_id: int,
    ) -> CharacterReserve:
        viewer = self.viewer()
        wanted_ad = self.repo.get_wanted_ad_by_slug(viewer.community.id, wanted_slug)
        if wanted_ad.creator_membership_id != viewer.membership.id and not viewer.role.is_admin:
            raise PermissionError(
                f"membership {viewer.membership.id} cannot manage wanted hook {wanted_ad.id}"
            )
        if wanted_ad.status != "reserved":
            raise ValueError(f"wanted hook {wanted_ad.id} is not reserved")
        interest = self.repo.get_wanted_ad_interest(viewer.community.id, interest_id)
        if interest.wanted_ad_id != wanted_ad.id:
            raise LookupError(
                f"wanted interest {interest_id} not found for wanted hook {wanted_ad.id}"
            )
        if interest.status != "reserved":
            raise ValueError(f"wanted interest {interest.id} is not reserved")
        reserve = self.repo.create_character_reserve(
            viewer.community.id,
            interest.membership_id,
            interest.character_id,
            wanted_ad.title,
            wanted_ad_id=wanted_ad.id,
            wanted_ad_interest_id=interest.id,
            reserve_type="wanted",
            notes=f"Reserved from wanted hook: {wanted_ad.title}",
        )
        actor_character_id = _wanted_actor_character_id(self.repo, viewer, wanted_ad)
        if reserve.membership_id != viewer.membership.id:
            self.repo.create_notification(
                viewer.community.id,
                reserve.membership_id,
                kind="reserve_created",
                wanted_ad_id=wanted_ad.id,
                wanted_ad_interest_id=interest.id,
                actor_membership_id=viewer.membership.id,
                actor_character_id=actor_character_id,
            )
        return reserve

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

    def submit_character_application(self, character_slug: str) -> Character:
        viewer = self.viewer()
        character = self.repo.get_character_by_slug(viewer.community.id, character_slug)
        if not policies.can_post_as(viewer.membership, character):
            raise PermissionError(
                f"membership {viewer.membership.id} cannot submit character {character.id}"
            )
        if character.application_status not in {"draft", "revision_requested"}:
            raise ValueError(
                f"character {character.id} cannot be submitted from {character.application_status}"
            )
        character = self.repo.update_character_application_status(
            viewer.community.id,
            character.id,
            "submitted",
        )
        self._notify_application_directors(viewer, character)
        return character

    def accept_character_application(self, character_slug: str) -> Character:
        viewer = self.viewer()
        if not viewer.role.is_admin:
            raise PermissionError(f"membership {viewer.membership.id} cannot review applications")
        character = self.repo.get_character_by_slug(viewer.community.id, character_slug)
        if character.application_status != "submitted":
            raise ValueError(
                f"character {character.id} cannot be accepted from {character.application_status}"
            )
        character = self.repo.update_character_application_status(
            viewer.community.id,
            character.id,
            "accepted",
        )
        self._notify_application_owner(viewer, character, "application_accepted")
        return character

    def request_character_application_revision(self, character_slug: str) -> Character:
        viewer = self.viewer()
        if not viewer.role.is_admin:
            raise PermissionError(f"membership {viewer.membership.id} cannot review applications")
        character = self.repo.get_character_by_slug(viewer.community.id, character_slug)
        if character.application_status != "submitted":
            raise ValueError(
                f"character {character.id} cannot be revised from {character.application_status}"
            )
        character = self.repo.update_character_application_status(
            viewer.community.id,
            character.id,
            "revision_requested",
        )
        self._notify_application_owner(viewer, character, "application_revision_requested")
        return character

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
            facets=_facet_tags(
                self.repo,
                viewer.community.id,
                self.repo.list_character_facets(viewer.community.id, character.id),
            ),
            wanted_ads=[
                _wanted_ad_summary(self.repo, viewer.community.id, wanted_ad)
                for wanted_ad in self.repo.list_wanted_ads_for_character(
                    viewer.community.id,
                    character.id,
                )
            ],
            reserves=[
                _character_reserve_view(self.repo, viewer.community.id, reserve)
                for reserve in self.repo.list_character_reserves(
                    viewer.community.id,
                    character.id,
                )
            ],
            application_status_label=_application_status_label(character.application_status),
            application_status_variant=_application_status_variant(character.application_status),
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
            application_status="draft",
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

    def _notify_application_directors(self, viewer: ForumView, character: Character) -> None:
        for membership in self.repo.list_memberships(viewer.community.id):
            role = self.repo.get_role(viewer.community.id, membership.role_id)
            if not role.is_admin or membership.id == viewer.membership.id:
                continue
            self.repo.create_notification(
                viewer.community.id,
                membership.id,
                kind="application_submitted",
                character_id=character.id,
                actor_membership_id=viewer.membership.id,
                actor_character_id=character.id,
            )

    def _notify_application_owner(
        self,
        viewer: ForumView,
        character: Character,
        kind: str,
    ) -> None:
        actor_character_id = _application_actor_character_id(viewer, character)
        if character.membership_id == viewer.membership.id:
            return
        self.repo.create_notification(
            viewer.community.id,
            character.membership_id,
            kind=kind,
            character_id=character.id,
            actor_membership_id=viewer.membership.id,
            actor_character_id=actor_character_id,
        )

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


def _location_navigation_groups(
    navigation_boards: list[BoardNavigationItem],
) -> list[LocationNavigationGroup]:
    parents = [
        item
        for item in navigation_boards
        if item.board.parent_board_id is None and is_location_board(item.board)
    ]
    children_by_parent: dict[int, list[BoardNavigationItem]] = {
        item.board.id: [] for item in parents
    }
    for item in navigation_boards:
        parent_id = item.board.parent_board_id
        if parent_id is None or not is_location_board(item.board):
            continue
        if parent_id in children_by_parent:
            children_by_parent[parent_id].append(item)
    return [
        LocationNavigationGroup(
            parent=parent,
            children=children_by_parent[parent.board.id],
        )
        for parent in parents
    ]


def _board_summary(
    repo: ForumRepository,
    viewer: ForumView,
    board: Board,
    current_facet_ids: set[int],
) -> BoardSummary:
    child_boards = [
        child
        for child in repo.list_child_boards(viewer.community.id, board.id)
        if policies.can_view_board(viewer.membership, child, viewer.role)
    ]
    boards_for_activity = [board, *child_boards]
    board_facets = _facet_tags(
        repo,
        viewer.community.id,
        repo.list_board_facets(viewer.community.id, board.id),
    )
    threads_with_boards: list[tuple[Board, Thread]] = []
    posts_by_thread: dict[int, list[Post]] = {}
    for activity_board in boards_for_activity:
        for thread in repo.list_threads(viewer.community.id, activity_board.id):
            threads_with_boards.append((activity_board, thread))
            posts_by_thread[thread.id] = repo.list_posts(viewer.community.id, thread.id)
    latest_board: Board | None = None
    latest_thread: Thread | None = None
    if threads_with_boards:
        latest_board, latest_thread = max(
            threads_with_boards,
            key=lambda item: (_timestamp_key(item[1].updated_at), item[1].id),
        )
    latest_thread_posts = posts_by_thread.get(latest_thread.id, []) if latest_thread else []
    latest_post = (
        _post_view(repo, viewer.community.id, latest_thread_posts[-1])
        if latest_thread_posts
        else None
    )
    threads = [thread for _, thread in threads_with_boards]
    return BoardSummary(
        board=board,
        child_boards=child_boards,
        thread_count=len(threads),
        post_count=sum(len(posts) for posts in posts_by_thread.values()),
        unread_thread_count=sum(
            1
            for thread in threads
            if _is_unread(
                repo,
                viewer.community.id,
                viewer.membership.id,
                thread,
            )
        ),
        latest_thread=latest_thread,
        latest_board=latest_board,
        latest_post=latest_post,
        facets=board_facets,
        is_relevant_to_current_face=bool(
            current_facet_ids
            and {tag.facet.id for tag in board_facets}.intersection(current_facet_ids)
        ),
    )


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


def _current_character_facet_tags(repo: ForumRepository, viewer: ForumView) -> list[FacetTag]:
    if viewer.current_character is None:
        return []
    return _facet_tags(
        repo,
        viewer.community.id,
        repo.list_character_facets(viewer.community.id, viewer.current_character.id),
    )


def _current_character_facet_ids(repo: ForumRepository, viewer: ForumView) -> set[int]:
    return {tag.facet.id for tag in _current_character_facet_tags(repo, viewer)}


def _facet_tags(repo: ForumRepository, community_id: int, facets: list[Facet]) -> list[FacetTag]:
    groups = {group.id: group for group in repo.list_facet_groups(community_id)}
    return [
        FacetTag(group=groups[facet.facet_group_id], facet=facet)
        for facet in facets
        if facet.facet_group_id in groups
    ]


def _resolve_facets(repo: ForumRepository, community_id: int, slugs: list[str]) -> list[Facet]:
    facets = []
    for slug in _clean_facet_slugs(slugs):
        try:
            facets.append(repo.get_facet_by_slug(community_id, slug))
        except LookupError:
            continue
    return facets


def _clean_facet_slugs(values: list[str]) -> list[str]:
    slugs: list[str] = []
    for value in values:
        for part in value.split(","):
            slug = part.strip().lower()
            if slug and slug not in slugs:
                slugs.append(slug)
    return slugs


def _facet_filter_groups(
    repo: ForumRepository,
    community_id: int,
    selected_slugs: list[str],
) -> list[FacetFilterGroup]:
    selected = set(selected_slugs)
    selected_order = [slug for slug in selected_slugs if slug in selected]
    tags = _facet_tags(repo, community_id, repo.list_facets(community_id))
    groups = repo.list_facet_groups(community_id)
    return [
        FacetFilterGroup(
            group=group,
            options=[
                FacetFilterOption(
                    tag=tag,
                    href=_facet_filter_href(selected_order, tag.facet.slug),
                    is_selected=tag.facet.slug in selected,
                )
                for tag in tags
                if tag.group.id == group.id
            ],
        )
        for group in groups
        if group.visibility == "public"
    ]


def _facet_filter_href(selected_slugs: list[str], slug: str) -> str:
    if slug in selected_slugs:
        next_slugs = [selected_slug for selected_slug in selected_slugs if selected_slug != slug]
    else:
        next_slugs = [*selected_slugs, slug]
    if not next_slugs:
        return "/discover?facets=none"
    return f"/discover?facets={','.join(next_slugs)}"


def _material_summary(
    repo: ForumRepository,
    community_id: int,
    material: Material,
) -> MaterialSummary:
    return MaterialSummary(
        material=material,
        facets=_facet_tags(
            repo,
            community_id,
            repo.list_material_facets(community_id, material.id),
        ),
        rendered_summary=material.summary or post_snippet(material.body, limit=160),
        type_label=_material_type_label(material.material_type),
    )


def _material_type_label(material_type: str) -> str:
    return {
        "premise": "Premise",
        "guide": "Guide",
        "factions": "Factions",
        "application": "Application",
        "event": "Event",
    }.get(material_type, material_type.replace("_", " ").title())


def _wanted_ad_summary(
    repo: ForumRepository,
    community_id: int,
    wanted_ad: WantedAd,
) -> WantedAdSummary:
    return WantedAdSummary(
        wanted_ad=wanted_ad,
        creator_membership=repo.get_membership(community_id, wanted_ad.creator_membership_id),
        creator_character=(
            repo.get_character(community_id, wanted_ad.creator_character_id)
            if wanted_ad.creator_character_id is not None
            else None
        ),
        related_material=(
            repo.get_material(community_id, wanted_ad.related_material_id)
            if wanted_ad.related_material_id is not None
            else None
        ),
        related_characters=repo.list_wanted_ad_related_characters(community_id, wanted_ad.id),
        facets=_facet_tags(
            repo,
            community_id,
            repo.list_wanted_ad_facets(community_id, wanted_ad.id),
        ),
        type_label=_wanted_type_label(wanted_ad.wanted_type),
    )


def _wanted_type_label(wanted_type: str) -> str:
    return {
        "canon": "Canon",
        "connection": "Connection",
        "event_role": "Event Role",
        "faction_need": "Faction Need",
        "plot_role": "Plot Role",
        "rival": "Rival",
    }.get(wanted_type, wanted_type.replace("_", " ").title())


def _wanted_ad_interest_view(
    repo: ForumRepository,
    community_id: int,
    interest: WantedAdInterest,
) -> WantedAdInterestView:
    return WantedAdInterestView(
        interest=interest,
        membership=repo.get_membership(community_id, interest.membership_id),
        character=repo.get_character(community_id, interest.character_id),
        created_at_label=_timestamp_label(interest.created_at),
    )


def _character_reserve_view(
    repo: ForumRepository,
    community_id: int,
    reserve: CharacterReserve,
) -> CharacterReserveView:
    return CharacterReserveView(
        reserve=reserve,
        membership=repo.get_membership(community_id, reserve.membership_id),
        character=repo.get_character(community_id, reserve.character_id),
        wanted_ad=(
            repo.get_wanted_ad(community_id, reserve.wanted_ad_id)
            if reserve.wanted_ad_id is not None
            else None
        ),
        created_at_label=_timestamp_label(reserve.created_at),
    )


def _application_character_view(
    repo: ForumRepository,
    viewer: ForumView,
    character: Character,
) -> ApplicationCharacterView:
    return ApplicationCharacterView(
        character=character,
        membership=repo.get_membership(viewer.community.id, character.membership_id),
        facets=_facet_tags(
            repo,
            viewer.community.id,
            repo.list_character_facets(viewer.community.id, character.id),
        ),
        reserves=[
            _character_reserve_view(repo, viewer.community.id, reserve)
            for reserve in repo.list_character_reserves(
                viewer.community.id,
                character.id,
            )
        ],
        status_label=_application_status_label(character.application_status),
        status_variant=_application_status_variant(character.application_status),
        is_owned_by_viewer=character.membership_id == viewer.membership.id,
    )


def _application_status_label(status: str) -> str:
    return APPLICATION_STATUS_LABELS.get(status, status.replace("_", " ").title())


def _application_status_variant(status: str) -> str:
    return APPLICATION_STATUS_VARIANTS.get(status, "muted")


def _application_actor_character_id(viewer: ForumView, target_character: Character) -> int:
    if (
        viewer.current_character is not None
        and viewer.current_character.membership_id == viewer.membership.id
    ):
        return viewer.current_character.id
    if viewer.roster:
        return viewer.roster[0].id
    if target_character.membership_id == viewer.membership.id:
        return target_character.id
    raise ValueError("application actor needs a character")


def _wanted_actor_character_id(
    repo: ForumRepository,
    viewer: ForumView,
    wanted_ad: WantedAd,
) -> int:
    if (
        viewer.current_character is not None
        and viewer.current_character.membership_id == viewer.membership.id
    ):
        return viewer.current_character.id
    if wanted_ad.creator_character_id is not None:
        creator_character = repo.get_character(viewer.community.id, wanted_ad.creator_character_id)
        if creator_character.membership_id == viewer.membership.id:
            return creator_character.id
    roster = repo.list_characters(viewer.community.id, viewer.membership.id)
    if roster:
        return roster[0].id
    raise ValueError("create a character before managing wanted hooks")


def _discovery_characters(
    repo: ForumRepository,
    viewer: ForumView,
    character_ids: set[int],
    selected_facet_ids: list[int],
) -> list[DiscoveryCharacterResult]:
    selected = set(selected_facet_ids)
    results = []
    for character in repo.list_community_characters(viewer.community.id):
        if character.id not in character_ids:
            continue
        owner = repo.get_membership(viewer.community.id, character.membership_id)
        if not owner.is_active:
            continue
        facets = _facet_tags(
            repo,
            viewer.community.id,
            repo.list_character_facets(viewer.community.id, character.id),
        )
        matching_facets = [tag for tag in facets if tag.facet.id in selected]
        results.append(
            DiscoveryCharacterResult(
                character=character,
                owner_membership=owner,
                facets=facets,
                matching_facets=matching_facets,
            )
        )
    return sorted(
        results,
        key=lambda item: (
            -len(item.matching_facets),
            item.character.name,
            item.character.id,
        ),
    )


def _discovery_open_threads(
    repo: ForumRepository,
    viewer: ForumView,
    thread_ids: set[int],
    selected_facet_ids: list[int],
) -> list[DiscoveryThreadResult]:
    selected = set(selected_facet_ids)
    visible_boards = {
        board.id: board
        for board in repo.list_boards(viewer.community.id)
        if policies.can_view_board(viewer.membership, board, viewer.role)
    }
    results = []
    for thread in repo.list_threads(viewer.community.id):
        if thread.id not in thread_ids or thread.status != "open" or thread.is_locked:
            continue
        board = visible_boards.get(thread.board_id)
        if board is None:
            continue
        facets = _facet_tags(
            repo,
            viewer.community.id,
            repo.list_thread_facets(viewer.community.id, thread.id),
        )
        matching_facets = [tag for tag in facets if tag.facet.id in selected]
        posts = repo.list_posts(viewer.community.id, thread.id)
        results.append(
            DiscoveryThreadResult(
                board=board,
                thread=thread,
                author=repo.get_character(viewer.community.id, thread.author_character_id),
                participants=repo.list_thread_participants(viewer.community.id, thread.id),
                facets=facets,
                matching_facets=matching_facets,
                reply_count=max(0, len(posts) - 1),
            )
        )
    return sorted(
        results,
        key=lambda item: (
            -len(item.matching_facets),
            _timestamp_key(item.thread.updated_at),
            item.thread.id,
        ),
        reverse=True,
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
    actor = repo.get_character(viewer.community.id, notification.actor_character_id)
    actor_membership = repo.get_membership(
        viewer.community.id,
        notification.actor_membership_id,
    )
    if notification.character_id is not None:
        character = repo.get_character(viewer.community.id, notification.character_id)
        match notification.kind:
            case "application_submitted":
                snippet = f"{actor.name} submitted this character for review."
            case "application_accepted":
                snippet = f"{actor.name} accepted this character application."
            case "application_revision_requested":
                snippet = f"{actor.name} requested revisions for this character application."
            case _:
                snippet = f"{actor.name} updated this character application."
        return NotificationItem(
            notification=notification,
            board=None,
            thread=None,
            post=None,
            wanted_ad=None,
            actor=actor,
            actor_membership=actor_membership,
            label=_notification_label(notification.kind),
            title=character.name,
            created_at_label=_timestamp_label(notification.created_at),
            snippet=snippet,
            href=f"/characters/{character.slug}",
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
        if notification.kind == "wanted_reserved":
            snippet = f"{actor.name} reserved this wanted hook."
        elif notification.kind == "reserve_created":
            snippet = f"{actor.name} created a reserve from this wanted hook."
        else:
            snippet = f"{actor.name} is interested in this wanted hook."
        if interest is not None and interest.note:
            snippet = interest.note
        return NotificationItem(
            notification=notification,
            board=None,
            thread=None,
            post=None,
            wanted_ad=wanted_ad,
            actor=actor,
            actor_membership=actor_membership,
            label=_notification_label(notification.kind),
            title=wanted_ad.title,
            created_at_label=_timestamp_label(notification.created_at),
            snippet=snippet,
            href=f"/wanted/{wanted_ad.slug}",
        )
    if notification.thread_id is None or notification.post_id is None:
        return None
    thread = repo.get_thread(viewer.community.id, notification.thread_id)
    board = repo.get_board(viewer.community.id, thread.board_id)
    if not policies.can_view_board(viewer.membership, board, viewer.role):
        return None
    post = repo.get_post(viewer.community.id, notification.post_id)
    post_view = _post_view(repo, viewer.community.id, post)
    return NotificationItem(
        notification=notification,
        board=board,
        thread=thread,
        post=post_view,
        wanted_ad=None,
        actor=actor,
        actor_membership=actor_membership,
        label=_notification_label(notification.kind),
        title=thread.title,
        created_at_label=post_view.created_at_label,
        snippet=post_view.snippet,
        href=f"/boards/{board.slug}/threads/{thread.slug}#{post_view.anchor}",
    )


def _notification_label(kind: str) -> str:
    match kind:
        case "mention":
            return "Mention"
        case "thread_reply":
            return "Watched thread"
        case "wanted_interest":
            return "Wanted interest"
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


def _post_mention_links(repo: ForumRepository, community_id: int) -> list[MentionLink]:
    links: list[MentionLink] = []
    seen: set[str] = set()
    for character in repo.list_community_characters(community_id):
        for handle in _character_mention_handles(character):
            if handle.lower() in seen:
                continue
            links.append(
                MentionLink(
                    handle=handle,
                    href=f"/characters/{character.slug}",
                    label=character.name,
                    kind="character",
                )
            )
            seen.add(handle.lower())
    for membership in repo.list_memberships(community_id):
        if not membership.is_active or membership.username.lower() in seen:
            continue
        links.append(
            MentionLink(
                handle=membership.username,
                href=f"/members/{membership.username}",
                label=membership.display_name,
                kind="writer",
            )
        )
        seen.add(membership.username.lower())
    return links


def _character_mention_handles(character: Character) -> set[str]:
    handles = {character.slug}
    if re.fullmatch(r"[\w-]+", character.name):
        handles.add(character.name)
    return handles


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
        rendered_body=render_post_body(
            post.body,
            mentions=_post_mention_links(repo, community_id),
        ),
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
