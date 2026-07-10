"""Full, boosted, and targeted response-shape contracts."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from chirp.testing import TestClient

from elbysodic.db.seed import DemoSeed, resolve_seed_persona
from elbysodic.services import AppServices, create_services
from elbysodic.web import create_app

_DOCUMENT_WRAPPERS = ("<!DOCTYPE", "<html", "<body")
_SHELL_OUTLET_MARKERS = (
    'id="main"',
    'hx-select="#page-content"',
    'id="page-content"',
    'id="page-root"',
)


@dataclass(frozen=True, slots=True)
class _AudienceRoute:
    name: str
    path: str
    content_marker: str


_MEMBER_ROUTES = (
    _AudienceRoute("network", "/network", 'id="network-explore-heading"'),
    _AudienceRoute("character", "/characters/rogue", 'aria-label="Rogue posts"'),
)
_STAFF_ROUTES = (_AudienceRoute("director", "/studio", "Director Studio"),)


def _assert_contains(response_text: str, markers: tuple[str, ...], *, case: str) -> None:
    for marker in markers:
        assert marker in response_text, f"{case} is missing {marker!r}"


def _assert_omits(response_text: str, markers: tuple[str, ...], *, case: str) -> None:
    for marker in markers:
        assert marker not in response_text, f"{case} unexpectedly contains {marker!r}"


async def _assert_response_matrix(
    client: TestClient,
    routes: tuple[_AudienceRoute, ...],
) -> None:
    for route in routes:
        full = await client.get(route.path)
        full_case = f"{route.name} full document"
        assert full.status == 200, full_case
        assert full.header("X-Chirp-Render-Intent") == "full_page", full_case
        _assert_contains(
            full.text,
            (*_DOCUMENT_WRAPPERS, *_SHELL_OUTLET_MARKERS, route.content_marker),
            case=full_case,
        )
        _assert_omits(full.text, ("hx-swap-oob",), case=full_case)

        boosted = await client.boosted(route.path, target="main")
        boosted_case = f"{route.name} boosted shell outlet"
        assert boosted.status == 200, boosted_case
        assert boosted.header("X-Chirp-Render-Intent") == "fragment", boosted_case
        _assert_contains(
            boosted.text,
            (
                *_DOCUMENT_WRAPPERS,
                *_SHELL_OUTLET_MARKERS,
                route.content_marker,
                "hx-swap-oob",
            ),
            case=boosted_case,
        )

        targeted = await client.fragment(route.path, target="page-root")
        targeted_case = f"{route.name} targeted fragment"
        assert targeted.status == 200, targeted_case
        assert targeted.header("X-Chirp-Render-Intent") == "fragment", targeted_case
        _assert_contains(
            targeted.text,
            (route.content_marker, "hx-swap-oob"),
            case=targeted_case,
        )
        _assert_omits(
            targeted.text,
            (*_DOCUMENT_WRAPPERS, *_SHELL_OUTLET_MARKERS),
            case=targeted_case,
        )


def test_member_response_shape_matrix_preserves_the_negotiated_shell() -> None:
    """Boosted documents stay safe because #main selects only #page-content."""

    async def run() -> None:
        app = create_app(debug=False, services=create_services(path=":memory:"))
        async with TestClient(app) as client:
            await _assert_response_matrix(client, _MEMBER_ROUTES)

    asyncio.run(run())


def test_staff_response_shape_matrix_preserves_the_director_boundary() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        staff = resolve_seed_persona(services.repo, "xmen_staff")
        app = create_app(
            debug=False,
            services=AppServices(
                services.repo,
                DemoSeed(staff.community, staff.user, staff.membership, staff.character),
            ),
        )
        async with TestClient(app) as client:
            await _assert_response_matrix(client, _STAFF_ROUTES)

    asyncio.run(run())
