"""Continuity Graph source visibility gates."""

from __future__ import annotations

from collections.abc import Iterable
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Literal, Protocol

from elbysodic.domain.continuity import (
    ContinuityAffectedObject,
    ContinuityAffectedObjectDraft,
    ContinuityCanonEntry,
    ContinuityProposal,
    ContinuityProposalState,
    ContinuityReviewAction,
    ContinuityReviewEvent,
    ContinuitySourceCitation,
    ContinuitySourceCitationDraft,
    ContinuityVisibility,
    can_transition_continuity_proposal,
)
from elbysodic.domain.models import (
    Board,
    Character,
    CharacterClaim,
    CharacterPlotHook,
    CharacterReserve,
    ClaimType,
    CommunityMembership,
    Material,
    Post,
    Role,
    Thread,
    WantedAd,
)
from elbysodic.services import policies
from elbysodic.services.read_models import ForumView

type ContinuitySourceFamily = Literal[
    "board",
    "character",
    "claim",
    "location",
    "material",
    "plot_hook",
    "post",
    "reserve",
    "scene",
    "thread",
    "wanted_ad",
]

type ContinuitySourceVisibilityStatus = Literal[
    "visible",
    "hidden",
    "not_found",
    "cross_community",
    "inactive_viewer",
    "malformed",
]


@dataclass(frozen=True, slots=True)
class ContinuitySourceReference:
    community_id: int
    source_family: ContinuitySourceFamily
    source_id: int
    source_thread_id: int | None = None

    def __post_init__(self) -> None:
        if self.community_id <= 0:
            raise ValueError("community_id must be a positive id")
        if self.source_id <= 0:
            raise ValueError("source_id must be a positive id")
        if self.source_thread_id is not None and self.source_thread_id <= 0:
            raise ValueError("source_thread_id must be a positive id")
        if self.source_family == "post" and self.source_thread_id is None:
            raise ValueError("post source references require source_thread_id")


@dataclass(frozen=True, slots=True)
class ContinuitySourceViewer:
    community_id: int
    membership: CommunityMembership | None = None
    role: Role | None = None

    @classmethod
    def from_forum_view(cls, viewer: ForumView) -> ContinuitySourceViewer:
        return cls(
            community_id=viewer.community.id,
            membership=viewer.membership,
            role=viewer.role,
        )


@dataclass(frozen=True, slots=True)
class ContinuitySourceVisibility:
    community_id: int
    source_family: ContinuitySourceFamily
    source_id: int
    status: ContinuitySourceVisibilityStatus
    label: str
    reason: str

    @property
    def visible(self) -> bool:
        return self.status == "visible"


class ContinuitySourceVisibilityRepository(Protocol):
    def get_board(self, community_id: int, board_id: int) -> Board: ...

    def get_thread(self, community_id: int, thread_id: int) -> Thread: ...

    def get_post(self, community_id: int, post_id: int) -> Post: ...

    def get_character(self, community_id: int, character_id: int) -> Character: ...

    def get_material(self, community_id: int, material_id: int) -> Material: ...

    def get_character_plot_hook(
        self,
        community_id: int,
        plot_hook_id: int,
    ) -> CharacterPlotHook: ...

    def get_wanted_ad(self, community_id: int, wanted_ad_id: int) -> WantedAd: ...

    def get_claim_type(self, community_id: int, claim_type_id: int) -> ClaimType: ...

    def get_character_claim(self, community_id: int, claim_id: int) -> CharacterClaim: ...

    def get_character_reserve(self, community_id: int, reserve_id: int) -> CharacterReserve: ...

    def list_thread_participants(self, community_id: int, thread_id: int) -> list[Character]: ...


def public_continuity_source_visibility(
    repo: ContinuitySourceVisibilityRepository,
    community_id: int,
    reference: ContinuitySourceReference,
) -> ContinuitySourceVisibility:
    return continuity_source_visibility(
        repo,
        ContinuitySourceViewer(community_id=community_id),
        reference,
    )


