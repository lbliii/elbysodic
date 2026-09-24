from __future__ import annotations

import asyncio
from pathlib import Path

from chirp.testing import TestClient

from elbysodic.db.seed import DemoSeed, SeedPersonaContext, resolve_seed_persona
from elbysodic.services import AppServices, create_services
from elbysodic.web import create_app

_PAGES = Path(__file__).parents[1] / "src/elbysodic/web/pages"
_DOC = Path(__file__).parents[1] / "docs/product/invite-to-first-face-onboarding-journey.md"


def _dev_identity_cookie(seed: DemoSeed | SeedPersonaContext) -> str:
    return f"elbysodic_dev_identity={seed.community.id}:{seed.user.id}:{seed.membership.id}"


def _create_member_seed(services: AppServices, *, prefix: str) -> DemoSeed:
    repo = services.repo
    community = services.seed.community
    user = repo.create_user(f"{prefix}@example.com", "hash")
    role = repo.get_role_by_slug(community.id, "member")
    membership = repo.create_membership(
        community.id,
        user.id,
        role.id,
        prefix,
        prefix.replace("-", " ").title(),
    )
    return DemoSeed(community, user, membership, None)


def _create_application_face(
    services: AppServices,
    seed: DemoSeed,
    *,
    slug: str,
    name: str,
    status: str,
    revision_notes: str = "",
    staff_notes: str = "",
):
    repo = services.repo
    community = seed.community
    character = repo.create_character(
        community.id,
        seed.membership.id,
        slug,
        name,
        summary=f"{name} is finding a first way into play.",
        application_status="draft",
    )
    application = repo.ensure_character_application(community.id, character.id)
    repo.update_character_application_draft(
        community.id,
        application.id,
        title=name,
        summary=f"{name} application summary.",
        body=f"{name} application notes for directors.",
    )
    if revision_notes or staff_notes:
        repo.update_character_application_review(
            community.id,
            application.id,
            revision_notes=revision_notes,
            staff_notes=staff_notes,
            checklist="Private staff checklist.",
        )
    if status != "draft":
        staff = resolve_seed_persona(repo, "xmen_staff")
        repo.transition_character_application_status(
            community.id,
            application.id,
            status=status,
            actor_membership_id=staff.membership.id,
            actor_character_id=staff.character.id if staff.character is not None else None,
            note=revision_notes or f"{name} moved to {status}.",
        )
    return repo.get_character(community.id, character.id)


def _claim_required_slots_for_face(
    services: AppServices, seed: DemoSeed, character_id: int
) -> None:
    repo = services.repo
    for claim_type in repo.list_claim_types(seed.community.id):
        if claim_type.is_required:
            repo.create_character_claim(
                seed.community.id,
                claim_type.id,
                f"{claim_type.slug}-{character_id}",
                f"{claim_type.name} for first move",
                character_id=character_id,
                status="claimed",
            )


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


def test_seeded_harbor_personas_show_reviewed_and_accepted_writer_entry() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        director = resolve_seed_persona(repo, "harbor_director")
        writer = resolve_seed_persona(repo, "harbor_writer")
        assert writer.character is not None

        requests = repo.list_community_access_requests(director.community.id)
        accepted_request = next(request for request in requests if request.status == "accepted")
        pending_request = next(request for request in requests if request.status == "pending")
        assert accepted_request.invitation_id is not None
        invitation = repo.get_community_invitation(
            director.community.id,
            accepted_request.invitation_id,
        )
        accepted_events = repo.list_community_access_request_events(
            director.community.id,
            accepted_request.id,
        )
        pending_events = repo.list_community_access_request_events(
            director.community.id,
            pending_request.id,
        )
        app = create_app(
            debug=False,
            services=AppServices(
                repo,
                DemoSeed(
                    director.community,
                    director.user,
                    director.membership,
                    director.character,
                ),
            ),
        )

        async with TestClient(app) as client:
            launch = await client.get("/studio/launch")

        assert writer.community.id == director.community.id
        assert writer.character.name == "Celia Fairbourne"
        assert accepted_request.email == writer.user.email
        assert accepted_request.invitation_id == invitation.id
        assert invitation.status == "accepted"
        assert invitation.accepted_user_id == writer.user.id
        assert invitation.accepted_membership_id == writer.membership.id
        assert [event.event_type for event in accepted_events] == [
            "submitted",
            "reviewed",
            "invited",
            "accepted",
        ]
        assert [event.event_type for event in pending_events] == ["submitted"]
        assert launch.status == 200
        assert "Eloise Byrne" in launch.text
        assert "Pending" in launch.text
        assert "Juniper Gray" in launch.text
        assert "Accepted" in launch.text
        assert "Rival committee chair" in launch.text
        services.close()

    asyncio.run(run())


