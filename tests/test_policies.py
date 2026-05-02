from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from elbysodic.domain.models import Board, CommunityMembership, Post, Role, Thread
from elbysodic.services import policies


@pytest.fixture
def membership() -> CommunityMembership:
    return CommunityMembership(
        id=10,
        community_id=1,
        user_id=20,
        username="director",
        display_name="Director",
        avatar_url=None,
        role_id=30,
        default_character_id=None,
        post_count=0,
        is_active=True,
        joined_at="2026-01-01T00:00:00+00:00",
    )


@pytest.fixture
def admin_role() -> Role:
    return Role(
        id=30,
        community_id=1,
        slug="director",
        name="Director",
        is_admin=True,
        created_at="2026-01-01T00:00:00+00:00",
        updated_at="2026-01-01T00:00:00+00:00",
    )


@pytest.fixture
def member_role() -> Role:
    return Role(
        id=30,
        community_id=1,
        slug="member",
        name="Member",
        is_admin=False,
        created_at="2026-01-01T00:00:00+00:00",
        updated_at="2026-01-01T00:00:00+00:00",
    )


def test_admin_role_grants_named_capabilities(
    membership: CommunityMembership,
    admin_role: Role,
) -> None:
    assert policies.can_manage_threads(membership, admin_role)
    assert policies.can_manage_world(membership, admin_role)
    assert policies.can_manage_navigation(membership, admin_role)
    assert policies.can_manage_casting(membership, admin_role)
    assert policies.can_manage_applications(membership, admin_role)


def test_page_handlers_and_services_do_not_check_admin_flag_directly() -> None:
    checked_paths = [
        *Path("src/elbysodic/web/pages").rglob("page.py"),
        *(
            path
            for path in Path("src/elbysodic/services").glob("*.py")
            if path.name != "policies.py"
        ),
    ]

    offenders = [
        str(path) for path in checked_paths if ".is_admin" in path.read_text(encoding="utf-8")
    ]

    assert offenders == []


def test_capabilities_require_active_membership_and_matching_role(
    membership: CommunityMembership,
    admin_role: Role,
) -> None:
    inactive = replace(membership, is_active=False)
    wrong_community_role = replace(admin_role, community_id=2)
    wrong_role_id = replace(admin_role, id=99)

    assert not policies.can_manage_world(inactive, admin_role)
    assert not policies.can_manage_world(membership, wrong_community_role)
    assert not policies.can_manage_world(membership, wrong_role_id)


def test_private_board_and_locked_thread_use_named_capabilities(
    membership: CommunityMembership,
    admin_role: Role,
    member_role: Role,
) -> None:
    board = Board(
        id=1,
        community_id=1,
        parent_board_id=None,
        slug="staff-room",
        name="Staff Room",
        board_kind="community",
        sidebar_section="community",
        tagline="",
        description="",
        image_url=None,
        image_alt="",
        image_treatment="poster",
        image_focal_point="center",
        image_overlay="medium",
        sort_order=0,
        navigation_order=0,
        show_in_navigation=True,
        is_private=True,
        created_at="2026-01-01T00:00:00+00:00",
        updated_at="2026-01-01T00:00:00+00:00",
    )
    thread = Thread(
        id=2,
        community_id=1,
        board_id=board.id,
        author_membership_id=membership.id,
        author_character_id=40,
        slug="locked-scene",
        title="Locked Scene",
        status="active",
        location="",
        timeline="",
        summary="",
        posting_mode="freeform",
        is_locked=True,
        is_pinned=False,
        created_at="2026-01-01T00:00:00+00:00",
        updated_at="2026-01-01T00:00:00+00:00",
    )

    assert policies.can_view_board(membership, board, admin_role)
    assert policies.can_reply(membership, thread, admin_role)
    assert not policies.can_view_board(membership, board, member_role)
    assert not policies.can_reply(membership, thread, member_role)


def test_staff_can_edit_posts_through_thread_management_capability(
    membership: CommunityMembership,
    admin_role: Role,
    member_role: Role,
) -> None:
    post = Post(
        id=5,
        community_id=1,
        thread_id=2,
        post_number=1,
        author_membership_id=99,
        author_character_id=100,
        body="A post from someone else.",
        created_at="2026-01-01T00:00:00+00:00",
        updated_at="2026-01-01T00:00:00+00:00",
    )

    assert policies.can_edit_post(membership, post, admin_role)
    assert not policies.can_edit_post(membership, post, member_role)
