"""Continuity Graph vocabulary and schema-neutral draft primitives."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

type ContinuityProposalState = Literal[
    "draft",
    "submitted",
    "revision_requested",
    "approved",
    "rejected",
    "archived",
]

type ContinuitySourceType = Literal["thread", "post"]

type ContinuityAffectedObjectType = Literal[
    "board",
    "character",
    "claim",
    "material",
    "plot_hook",
    "reserve",
    "thread",
    "wanted_ad",
]

type ContinuityReviewAction = Literal[
    "submitted",
    "revision_requested",
    "approved",
    "rejected",
    "archived",
]

type ContinuityVisibility = Literal["private", "participants", "staff", "public"]

CONTINUITY_PROPOSAL_STATES: frozenset[ContinuityProposalState] = frozenset(
    {
        "draft",
        "submitted",
        "revision_requested",
        "approved",
        "rejected",
        "archived",
    }
)

CONTINUITY_SOURCE_TYPES: frozenset[ContinuitySourceType] = frozenset({"thread", "post"})

CONTINUITY_AFFECTED_OBJECT_TYPES: frozenset[ContinuityAffectedObjectType] = frozenset(
    {
        "board",
        "character",
        "claim",
        "material",
        "plot_hook",
        "reserve",
        "thread",
        "wanted_ad",
    }
)

CONTINUITY_REVIEW_ACTIONS: frozenset[ContinuityReviewAction] = frozenset(
    {
        "submitted",
        "revision_requested",
        "approved",
        "rejected",
        "archived",
    }
)

CONTINUITY_VISIBILITIES: frozenset[ContinuityVisibility] = frozenset(
    {"private", "participants", "staff", "public"}
)

CONTINUITY_AUTHOR_TRANSITIONS: dict[
    ContinuityProposalState,
    frozenset[ContinuityProposalState],
] = {
    "draft": frozenset({"submitted", "archived"}),
    "revision_requested": frozenset({"submitted", "archived"}),
    "submitted": frozenset({"archived"}),
    "approved": frozenset(),
    "rejected": frozenset({"archived"}),
    "archived": frozenset(),
}

CONTINUITY_REVIEWER_TRANSITIONS: dict[
    ContinuityProposalState,
    frozenset[ContinuityProposalState],
] = {
    "draft": frozenset(),
    "submitted": frozenset({"revision_requested", "approved", "rejected", "archived"}),
    "revision_requested": frozenset({"archived"}),
    "approved": frozenset(),
    "rejected": frozenset({"archived"}),
    "archived": frozenset(),
}


@dataclass(frozen=True, slots=True)
class ContinuitySourceCitationDraft:
    community_id: int
    source_type: ContinuitySourceType
    source_id: int
    source_thread_id: int | None = None

    def __post_init__(self) -> None:
        _require_positive_id(self.community_id, "community_id")
        _require_known(self.source_type, CONTINUITY_SOURCE_TYPES, "source_type")
        _require_positive_id(self.source_id, "source_id")
        if self.source_thread_id is not None:
            _require_positive_id(self.source_thread_id, "source_thread_id")
        if self.source_type == "post" and self.source_thread_id is None:
            raise ValueError("post source citations require source_thread_id")


@dataclass(frozen=True, slots=True)
class ContinuityAffectedObjectDraft:
    community_id: int
    object_type: ContinuityAffectedObjectType
    object_id: int

    def __post_init__(self) -> None:
        _require_positive_id(self.community_id, "community_id")
        _require_known(self.object_type, CONTINUITY_AFFECTED_OBJECT_TYPES, "object_type")
        _require_positive_id(self.object_id, "object_id")


@dataclass(frozen=True, slots=True)
class ContinuityProposalDraft:
    community_id: int
    author_membership_id: int
    title: str
    summary: str
    state: ContinuityProposalState = "draft"
    author_character_id: int | None = None
    citations: tuple[ContinuitySourceCitationDraft, ...] = ()
    affected_objects: tuple[ContinuityAffectedObjectDraft, ...] = ()
    visibility: ContinuityVisibility = "private"

    def __post_init__(self) -> None:
        _require_positive_id(self.community_id, "community_id")
        _require_positive_id(self.author_membership_id, "author_membership_id")
        if self.author_character_id is not None:
            _require_positive_id(self.author_character_id, "author_character_id")
        _require_known(self.state, CONTINUITY_PROPOSAL_STATES, "state")
        _require_known(self.visibility, CONTINUITY_VISIBILITIES, "visibility")
        _require_text(self.title, "title")
        _require_same_community(self.community_id, self.citations, "citation")
        _require_same_community(self.community_id, self.affected_objects, "affected object")
        if self.state in {"submitted", "approved"} and not self.is_ready_for_submission:
            raise ValueError("submitted continuity proposals require source and affected links")
        if self.state != "approved" and self.visibility == "public":
            raise ValueError("public continuity visibility requires approved state")

    @property
    def is_ready_for_submission(self) -> bool:
        return bool(self.citations and self.affected_objects)


@dataclass(frozen=True, slots=True)
class ContinuityReviewEventDraft:
    community_id: int
    proposal_id: int
    actor_membership_id: int
    action: ContinuityReviewAction
    actor_character_id: int | None = None
    note: str = ""

    def __post_init__(self) -> None:
        _require_positive_id(self.community_id, "community_id")
        _require_positive_id(self.proposal_id, "proposal_id")
        _require_positive_id(self.actor_membership_id, "actor_membership_id")
        if self.actor_character_id is not None:
            _require_positive_id(self.actor_character_id, "actor_character_id")
        _require_known(self.action, CONTINUITY_REVIEW_ACTIONS, "action")


@dataclass(frozen=True, slots=True)
class ContinuityCanonEntryDraft:
    community_id: int
    approved_proposal_id: int
    approved_by_membership_id: int
    title: str
    summary: str
    visibility: ContinuityVisibility = "public"

    def __post_init__(self) -> None:
        _require_positive_id(self.community_id, "community_id")
        _require_positive_id(self.approved_proposal_id, "approved_proposal_id")
        _require_positive_id(self.approved_by_membership_id, "approved_by_membership_id")
        _require_text(self.title, "title")
        _require_known(self.visibility, CONTINUITY_VISIBILITIES, "visibility")
        if self.visibility != "public":
            raise ValueError("canon entries must use public visibility after approval")


@dataclass(frozen=True, slots=True)
class ContinuityProposal:
    id: int
    community_id: int
    author_membership_id: int
    author_character_id: int | None
    title: str
    summary: str
    state: ContinuityProposalState
    visibility: ContinuityVisibility
    revision_note: str
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class ContinuitySourceCitation:
    id: int
    community_id: int
    proposal_id: int
    source_type: ContinuitySourceType
    source_id: int
    source_thread_id: int
    created_at: str


@dataclass(frozen=True, slots=True)
class ContinuityAffectedObject:
    id: int
    community_id: int
    proposal_id: int
    object_type: ContinuityAffectedObjectType
    object_id: int
    created_at: str


@dataclass(frozen=True, slots=True)
class ContinuityReviewEvent:
    id: int
    community_id: int
    proposal_id: int
    actor_membership_id: int
    actor_character_id: int | None
    action: ContinuityReviewAction
    note: str
    created_at: str


@dataclass(frozen=True, slots=True)
class ContinuityCanonEntry:
    id: int
    community_id: int
    approved_proposal_id: int
    approved_by_membership_id: int
    title: str
    summary: str
    visibility: ContinuityVisibility
    created_at: str
    updated_at: str


def can_transition_continuity_proposal(
    current: ContinuityProposalState,
    target: ContinuityProposalState,
    *,
    reviewer: bool = False,
) -> bool:
    _require_known(current, CONTINUITY_PROPOSAL_STATES, "current")
    _require_known(target, CONTINUITY_PROPOSAL_STATES, "target")
    if current == target:
        return True
    transitions = CONTINUITY_REVIEWER_TRANSITIONS if reviewer else CONTINUITY_AUTHOR_TRANSITIONS
    return target in transitions[current]


def _require_positive_id(value: int, field_name: str) -> None:
    if value <= 0:
        raise ValueError(f"{field_name} must be a positive id")


def _require_text(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} is required")


def _require_known(value: str, allowed: frozenset[str], field_name: str) -> None:
    if value not in allowed:
        raise ValueError(f"unknown {field_name}: {value}")


def _require_same_community(
    community_id: int,
    items: tuple[ContinuitySourceCitationDraft | ContinuityAffectedObjectDraft, ...],
    label: str,
) -> None:
    for item in items:
        if item.community_id != community_id:
            raise ValueError(f"continuity {label} belongs to another community")
