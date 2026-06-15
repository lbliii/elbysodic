"""Read models and contracts for the forum service layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from elbysodic.domain.boards import BOARD_SIDEBAR_SECTION_LABELS
from elbysodic.domain.models import (
    ApplicationFieldValue,
    ApplicationTemplateField,
    Board,
    Character,
    CharacterApplication,
    CharacterApplicationEvent,
    CharacterClaim,
    CharacterPlotHook,
    CharacterPlotHookInterest,
    CharacterReserve,
    ClaimType,
    Community,
    CommunityDiscoveryProfile,
    CommunityDiscoveryTag,
    CommunityGatewaySlot,
    CommunityMembership,
    Facet,
    FacetGroup,
    Material,
    Notification,
    PlottingRoom,
    PlottingRoomMessage,
    PlottingRoomParticipant,
    Post,
    PostRevision,
    RealmInteraction,
    RealmInteractionAnswer,
    RealmInteractionOption,
    RealmInteractionQuestion,
    RealmInteractionResponse,
    Role,
    SidebarSectionConfig,
    Thread,
    User,
    WantedAd,
    WantedAdInterest,
)
from elbysodic.services.themes import ProgramThemeView, ThemeEditorView, ThemeHealthWarning
from elbysodic.services.timestamps import relative_timestamp_label

type BoardThreadFilter = Literal["all", "unread", "attention", "mine", "pinned", "locked"]
type ThreadStatus = Literal["open", "active", "paused", "complete", "private", "archived"]
type PostingMode = Literal["freeform", "posting_order"]
type MentionableKind = Literal["character", "writer"]
type MentionableScope = Literal["all", "cast", "characters", "writers", "ooc"]
type PostProfileVariant = Literal["bio", "poster", "dock", "crest"]
type PostAccentStyle = Literal["soft", "line", "glow", "block"]
type PostBorderStyle = Literal["none", "hairline", "bracket", "double"]
type PostTitleStyle = Literal["standard", "serif", "condensed", "mono"]
type PostDensity = Literal["calm", "compact", "dramatic"]
type NavigationHealthSeverity = Literal["note", "warning", "attention"]
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
POST_PROFILE_VARIANTS: tuple[PostProfileVariant, ...] = ("bio", "poster", "dock", "crest")
POST_PROFILE_VARIANT_LABELS: dict[str, str] = {
    "bio": "Bio card",
    "poster": "Poster focus",
    "dock": "Docked profile",
    "crest": "Crest mark",
}
POST_ACCENT_STYLES: tuple[PostAccentStyle, ...] = ("soft", "line", "glow", "block")
POST_ACCENT_STYLE_LABELS: dict[str, str] = {
    "soft": "Soft wash",
    "line": "Accent line",
    "glow": "Low glow",
    "block": "Color block",
}
POST_BORDER_STYLES: tuple[PostBorderStyle, ...] = ("none", "hairline", "bracket", "double")
POST_BORDER_STYLE_LABELS: dict[str, str] = {
    "none": "No frame",
    "hairline": "Hairline",
    "bracket": "Bracket",
    "double": "Double line",
}
POST_TITLE_STYLES: tuple[PostTitleStyle, ...] = ("standard", "serif", "condensed", "mono")
POST_TITLE_STYLE_LABELS: dict[str, str] = {
    "standard": "Standard",
    "serif": "Literary",
    "condensed": "Condensed",
    "mono": "Archive",
}
POST_DENSITIES: tuple[PostDensity, ...] = ("calm", "compact", "dramatic")
POST_DENSITY_LABELS: dict[str, str] = {
    "calm": "Calm",
    "compact": "Compact",
    "dramatic": "Dramatic",
}
POST_STYLE_PRESETS: dict[str, dict[str, str]] = {
    "classic-bio": {
        "label": "Classic Bio",
        "post_profile_variant": "bio",
        "post_accent_style": "soft",
        "post_border_style": "hairline",
        "post_title_style": "standard",
        "post_density": "calm",
    },
    "portrait-poster": {
        "label": "Portrait Poster",
        "post_profile_variant": "poster",
        "post_accent_style": "line",
        "post_border_style": "hairline",
        "post_title_style": "standard",
        "post_density": "calm",
    },
    "faction-dossier": {
        "label": "Faction Dossier",
        "post_profile_variant": "crest",
        "post_accent_style": "block",
        "post_border_style": "double",
        "post_title_style": "mono",
        "post_density": "compact",
    },
    "dramatic-scene": {
        "label": "Dramatic Scene",
        "post_profile_variant": "dock",
        "post_accent_style": "glow",
        "post_border_style": "bracket",
        "post_title_style": "serif",
        "post_density": "dramatic",
    },
}


@dataclass(frozen=True, slots=True)
class PostStylePolicy:
    enabled_profile_variants: tuple[str, ...]
    enabled_accent_styles: tuple[str, ...]
    enabled_border_styles: tuple[str, ...]
    enabled_title_styles: tuple[str, ...]
    enabled_densities: tuple[str, ...]

    def profile_variant_labels(self, current_value: str | None = None) -> dict[str, str]:
        return _style_labels(
            POST_PROFILE_VARIANT_LABELS, self.enabled_profile_variants, current_value
        )

    def accent_style_labels(self, current_value: str | None = None) -> dict[str, str]:
        return _style_labels(POST_ACCENT_STYLE_LABELS, self.enabled_accent_styles, current_value)

    def border_style_labels(self, current_value: str | None = None) -> dict[str, str]:
        return _style_labels(POST_BORDER_STYLE_LABELS, self.enabled_border_styles, current_value)

    def title_style_labels(self, current_value: str | None = None) -> dict[str, str]:
        return _style_labels(POST_TITLE_STYLE_LABELS, self.enabled_title_styles, current_value)

    def density_labels(self, current_value: str | None = None) -> dict[str, str]:
        return _style_labels(POST_DENSITY_LABELS, self.enabled_densities, current_value)


def _style_labels(
    all_labels: dict[str, str],
    enabled_values: tuple[str, ...],
    current_value: str | None,
) -> dict[str, str]:
    values = list(enabled_values)
    if current_value and current_value in all_labels and current_value not in values:
        values.append(current_value)
    return {value: all_labels[value] for value in values if value in all_labels}


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
class BoardPage:
    board: Board
    summary: BoardSummary
    parent_board: Board | None
    is_location_board: bool
    is_community_board: bool
    board_facets: list[FacetTag]
    subboards: list[BoardSummary]
    sibling_boards: list[BoardSummary]
    current_event: MaterialSummary | None
    threads: list[ThreadSummary]
    direct_thread_count: int
    next_unread_thread: ThreadNavigationItem | None
    can_start_thread: bool
    can_manage_board: bool


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


def scene_location_lane_item_badges(
    summary: ThreadSummary,
    *,
    is_current: bool,
    is_watched: bool,
    waiting_on_others: bool,
) -> tuple[ThreadCardBadge, ...]:
    """Template-visible badge tuples (Kida/Chirp read models omit `@property`)."""
    badges: list[ThreadCardBadge] = []
    if is_current:
        badges.append(ThreadCardBadge("current scene", "success"))
    badges.extend(summary.badges)
    if waiting_on_others:
        badges.append(ThreadCardBadge("waiting", "info"))
    if is_watched:
        badges.append(ThreadCardBadge("watching", "info"))
    return tuple(badges)


@dataclass(frozen=True, slots=True)
class SceneLocationLaneItem:
    summary: ThreadSummary
    is_current: bool
    is_watched: bool
    waiting_on_others: bool
    badges: tuple[ThreadCardBadge, ...]


def _derive_scene_lane_placement(
    board: Board, placement_path: tuple[Board, ...]
) -> tuple[str, Board, tuple[Board, ...]]:
    label = BOARD_SIDEBAR_SECTION_LABELS[board.sidebar_section]
    placement_sidebar_eyebrow = f"In {label}"
    place_headline_board = placement_path[0] if placement_path else board
    placement_trail_boards = () if len(placement_path) <= 1 else placement_path[1:]
    return placement_sidebar_eyebrow, place_headline_board, placement_trail_boards


def _derive_scene_lane_item_slices(
    items: list[SceneLocationLaneItem],
) -> tuple[
    tuple[SceneLocationLaneItem, ...],
    tuple[SceneLocationLaneItem, ...],
]:
    attention_items = tuple(item for item in items if item.summary.needs_attention)
    active_items = tuple(
        item
        for item in items
        if not item.summary.needs_attention
        and not item.waiting_on_others
        and item.summary.thread.status in {"open", "active"}
    )
    return attention_items, active_items


@dataclass(frozen=True, slots=True)
class SceneLocationLane:
    board: Board
    parent_board: Board | None
    placement_path: tuple[Board, ...]
    sidebar_section_label: str
    items: list[SceneLocationLaneItem]
    placement_sidebar_eyebrow: str
    place_headline_board: Board
    placement_trail_boards: tuple[Board, ...]
    attention_items: tuple[SceneLocationLaneItem, ...]
    active_items: tuple[SceneLocationLaneItem, ...]
    current_item: SceneLocationLaneItem | None

    @classmethod
    def assembled(
        cls,
        board: Board,
        parent_board: Board | None,
        placement_path: tuple[Board, ...],
        items: list[SceneLocationLaneItem],
        current_item: SceneLocationLaneItem | None = None,
    ) -> SceneLocationLane:
        placement_sidebar_eyebrow, place_headline_board, placement_trail_boards = (
            _derive_scene_lane_placement(board, placement_path)
        )
        attention_items, active_items = _derive_scene_lane_item_slices(items)
        return cls(
            board=board,
            parent_board=parent_board,
            placement_path=placement_path,
            sidebar_section_label=BOARD_SIDEBAR_SECTION_LABELS[board.sidebar_section],
            items=items,
            placement_sidebar_eyebrow=placement_sidebar_eyebrow,
            place_headline_board=place_headline_board,
            placement_trail_boards=placement_trail_boards,
            attention_items=attention_items,
            active_items=active_items,
            current_item=current_item,
        )


@dataclass(frozen=True, slots=True)
class PostView:
    post: Post
    author: Character
    author_accent_color: str
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
class RealmHome:
    realm_gateway: RealmGatewayView | None
    can_manage_home: bool
    world_status_label: str
    world_status_copy: str
    boards: list[BoardSummary]
    location_boards: list[BoardSummary]
    community_boards: list[BoardSummary]
    desk_boards: list[BoardSummary]
    attention: list[AttentionItem]
    activity: list[ActivityItem]


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
class NotificationCenter:
    inbox: NotificationInbox


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
    accent_color: str
    accent_source_label: str
    accent_source_detail: str
    is_default: bool
    activity: CharacterThreadActivity
    application_status_label: str
    application_status_variant: str


@dataclass(frozen=True, slots=True)
class CharacterRosterDashboard:
    cards: list[CharacterRosterCard]


@dataclass(frozen=True, slots=True)
class CharacterRosterPage:
    roster_dashboard: CharacterRosterDashboard
    post_style_policy: PostStylePolicy
    post_style_preview_config_id: str
    post_style_preview_config: dict[str, object]


@dataclass(frozen=True, slots=True)
class ApplicationCharacterView:
    character: Character
    application: CharacterApplication | None
    membership: CommunityMembership
    facets: list[FacetTag]
    reserves: list[CharacterReserveView]
    status_label: str
    status_variant: str
    is_owned_by_viewer: bool
    claim_conflict_count: int = 0
    claim_conflict_summary: str = ""

    @property
    def has_claim_conflicts(self) -> bool:
        return self.claim_conflict_count > 0


@dataclass(frozen=True, slots=True)
class ApplicationsDesk:
    my_applications: list[ApplicationCharacterView]
    review_queue: list[ApplicationCharacterView]
    accepted_characters: list[ApplicationCharacterView]
    application_materials: list[MaterialSummary]
    can_review: bool


type WriterActivationStage = Literal[
    "needs_face",
    "application_draft",
    "application_submitted",
    "application_revision",
    "accepted_no_scene",
    "wanted_interest",
    "plotting",
    "active_scene",
]


@dataclass(frozen=True, slots=True)
class WriterActivationOpening:
    kind: str
    label: str
    href: str
    summary: str
    detail: str = ""


@dataclass(frozen=True, slots=True)
class WriterActivation:
    stage: WriterActivationStage
    headline: str
    summary: str
    primary_label: str
    primary_href: str
    secondary_label: str = ""
    secondary_href: str = ""
    roster_count: int = 0
    accepted_face_count: int = 0
    open_application_count: int = 0
    active_scene_count: int = 0
    wanted_interest_count: int = 0
    plotting_room_count: int = 0
    claim_gap_count: int = 0
    claim_conflict_count: int = 0
    reserve_count: int = 0

    @property
    def needs_first_face(self) -> bool:
        return self.stage == "needs_face"

    @property
    def has_application_work(self) -> bool:
        return self.stage in {
            "application_draft",
            "application_submitted",
            "application_revision",
        }

    @property
    def has_playable_scene(self) -> bool:
        return self.stage == "active_scene"


@dataclass(frozen=True, slots=True)
class ApplicationOnboarding:
    facets: list[FacetTag]
    application_materials: list[MaterialSummary]
    interactions: list[RealmInteractionSummary]
    template_fields: list[ApplicationTemplateFieldView]


@dataclass(frozen=True, slots=True)
class ApplicationReviewEventView:
    event: CharacterApplicationEvent
    actor_membership: CommunityMembership
    actor: Character | None
    actor_label: str
    created_at_label: str
    from_label: str | None
    to_label: str


@dataclass(frozen=True, slots=True)
class ApplicationReviewRoom:
    application: CharacterApplication
    character_view: ApplicationCharacterView
    intake_fields: list[ApplicationFieldDraftView]
    field_values: list[ApplicationFieldValueView]
    events: list[ApplicationReviewEventView]
    can_edit_application: bool
    can_review: bool

    @property
    def blocking_claim_conflicts(self) -> list[ApplicationFieldValueView]:
        return [
            item
            for item in self.field_values
            if item.claim_check is not None and item.claim_check.status == "conflict"
        ]

    @property
    def has_blocking_claim_conflicts(self) -> bool:
        return bool(self.blocking_claim_conflicts)

    @property
    def claim_conflict_revision_note(self) -> str:
        conflicts = self.blocking_claim_conflicts
        if not conflicts:
            return ""
        lines = ["Please revise the mapped claim details before we can accept this face."]
        for item in conflicts:
            holder = "the casting desk"
            if (
                item.claim_check is not None
                and item.claim_check.claim is not None
                and item.claim_check.claim.character is not None
            ):
                holder = item.claim_check.claim.character.name
            lines.append(
                f"- {item.field.field.label}: {item.value.value} is already held by {holder}."
            )
        return "\n".join(lines)


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
class RealmInteractionSummary:
    interaction: RealmInteraction
    response_count: int
    has_response: bool

    @property
    def type_label(self) -> str:
        return {
            "quiz": "Quiz",
            "poll": "Poll",
            "survey": "Survey",
        }.get(self.interaction.interaction_type, "Interaction")

    @property
    def status_label(self) -> str:
        return "Open" if self.interaction.status == "open" else self.interaction.status.title()


@dataclass(frozen=True, slots=True)
class RealmInteractionOptionView:
    option: RealmInteractionOption
    response_count: int
    is_selected: bool


@dataclass(frozen=True, slots=True)
class RealmInteractionQuestionView:
    question: RealmInteractionQuestion
    options: list[RealmInteractionOptionView]


@dataclass(frozen=True, slots=True)
class RealmInteractionDetail:
    summary: RealmInteractionSummary
    questions: list[RealmInteractionQuestionView]
    response: RealmInteractionResponse | None
    answers: list[RealmInteractionAnswer]


@dataclass(frozen=True, slots=True)
class RealmInteractionHub:
    interactions: list[RealmInteractionSummary]


@dataclass(frozen=True, slots=True)
class ApplicationTemplateFieldView:
    field: ApplicationTemplateField
    options: list[str]
    mapped_claim_type: ClaimType | None

    @property
    def options_text(self) -> str:
        return "\n".join(self.options)


@dataclass(frozen=True, slots=True)
class ApplicationFieldValueView:
    value: ApplicationFieldValue
    field: ApplicationTemplateFieldView
    claim_check: ApplicationClaimCheck | None = None


@dataclass(frozen=True, slots=True)
class ApplicationFieldDraftView:
    field: ApplicationTemplateFieldView
    value: str
    claim_check: ApplicationClaimCheck | None = None


@dataclass(frozen=True, slots=True)
class CharacterClaimView:
    claim: CharacterClaim
    claim_type: ClaimType
    character: Character | None
    application: CharacterApplication | None

    @property
    def status_label(self) -> str:
        return self.claim.status.title()


@dataclass(frozen=True, slots=True)
class ApplicationClaimCheck:
    status: str
    label: str
    variant: str
    claim: CharacterClaimView | None = None


@dataclass(frozen=True, slots=True)
class ClaimTypeDirectory:
    claim_type: ClaimType
    claims: list[CharacterClaimView]
    template_fields: list[ApplicationTemplateFieldView]
    total_count: int = 0
    claimed_count: int = 0
    reserved_count: int = 0
    available_count: int = 0

    @property
    def live_count(self) -> int:
        return self.claimed_count + self.reserved_count


@dataclass(frozen=True, slots=True)
class ClaimsDirectory:
    groups: list[ClaimTypeDirectory]
    status_filter: str | None = None
    search_query: str = ""
    can_manage: bool = False

    @property
    def claim_count(self) -> int:
        return sum(group.total_count for group in self.groups)

    @property
    def visible_claim_count(self) -> int:
        return sum(len(group.claims) for group in self.groups)

    @property
    def claimed_count(self) -> int:
        return sum(group.claimed_count for group in self.groups)

    @property
    def reserved_count(self) -> int:
        return sum(group.reserved_count for group in self.groups)

    @property
    def available_count(self) -> int:
        return sum(group.available_count for group in self.groups)

    @property
    def required_count(self) -> int:
        return len([group for group in self.groups if group.claim_type.is_required])

    @property
    def claim_type_names(self) -> list[str]:
        return [group.claim_type.name for group in self.groups]

    @property
    def has_active_filter(self) -> bool:
        return self.status_filter is not None or bool(self.search_query)


@dataclass(frozen=True, slots=True)
class ClaimsPage:
    directory: ClaimsDirectory
    characters: list[Character]


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


def _story_material_display_title(title: str) -> str:
    for prefix in ("Current Chapter:", "Premise:"):
        if title.lower().startswith(prefix.lower()):
            return title[len(prefix) :].strip() or title
    return title


@dataclass(frozen=True, slots=True)
class MaterialSummary:
    material: Material
    facets: list[FacetTag]
    rendered_summary: str
    type_label: str

    @property
    def display_title(self) -> str:
        return _story_material_display_title(self.material.title)


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

    @property
    def display_title(self) -> str:
        return _story_material_display_title(self.material.title)


@dataclass(frozen=True, slots=True)
class WorldHub:
    featured: list[MaterialSummary]
    guides: list[MaterialSummary]
    events: list[MaterialSummary]
    application_materials: list[MaterialSummary]
    can_manage: bool


@dataclass(frozen=True, slots=True)
class BoardTaxonomyItem:
    summary: BoardSummary
    parent: Board | None
    child_count: int
    kind_label: str
    realm_label: str
    sidebar_label: str
    sidebar_section_label: str
    guidance: str

    @property
    def board(self) -> Board:
        return self.summary.board


@dataclass(frozen=True, slots=True)
class NavigationPreviewItem:
    label: str
    href: str
    source_label: str
    behavior_label: str
    count: int | None = None


@dataclass(frozen=True, slots=True)
class NavigationPreviewSection:
    realm_label: str
    title: str
    description: str
    label_visible: bool
    items: list[NavigationPreviewItem]


@dataclass(frozen=True, slots=True)
class NavigationHealthWarning:
    severity: NavigationHealthSeverity
    title: str
    message: str
    board: Board | None = None
    section: SidebarSectionConfig | None = None
    href: str | None = None


@dataclass(frozen=True, slots=True)
class StudioBoardEditor:
    board: Board
    summary: BoardSummary
    parent: Board | None
    parent_options: list[Board]
    kind_label: str
    realm_label: str
    sidebar_label: str
    sidebar_section_label: str
    sidebar_section_guidance: str
    guidance: str
    can_manage: bool


@dataclass(frozen=True, slots=True)
class RealmLaunchChecklistItem:
    label: str
    summary: str
    href: str
    cta: str
    is_complete: bool
    is_required: bool = True

    @property
    def status_label(self) -> str:
        if self.is_complete:
            return "Ready"
        return "Needed" if self.is_required else "Optional"

    @property
    def status_variant(self) -> str:
        if self.is_complete:
            return "success"
        return "warning" if self.is_required else "muted"


@dataclass(frozen=True, slots=True)
class RealmLaunchReadiness:
    items: list[RealmLaunchChecklistItem]

    @property
    def completed_count(self) -> int:
        return sum(1 for item in self.items if item.is_complete)

    @property
    def required_count(self) -> int:
        return sum(1 for item in self.items if item.is_required)

    @property
    def completed_required_count(self) -> int:
        return sum(1 for item in self.items if item.is_required and item.is_complete)

    @property
    def missing_required_count(self) -> int:
        return self.required_count - self.completed_required_count

    @property
    def is_ready(self) -> bool:
        return self.missing_required_count == 0

    @property
    def status_label(self) -> str:
        if self.is_ready:
            return "Ready for invite-only opening"
        return f"{self.missing_required_count} required lanes still backstage"


@dataclass(frozen=True, slots=True)
class GatewayCurationChoice:
    target_id: int
    title: str
    summary: str
    href: str
    is_selected: bool
    position_value: int
    slot: CommunityGatewaySlot | None = None


@dataclass(frozen=True, slots=True)
class GatewayCurationSection:
    slot_type: str
    title: str
    summary: str
    choices: tuple[GatewayCurationChoice, ...]

    @property
    def selected_count(self) -> int:
        return sum(1 for choice in self.choices if choice.is_selected)


@dataclass(frozen=True, slots=True)
class GatewayCurationEditor:
    scene_hubs: GatewayCurationSection
    wanted_hooks: GatewayCurationSection
    guidebook_materials: GatewayCurationSection


@dataclass(frozen=True, slots=True)
class DirectorStudio:
    can_manage: bool
    gateway_curation: GatewayCurationEditor
    launch_readiness: RealmLaunchReadiness
    theme_editor: ThemeEditorView
    theme_warnings: tuple[ThemeHealthWarning, ...]
    facet_groups: list[FacetGroup]
    identity_accent_group: FacetGroup | None
    post_style_policy: PostStylePolicy
    materials: list[MaterialSummary]
    draft_materials: list[MaterialSummary]
    featured_materials: list[MaterialSummary]
    events: list[MaterialSummary]
    current_event: MaterialSummary | None
    application_materials: list[MaterialSummary]
    board_taxonomy: list[BoardTaxonomyItem]
    sidebar_sections: list[SidebarSectionConfig]
    navigation_preview_sections: list[NavigationPreviewSection]
    navigation_warnings: list[NavigationHealthWarning]
    location_boards: list[BoardSummary]
    sublocation_boards: list[BoardSummary]
    wanted_ads: list[WantedAdSummary]
    open_wanted_ads: list[WantedAdSummary]
    applications: ApplicationsDesk
    claims: ClaimsDirectory

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
    def navigation_attention_count(self) -> int:
        return sum(1 for warning in self.navigation_warnings if warning.severity == "attention")

    @property
    def navigation_warning_count(self) -> int:
        return sum(1 for warning in self.navigation_warnings if warning.severity == "warning")

    @property
    def navigation_note_count(self) -> int:
        return sum(1 for warning in self.navigation_warnings if warning.severity == "note")

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
    def community_board_count(self) -> int:
        return sum(1 for item in self.board_taxonomy if item.board.board_kind == "community")

    @property
    def archive_board_count(self) -> int:
        return sum(1 for item in self.board_taxonomy if item.board.board_kind == "archive")

    @property
    def staff_board_count(self) -> int:
        return sum(1 for item in self.board_taxonomy if item.board.board_kind == "staff")

    @property
    def desk_board_count(self) -> int:
        return sum(1 for item in self.board_taxonomy if item.board.board_kind == "desk")

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

    @property
    def related_material_display_title(self) -> str:
        if self.related_material is None:
            return ""
        return _story_material_display_title(self.related_material.title)


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
class WantedAdInterestDetailItem:
    view: WantedAdInterestView
    room: PlottingRoom | None
    room_id: int | None
    room_status: str
    can_view_note: bool
    can_manage: bool
    can_open_room: bool
    show_room_link: bool
    stage_label: str
    stage_variant: str
    thread_href: str | None
    primary_action_label: str
    primary_action_href: str
    secondary_action_label: str
    secondary_action_href: str

    @property
    def interest(self) -> WantedAdInterest:
        return self.view.interest

    @property
    def membership(self) -> CommunityMembership:
        return self.view.membership

    @property
    def character(self) -> Character | None:
        return self.view.character

    @property
    def created_at_label(self) -> str:
        return self.view.created_at_label

    @property
    def display_name(self) -> str:
        return self.view.display_name


@dataclass(frozen=True, slots=True)
class WantedCastingPacket:
    why_it_matters: list[str]
    first_scene_invitations: list[str]
    relationship_lanes: list[str]
    negotiables: list[str]

    @property
    def has_content(self) -> bool:
        return bool(
            self.why_it_matters
            or self.first_scene_invitations
            or self.relationship_lanes
            or self.negotiables
        )


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
class PlottingRoomMessageView:
    message: PlottingRoomMessage
    author_membership: CommunityMembership
    author_character: Character | None
    created_at_label: str

    @property
    def author_label(self) -> str:
        if self.author_character is not None:
            return self.author_character.name
        return self.author_membership.display_name or self.author_membership.username

    @property
    def author_href(self) -> str:
        if self.author_character is not None:
            return f"/characters/{self.author_character.slug}"
        return f"/members/{self.author_membership.username}"


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
    stage_group: str
    stage_label: str
    stage_variant: str


@dataclass(frozen=True, slots=True)
class PlottingDesk:
    rooms: list[PlottingRoomSummary]
    plot_hook_interests: list[PlotHookInterestInboxItem]
    wanted_interests: list[WantedInterestInboxItem]

    @property
    def wanted_raised_interests(self) -> list[WantedInterestInboxItem]:
        return [item for item in self.wanted_interests if item.stage_group == "raised"]

    @property
    def wanted_plotting_interests(self) -> list[WantedInterestInboxItem]:
        return [item for item in self.wanted_interests if item.stage_group == "plotting"]

    @property
    def wanted_ready_interests(self) -> list[WantedInterestInboxItem]:
        return [item for item in self.wanted_interests if item.stage_group == "ready"]

    @property
    def wanted_threaded_interests(self) -> list[WantedInterestInboxItem]:
        return [item for item in self.wanted_interests if item.stage_group == "threaded"]


@dataclass(frozen=True, slots=True)
class PlottingRoomDetail:
    room: PlottingRoom
    owner_membership: CommunityMembership
    participants: list[PlottingRoomParticipantView]
    source_plot_hook: CharacterPlotHookSummary | None
    source_wanted_ad: WantedAdSummary | None
    target_board: Board | None
    target_thread: Thread | None
    scene_boards: list[Board]
    scene_character_options: list[Character]
    messages: list[PlottingRoomMessageView]
    created_at_label: str
    can_manage: bool
    can_edit_plan: bool
    can_create_scene: bool


@dataclass(frozen=True, slots=True)
class WantedAdDetail:
    wanted_ad: WantedAd
    creator_membership: CommunityMembership
    creator_character: Character | None
    related_material: Material | None
    related_characters: list[Character]
    facets: list[FacetTag]
    interests: list[WantedAdInterestDetailItem]
    reserves: list[CharacterReserveView]
    reserve_interest_ids: set[int]
    viewer_interest: WantedAdInterestDetailItem | None
    can_express_interest: bool
    can_express_prospective_interest: bool
    is_created_by_viewer: bool
    can_manage: bool
    rendered_body: object
    casting_packet: WantedCastingPacket
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
    accent_color: str
    accent_source_label: str
    accent_source_detail: str
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
class SceneGroundingFact:
    label: str
    value: str


@dataclass(frozen=True, slots=True)
class SceneStoryLink:
    kind: str
    label: str
    title: str
    summary: str
    href: str
    status_label: str
    source_label: str
    participant_labels: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SceneGroundingPanel:
    board: Board
    parent_board: Board | None
    participants: list[Character]
    current_event: MaterialSummary | None
    visibility_label: str
    visibility_detail: str
    active_face_label: str
    active_face_variant: str
    facts: tuple[SceneGroundingFact, ...]
    can_manage_scene: bool
    can_moderate_scene: bool
    is_watched: bool
    story_links: tuple[SceneStoryLink, ...]


@dataclass(frozen=True, slots=True)
class SceneMediaBand:
    source_board: Board
    source_label: str
    heading: str
    summary: str
    is_inherited: bool
    current_event: MaterialSummary | None


@dataclass(frozen=True, slots=True)
class SceneWriterActivity:
    selected_character: Character
    needs_reply: list[ThreadObligationItem]
    waiting_on_others: list[ThreadObligationItem]
    is_watching_current_scene: bool
    is_caught_up_current_scene: bool

    @property
    def has_queue_items(self) -> bool:
        return bool(self.needs_reply or self.waiting_on_others)

    @property
    def visible_count(self) -> int:
        return len(self.needs_reply) + len(self.waiting_on_others)


@dataclass(frozen=True, slots=True)
class SceneContextView:
    thread_view: ThreadView
    parent_board: Board | None
    location_lane: SceneLocationLane
    grounding: SceneGroundingPanel
    media_band: SceneMediaBand | None
    current_event: MaterialSummary | None
    writer_activity: SceneWriterActivity | None


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
    first_unread_post: PostView | None
    viewer_needs_reply: bool
    needs_reply_since_label: str | None
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
    previous_unreplied_thread: ThreadNavigationItem | None
    next_unread_thread: ThreadNavigationItem | None
    is_watched: bool


@dataclass(frozen=True, slots=True)
class StudioIdentityOption:
    community: Community
    membership: CommunityMembership
    role: Role
    current_character: Character | None
    unread_notification_count: int
    is_current: bool

    @property
    def entry_href(self) -> str:
        return f"/c/{self.community.slug}"


@dataclass(frozen=True, slots=True)
class AccountVisitorView:
    user: User
    current_community: Community | None
    identity_options: list[StudioIdentityOption]

    @property
    def display_label(self) -> str:
        return self.user.email

    @property
    def avatar_label(self) -> str:
        return self.display_label[:1].upper()


@dataclass(frozen=True, slots=True)
class DevPersonaView:
    key: str
    label: str
    purpose: str
    default_path: str
    user: User
    community: Community
    membership: CommunityMembership
    role: Role
    character: Character | None
    can_switch: bool
    is_current: bool
    can_manage_studio: bool


@dataclass(frozen=True, slots=True)
class FirstRealmSetupResult:
    community: Community
    user: User
    membership: CommunityMembership
    role: Role


@dataclass(frozen=True, slots=True)
class StudioNetworkThemePreview:
    accent: str
    surface: str
    text: str
    display_font: str


@dataclass(frozen=True, slots=True)
class StudioNetworkProgramView:
    community: Community
    membership: CommunityMembership | None
    role: Role | None
    current_character: Character | None
    premise: MaterialSummary | None
    current_event: MaterialSummary | None
    roster_count: int
    open_wanted_count: int
    application_material_count: int
    claim_type_count: int
    application_count: int
    plotting_room_count: int
    unread_notification_count: int
    theme_preview: StudioNetworkThemePreview
    is_current: bool
    latest_public_activity_at: str = ""

    @property
    def is_authenticated(self) -> bool:
        return self.membership is not None and self.role is not None

    @property
    def entry_href(self) -> str:
        return _program_href(self, "/")

    @property
    def monogram(self) -> str:
        parts = [
            part for part in self.community.name.replace("-", " ").replace("_", " ").split() if part
        ]
        if not parts:
            return "EB"
        if len(parts) == 1:
            return parts[0][:2].upper()
        return "".join(part[:1] for part in parts[:3]).upper()

    @property
    def application_href(self) -> str:
        return _program_href(self, "/applications/new")

    @property
    def request_access_href(self) -> str:
        if self.community.launch_status != "public-preview":
            return ""
        return _program_href(self, "/request-access")

    @property
    def access_posture_label(self) -> str:
        if self.request_access_href:
            return "Request access open"
        if self.community.launch_status == "invite-only":
            return "Invitation required"
        if self.community.launch_status == "public-preview":
            return "Public preview open"
        return self.launch_status_label

    @property
    def activity_freshness_label(self) -> str:
        if not self.latest_public_activity_at:
            return "No public activity yet"
        return f"Public activity {relative_timestamp_label(self.latest_public_activity_at)}"

    @property
    def launch_status_label(self) -> str:
        return self.community.launch_status.replace("-", " ").title()

    @property
    def application_posture_label(self) -> str:
        if self.application_material_count:
            return "Application guide ready"
        return "Application guide pending"

    @property
    def claims_posture_label(self) -> str:
        if self.claim_type_count:
            return "Claims configured"
        return "Claims not configured"

    @property
    def invite_posture_label(self) -> str:
        if self.community.launch_status == "public-preview":
            return "Public preview"
        if self.community.launch_status == "invite-only":
            return "Invite-only"
        return "Backstage"

    @property
    def premise_href(self) -> str | None:
        if self.premise is None:
            return None
        return _program_href(self, f"/world/{self.premise.material.slug}")

    @property
    def current_event_href(self) -> str | None:
        if self.current_event is None:
            return None
        return _program_href(self, f"/world/{self.current_event.material.slug}")


@dataclass(frozen=True, slots=True)
class RealmGatewayAction:
    label: str
    href: str
    is_hx_boost_safe: bool = True


@dataclass(frozen=True, slots=True)
class RealmGatewayHero:
    kicker: str
    title: str
    lead: str
    now_playing_label: str
    now_playing_copy: str
    first_face_path: str
    primary_action: RealmGatewayAction
    secondary_action: RealmGatewayAction | None = None


@dataclass(frozen=True, slots=True)
class RealmGatewayPremise:
    discovery_profile: CommunityDiscoveryProfile | None
    catalog_pitch: str
    onboarding_pitch: str
    premise_label: str
    play_label: str
    lore_label: str
    roster_posture: str


@dataclass(frozen=True, slots=True)
class RealmGatewayStoryFrame:
    eyebrow: str
    access_label: str
    rating_label: str
    cadence_label: str
    writing_expectation: str
    roster_posture: str

    @property
    def fit_labels(self) -> tuple[str, ...]:
        labels = [
            self.access_label,
            self.rating_label,
            self.cadence_label,
            self.roster_posture,
        ]
        return tuple(label for label in labels if label)

    @property
    def fit_summary(self) -> str:
        return ", ".join(self.fit_labels)


@dataclass(frozen=True, slots=True)
class RealmGatewayAtmosphere:
    title: str
    label: str
    copy: str
    href: str | None
    source_type: str


@dataclass(frozen=True, slots=True)
class RealmGatewayPremiseStage:
    label: str
    title: str
    summary: str
    playable_pressure: str
    action: RealmGatewayAction | None = None


@dataclass(frozen=True, slots=True)
class RealmGatewayPremiseEvolution:
    premise_title: str
    premise_summary: str
    inciting_incident: str
    current_pressure_title: str
    current_pressure_summary: str
    consequences: str
    next_openings: str
    source_href: str | None
    source_kind: str

    @property
    def has_current_pressure(self) -> bool:
        return self.source_kind == "event"


@dataclass(frozen=True, slots=True)
class RealmGatewaySocialLane:
    title: str
    summary: str
    tone: str


@dataclass(frozen=True, slots=True)
class RealmGatewayCastMember:
    character: Character
    summary: str

    @property
    def href(self) -> str:
        return f"/characters/{self.character.slug}"

    @property
    def monogram(self) -> str:
        parts = [part for part in self.character.name.split() if part]
        if not parts:
            return "?"
        if len(parts) == 1:
            return parts[0][:1].upper()
        return "".join(part[:1] for part in parts[:2]).upper()


@dataclass(frozen=True, slots=True)
class RealmGatewaySceneHub:
    board: Board
    public_thread_count: int
    emphasis: str = "normal"
    summary: str = ""
    image_url: str | None = None
    image_alt: str = ""
    image_treatment: str = "standard"

    @property
    def href(self) -> str:
        return f"/boards/{self.board.slug}"

    @property
    def display_summary(self) -> str:
        return self.summary or self.board.tagline or self.board.description or self.board.board_kind


@dataclass(frozen=True, slots=True)
class RealmGatewayScenePreview:
    title: str
    summary: str
    href: str
    board_label: str
    cast_label: str


@dataclass(frozen=True, slots=True)
class RealmGatewayEntryPath:
    title: str
    summary: str
    href: str
    metric_label: str
    metric_value: int | None = None


@dataclass(frozen=True, slots=True)
class RealmGatewaySignalItem:
    title: str
    summary: str
    value: str | None = None


@dataclass(frozen=True, slots=True)
class RealmGatewayWantedPreview:
    title: str
    summary: str
    href: str
    type_label: str
    related_label: str | None = None


@dataclass(frozen=True, slots=True)
class RealmGatewayGuidebookPreview:
    material: MaterialSummary
    display_title: str


@dataclass(frozen=True, slots=True)
class RealmGatewayContinuation:
    audience: str
    title: str
    summary: str
    primary_action: RealmGatewayAction
    secondary_action: RealmGatewayAction | None = None
    active_face_label: str | None = None


@dataclass(frozen=True, slots=True)
class RealmGatewayView:
    program: StudioNetworkProgramView
    guidebook: WorldHub
    hero: RealmGatewayHero
    premise: RealmGatewayPremise
    story_frame: RealmGatewayStoryFrame
    premise_stage: RealmGatewayPremiseStage
    premise_evolution: RealmGatewayPremiseEvolution
    atmosphere: RealmGatewayAtmosphere
    signals: tuple[RealmGatewaySignalItem, ...]
    scene_hubs: tuple[RealmGatewaySceneHub, ...]
    scene_previews: tuple[RealmGatewayScenePreview, ...]
    entry_paths: tuple[RealmGatewayEntryPath, ...]
    guidebook_previews: tuple[RealmGatewayGuidebookPreview, ...]
    social_lanes: tuple[RealmGatewaySocialLane, ...]
    cast_members: tuple[RealmGatewayCastMember, ...]
    wanted_previews: tuple[RealmGatewayWantedPreview, ...]
    continuation: RealmGatewayContinuation | None = None


@dataclass(frozen=True, slots=True)
class PublicCatalogCard:
    community: Community
    premise: MaterialSummary | None
    current_event: MaterialSummary | None
    discovery_profile: CommunityDiscoveryProfile | None
    discovery_tags: tuple[CommunityDiscoveryTag, ...]
    roster_count: int
    open_wanted_count: int
    application_material_count: int
    claim_type_count: int
    theme_preview: StudioNetworkThemePreview
    latest_public_activity_at: str = ""

    @property
    def entry_href(self) -> str:
        return f"/c/{self.community.slug}"

    @property
    def monogram(self) -> str:
        parts = [
            part for part in self.community.name.replace("-", " ").replace("_", " ").split() if part
        ]
        if not parts:
            return "EB"
        if len(parts) == 1:
            return parts[0][:2].upper()
        return "".join(part[:1] for part in parts[:3]).upper()

    @property
    def invite_posture_label(self) -> str:
        if self.community.launch_status == "public-preview":
            return "Public preview"
        if self.community.launch_status == "invite-only":
            return "Invite-only"
        return "Backstage"

    @property
    def request_access_href(self) -> str:
        if self.community.launch_status != "public-preview":
            return ""
        return f"{self.entry_href}/request-access"

    @property
    def access_posture_label(self) -> str:
        access_model = ""
        if self.discovery_profile is not None:
            access_model = self.discovery_profile.access_model
        if access_model == "invite-only":
            return "Invitation required"
        if access_model == "interest-form":
            return "Interest form open"
        if access_model == "request-access" or self.request_access_href:
            return "Request access open"
        if self.community.launch_status == "public-preview":
            return "Public preview open"
        return self.invite_posture_label

    @property
    def activity_freshness_label(self) -> str:
        if not self.latest_public_activity_at:
            return "No public activity yet"
        return f"Public activity {relative_timestamp_label(self.latest_public_activity_at)}"

    @property
    def application_posture_label(self) -> str:
        if self.application_material_count:
            return "Application guide ready"
        return "Application guide pending"

    @property
    def claims_posture_label(self) -> str:
        if self.claim_type_count:
            return "Claims configured"
        return "Claims not configured"

    @property
    def premise_href(self) -> str | None:
        if self.premise is None:
            return None
        return f"{self.entry_href}/world/{self.premise.material.slug}"

    @property
    def current_event_href(self) -> str | None:
        if self.current_event is None:
            return None
        return f"{self.entry_href}/world/{self.current_event.material.slug}"


@dataclass(frozen=True, slots=True)
class NetworkSlice:
    title: str
    href: str
    programs: list[PublicCatalogCard]


@dataclass(frozen=True, slots=True)
class NetworkBrowseFacet:
    label: str
    href: str
    tone: str = "neutral"
    result_count: int = 0


@dataclass(frozen=True, slots=True)
class NetworkDiscoveryFilterGroup:
    title: str
    options: list[NetworkBrowseFacet]


@dataclass(frozen=True, slots=True)
class NetworkExploreLane:
    title: str
    summary: str
    href: str
    metric_label: str
    result_count: int = 0


@dataclass(frozen=True, slots=True)
class NetworkReturnPath:
    desk_href: str
    notification_href: str
    unread_notification_count: int


@dataclass(frozen=True, slots=True)
class NetworkHomeView:
    featured: PublicCatalogCard | None
    slices: list[NetworkSlice]
    browse_facets: list[NetworkBrowseFacet]
    filter_groups: list[NetworkDiscoveryFilterGroup]
    return_path: NetworkReturnPath | None


@dataclass(frozen=True, slots=True)
class NetworkExploreView:
    query: str
    browse_facets: list[NetworkBrowseFacet]
    filter_groups: list[NetworkDiscoveryFilterGroup]
    relationship_lanes: list[NetworkExploreLane]
    results: list[PublicCatalogCard]


@dataclass(frozen=True, slots=True)
class ScopedSearchResult:
    title: str
    summary: str
    href: str
    meta: str = ""


@dataclass(frozen=True, slots=True)
class ScopedSearchSection:
    title: str
    results: list[ScopedSearchResult]


@dataclass(frozen=True, slots=True)
class ScopedSearchView:
    query: str
    scope_label: str
    scope_kind: str
    action_href: str
    broaden_href: str | None
    sections: list[ScopedSearchSection]

    @property
    def result_count(self) -> int:
        return sum(len(section.results) for section in self.sections)

    @property
    def scope_short_label(self) -> str:
        if self.scope_kind == "global":
            return "All"
        initials = "".join(
            part[0].upper()
            for part in self.scope_label.replace("&", " ").split()
            if part and part[0].isalnum()
        )
        return initials[:4] if initials else self.scope_label[:3].upper()


@dataclass(frozen=True, slots=True)
class DiscoveryProfileChoice:
    value: str
    label: str


@dataclass(frozen=True, slots=True)
class DiscoveryProfileChoiceGroup:
    field_name: str
    label: str
    choices: tuple[DiscoveryProfileChoice, ...]


@dataclass(frozen=True, slots=True)
class DiscoveryProfileEditor:
    profile: CommunityDiscoveryProfile | None
    tags: tuple[CommunityDiscoveryTag, ...]
    preview_card: PublicCatalogCard
    choice_groups: tuple[DiscoveryProfileChoiceGroup, ...]

    @property
    def tag_lines(self) -> str:
        return "\n".join(
            "|".join((tag.tag_type, tag.tag_key, tag.label, tag.search_text)) for tag in self.tags
        )

    def value_for(self, field_name: str) -> str:
        if self.profile is None:
            return ""
        return str(getattr(self.profile, field_name, "") or "")


def _program_href(program: StudioNetworkProgramView, path: str) -> str:
    if path == "/":
        return f"/c/{program.community.slug}"
    return f"/c/{program.community.slug}{path}"


@dataclass(frozen=True, slots=True)
class StudioNetworkDirectory:
    programs: list[StudioNetworkProgramView]


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
    location_sidebar_section: SidebarSectionConfig
    community_navigation_boards: list[BoardNavigationItem]
    community_sidebar_section: SidebarSectionConfig
    desk_navigation_boards: list[BoardNavigationItem]
    desk_sidebar_section: SidebarSectionConfig
    studio_navigation_boards: list[BoardNavigationItem]
    studio_sidebar_section: SidebarSectionConfig
    unread_notification_count: int
    identity_options: list[StudioIdentityOption]
    program_theme: ProgramThemeView | None


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
