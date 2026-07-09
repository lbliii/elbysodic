from __future__ import annotations

import asyncio

from chirp.testing import RouteSmokeCase, TestClient, assert_route_smoke

from elbysodic.db.seed import DemoSeed, resolve_seed_persona
from elbysodic.services import AppServices, create_services
from elbysodic.web import create_app


def test_member_route_smoke_covers_full_pages_and_fragments() -> None:
    async def run() -> None:
        app = create_app(debug=False, services=create_services(path=":memory:"))

        async with TestClient(app) as client:
            await assert_route_smoke(
                client,
                [
                    "/",
                    "/network",
                    "/characters/rogue",
                    RouteSmokeCase("/boards/danger-room", mode="both"),
                    RouteSmokeCase("/boards/danger-room/threads/sentinel-drill", mode="both"),
                ],
            )

    asyncio.run(run())


def test_member_route_smoke_covers_boosted_shell_outlets() -> None:
    """Boosted navigation must negotiate the Page shell outlet, never a raw Template.

    ``mode="boosted"`` sends ``HX-Boosted``/``HX-Target`` and fails on any
    route whose response carries a ``full_page`` render intent (an unshelled
    ``Template`` response that would nest a document inside the outlet).
    """

    async def run() -> None:
        app = create_app(debug=False, services=create_services(path=":memory:"))

        async with TestClient(app) as client:
            await assert_route_smoke(
                client,
                [
                    RouteSmokeCase(path, mode="boosted", target="main")
                    for path in (
                        "/",
                        "/network",
                        "/characters/rogue",
                        "/boards/danger-room",
                        "/boards/danger-room/threads/sentinel-drill",
                    )
                ],
            )

    asyncio.run(run())


def test_staff_route_smoke_covers_director_surfaces() -> None:
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
            await assert_route_smoke(client, ["/studio", "/studio/launch", "/applications"])
            await assert_route_smoke(
                client,
                [
                    RouteSmokeCase(path, mode="boosted", target="main")
                    for path in ("/studio", "/studio/launch", "/applications")
                ],
            )

    asyncio.run(run())
