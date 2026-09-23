from __future__ import annotations

import asyncio
import re

from chirp.testing import TestClient

from elbysodic.db.seed import DemoSeed, resolve_seed_persona
from elbysodic.services import AppServices, create_services
from elbysodic.web import create_app


def _staff_app():
    services = create_services(path=":memory:")
    staff = resolve_seed_persona(services.repo, "xmen_staff")
    app = create_app(
        debug=False,
        services=AppServices(
            services.repo,
            DemoSeed(staff.community, staff.user, staff.membership, staff.character),
        ),
    )
    return services, staff, app


def _empty_staff_app():
    services = create_services(path=":memory:", seed_demo=False)
    repo = services.repo
    community = repo.create_community("quiet-realm", "Quiet Realm")
    role = repo.create_role(community.id, "director", "Director", is_admin=True)
    user = repo.create_user("quiet-director@example.com", "hash")
    membership = repo.create_membership(
        community.id,
        user.id,
        role.id,
        "quiet-director",
        "Quiet Director",
    )
    character = repo.create_character(
        community.id,
        membership.id,
        "quiet-face",
        "Quiet Face",
        make_default=True,
    )
    repo.create_board(community.id, "the-square", "The Square", board_kind="location")
    app = create_app(
        debug=False,
        services=AppServices(
            repo,
            DemoSeed(community, user, membership, character),
        ),
    )
    return app


def test_studio_today_empty_state_keeps_launch_setup_separate() -> None:
    async def run() -> None:
        app = _empty_staff_app()
        async with TestClient(app) as client:
            today = await client.get("/studio")
            launch = await client.get("/studio/launch")

        assert today.status == 200
        assert launch.status == 200
        assert today.text.count("No daily staff queues need attention right now.") == 1
        assert "The realm is calm. Launch readiness stays separate in Open." in today.text
        assert "Operations clear" not in today.text
        assert "Opening checklist" not in today.text
        assert "Opening checklist" in launch.text
        assert "Operations attention lanes" not in today.text
        assert "Operations queue shortcuts" not in today.text
        diagnostics = re.search(
            r'<details class="elbysodic-operations-diagnostics">(.*?)</details>',
            today.text,
            re.DOTALL,
        )
        assert diagnostics is not None
        assert "Queue contracts" in diagnostics.group(1)
        assert "open" not in diagnostics.group(0).split(">", 1)[0]

    asyncio.run(run())


def test_studio_today_presents_writer_activation_as_one_queue() -> None:
    async def run() -> None:
        services, staff, app = _staff_app()
        access_request = services.repo.create_community_access_request(
            staff.community.id,
            email="today-prospect@example.com",
            display_name="Today Prospect",
            face_concept="Exchange student",
            wanted_hook="A first scene at the school",
            notes="Looking for the next step.",
        )

        async with TestClient(app) as client:
            today = await client.get("/studio")
            request = await client.get(f"/studio/access-requests/{access_request.id}")

        assert today.status == 200
        assert request.status == 200
        primary = re.search(
            r'<section id="director-operation-signals".*?</section>',
            today.text,
            re.DOTALL,
        )
        assert primary is not None
        primary_html = primary.group(0)
        queue_cards = re.findall(
            r'<article class="elbysodic-operations-card(?:\s[^\"]*)?".*?</article>',
            primary_html,
            re.DOTALL,
        )
        activation_cards = [card for card in queue_cards if "Writer activation" in card]
        assert len(activation_cards) == 1
        activation_card = activation_cards[0]
        assert set(re.findall(r'href="([^"]+)"', activation_card)) == {
            f"/studio/access-requests/{access_request.id}"
        }
        assert "1 access request(s)" in activation_card
        assert "Operations attention lanes" not in today.text
        assert "Operations queue shortcuts" not in today.text
        assert "Ready to review" not in today.text
        assert "Blocked by claims" not in today.text
        assert "Community builder checklist" not in today.text

    asyncio.run(run())