def continuity_source_visibility(
    repo: ContinuitySourceVisibilityRepository,
    viewer: ForumView | ContinuitySourceViewer,
    reference: ContinuitySourceReference,
) -> ContinuitySourceVisibility:
    source_viewer = _source_viewer(viewer)
    if reference.community_id != source_viewer.community_id:
        return _hidden(reference, "cross_community", "source belongs to another community")
    if source_viewer.membership is not None and not source_viewer.membership.is_active:
        return _hidden(reference, "inactive_viewer", "viewer is inactive in this community")
    try:
        match reference.source_family:
            case "board":
                return _board_visibility(repo, source_viewer, reference)
            case "location":
                return _location_visibility(repo, source_viewer, reference)
            case "thread" | "scene":
                return _thread_visibility(repo, source_viewer, reference)
            case "post":
                return _post_visibility(repo, source_viewer, reference)
            case "character":
                return _character_visibility(repo, source_viewer, reference)
            case "material":
                return _material_visibility(repo, source_viewer, reference)
            case "plot_hook":
                return _plot_hook_visibility(repo, source_viewer, reference)
            case "wanted_ad":
                return _wanted_visibility(repo, source_viewer, reference)
            case "claim":
                return _claim_visibility(repo, source_viewer, reference)
            case "reserve":
                return _reserve_visibility(repo, source_viewer, reference)
    except LookupError:
        return _hidden(reference, "not_found", "source is not visible in this community")


def _board_visibility(
    repo: ContinuitySourceVisibilityRepository,
    viewer: ContinuitySourceViewer,
    reference: ContinuitySourceReference,
) -> ContinuitySourceVisibility:
    board = repo.get_board(reference.community_id, reference.source_id)
    if _can_view_board(viewer, board):
        return _visible(reference, board.name, "viewer can read this board")
    return _hidden(reference, "hidden", "viewer cannot read this board")


def _location_visibility(
    repo: ContinuitySourceVisibilityRepository,
    viewer: ContinuitySourceViewer,
    reference: ContinuitySourceReference,
) -> ContinuitySourceVisibility:
    board = repo.get_board(reference.community_id, reference.source_id)
    if board.board_kind not in {"location", "sublocation"}:
        return _hidden(reference, "malformed", "location sources must target location boards")
    if _can_view_board(viewer, board):
        return _visible(reference, board.name, "viewer can read this location")
    return _hidden(reference, "hidden", "viewer cannot read this location")


def _thread_visibility(
    repo: ContinuitySourceVisibilityRepository,
    viewer: ContinuitySourceViewer,
    reference: ContinuitySourceReference,
) -> ContinuitySourceVisibility:
    thread = repo.get_thread(reference.community_id, reference.source_id)
    board = repo.get_board(reference.community_id, thread.board_id)
    if _can_view_thread(repo, viewer, board, thread):
        return _visible(reference, thread.title, "viewer can read this scene")
    return _hidden(reference, "hidden", "viewer cannot read this scene")


def _post_visibility(
    repo: ContinuitySourceVisibilityRepository,
    viewer: ContinuitySourceViewer,
    reference: ContinuitySourceReference,
) -> ContinuitySourceVisibility:
    post = repo.get_post(reference.community_id, reference.source_id)
    if post.thread_id != reference.source_thread_id:
        return _hidden(reference, "malformed", "post source_thread_id does not match source_id")
    thread = repo.get_thread(reference.community_id, post.thread_id)
    board = repo.get_board(reference.community_id, thread.board_id)
    if _can_view_thread(repo, viewer, board, thread):
        return _visible(reference, f"post #{post.post_number}", "viewer can read this post")
    return _hidden(reference, "hidden", "viewer cannot read this post")


def _character_visibility(
    repo: ContinuitySourceVisibilityRepository,
    viewer: ContinuitySourceViewer,
    reference: ContinuitySourceReference,
) -> ContinuitySourceVisibility:
    character = repo.get_character(reference.community_id, reference.source_id)
    if character.application_status == "accepted" or _can_manage_casting(viewer):
        return _visible(reference, character.name, "viewer can read this face")
    if viewer.membership is not None and character.membership_id == viewer.membership.id:
        return _visible(reference, character.name, "viewer owns this face")
    return _hidden(reference, "hidden", "viewer cannot read this face")


def _material_visibility(
    repo: ContinuitySourceVisibilityRepository,
    viewer: ContinuitySourceViewer,
    reference: ContinuitySourceReference,
) -> ContinuitySourceVisibility:
    material = repo.get_material(reference.community_id, reference.source_id)
    if material.status == "published" or _can_manage_world(viewer):
        return _visible(reference, material.title, "viewer can read this material")
    return _hidden(reference, "hidden", "viewer cannot read this material")


