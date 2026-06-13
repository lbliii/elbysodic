from __future__ import annotations

import asyncio
from pathlib import Path

from chirp.testing import TestClient

from elbysodic.db.seed import DemoSeed, resolve_seed_persona
from elbysodic.services import AppServices, create_services
from elbysodic.web import create_app

_PAGES = Path(__file__).parents[1] / "src/elbysodic/web/pages"
_DOC = Path(__file__).parents[1] / "docs/product/invite-to-first-face-onboarding-journey.md"


def _dev_identity_cookie(seed: DemoSeed) -> str:
    return f"elbysodic_dev_identity={seed.community.id}:{seed.user.id}:{seed.membership.id}"


def test_onboarding_journey_templates_and_docs_name_first_face_path() -> None:
    request_access = (_PAGES / "request-access/page.html").read_text(encoding="utf-8")
    invite = (_PAGES / "invite/{invite_token}/page.html").read_text(encoding="utf-8")
    application = (_PAGES / "applications/new/page.html").read_text(encoding="utf-8")
    doc = _DOC.read_text(encoding="utf-8")

    for snippet in [
        "Request access",
        "director controls the roster gate",
        "first faces start in the right realm",
        "Wanted hook or way in",
        "Notes for directors",
    ]:
        assert snippet in request_access
    for snippet in [
        "Accept invitation",
        "writer identity you will use here",
        "writer name, role, and faces belong to this realm",
        "First face",
        "Enter realm",
    ]:
        assert snippet in invite
    for snippet in [
        "Start a face",
        "Begin a new face",
        "first active face",
        "Claims and reserves",
        "Open calls",
        "First scene",
        "Application materials",
    ]:
        assert snippet in application
    for snippet in [
        "public preview -> request access or invitation -> local membership",
        "Public visitor",
        "Signed-in account visitor",
        "Invited writer",
        "Faceless member",
        "Applicant",
        "Accepted face",
        "Inactive or cross-community visitor",
    ]:
        assert snippet in doc


def test_invited_writer_page_explains_local_membership_and_first_face() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        staff = resolve_seed_persona(services.repo, "xmen_staff")
        staff_services = AppServices(
            services.repo,
            DemoSeed(staff.community, staff.user, staff.membership, staff.character),
        )
        created = staff_services.create_writer_invitation("journey-invite@example.com")
        app = create_app(debug=False, services=services, dev_tools=True)

        async with TestClient(app) as client:
            response = await client.get(f"/invite/{created.token}")

        assert response.status == 200
        assert "Accept invitation" in response.text
        assert "X-Men Apocalypse" in response.text
        assert "This invitation is for journey-invite@example.com" in response.text
        assert "writer name, role, and faces belong to this realm" in response.text
        assert "Writer username" in response.text
        assert "Display name" in response.text
        assert "First face" in response.text
        assert "Enter realm" in response.text
        assert "Staff notes" not in response.text
        assert "Application Review Room" not in response.text

    asyncio.run(run())


def test_faceless_member_application_starter_points_to_next_pbp_actions() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        community = services.seed.community
        user = repo.create_user("faceless-journey@example.com", "hash")
        role = repo.get_role_by_slug(community.id, "member")
        membership = repo.create_membership(
            community.id,
            user.id,
            role.id,
            "faceless-journey",
            "Faceless Journey",
        )
        seed = DemoSeed(community, user, membership, None)
        app = create_app(debug=False, services=AppServices(repo, seed), dev_tools=True)

        async with TestClient(app) as client:
            response = await client.get(
                "/applications/new",
                headers={"Cookie": _dev_identity_cookie(seed)},
            )

        assert response.status == 200
        assert "Start a face" in response.text
        assert "Begin a new face" in response.text
        assert "This will become your first active face in X-Men Apocalypse" in response.text
        assert "Application materials" in response.text
        assert "Face name" in response.text
        assert "Application notes" in response.text
        assert "Claims and reserves" in response.text
        assert "Open calls" in response.text
        assert "First scene" in response.text
        assert "playing as" not in response.text
        assert "Application Review Room" not in response.text
        assert "Staff notes" not in response.text

    asyncio.run(run())


def test_public_request_access_keeps_interest_separate_from_permission() -> None:
    async def run() -> None:
        app = create_app(debug=False, services=create_services(path=":memory:"), dev_tools=True)

        async with TestClient(app) as client:
            response = await client.get("/c/x-men-apocalypse/request-access")

        assert response.status == 200
        assert "Request access" in response.text
        assert "Access opens through a director invitation." in response.text
        assert "Writer email" in response.text
        assert "Face concept" in response.text
        assert "Wanted hook or way in" in response.text
        assert "Notes for directors" in response.text
        assert "Send access request" in response.text
        assert "Enter realm" not in response.text
        assert "Staff notes" not in response.text
        assert "Application Review Room" not in response.text

    asyncio.run(run())
