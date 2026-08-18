from __future__ import annotations

import asyncio
from pathlib import Path

from chirp.testing import TestClient

from elbysodic.db.seed import SeedPersonaContext, resolve_seed_persona
from elbysodic.services import create_services
from elbysodic.web import create_app

_PAGES = Path(__file__).parents[1] / "src/elbysodic/web/pages"
_DOC = Path(__file__).parents[1] / "docs/product/director-realm-opening-front-end.md"


def _dev_identity_cookie(persona: SeedPersonaContext) -> str:
    return (
        f"elbysodic_dev_identity={persona.community.id}:{persona.user.id}:{persona.membership.id}"
    )


def _set_production_env(monkeypatch) -> None:
    monkeypatch.setenv("ELBYSODIC_ENV", "production")
    monkeypatch.setenv("ELBYSODIC_SECRET_KEY", "x" * 32)
    monkeypatch.setenv("ELBYSODIC_ALLOWED_HOSTS", "*")
    monkeypatch.setenv("ELBYSODIC_DEMO_MODE", "1")


def test_director_opening_templates_and_docs_use_realm_studio_language() -> None:
    launch = (_PAGES / "studio/launch/page.html").read_text(encoding="utf-8")
    studio = (_PAGES / "studio/page.html").read_text(encoding="utf-8")
    doc = _DOC.read_text(encoding="utf-8")

    for snippet in [
        "Open realm",
        "Scene hubs",
        "director materials",
        "intake, claims",
        "wanted hooks",
        "Opening checklist",
        "Opening packet",
        "Writer invitations",
        "Create invitation",
        "Access requests",
        "Discovery profile",
        "Edit discovery profile",
    ]:
        assert snippet in launch
    for snippet in ["Director Studio", "Needs attention", "Open hooks", "Today"]:
        assert snippet in studio
    for snippet in [
        "No realm",
        "Empty configured realm",
        "Backstage realm",
        "Invite-only realm",
        "Public-preview realm",
        "director production room",
    ]:
        assert snippet in doc


def test_director_launch_room_renders_opening_contract() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        staff = resolve_seed_persona(services.repo, "xmen_staff")
        app = create_app(debug=False, services=services, dev_tools=True)

        async with TestClient(app) as client:
            launch = await client.get(
                "/studio/launch",
                headers={"Cookie": _dev_identity_cookie(staff)},
            )

        assert launch.status == 200
        assert "Open realm" in launch.text
        assert "Open the realm with the writing surface intact." in launch.text
        assert "Launch readiness" in launch.text
        assert "Opening checklist" in launch.text
        assert "Opening packet" in launch.text
        assert "Scene hub" in launch.text
        assert "Application guide" in launch.text
        assert "Invite-only before public self-serve." in launch.text
        assert "Writer invitations" in launch.text
        assert "Discovery profile" in launch.text
        assert "Edit discovery profile" in launch.text
        assert "Create invitation" in launch.text
        assert "global login account if needed" in launch.text
        assert "writer's membership inside X-Men Apocalypse" in launch.text

    asyncio.run(run())


def test_member_and_public_visitors_do_not_see_director_launch_body(monkeypatch) -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        writer = resolve_seed_persona(services.repo, "xmen_writer")
        member_app = create_app(debug=False, services=services, dev_tools=True)

        async with TestClient(member_app) as client:
            member_launch = await client.get(
                "/studio/launch",
                headers={"Cookie": _dev_identity_cookie(writer)},
            )

        _set_production_env(monkeypatch)
        public_app = create_app(debug=False, services=create_services(path=":memory:"))
        async with TestClient(public_app) as client:
            public_realm = await client.get("/c/x-men-apocalypse")
            public_launch = await client.get("/c/x-men-apocalypse/studio/launch")

        assert member_launch.status == 403
        for forbidden in [
            "Opening checklist",
            "Opening packet",
            "Writer invitations",
            "Access requests",
            "Create invitation",
        ]:
            assert forbidden not in member_launch.text
            assert forbidden not in public_realm.text

        assert public_realm.status == 200
        assert "Where the story is opening" in public_realm.text
        assert "Public preview" in public_realm.text
        assert "Launch readiness" not in public_realm.text
        assert public_launch.status == 302
        assert dict(public_launch.headers)["location"] == (
            "/login?next=%2Fc%2Fx-men-apocalypse%2Fstudio%2Flaunch"
        )

    asyncio.run(run())
