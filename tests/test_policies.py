from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from elbysodic.domain.models import Board, Character, CommunityMembership, Post, Role, Thread
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


@pytest.mark.parametrize("capability", sorted(policies.ADMIN_CAPABILITIES))
def test_named_capability_helpers_stay_registered(
    capability: policies.Capability,
    membership: CommunityMembership,
    admin_role: Role,
) -> None:
    helper = getattr(policies, f"can_{capability}")

    assert helper(membership, admin_role) is True


def test_staff_capability_contracts_cover_named_helpers(
    membership: CommunityMembership,
    admin_role: Role,
) -> None:
    contracts = policies.staff_capability_contracts()

    assert {contract.capability for contract in contracts} == policies.ADMIN_CAPABILITIES
    for contract in contracts:
        helper = getattr(policies, contract.helper_name)
        assert helper(membership, admin_role) is True
        assert contract.storage_contract == "roles.is_admin grants every V1 staff capability"
        assert "membership" in contract.actor_contract
        assert "global user" not in contract.actor_contract
        assert contract.protected_workflows
        assert contract.audit_event_candidates


def test_page_handlers_templates_and_services_do_not_check_admin_flag_directly() -> None:
    checked_paths = [
        *Path("src/elbysodic/web/pages").rglob("page.py"),
        *Path("src/elbysodic/web/pages").rglob("*.html"),
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


@pytest.mark.parametrize(
    ("membership_updates", "role_updates", "expected_reason"),
    [
        ({}, None, "missing_role"),
        ({"is_active": False}, {}, "inactive_membership"),
        ({}, {"community_id": 2}, "role_community_mismatch"),
        ({}, {"id": 99}, "role_not_assigned"),
        ({}, {"is_admin": False}, "role_lacks_staff_power"),
    ],
)
def test_capability_denial_diagnostics_are_safe_and_specific(
    membership_updates: dict[str, object],
    role_updates: dict[str, object] | None,
    expected_reason: policies.CapabilityDenialReason,
    membership: CommunityMembership,
    admin_role: Role,
) -> None:
    scoped_membership = replace(membership, **membership_updates)
    role = None if role_updates is None else replace(admin_role, **role_updates)

    diagnostic = policies.explain_capability(scoped_membership, role, "manage_world")

    assert diagnostic.allowed is False
    assert diagnostic.capability == "manage_world"
    assert diagnostic.reason == expected_reason
    assert scoped_membership.username not in diagnostic.message
    assert scoped_membership.display_name not in diagnostic.message
    if role is not None:
        assert role.name not in diagnostic.message
        assert role.slug not in diagnostic.message


def test_capability_diagnostics_report_allowed_without_target_details(
    membership: CommunityMembership,
    admin_role: Role,
) -> None:
    diagnostic = policies.explain_capability(membership, admin_role, "manage_casting")

    assert diagnostic.allowed is True
    assert diagnostic.capability == "manage_casting"
    assert diagnostic.reason == "allowed"
    assert membership.username not in diagnostic.message
    assert admin_role.name not in diagnostic.message


def test_same_global_user_can_have_different_capabilities_per_community(
    membership: CommunityMembership,
    admin_role: Role,
) -> None:
    staffed_membership = replace(membership, community_id=2, role_id=40)
    staffed_role = replace(admin_role, id=40, community_id=2, slug="director", is_admin=True)
    writer_membership = replace(membership, community_id=3, role_id=41)
    writer_role = replace(admin_role, id=41, community_id=3, slug="member", is_admin=False)

    assert staffed_membership.user_id == writer_membership.user_id
    assert policies.can_manage_applications(staffed_membership, staffed_role)
    assert not policies.can_manage_applications(writer_membership, writer_role)


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


def test_story_actions_require_accepted_character(membership: CommunityMembership) -> None:
    accepted = Character(
        id=40,
        community_id=membership.community_id,
        membership_id=membership.id,
        name="Accepted Face",
        slug="accepted-face",
        avatar_url=None,
        poster_url=None,
        poster_alt="",
        tagline="",
        accent_color="",
        summary="Ready for scenes.",
        post_profile_variant="bio",
        post_accent_style="soft",
        post_border_style="hairline",
        post_title_style="standard",
        post_density="calm",
        application_status="accepted",
        created_at="2026-01-01T00:00:00+00:00",
        updated_at="2026-01-01T00:00:00+00:00",
    )
    submitted = replace(accepted, id=41, slug="submitted-face", application_status="submitted")
    revision_requested = replace(
        accepted,
        id=42,
        slug="revision-face",
        application_status="revision_requested",
    )

    assert policies.can_post_as(membership, submitted)
    assert policies.can_story_act_as(membership, accepted)
    assert not policies.can_story_act_as(membership, submitted)
    assert not policies.can_story_act_as(membership, revision_requested)