def _wanted_visibility(
    repo: ContinuitySourceVisibilityRepository,
    viewer: ContinuitySourceViewer,
    reference: ContinuitySourceReference,
) -> ContinuitySourceVisibility:
    wanted = repo.get_wanted_ad(reference.community_id, reference.source_id)
    if wanted.status == "open" or _can_manage_casting(viewer):
        return _visible(reference, wanted.title, "viewer can read this wanted hook")
    if viewer.membership is not None and wanted.creator_membership_id == viewer.membership.id:
        return _visible(reference, wanted.title, "viewer owns this wanted hook")
    return _hidden(reference, "hidden", "viewer cannot read this wanted hook")


def _plot_hook_visibility(
    repo: ContinuitySourceVisibilityRepository,
    viewer: ContinuitySourceViewer,
    reference: ContinuitySourceReference,
) -> ContinuitySourceVisibility:
    hook = repo.get_character_plot_hook(reference.community_id, reference.source_id)
    if hook.status == "open" or _can_manage_casting(viewer):
        return _visible(reference, hook.title, "viewer can read this plot hook")
    if viewer.membership is not None and hook.author_membership_id == viewer.membership.id:
        return _visible(reference, hook.title, "viewer owns this plot hook")
    return _hidden(reference, "hidden", "viewer cannot read this plot hook")


def _claim_visibility(
    repo: ContinuitySourceVisibilityRepository,
    viewer: ContinuitySourceViewer,
    reference: ContinuitySourceReference,
) -> ContinuitySourceVisibility:
    claim = repo.get_character_claim(reference.community_id, reference.source_id)
    claim_type = repo.get_claim_type(reference.community_id, claim.claim_type_id)
    if claim.status == "claimed" and claim_type.visibility == "public":
        return _visible(reference, claim.label, "viewer can read this public claim")
    if _can_manage_casting(viewer) or _can_manage_applications(viewer):
        return _visible(reference, claim.label, "viewer can review this claim")
    return _hidden(reference, "hidden", "viewer cannot read this claim")


def _reserve_visibility(
    repo: ContinuitySourceVisibilityRepository,
    viewer: ContinuitySourceViewer,
    reference: ContinuitySourceReference,
) -> ContinuitySourceVisibility:
    reserve = repo.get_character_reserve(reference.community_id, reference.source_id)
    if _can_manage_casting(viewer):
        return _visible(reference, reserve.title, "viewer can review this reserve")
    if viewer.membership is not None and reserve.membership_id == viewer.membership.id:
        return _visible(reference, reserve.title, "viewer owns this reserve")
    return _hidden(reference, "hidden", "viewer cannot read this reserve")


def _can_view_board(viewer: ContinuitySourceViewer, board: Board) -> bool:
    if viewer.membership is None:
        return not board.is_private
    return policies.can_view_board(viewer.membership, board, viewer.role)


def _can_view_thread(
    repo: ContinuitySourceVisibilityRepository,
    viewer: ContinuitySourceViewer,
    board: Board,
    thread: Thread,
) -> bool:
    if not _can_view_board(viewer, board):
        return False
    if viewer.membership is None:
        return (
            thread.visibility == "public_preview"
            and thread.status in {"active", "open"}
            and not thread.is_locked
        )
    if thread.status != "private" and thread.visibility != "private":
        return True
    if _can_moderate_thread(viewer, thread):
        return True
    if viewer.membership is None:
        return False
    if thread.author_membership_id == viewer.membership.id:
        return True
    participants = repo.list_thread_participants(thread.community_id, thread.id)
    return any(character.membership_id == viewer.membership.id for character in participants)


def _can_manage_world(viewer: ContinuitySourceViewer) -> bool:
    if viewer.membership is None:
        return False
    return policies.can_manage_world(viewer.membership, viewer.role)


def _can_manage_casting(viewer: ContinuitySourceViewer) -> bool:
    if viewer.membership is None:
        return False
    return policies.can_manage_casting(viewer.membership, viewer.role)


def _can_manage_applications(viewer: ContinuitySourceViewer) -> bool:
    if viewer.membership is None:
        return False
    return policies.can_manage_applications(viewer.membership, viewer.role)


