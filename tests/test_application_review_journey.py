from __future__ import annotations

import asyncio
from urllib.parse import urlencode

from chirp.testing import TestClient

from elbysodic.db.seed import DemoSeed, resolve_seed_persona
from elbysodic.services import AppServices, create_services
from elbysodic.web import create_app

_FORM = {"Content-Type": "application/x-www-form-urlencoded"}


def test_review_decisions_save_current_notes_without_exposing_staff_fields() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        writer = resolve_seed_persona(repo, "xmen_writer")
        staff = resolve_seed_persona(repo, "xmen_staff")
        writer_services = AppServices(
            repo,
            DemoSeed(writer.community, writer.user, writer.membership, writer.character),
        )
        staff_services = AppServices(
            repo,
            DemoSeed(staff.community, staff.user, staff.membership, staff.character),
        )

        revision_face = writer_services.create_character(
            name="Review Notes Revision Face",
            summary="A face used to review revision feedback.",
            application_body="The writer's initial application notes.",
        )
        writer_services.submit_character_application(revision_face.slug)

        accepted_face = writer_services.create_character(
            name="Review Notes Accepted Face",
            summary="A face used to review acceptance notes.",
            application_body="The writer's second application notes.",
        )
        writer_services.submit_character_application(accepted_face.slug)

        staff_app = create_app(debug=False, services=staff_services)
        async with TestClient(staff_app) as staff_client:
            review_room = await staff_client.get(f"/applications/{revision_face.slug}")
            assert review_room.status == 200
            assert "Revision note for applicant" in review_room.text
            assert "Visible to the applicant after you request revisions." in review_room.text
            assert "Staff notes · staff-only" in review_room.text
            assert "Checklist · staff-only" in review_room.text
            assert "Only staff can see these notes." in review_room.text
            assert "Only staff can see this checklist." in review_room.text

            form_start = review_room.text.index('name="revision_notes"')
            form_end = review_room.text.index("</form>", form_start)
            decision_form = review_room.text[form_start:form_end]
            assert 'name="_action"' in decision_form
            assert 'value="save_review"' in decision_form
            assert 'value="request_revision"' in decision_form
            assert 'value="accept_application"' in decision_form

            revision_response = await staff_client.post(
                f"/applications/{revision_face.slug}",
                body=urlencode(
                    {
                        "_action": "request_revision",
                        "revision_notes": "Please add a concrete first-scene hook.",
                        "staff_notes": "REVISION_STAFF_ONLY: strong voice.",
                        "checklist": "REVISION_CHECKLIST_ONLY: hook; cast tie.",
                    }
                ).encode(),
                headers=_FORM,
            )
            assert revision_response.status == 302

            accept_response = await staff_client.post(
                f"/applications/{accepted_face.slug}",
                body=urlencode(
                    {
                        "_action": "accept_application",
                        "revision_notes": "ACCEPTED_APPLICANT_NOTE: welcome aboard.",
                        "staff_notes": "ACCEPT_STAFF_ONLY: clear concept.",
                        "checklist": "ACCEPT_CHECKLIST_ONLY: ready.",
                    }
                ).encode(),
                headers=_FORM,
            )
            assert accept_response.status == 302

        revision_application = repo.get_character_application_for_character(
            writer.community.id,
            revision_face.id,
        )
        assert revision_application.revision_notes == "Please add a concrete first-scene hook."
        assert revision_application.staff_notes == "REVISION_STAFF_ONLY: strong voice."
        assert revision_application.checklist == "REVISION_CHECKLIST_ONLY: hook; cast tie."
        assert (
            repo.get_character_by_slug(writer.community.id, revision_face.slug).application_status
            == "revision_requested"
        )

        accepted_application = repo.get_character_application_for_character(
            writer.community.id,
            accepted_face.id,
        )
        assert accepted_application.revision_notes == "ACCEPTED_APPLICANT_NOTE: welcome aboard."
        assert accepted_application.staff_notes == "ACCEPT_STAFF_ONLY: clear concept."
        assert accepted_application.checklist == "ACCEPT_CHECKLIST_ONLY: ready."
        assert (
            repo.get_character_by_slug(writer.community.id, accepted_face.slug).application_status
            == "accepted"
        )

        applicant_app = create_app(debug=False, services=writer_services)
        async with TestClient(applicant_app) as applicant_client:
            revision_room = await applicant_client.get(f"/applications/{revision_face.slug}")
            accepted_room = await applicant_client.get(f"/applications/{accepted_face.slug}")

        assert revision_room.status == 200
        assert "Please add a concrete first-scene hook." in revision_room.text
        assert "REVISION_STAFF_ONLY" not in revision_room.text
        assert "REVISION_CHECKLIST_ONLY" not in revision_room.text
        assert "Director Review" not in revision_room.text

        assert accepted_room.status == 200
        assert "ACCEPTED_APPLICANT_NOTE: welcome aboard." in accepted_room.text
        assert "ACCEPT_STAFF_ONLY" not in accepted_room.text
        assert "ACCEPT_CHECKLIST_ONLY" not in accepted_room.text
        assert "Director Review" not in accepted_room.text

    asyncio.run(run())
