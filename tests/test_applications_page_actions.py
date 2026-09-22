"""Route proof for the /applications desk page actions."""

from __future__ import annotations

import asyncio
from urllib.parse import urlencode

import pytest
from chirp.testing import TestClient

from elbysodic.db.seed import DemoSeed
from elbysodic.services import AppServices, create_services
from elbysodic.web import create_app

_FORM = {"Content-Type": "application/x-www-form-urlencoded"}


async def _post(client: TestClient, action_name: str, slug: str, **fields: str):
    return await client.post(
        "/applications",
        body=urlencode({"_action": action_name, "character_slug": slug, **fields}).encode(),
        headers=_FORM,
    )


def _director_services(services: AppServices) -> AppServices:
    community = services.seed.community
    membership = services.repo.get_membership_by_username(community.id, "alex")
    user = services.repo.get_user(membership.user_id)
    character = services.repo.get_character_by_slug(community.id, "cyclops")
    return AppServices(
        services.repo,
        DemoSeed(community, user, membership, character),
    )


def test_desk_actions_submit_accept_and_request_revision() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        first = services.create_character(name="Action One")
        second = services.create_character(name="Action Two")
        app = create_app(debug=False, services=services)
        async with TestClient(app) as client:
            desk = await client.get("/applications")
            assert desk.status == 200
            assert 'name="_action" value="submit_application"' in desk.text
            assert 'name="intent" value="submit_application"' not in desk.text

            for character in (first, second):
                response = await _post(client, "submit_application", character.slug)
                assert response.status == 302
                assert dict(response.headers)["location"] == "/applications"

        director_app = create_app(debug=False, services=_director_services(services))
        async with TestClient(director_app) as client:
            desk = await client.get("/applications")
            assert 'name="_action" value="accept_application"' in desk.text

            accepted = await _post(client, "accept_application", first.slug)
            assert accepted.status == 302
            assert dict(accepted.headers)["location"] == "/applications"

            revision = await _post(
                client,
                "request_revision",
                second.slug,
                revision_note="Add a stronger opening hook.",
            )
            assert revision.status == 302
            assert dict(revision.headers)["location"] == "/applications"

        community_id = services.seed.community.id
        assert (
            services.repo.get_character_by_slug(community_id, first.slug).application_status
            == "accepted"
        )
        assert (
            services.repo.get_character_by_slug(community_id, second.slug).application_status
            == "revision_requested"
        )
        second_application = services.repo.get_character_application_for_character(
            community_id, second.id
        )
        assert second_application.revision_notes == "Add a stronger opening hook."

    asyncio.run(run())


@pytest.mark.parametrize(
    ("exception", "expected_status"),
    [
        (PermissionError("not allowed"), 403),
        (LookupError("missing face"), 404),
        (ValueError("invalid status"), 400),
    ],
)
@pytest.mark.parametrize(
    ("action_name", "method_name"),
    [
        ("submit_application", "submit_character_application"),
        ("accept_application", "accept_character_application"),
        ("request_revision", "request_character_application_revision"),
    ],
)
def test_desk_actions_preserve_service_error_statuses(
    monkeypatch: pytest.MonkeyPatch,
    exception: Exception,
    expected_status: int,
    action_name: str,
    method_name: str,
) -> None:
    def fail(*_args: object, **_kwargs: object) -> None:
        raise exception

    monkeypatch.setattr(AppServices, method_name, fail)

    async def run() -> None:
        app = create_app(debug=False, services=create_services(path=":memory:"))
        async with TestClient(app) as client:
            response = await _post(client, action_name, "action-face")
            assert response.status == expected_status

    asyncio.run(run())


def test_legacy_intent_does_not_dispatch_desk_action() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        character = services.create_character(name="Legacy Intent")
        app = create_app(debug=False, services=services)
        async with TestClient(app) as client:
            response = await client.post(
                "/applications",
                body=urlencode(
                    {"intent": "submit_application", "character_slug": character.slug}
                ).encode(),
                headers=_FORM,
            )
            assert response.status == 200
        assert (
            services.repo.get_character_by_slug(
                services.seed.community.id, character.slug
            ).application_status
            == "draft"
        )

    asyncio.run(run())