def _can_moderate_thread(viewer: ContinuitySourceViewer, thread: Thread) -> bool:
    if viewer.membership is None:
        return False
    return policies.can_moderate_thread(viewer.membership, thread, viewer.role)


def _source_viewer(viewer: ForumView | ContinuitySourceViewer) -> ContinuitySourceViewer:
    if isinstance(viewer, ContinuitySourceViewer):
        return viewer
    return ContinuitySourceViewer.from_forum_view(viewer)


def _visible(
    reference: ContinuitySourceReference,
    label: str,
    reason: str,
) -> ContinuitySourceVisibility:
    return ContinuitySourceVisibility(
        community_id=reference.community_id,
        source_family=reference.source_family,
        source_id=reference.source_id,
        status="visible",
        label=label,
        reason=reason,
    )


def _hidden(
    reference: ContinuitySourceReference,
    status: ContinuitySourceVisibilityStatus,
    reason: str,
) -> ContinuitySourceVisibility:
    return ContinuitySourceVisibility(
        community_id=reference.community_id,
        source_family=reference.source_family,
        source_id=reference.source_id,
        status=status,
        label="",
        reason=reason,
    )


@dataclass(frozen=True, slots=True)
class ContinuityCitationView:
    citation: ContinuitySourceCitation
    visibility: ContinuitySourceVisibility
    excerpt: str


@dataclass(frozen=True, slots=True)
class ContinuityAffectedObjectView:
    affected_object: ContinuityAffectedObject
    visibility: ContinuitySourceVisibility


@dataclass(frozen=True, slots=True)
class ContinuityProposalView:
    proposal: ContinuityProposal
    citations: tuple[ContinuityCitationView, ...]
    affected_objects: tuple[ContinuityAffectedObjectView, ...]
    review_events: tuple[ContinuityReviewEvent, ...]
    canon_entry: ContinuityCanonEntry | None
    can_review: bool


@dataclass(frozen=True, slots=True)
class ContinuityReviewQueue:
    items: tuple[ContinuityProposalView, ...]


@dataclass(frozen=True, slots=True)
class ContinuityNotificationTarget:
    membership_id: int
    source_labels: tuple[str, ...]
    affected_labels: tuple[str, ...]


class ContinuityWorkflowRepository(ContinuitySourceVisibilityRepository, Protocol):
    def transaction(self) -> AbstractContextManager[None]: ...

    def get_membership(
        self,
        community_id: int,
        membership_id: int,
    ) -> CommunityMembership: ...

    def get_role(self, community_id: int, role_id: int) -> Role: ...

    def list_memberships(self, community_id: int) -> list[CommunityMembership]: ...

    def create_continuity_proposal(
        self,
        community_id: int,
        author_membership_id: int,
        *,
        title: str,
        summary: str = "",
        author_character_id: int | None = None,
        citations: Iterable[ContinuitySourceCitationDraft] = (),
        affected_objects: Iterable[ContinuityAffectedObjectDraft] = (),
    ) -> ContinuityProposal: ...

    def get_continuity_proposal(
        self,
        community_id: int,
        proposal_id: int,
    ) -> ContinuityProposal: ...

    def list_continuity_proposals(
        self,
        community_id: int,
        *,
        states: Iterable[ContinuityProposalState] | None = None,
        author_membership_id: int | None = None,
    ) -> list[ContinuityProposal]: ...

    def list_continuity_source_citations(
        self,
        community_id: int,
        proposal_id: int,
    ) -> list[ContinuitySourceCitation]: ...

    def list_continuity_affected_objects(
        self,
        community_id: int,
        proposal_id: int,
    ) -> list[ContinuityAffectedObject]: ...

    def update_continuity_proposal_state(
        self,
        community_id: int,
        proposal_id: int,
        *,
        state: ContinuityProposalState,
        visibility: ContinuityVisibility,
        revision_note: str = "",
    ) -> ContinuityProposal: ...

    def create_continuity_review_event(
        self,
        community_id: int,
        proposal_id: int,
        actor_membership_id: int,
        *,
        action: ContinuityReviewAction,
        actor_character_id: int | None = None,
        note: str = "",
    ) -> ContinuityReviewEvent: ...

    def list_continuity_review_events(
        self,
        community_id: int,
        proposal_id: int,
    ) -> list[ContinuityReviewEvent]: ...

    def create_continuity_canon_entry(
        self,
        community_id: int,
        approved_proposal_id: int,
        approved_by_membership_id: int,
        *,
        title: str,
        summary: str,
    ) -> ContinuityCanonEntry: ...

    def get_continuity_canon_entry_for_proposal(
        self,
        community_id: int,
        proposal_id: int,
    ) -> ContinuityCanonEntry | None: ...

    def create_staff_audit_event(
        self,
        community_id: int,
        actor_membership_id: int,
        *,
        capability: str,
        target_family: str,
        action: str,
        outcome: str,
        target_id: int | None = None,
        actor_character_id: int | None = None,
        reason: str = "",
        public_aftermath: str = "",
    ) -> object: ...