def test_harbor_writer_sees_live_results_on_the_seeded_realm_artifact() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        director = resolve_seed_persona(repo, "harbor_director")
        writer = resolve_seed_persona(repo, "harbor_writer")
        app = create_app(
            debug=False,
            services=AppServices(
                repo,
                DemoSeed(
                    director.community,
                    director.user,
                    director.membership,
                    director.character,
                ),
            ),
            dev_tools=True,
        )

        async with TestClient(app) as client:
            hub = await client.get("/interactions")
            writer_seed = DemoSeed(
                writer.community,
                writer.user,
                writer.membership,
                writer.character,
            )
            detail = await client.get(
                "/interactions/founders-gala-next-reveal",
                headers={"Cookie": _dev_identity_cookie(writer_seed)},
            )

        assert hub.status == 200
        assert "Founders Gala: The Next Reveal" in hub.text
        assert "3 responses" in hub.text
        assert detail.status == 200
        assert "A seating card changed after printing" in detail.text
        assert "You responded" in detail.text
        assert "1 · 33%" in detail.text
        services.close()

    asyncio.run(run())


def test_harbor_writer_desk_prioritizes_a_seeded_scene_reply() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        writer = resolve_seed_persona(services.repo, "harbor_writer")
        assert writer.character is not None
        app = create_app(
            debug=False,
            services=AppServices(
                services.repo,
                DemoSeed(
                    writer.community,
                    writer.user,
                    writer.membership,
                    writer.character,
                ),
            ),
        )

        async with TestClient(app) as client:
            desk = await client.get("/desk")

        assert desk.status == 200
        assert "Pick up where you left off" in desk.text
        assert "Return to a scene, catch up on reading, or move a plot forward." in desk.text
        assert "Breakfast Before The Vote needs a reply" in desk.text
        assert desk.text.count("Reply where owed") == 1
        assert "Read latest" in desk.text
        assert "The Ledger Page Under Table Six" in desk.text
        services.close()

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


