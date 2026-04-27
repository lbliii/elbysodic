"""Read models and contracts for the forum service layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from elbysodic.domain.models import (
    Board,
    Character,
    CharacterPlotHook,
    CharacterPlotHookInterest,
    CharacterReserve,
    Community,
    CommunityMembership,
    Facet,
    FacetGroup,
    Material,
    Notification,
    PlottingRoom,
    PlottingRoomParticipant,
    Post,
    PostRevision,
    Role,
    Thread,
    WantedAd,
    WantedAdInterest,
)

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
MATERIAL_TYPES = ("premise", "guide", "factions", "application", "event")
MATERIAL_STATUSES = ("published", "draft")


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
class EpisodeCredits:
    word_count: int
    read_minutes: int
    read_estimate_label: str
    post_count: int
    writer_memberships: list[CommunityMembership]

    @property
    def writer_count(self) -> int:
        return len(self.writer_memberships)


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
    episode: EpisodeCredits
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
        badges.extend(thread_state_badges(self.thread))
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
    created_at_relative_label: str
    updated_at_label: str
    updated_at_relative_label: str
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
    plot_hook: CharacterPlotHook | None
    plotting_room: PlottingRoom | None
    actor: Character | None
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
    episode: EpisodeCredits
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
        badges.extend(thread_state_badges(self.thread))
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
    known_for: list[Character]
    visible_post_count: int
    active_thread_count: int
    latest_post: CharacterAppearance | None
    is_current_member: bool


@dataclass(frozen=True, slots=True)
class MemberDirectory:
    cards: list[MemberDirectoryCard]


@dataclass(frozen=True, slots=True)
class WriterCollaborator:
    membership: CommunityMembership
    shared_thread_count: int
    latest_thread: Thread
    latest_board: Board


@dataclass(frozen=True, slots=True)
class MemberProfile:
    membership: CommunityMembership
    role: Role
    roster: list[Character]
    default_character: Character | None
    known_for: list[Character]
    collaborators: list[WriterCollaborator]
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
class FacetChoice:
    tag: FacetTag
    is_selected: bool


@dataclass(frozen=True, slots=True)
class FacetChoiceGroup:
    group: FacetGroup
    choices: list[FacetChoice]


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
class DiscoveryPlotHookResult:
    plot_hook: CharacterPlotHook
    character: Character
    author_membership: CommunityMembership
    facets: list[FacetTag]
    matching_facets: list[FacetTag]


@dataclass(frozen=True, slots=True)
class PlotDiscovery:
    selected_facets: list[FacetTag]
    active_face_facets: list[FacetTag]
    filter_groups: list[FacetFilterGroup]
    plot_hooks: list[DiscoveryPlotHookResult]
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
class ContinuityBeat:
    title: str
    date_label: str
    content: str
    href: str | None = None
    variant: str = ""


@dataclass(frozen=True, slots=True)
class EventAction:
    kind: str
    label: str
    title: str
    description: str
    href: str
    cta: str


@dataclass(frozen=True, slots=True)
class MaterialDetail:
    material: Material
    facets: list[FacetTag]
    rendered_body: object
    type_label: str
    related_materials: list[MaterialSummary]
    related_locations: list[BoardSummary]
    related_scenes: list[DiscoveryThreadResult]
    related_wanted_ads: list[WantedAdSummary]
    continuity_beats: list[ContinuityBeat]
    event_actions: list[EventAction]
    can_manage: bool


@dataclass(frozen=True, slots=True)
class WorldHub:
    featured: list[MaterialSummary]
    guides: list[MaterialSummary]
    events: list[MaterialSummary]
    application_materials: list[MaterialSummary]
    can_manage: bool


@dataclass(frozen=True, slots=True)
class DirectorStudio:
    can_manage: bool
    materials: list[MaterialSummary]
    draft_materials: list[MaterialSummary]
    featured_materials: list[MaterialSummary]
    events: list[MaterialSummary]
    current_event: MaterialSummary | None
    application_materials: list[MaterialSummary]
    location_boards: list[BoardSummary]
    sublocation_boards: list[BoardSummary]
    wanted_ads: list[WantedAdSummary]
    open_wanted_ads: list[WantedAdSummary]
    applications: ApplicationsDesk

    @property
    def material_count(self) -> int:
        return len(self.materials)

    @property
    def location_count(self) -> int:
        return len(self.location_boards)

    @property
    def sublocation_count(self) -> int:
        return len(self.sublocation_boards)

    @property
    def wanted_count(self) -> int:
        return len(self.wanted_ads)

    @property
    def open_wanted_count(self) -> int:
        return len(self.open_wanted_ads)

    @property
    def review_queue_count(self) -> int:
        return len(self.applications.review_queue)

    @property
    def featured_material_titles(self) -> list[str]:
        return [item.material.title for item in self.featured_materials]

    @property
    def event_titles(self) -> list[str]:
        return [item.material.title for item in self.events]

    @property
    def application_material_titles(self) -> list[str]:
        return [item.material.title for item in self.application_materials]

    @property
    def location_board_names(self) -> list[str]:
        return [item.board.name for item in self.location_boards]


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
    character: Character | None
    created_at_label: str

    @property
    def display_name(self) -> str:
        if self.character is not None:
            return self.character.name
        return self.interest.prospective_character_name


@dataclass(frozen=True, slots=True)
class CharacterReserveView:
    reserve: CharacterReserve
    membership: CommunityMembership
    character: Character
    wanted_ad: WantedAd | None
    created_at_label: str


@dataclass(frozen=True, slots=True)
class CharacterPlotHookSummary:
    plot_hook: CharacterPlotHook
    character: Character
    author_membership: CommunityMembership
    related_material: Material | None
    facets: list[FacetTag]
    hook_type_label: str


@dataclass(frozen=True, slots=True)
class CharacterPlotHookInterestView:
    interest: CharacterPlotHookInterest
    membership: CommunityMembership
    character: Character
    created_at_label: str


@dataclass(frozen=True, slots=True)
class CharacterPlotHookDetail:
    plot_hook: CharacterPlotHook
    character: Character
    author_membership: CommunityMembership
    related_material: Material | None
    facets: list[FacetTag]
    facet_choices: list[FacetChoiceGroup]
    interests: list[CharacterPlotHookInterestView]
    viewer_interest: CharacterPlotHookInterestView | None
    can_express_interest: bool
    can_manage: bool
    rendered_body: object
    hook_type_label: str


@dataclass(frozen=True, slots=True)
class PlottingRoomParticipantView:
    participant: PlottingRoomParticipant
    membership: CommunityMembership
    character: Character | None
    created_at_label: str

    @property
    def display_name(self) -> str:
        if self.character is not None:
            return self.character.name
        if self.participant.prospective_character_name:
            return self.participant.prospective_character_name
        return self.membership.display_name


@dataclass(frozen=True, slots=True)
class PlottingRoomSummary:
    room: PlottingRoom
    participants: list[PlottingRoomParticipantView]
    source_label: str
    source_href: str
    created_at_label: str


@dataclass(frozen=True, slots=True)
class PlotHookInterestInboxItem:
    hook: CharacterPlotHookSummary
    interest: CharacterPlotHookInterestView
    room: PlottingRoomSummary | None


@dataclass(frozen=True, slots=True)
class WantedInterestInboxItem:
    wanted_ad: WantedAdSummary
    interest: WantedAdInterestView
    room: PlottingRoomSummary | None


@dataclass(frozen=True, slots=True)
class PlottingDesk:
    rooms: list[PlottingRoomSummary]
    plot_hook_interests: list[PlotHookInterestInboxItem]
    wanted_interests: list[WantedInterestInboxItem]


@dataclass(frozen=True, slots=True)
class PlottingRoomDetail:
    room: PlottingRoom
    owner_membership: CommunityMembership
    participants: list[PlottingRoomParticipantView]
    source_plot_hook: CharacterPlotHookSummary | None
    source_wanted_ad: WantedAdSummary | None
    created_at_label: str
    can_manage: bool


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
    can_express_prospective_interest: bool
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
    facet_choices: list[FacetChoiceGroup]
    plotting_rooms: list[PlottingRoomSummary]
    plot_hooks: list[CharacterPlotHookSummary]
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
    latest_post: PostView | None
    episode: EpisodeCredits
    reply_count: int
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


def thread_state_badges(thread: Thread) -> tuple[ThreadCardBadge, ...]:
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