def create_manual_continuity_proposal(
    repo: ContinuityWorkflowRepository,
    viewer: ForumView,
    *,
    title: str,
    summary: str,
    citations: Iterable[ContinuitySourceCitationDraft],
    affected_objects: Iterable[ContinuityAffectedObjectDraft],
    author_character_id: int | None = None,
) -> ContinuityProposal:
    citation_rows = tuple(citations)
    affected_rows = tuple(affected_objects)
    if not citation_rows or not affected_rows:
        raise ValueError("continuity proposals require source and affected-object links")
    with repo.transaction():
        source_viewer = _authoritative_continuity_viewer(repo, viewer)
        membership = _require_active_continuity_source_viewer(source_viewer)
        for citation in citation_rows:
            result = continuity_source_visibility(
                repo,
                source_viewer,
                _citation_reference(citation),
            )
            if not result.visible:
                raise PermissionError("continuity proposal source is not visible to its author")
        for affected in affected_rows:
            result = continuity_source_visibility(
                repo,
                source_viewer,
                _affected_reference(affected),
            )
            if not result.visible:
                raise PermissionError("continuity affected object is not visible to its author")
        if not policies.can_manage_world(membership, source_viewer.role) and not any(
            _membership_participates_in_citation(repo, membership.id, citation)
            for citation in citation_rows
        ):
            raise PermissionError(
                "continuity proposal authors must start or participate in a source scene"
            )
        return repo.create_continuity_proposal(
            viewer.community.id,
            membership.id,
            title=title,
            summary=summary,
            author_character_id=author_character_id,
            citations=citation_rows,
            affected_objects=affected_rows,
        )


def submit_manual_continuity_proposal(
    repo: ContinuityWorkflowRepository,
    viewer: ForumView,
    proposal_id: int,
) -> ContinuityProposal:
    with repo.transaction():
        source_viewer = _authoritative_continuity_viewer(repo, viewer)
        membership = _require_active_continuity_source_viewer(source_viewer)
        proposal = repo.get_continuity_proposal(viewer.community.id, proposal_id)
        if proposal.author_membership_id != membership.id:
            raise PermissionError("only the proposal author can submit continuity work")
        if proposal.state == "submitted":
            return proposal
        if not can_transition_continuity_proposal(proposal.state, "submitted"):
            raise ValueError(f"continuity proposal cannot move from {proposal.state} to submitted")
        if not repo.list_continuity_source_citations(
            viewer.community.id, proposal.id
        ) or not repo.list_continuity_affected_objects(viewer.community.id, proposal.id):
            raise ValueError("submitted continuity proposals require source and affected links")
        updated = repo.update_continuity_proposal_state(
            viewer.community.id,
            proposal.id,
            state="submitted",
            visibility="participants",
        )
        repo.create_continuity_review_event(
            viewer.community.id,
            proposal.id,
            membership.id,
            action="submitted",
            actor_character_id=viewer.current_character.id if viewer.current_character else None,
        )
    return updated


