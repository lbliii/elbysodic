"""Continuity Graph source visibility gates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from elbysodic.domain.models import (
    Board,
    Character,
    CharacterClaim,
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
    if thread.status != "private":
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