def test_no_face_and_application_states_keep_next_move_visible_without_staff_leaks() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        no_face_seed = _create_member_seed(services, prefix="next-move-no-face")
        draft_seed = _create_member_seed(services, prefix="next-move-draft")
        draft_face = _create_application_face(
            services,
            draft_seed,
            slug="next-move-draft",
            name="Next Move Draft",
            status="draft",
        )
        submitted_seed = _create_member_seed(services, prefix="next-move-submitted")
        _create_application_face(
            services,
            submitted_seed,
            slug="next-move-submitted",
            name="Next Move Submitted",
            status="submitted",
            staff_notes="Private submitted staff read.",
        )
        revision_seed = _create_member_seed(services, prefix="next-move-revision")
        revision_face = _create_application_face(
            services,
            revision_seed,
            slug="next-move-revision",
            name="Next Move Revision",
            status="revision_requested",
            revision_notes="Please clarify the opening wanted hook.",
            staff_notes="Private revision staff read.",
        )
        app = create_app(debug=False, services=services, dev_tools=True)

        async with TestClient(app) as client:
            no_face_desk = await client.get(
                "/desk",
                headers={"Cookie": _dev_identity_cookie(no_face_seed)},
            )
            draft_desk = await client.get(
                "/desk",
                headers={"Cookie": _dev_identity_cookie(draft_seed)},
            )
            draft_room = await client.get(
                f"/applications/{draft_face.slug}",
                headers={"Cookie": _dev_identity_cookie(draft_seed)},
            )
            submitted_desk = await client.get(
                "/desk",
                headers={"Cookie": _dev_identity_cookie(submitted_seed)},
            )
            submitted_applications = await client.get(
                "/applications",
                headers={"Cookie": _dev_identity_cookie(submitted_seed)},
            )
            revision_desk = await client.get(
                "/desk",
                headers={"Cookie": _dev_identity_cookie(revision_seed)},
            )
            revision_room = await client.get(
                f"/applications/{revision_face.slug}",
                headers={"Cookie": _dev_identity_cookie(revision_seed)},
            )

        assert no_face_desk.status == 200
        assert "Your story starts here" in no_face_desk.text
        assert "Start with a face, then find a scene, hook, or place to begin." in no_face_desk.text
        assert "No faces on your roster yet." not in no_face_desk.text
        assert "Start first face" in no_face_desk.text
        assert no_face_desk.text.count("Start first face") == 1
        assert "playing as" not in no_face_desk.text
        assert "Application Review Room" not in no_face_desk.text

        assert draft_desk.status == 200
        assert "Move a face toward play" in draft_desk.text
        assert "Continue the application, check its status, and prepare the next move." in draft_desk.text
        assert "Finish Next Move Draft" in draft_desk.text
        assert "Continue application" in draft_desk.text
        assert "Application Review Room" not in draft_desk.text

        assert draft_room.status == 200
        assert "Applicant Notes" in draft_room.text
        assert "Save notes" in draft_room.text
        assert "Director Review" not in draft_room.text
        assert "Staff notes" not in draft_room.text

        assert submitted_desk.status == 200
        assert "Move a face toward play" in submitted_desk.text
        assert "Next Move Submitted is in review" in submitted_desk.text
        assert "Watch the application room for director notes or approval." in submitted_desk.text
        assert "Open application" in submitted_desk.text
        assert "Private submitted staff read." not in submitted_desk.text

        assert submitted_applications.status == 200
        assert "Submitted" in submitted_applications.text
        assert "Open application room" in submitted_applications.text
        assert ">Accept<" not in submitted_applications.text
        assert 'data-elbysodic-submit-label="Accepting..."' not in submitted_applications.text
        assert "Review Queue" not in submitted_applications.text
        assert "Private submitted staff read." not in submitted_applications.text

        assert revision_desk.status == 200
        assert "Move a face toward play" in revision_desk.text
        assert "Next Move Revision needs revision" in revision_desk.text
        assert "Revise application" in revision_desk.text
        assert "Private revision staff read." not in revision_desk.text

        assert revision_room.status == 200
        assert "Revision Notes" in revision_room.text
        assert "Please clarify the opening wanted hook." in revision_room.text
        assert "Save notes" in revision_room.text
        assert "Private revision staff read." not in revision_room.text
        assert "Director Review" not in revision_room.text

    asyncio.run(run())