def review_manual_continuity_proposal(
    repo: ContinuityWorkflowRepository,
    viewer: ForumView,
    proposal_id: int,
    *,
    action: Literal["revision_requested", "approved", "rejected", "archived"],
    note: str = "",
    visibility: ContinuityVisibility = "staff",
) -> ContinuityProposal:
    with repo.transaction():
        source_viewer = _authoritative_continuity_viewer(repo, viewer)
        membership = _require_active_continuity_source_viewer(source_viewer)
        if not policies.can_manage_world(membership, source_viewer.role):
            raise PermissionError("manage_world is required to review continuity proposals")
        proposal = repo.get_continuity_proposal(viewer.community.id, proposal_id)
        target_state = action
        if proposal.state == target_state:
            if action != "approved" or proposal.visibility == visibility:
                return proposal
            if proposal.visibility == "public" or visibility != "public":
                raise ValueError("approved continuity visibility cannot be rewritten in place")
        if not can_transition_continuity_proposal(proposal.state, target_state, reviewer=True):
            raise ValueError(
                f"continuity proposal cannot move from {proposal.state} to {target_state}"
            )
        if action == "revision_requested" and not note.strip():
            raise ValueError("revision requests require an author-facing note")
        if action == "approved" and visibility == "public":
            _require_public_continuity_sources(repo, viewer.community.id, proposal.id)
        elif visibility == "public":
            raise ValueError("public continuity visibility requires approval")
        next_visibility: ContinuityVisibility = visibility if action == "approved" else "staff"
        updated = repo.update_continuity_proposal_state(
            viewer.community.id,
            proposal.id,
            state=target_state,
            visibility=next_visibility,
            revision_note=note if action == "revision_requested" else "",
        )
        repo.create_continuity_review_event(
            viewer.community.id,
            proposal.id,
            membership.id,
            action=action,
            actor_character_id=viewer.current_character.id if viewer.current_character else None,
            note=note,
        )
        if action == "approved" and next_visibility == "public":
            repo.create_continuity_canon_entry(
                viewer.community.id,
                proposal.id,
                membership.id,
                title=proposal.title,
                summary=proposal.summary,
            )
        repo.create_staff_audit_event(
            viewer.community.id,
            membership.id,
            capability="manage_world",
            target_family="continuity_proposal",
            target_id=proposal.id,
            action=f"continuity_{action}",
            outcome="accepted",
            actor_character_id=viewer.current_character.id if viewer.current_character else None,
            public_aftermath=(
                "approved public canon"
                if action == "approved" and next_visibility == "public"
                else ""
            ),
        )
    return updated


def continuity_proposal_view(
    repo: ContinuityWorkflowRepository,
    viewer: ForumView | ContinuitySourceViewer,
    proposal_id: int,
) -> ContinuityProposalView:
    source_viewer = _source_viewer(viewer)
    proposal = repo.get_continuity_proposal(source_viewer.community_id, proposal_id)
    canon = repo.get_continuity_canon_entry_for_proposal(proposal.community_id, proposal.id)
    staff = _can_manage_world(source_viewer)
    owner = (
        source_viewer.membership is not None
        and proposal.author_membership_id == source_viewer.membership.id
        and source_viewer.membership.is_active
    )
    participant = source_viewer.membership is not None and _membership_is_proposal_participant(
        repo,
        proposal,
        source_viewer.membership.id,
    )
    if not staff and not owner:
        if proposal.state != "approved":
            raise LookupError("continuity proposal not found")
        if proposal.visibility == "participants" and not participant:
            raise LookupError("continuity proposal not found")
        if proposal.visibility in {"private", "staff"}:
            raise LookupError("continuity proposal not found")
        if proposal.visibility == "public" and canon is None:
            raise LookupError("continuity proposal not found")
    citations = tuple(
        _citation_view(repo, source_viewer, citation)
        for citation in repo.list_continuity_source_citations(proposal.community_id, proposal.id)
    )
    affected = tuple(
        _affected_view(repo, source_viewer, item)
        for item in repo.list_continuity_affected_objects(proposal.community_id, proposal.id)
    )
    if (
        not staff
        and not owner
        and any(not item.visibility.visible for item in (*citations, *affected))
    ):
        raise LookupError("continuity proposal not found")
    if source_viewer.membership is None and canon is None:
        raise LookupError("continuity proposal not found")
    return ContinuityProposalView(
        proposal=proposal,
        citations=citations,
        affected_objects=affected,
        review_events=(
            tuple(repo.list_continuity_review_events(proposal.community_id, proposal.id))
            if staff
            else ()
        ),
        canon_entry=canon,
        can_review=staff,
    )


