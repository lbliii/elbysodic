"""Link-integrity crawl over the demo-seeded app.

Uses the chirp 0.8.1 ``chirp.testing`` crawl helpers: render seed pages,
collect every same-origin ``href``, and GET each discovered path. Fails on
any dead link (non-200) and on a vacuous crawl (no links discovered).
"""

from __future__ import annotations

import asyncio

import pytest
from chirp.testing import TestClient, assert_link_integrity

from elbysodic.db.seed import DemoSeed, resolve_seed_persona
from elbysodic.services import AppServices, create_services
from elbysodic.web import create_app

# "/stream" is chirp's default skip (SSE endpoints). "/logout" is a redirect
# endpoint (302 by design), not a renderable page, so it cannot satisfy the
# crawl's expected 200.
_SKIP_SUFFIXES = ("/stream", "/logout")


@pytest.mark.integration
def test_member_link_integrity_from_seeded_pages() -> None:
    """Every same-origin link reachable from the member shell resolves."""

    async def run() -> None:
        app = create_app(debug=False, services=create_services(path=":memory:"))

        async with TestClient(app) as client:
            result = await assert_link_integrity(
                client,
                [
                    "/",
                    "/network",
                    "/characters/rogue",
                    "/boards/danger-room",
                    "/boards/danger-room/threads/sentinel-drill",
                ],
                skip_suffixes=_SKIP_SUFFIXES,
            )
            # The seeded shell links out broadly; a steep drop means the crawl
            # silently lost coverage rather than the links going dead.
            assert len(result.discovered) >= 50

    asyncio.run(run())


@pytest.mark.integration
def test_staff_link_integrity_from_studio() -> None:
    """Every same-origin link on the seeded director surfaces resolves."""

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
            result = await assert_link_integrity(
                client,
                ["/studio", "/studio/launch", "/applications"],
                skip_suffixes=_SKIP_SUFFIXES,
            )
            assert len(result.discovered) >= 20

    asyncio.run(run())
