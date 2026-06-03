"""Permission primitives for the first forum slice."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from elbysodic.domain.models import Board, Character, CommunityMembership, Post, Role, Thread

type Capability = Literal[
    "manage_applications",
    "manage_casting",
    "manage_navigation",
    "manage_threads",
    "manage_world",
]

ADMIN_CAPABILITIES: frozenset[Capability] = frozenset(
    {
        "manage_applications",
        "manage_casting",
        "manage_navigation",
        "manage_threads",
        "manage_world",
    }
)

type CapabilityDenialReason = Literal[
    "allowed",
    "missing_role",
    "inactive_membership",
    "role_community_mismatch",
    "role_not_assigned",
    "role_lacks_staff_power",
    "unknown_capability",
]


@dataclass(frozen=True, slots=True)
class CapabilityDiagnostic:
    capability: Capability
    allowed: bool
    reason: CapabilityDenialReason
    message: str


def has_capability(
    membership: CommunityMembership,
    role: Role | None,
    capability: Capability,
) -> bool:
    return explain_capability(membership, role, capability).allowed


def explain_capability(
    membership: CommunityMembership,
    role: Role | None,
    capability: Capability,
) -> CapabilityDiagnostic:
    if capability not in ADMIN_CAPABILITIES:
        return CapabilityDiagnostic(
            capability=capability,
            allowed=False,
            reason="unknown_capability",
            message="Capability is not registered for this deployment.",
        )
    if role is None:
        return CapabilityDiagnostic(
            capability=capability,
            allowed=False,
            reason="missing_role",
            message="Membership has no resolved community role.",
        )
    if not membership.is_active:
        return CapabilityDiagnostic(
            capability=capability,
            allowed=False,
            reason="inactive_membership",
            message="Membership is inactive in this community.",
        )
    if role.community_id != membership.community_id:
        return CapabilityDiagnostic(
            capability=capability,
            allowed=False,
            reason="role_community_mismatch",
            message="Resolved role belongs to another community.",
        )
    if role.id != membership.role_id:
        return CapabilityDiagnostic(
            capability=capability,
            allowed=False,
            reason="role_not_assigned",
            message="Resolved role is not assigned to this membership.",
        )
    if not role.is_admin:
        return CapabilityDiagnostic(
            capability=capability,
            allowed=False,
            reason="role_lacks_staff_power",
            message="Role does not grant this staff capability.",
        )
    return CapabilityDiagnostic(
        capability=capability,
        allowed=True,
        reason="allowed",
        message="Membership grants this staff capability.",
    )


def can_manage_applications(membership: CommunityMembership, role: Role | None) -> bool:
    return has_capability(membership, role, "manage_applications")


def can_manage_casting(membership: CommunityMembership, role: Role | None) -> bool:
    return has_capability(membership, role, "manage_casting")


def can_manage_navigation(membership: CommunityMembership, role: Role | None) -> bool:
    return has_capability(membership, role, "manage_navigation")


def can_manage_threads(membership: CommunityMembership, role: Role | None) -> bool:
    return has_capability(membership, role, "manage_threads")


def can_manage_world(membership: CommunityMembership, role: Role | None) -> bool:
    return has_capability(membership, role, "manage_world")


def can_view_board(
    membership: CommunityMembership,
    board: Board,
    role: Role | None = None,
) -> bool:
    if membership.community_id != board.community_id or not membership.is_active:
        return False
    if not board.is_private:
        return True
    return can_manage_world(membership, role)


def can_start_thread(
    membership: CommunityMembership,
    board: Board,
    role: Role | None = None,
) -> bool:
    return can_view_board(membership, board, role)


def can_reply(
    membership: CommunityMembership,
    thread: Thread,
    role: Role | None = None,
) -> bool:
    if membership.community_id != thread.community_id or not membership.is_active:
        return False
    return not thread.is_locked or can_moderate_thread(membership, thread, role)


def can_moderate_thread(
    membership: CommunityMembership,
    thread: Thread,
    role: Role | None = None,
) -> bool:
    return (
        membership.community_id == thread.community_id
        and membership.is_active
        and can_manage_threads(membership, role)
    )


def can_post_as(membership: CommunityMembership, character: Character) -> bool:
    return (
        membership.community_id == character.community_id
        and membership.id == character.membership_id
        and membership.is_active
    )


def can_story_act_as(membership: CommunityMembership, character: Character) -> bool:
    return can_post_as(membership, character) and character.application_status == "accepted"


def can_edit_post(
    membership: CommunityMembership,
    post: Post,
    role: Role | None = None,
) -> bool:
    if membership.community_id != post.community_id or not membership.is_active:
        return False
    if post.author_membership_id == membership.id:
        return True
    return can_manage_threads(membership, role)