def continuity_review_queue(
    repo: ContinuityWorkflowRepository,
    viewer: ForumView,
) -> ContinuityReviewQueue:
    _require_active_continuity_viewer(viewer)
    if not policies.can_manage_world(viewer.membership, viewer.role):
        raise PermissionError("manage_world is required to read the continuity review queue")
    proposals = repo.list_continuity_proposals(viewer.community.id, states=("submitted",))
    return ContinuityReviewQueue(
        items=tuple(continuity_proposal_view(repo, viewer, proposal.id) for proposal in proposals)
    )


def continuity_notification_targets(
    repo: ContinuityWorkflowRepository,
    viewer: ForumView,
    proposal_id: int,
) -> tuple[ContinuityNotificationTarget, ...]:
    _require_active_continuity_viewer(viewer)
    proposal = repo.get_continuity_proposal(viewer.community.id, proposal_id)
    if proposal.author_membership_id != viewer.membership.id and not policies.can_manage_world(
        viewer.membership,
        viewer.role,
    ):
        raise PermissionError(
            "only the proposal author or continuity reviewers can compute notification targets"
        )
    citations = repo.list_continuity_source_citations(viewer.community.id, proposal.id)
    affected = repo.list_continuity_affected_objects(viewer.community.id, proposal.id)
    candidate_ids = {proposal.author_membership_id}
    for citation in citations:
        thread = repo.get_thread(viewer.community.id, citation.source_thread_id)
        candidate_ids.add(thread.author_membership_id)
        candidate_ids.update(
            character.membership_id
            for character in repo.list_thread_participants(viewer.community.id, thread.id)
        )
    candidate_ids.update(_affected_owner_ids(repo, viewer.community.id, affected))
    for membership in repo.list_memberships(viewer.community.id):
        if membership.is_active and policies.can_manage_world(
            membership,
            repo.get_role(viewer.community.id, membership.role_id),
        ):
            candidate_ids.add(membership.id)
    targets: list[ContinuityNotificationTarget] = []
    for membership_id in sorted(candidate_ids):
        membership = repo.get_membership(viewer.community.id, membership_id)
        if not membership.is_active:
            continue
        source_viewer = ContinuitySourceViewer(
            community_id=viewer.community.id,
            membership=membership,
            role=repo.get_role(viewer.community.id, membership.role_id),
        )
        source_results = tuple(
            continuity_source_visibility(repo, source_viewer, _stored_citation_reference(item))
            for item in citations
        )
        affected_results = tuple(
            continuity_source_visibility(repo, source_viewer, _stored_affected_reference(item))
            for item in affected
        )
        if all(result.visible for result in (*source_results, *affected_results)):
            targets.append(
                ContinuityNotificationTarget(
                    membership_id=membership.id,
                    source_labels=tuple(result.label for result in source_results),
                    affected_labels=tuple(result.label for result in affected_results),
                )
            )
    return tuple(targets)


def _require_active_continuity_viewer(viewer: ForumView) -> None:
    if not viewer.membership.is_active:
        raise PermissionError("continuity workflows require an active membership")


def _authoritative_continuity_viewer(
    repo: ContinuityWorkflowRepository,
    viewer: ForumView,
) -> ContinuitySourceViewer:
    membership = repo.get_membership(viewer.community.id, viewer.membership.id)
    return ContinuitySourceViewer(
        community_id=viewer.community.id,
        membership=membership,
        role=repo.get_role(viewer.community.id, membership.role_id),
    )


def _require_active_continuity_source_viewer(
    viewer: ContinuitySourceViewer,
) -> CommunityMembership:
    membership = viewer.membership
    if membership is None or not membership.is_active:
        raise PermissionError("continuity workflows require an active membership")
    return membership


def _citation_reference(citation: ContinuitySourceCitationDraft) -> ContinuitySourceReference:
    return ContinuitySourceReference(
        citation.community_id,
        citation.source_type,
        citation.source_id,
        source_thread_id=citation.source_thread_id,
    )


def _affected_reference(affected: ContinuityAffectedObjectDraft) -> ContinuitySourceReference:
    return ContinuitySourceReference(
        affected.community_id,
        affected.object_type,
        affected.object_id,
    )


def _stored_citation_reference(citation: ContinuitySourceCitation) -> ContinuitySourceReference:
    return ContinuitySourceReference(
        citation.community_id,
        citation.source_type,
        citation.source_id,
        source_thread_id=(citation.source_thread_id if citation.source_type == "post" else None),
    )