def test_accepted_face_without_clear_scene_points_to_claims_not_staff_queue() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        seed = _create_member_seed(services, prefix="accepted-no-scene")
        face = _create_application_face(
            services,
            seed,
            slug="accepted-no-scene",
            name="Accepted No Scene",
            status="accepted",
            staff_notes="Accepted private staff note.",
        )
        app = create_app(debug=False, services=services, dev_tools=True)

        async with TestClient(app) as client:
            desk = await client.get("/desk", headers={"Cookie": _dev_identity_cookie(seed)})
            room = await client.get(
                f"/applications/{face.slug}",
                headers={"Cookie": _dev_identity_cookie(seed)},
            )

        assert desk.status == 200
        assert "Settle first-face claims" in desk.text
        assert "Open claims" in desk.text
        assert "Review queue" not in desk.text
        assert "Accepted private staff note." not in desk.text

        assert room.status == 200
        assert "Accepted face handoff" in room.text
        assert "Settle first-face claims" in room.text
        assert "Open claims" in room.text
        assert "Settle claims and reserves" in room.text
        assert "Answer open calls" in room.text
        assert "Find a first scene" in room.text
        assert "Director Review" not in room.text
        assert "Staff notes" not in room.text
        assert "Accepted private staff note." not in room.text

    asyncio.run(run())


def test_accepted_face_browser_path_reaches_recommended_first_writing_move() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        seed = _create_member_seed(services, prefix="accepted-opening")
        face = _create_application_face(
            services,
            seed,
            slug="accepted-opening",
            name="Accepted Opening",
            status="accepted",
        )
        _claim_required_slots_for_face(services, seed, face.id)
        staff = resolve_seed_persona(services.repo, "xmen_staff")
        wanted = services.repo.create_wanted_ad(
            seed.community.id,
            staff.membership.id,
            "accepted-opening-first-hook",
            "Accepted opening first hook",
            creator_character_id=staff.character.id if staff.character is not None else None,
            summary="A staff-seeded hook for the accepted writer's first beat.",
        )
        interest = services.repo.create_wanted_ad_interest(
            seed.community.id,
            wanted.id,
            seed.membership.id,
            face.id,
            note="Accepted Opening is ready to plot the first scene.",
            status="plotting",
        )
        room = services.repo.create_plotting_room(
            seed.community.id,
            seed.membership.id,
            "First danger room opening",
            source_wanted_ad_id=wanted.id,
            source_wanted_ad_interest_id=interest.id,
            summary="Choose the first scene beat before posting.",
            status="ready",
        )
        services.repo.create_plotting_room_participant(
            seed.community.id,
            room.id,
            seed.membership.id,
            character_id=face.id,
            participant_role="owner",
        )
        app = create_app(debug=False, services=services, dev_tools=True)

        async with TestClient(app) as client:
            application_room = await client.get(
                f"/applications/{face.slug}",
                headers={"Cookie": _dev_identity_cookie(seed)},
            )
            desk = await client.get("/desk", headers={"Cookie": _dev_identity_cookie(seed)})
            plotting_room = await client.get(
                f"/plotting/{room.id}",
                headers={"Cookie": _dev_identity_cookie(seed)},
            )

        assert application_room.status == 200
        assert "Accepted face handoff" in application_room.text
        assert "A plotting room is waiting" in application_room.text
        assert "Open plotting room" in application_room.text
        assert f'href="/plotting/{room.id}"' in application_room.text
        assert "Application Review Room" in application_room.text
        assert "Staff notes" not in application_room.text

        assert desk.status == 200
        assert "A plotting room is waiting" in desk.text
        assert "Finish the handoff and turn the plan into a scene when it is ready." in desk.text
        assert "Open plotting room" in desk.text

        assert plotting_room.status == 200
        assert "First danger room opening" in plotting_room.text
        assert "Choose the first scene beat before posting." in plotting_room.text
        assert "Staff notes" not in plotting_room.text

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


