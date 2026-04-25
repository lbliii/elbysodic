"""Permission primitives for the first forum slice."""

from __future__ import annotations

from elbysodic.domain.models import Board, Character, CommunityMembership, Role, Thread


def can_view_board(
    membership: CommunityMembership,
    board: Board,
    role: Role | None = None,
) -> bool:
    if membership.community_id != board.community_id or not membership.is_active:
        return False
    if not board.is_private:
        return True
    return _is_admin_membership(membership, role)


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
        and _is_admin_membership(membership, role)
    )


def can_post_as(membership: CommunityMembership, character: Character) -> bool:
    return (
        membership.community_id == character.community_id
        and membership.id == character.membership_id
        and membership.is_active
    )


def _is_admin_membership(membership: CommunityMembership, role: Role | None) -> bool:
    return (
        role is not None
        and role.community_id == membership.community_id
        and role.id == membership.role_id
        and role.is_admin
    )