def _stored_affected_reference(affected: ContinuityAffectedObject) -> ContinuitySourceReference:
    return ContinuitySourceReference(
        affected.community_id,
        affected.object_type,
        affected.object_id,
    )


def _membership_participates_in_citation(
    repo: ContinuityWorkflowRepository,
    membership_id: int,
    citation: ContinuitySourceCitationDraft,
) -> bool:
    thread_id = (
        citation.source_id if citation.source_type == "thread" else citation.source_thread_id
    )
    if thread_id is None:
        return False
    thread = repo.get_thread(citation.community_id, thread_id)
    if thread.author_membership_id == membership_id:
        return True
    return any(
        character.membership_id == membership_id
        for character in repo.list_thread_participants(citation.community_id, thread.id)
    )


def _membership_is_proposal_participant(
    repo: ContinuityWorkflowRepository,
    proposal: ContinuityProposal,
    membership_id: int,
) -> bool:
    citations = repo.list_continuity_source_citations(proposal.community_id, proposal.id)
    if any(
        _membership_participates_in_citation(
            repo,
            membership_id,
            ContinuitySourceCitationDraft(
                community_id=citation.community_id,
                source_type=citation.source_type,
                source_id=citation.source_id,
                source_thread_id=(
                    citation.source_thread_id if citation.source_type == "post" else None
                ),
            ),
        )
        for citation in citations
    ):
        return True
    affected = repo.list_continuity_affected_objects(proposal.community_id, proposal.id)
    return membership_id in _affected_owner_ids(repo, proposal.community_id, affected)


def _require_public_continuity_sources(
    repo: ContinuityWorkflowRepository,
    community_id: int,
    proposal_id: int,
) -> None:
    public_viewer = ContinuitySourceViewer(community_id=community_id)
    citations = repo.list_continuity_source_citations(community_id, proposal_id)
    affected = repo.list_continuity_affected_objects(community_id, proposal_id)
    for citation in citations:
        result = continuity_source_visibility(
            repo,
            public_viewer,
            _stored_citation_reference(citation),
        )
        if not result.visible:
            raise ValueError("public canon requires public-safe source citations")
    for item in affected:
        result = continuity_source_visibility(
            repo,
            public_viewer,
            _stored_affected_reference(item),
        )
        if not result.visible:
            raise ValueError("public canon requires public-safe affected objects")


def _citation_view(
    repo: ContinuityWorkflowRepository,
    viewer: ContinuitySourceViewer,
    citation: ContinuitySourceCitation,
) -> ContinuityCitationView:
    visibility = continuity_source_visibility(
        repo,
        viewer,
        _stored_citation_reference(citation),
    )
    excerpt = ""
    if visibility.visible and citation.source_type == "post" and viewer.membership is not None:
        excerpt = repo.get_post(citation.community_id, citation.source_id).body.strip()[:240]
    return ContinuityCitationView(citation, visibility, excerpt)


def _affected_view(
    repo: ContinuityWorkflowRepository,
    viewer: ContinuitySourceViewer,
    affected: ContinuityAffectedObject,
) -> ContinuityAffectedObjectView:
    return ContinuityAffectedObjectView(
        affected,
        continuity_source_visibility(repo, viewer, _stored_affected_reference(affected)),
    )


def _affected_owner_ids(
    repo: ContinuityWorkflowRepository,
    community_id: int,
    affected: Iterable[ContinuityAffectedObject],
) -> set[int]:
    owner_ids: set[int] = set()
    for item in affected:
        match item.object_type:
            case "character":
                owner_ids.add(repo.get_character(community_id, item.object_id).membership_id)
            case "claim":
                claim = repo.get_character_claim(community_id, item.object_id)
                if claim.character_id is not None:
                    owner_ids.add(
                        repo.get_character(community_id, claim.character_id).membership_id
                    )
            case "plot_hook":
                owner_ids.add(
                    repo.get_character_plot_hook(community_id, item.object_id).author_membership_id
                )
            case "reserve":
                owner_ids.add(
                    repo.get_character_reserve(community_id, item.object_id).membership_id
                )
            case "thread":
                owner_ids.add(repo.get_thread(community_id, item.object_id).author_membership_id)
            case "wanted_ad":
                owner_ids.add(
                    repo.get_wanted_ad(community_id, item.object_id).creator_membership_id
                )
    return owner_ids