def test_seeded_xmen_application_shows_review_history_without_leaking_staff_notes() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        applicant = resolve_seed_persona(repo, "xmen_applicant")
        staff = resolve_seed_persona(repo, "xmen_staff")
        assert applicant.character is not None
        application = repo.get_character_application_for_character(
            applicant.community.id,
            applicant.character.id,
        )
        field_keys = {
            field.id: field.field_key
            for field in repo.list_application_template_fields(applicant.community.id)
        }
        fields = {
            field_keys[value.field_id]: value.value
            for value in repo.list_application_field_values(applicant.community.id, application.id)
        }
        events = repo.list_character_application_events(applicant.community.id, application.id)
        app = create_app(debug=False, services=services, dev_tools=True)

        async with TestClient(app) as client:
            applicant_room = await client.get(
                "/applications/kitty-pryde",
                headers={"Cookie": _dev_identity_cookie(applicant)},
            )
            staff_room = await client.get(
                "/applications/kitty-pryde",
                headers={"Cookie": _dev_identity_cookie(staff)},
            )

        assert application.status == "submitted"
        assert fields == {
            "face_claim": "Thomasin McKenzie",
            "faction_claim": "X-Men",
            "power_claim": "Phasing, route mapping, and analog systems triage",
        }
        assert [event.to_status for event in events] == ["submitted", "revision_requested"]
        assert applicant_room.status == 200
        assert "Intake Fields" in applicant_room.text
        assert "Status History" in applicant_room.text
        assert "Director Review" not in applicant_room.text
        assert "Keep the moving map as evidence" not in applicant_room.text
        assert staff_room.status == 200
        assert "Director Review" in staff_room.text
        assert "Face reference reviewed" in staff_room.text
        assert "Keep the moving map as evidence" in staff_room.text

    asyncio.run(run())


def test_seeded_harbor_application_shows_wanted_source_to_owner_and_director() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        writer = resolve_seed_persona(repo, "harbor_writer")
        director = resolve_seed_persona(repo, "harbor_director")
        assert writer.character is not None
        reporter_hook = repo.get_wanted_ad_by_slug(
            writer.community.id,
            "reporter-source-at-the-club",
        )
        daphne_application = repo.get_character_application_for_character(
            writer.community.id,
            repo.get_character_by_slug(writer.community.id, "daphne-pike").id,
        )
        beatrice = repo.get_character_by_slug(writer.community.id, "beatrice-crane")
        beatrice_application = repo.get_character_application_for_character(
            writer.community.id,
            beatrice.id,
        )
        interest = repo.get_prospective_wanted_ad_interest_for_membership(
            writer.community.id,
            reporter_hook.id,
            writer.membership.id,
        )
        private_note = (
            "Please keep my name off the first tip; the club still prints programs for my employer."
        )
        app = create_app(debug=False, services=services, dev_tools=True)

        async with TestClient(app) as client:
            writer_room = await client.get(
                "/applications/daphne-pike",
                headers={"Cookie": _dev_identity_cookie(writer)},
            )
            director_room = await client.get(
                "/applications/daphne-pike",
                headers={"Cookie": _dev_identity_cookie(director)},
            )
            interest_writer_room = await client.get(
                "/applications/beatrice-crane",
                headers={"Cookie": _dev_identity_cookie(writer)},
            )
            interest_director_room = await client.get(
                "/applications/beatrice-crane",
                headers={"Cookie": _dev_identity_cookie(director)},
            )

        for response in (writer_room, director_room, interest_writer_room, interest_director_room):
            assert response.status == 200
            assert 'class="elbysodic-application-card"' in response.text
            assert "From a wanted hook" in response.text
            assert 'href="/wanted/reporter-source-at-the-club"' in response.text
            assert "Reporter source at the club" in response.text
            assert private_note not in response.text
        assert "Director Review" not in writer_room.text
        assert "Staff notes" not in writer_room.text
        assert "Director Review" in director_room.text
        assert daphne_application.source_wanted_ad_id == reporter_hook.id
        assert daphne_application.source_wanted_ad_interest_id is None
        assert beatrice_application.source_wanted_ad_id is None
        assert beatrice_application.source_wanted_ad_interest_id == interest.id
        assert beatrice_application.status == "submitted"
        assert interest.note == private_note
        assert "Director Review" not in interest_writer_room.text
        assert "Director Review" in interest_director_room.text
        services.close()

    asyncio.run(run())
