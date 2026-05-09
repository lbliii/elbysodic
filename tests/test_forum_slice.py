from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from urllib.parse import urlencode

import pytest
from chirp.app import App
from chirp.http.response import Response
from chirp.testing import TestClient
from chirp_ui.alpine import check_alpine_runtime

from elbysodic.db import ForumRepository, connect, create_schema
from elbysodic.db.seed import DemoSeed, resolve_seed_persona, seed_demo_forum
from elbysodic.domain import Community, Thread
from elbysodic.services import AppServices, create_services, default_database_path
from elbysodic.web import create_app
from elbysodic.web.state import get_services
from elbysodic.web.tenant import scope_response_urls

_FORM = {"Content-Type": "application/x-www-form-urlencoded"}


def _sidebar_board_count(html: str, board_slug: str) -> int:
    match = re.search(
        rf'<a class="[^"]*elbysodic-sidebar-link[^"]*"\s+href="(?:/c/[^"]+)?/boards/{re.escape(board_slug)}"[^>]*>'
        r"(?P<body>.*?)</a>",
        html,
        re.DOTALL,
    )
    assert match is not None
    count = re.search(
        r'<span class="elbysodic-sidebar-count">(?P<count>\d+)</span>',
        match.group("body"),
    )
    return int(count.group("count")) if count is not None else 0


def _response_header(response: Any, name: str) -> str:
    headers = response.headers
    if isinstance(headers, dict):
        return str(headers[name])
    for key, value in headers:
        if str(key).lower() == name.lower():
            return str(value)
    raise AssertionError(f"response header not found: {name}")


def _response_headers(response: Any, name: str) -> list[str]:
    headers = response.headers
    if isinstance(headers, dict):
        value = headers.get(name)
        return [] if value is None else [str(value)]
    values = []
    for key, value in headers:
        if str(key).lower() == name.lower():
            values.append(str(value))
    return values


def _style_block(html: str, style_id: str) -> str:
    match = re.search(
        rf'<style id="{re.escape(style_id)}">(?P<body>.*?)</style>',
        html,
        re.DOTALL,
    )
    assert match is not None
    return match.group("body")


def _oob_block(html: str, target_id: str) -> str:
    match = re.search(
        rf'<div id="{re.escape(target_id)}" hx-swap-oob="innerHTML">(?P<body>.*?)</div>',
        html,
        re.DOTALL,
    )
    assert match is not None
    return match.group("body")


def _page_content(html: str) -> str:
    marker = '<div id="page-content">'
    start = html.find(marker)
    assert start >= 0
    return html[start:]


def _app():
    return create_app(debug=False, services=create_services(path=":memory:"))


def _outsider_services(
    services: AppServices, *, prefix: str = "outsider"
) -> tuple[AppServices, int]:
    repo = services.repo
    community = services.seed.community
    role = repo.get_role_by_slug(community.id, "member")
    user = repo.create_user(f"{prefix}@example.com", "hash")
    membership = repo.create_membership(
        community.id,
        user.id,
        role.id,
        prefix,
        prefix.title(),
    )
    character = repo.create_character(
        community.id,
        membership.id,
        f"{prefix}-face",
        f"{prefix.title()} Face",
        make_default=True,
    )
    membership = repo.get_membership(community.id, membership.id)
    return AppServices(repo, DemoSeed(community, user, membership, character)), character.id


def _faceless_services(services: AppServices, *, prefix: str = "faceless") -> AppServices:
    repo = services.repo
    community = services.seed.community
    role = repo.get_role_by_slug(community.id, "member")
    user = repo.create_user(f"{prefix}@example.com", "hash")
    membership = repo.create_membership(
        community.id,
        user.id,
        role.id,
        prefix,
        prefix.title(),
    )
    return AppServices(repo, DemoSeed(community, user, membership, None))


def _add_hosted_membership(
    services: AppServices,
    *,
    slug: str = "hosted",
    user_id: int | None = None,
    username: str = "hosted-lane",
    is_admin: bool = False,
) -> tuple[Community, int, int, int]:
    repo = services.repo
    community = repo.create_community(slug, "Hosted Program", host=f"{slug}.test")
    role = repo.create_role(
        community.id,
        "director" if is_admin else "member",
        "Director" if is_admin else "Member",
        is_admin=is_admin,
    )
    if user_id is None:
        user = repo.create_user(f"{slug}@example.com", "hash")
        user_id = user.id
    membership = repo.create_membership(
        community.id,
        user_id,
        role.id,
        username,
        "Hosted Lane",
    )
    character = repo.create_character(
        community.id,
        membership.id,
        "hosted-face",
        "Hosted Face",
        make_default=True,
    )
    return community, user_id, membership.id, character.id


def _dev_request(headers: dict[str, str]) -> SimpleNamespace:
    return SimpleNamespace(headers=headers)


def test_default_database_path_uses_railway_volume_when_available(monkeypatch) -> None:
    monkeypatch.delenv("ELBYSODIC_DB_PATH", raising=False)
    monkeypatch.setenv("RAILWAY_VOLUME_MOUNT_PATH", "/app/var")

    assert default_database_path() == Path("/app/var/elbysodic.sqlite3")


def test_explicit_database_path_overrides_railway_volume(monkeypatch) -> None:
    monkeypatch.setenv("ELBYSODIC_DB_PATH", "/app/custom/forum.sqlite3")
    monkeypatch.setenv("RAILWAY_VOLUME_MOUNT_PATH", "/app/var")

    assert default_database_path() == Path("/app/custom/forum.sqlite3")


def test_unknown_external_host_falls_back_to_default_community() -> None:
    async def run() -> None:
        app = _app()

        async with TestClient(app) as client:
            response = await client.get(
                "/",
                headers={"host": "elbysodic-demo.up.railway.app"},
            )

        assert response.status == 200
        assert "X-Men Apocalypse" in response.text
        assert "Rogue" in response.text

    asyncio.run(run())


def test_unknown_external_host_is_rejected_after_default_community_has_host() -> None:
    services = create_services(path=":memory:")
    services.repo.connection.execute(
        "UPDATE communities SET host = ? WHERE id = ?",
        ("demo.example.com", services.seed.community.id),
    )
    services.repo.connection.commit()

    with pytest.raises(LookupError, match=r"community not found for host: unknown\.example\.com"):
        services.for_request(_dev_request({"host": "unknown.example.com"}))


def test_health_check_does_not_require_registered_community_host() -> None:
    async def run() -> None:
        app = _app()

        async with TestClient(app) as client:
            response = await client.get(
                "/health",
                headers={"host": "elbysodic-demo.up.railway.app"},
            )

        assert response.status == 200
        assert response.text == "ok\n"
        assert "app;dur=" in _response_header(response, "Server-Timing")
        assert float(_response_header(response, "X-Elbysodic-Route-Time-Ms")) >= 0

    asyncio.run(run())


def test_request_identity_resolves_membership_inside_selected_community() -> None:
    services = create_services(path=":memory:")
    community, user_id, membership_id, character_id = _add_hosted_membership(
        services,
        user_id=services.seed.user.id,
    )

    scoped = services.for_request(
        _dev_request(
            {
                "x-elbysodic-community": community.slug,
                "x-elbysodic-user-id": str(user_id),
            }
        )
    )

    viewer = scoped.viewer()
    assert viewer.community.id == community.id
    assert viewer.membership.id == membership_id
    assert viewer.current_character is not None
    assert viewer.current_character.id == character_id
    assert viewer.current_character.community_id == community.id


def test_request_identity_does_not_leak_roles_between_communities() -> None:
    services = create_services(path=":memory:")
    community, user_id, _membership_id, _character_id = _add_hosted_membership(
        services,
        user_id=services.seed.user.id,
        is_admin=False,
    )

    default_viewer = services.viewer()
    hosted_viewer = services.for_request(
        _dev_request(
            {
                "host": "hosted.test",
                "x-elbysodic-user-id": str(user_id),
            }
        )
    ).viewer()

    assert default_viewer.community.id != hosted_viewer.community.id
    assert hosted_viewer.community.id == community.id
    assert hosted_viewer.role.community_id == community.id
    assert not hosted_viewer.role.is_admin


def test_request_identity_rejects_membership_that_belongs_to_another_user() -> None:
    services = create_services(path=":memory:")
    community, _user_id, membership_id, _character_id = _add_hosted_membership(services)
    other_user = services.repo.create_user("other-hosted@example.com", "hash")

    with pytest.raises(PermissionError, match="does not belong to user"):
        services.for_request(
            _dev_request(
                {
                    "x-elbysodic-community": community.slug,
                    "x-elbysodic-membership-id": str(membership_id),
                    "x-elbysodic-user-id": str(other_user.id),
                }
            )
        )


def test_request_identity_rejects_inactive_membership_viewer() -> None:
    services = create_services(path=":memory:")
    community, user_id, membership_id, _character_id = _add_hosted_membership(services)
    services.repo.connection.execute(
        "UPDATE community_memberships SET is_active = 0 WHERE community_id = ? AND id = ?",
        (community.id, membership_id),
    )
    services.repo.connection.commit()

    scoped = services.for_request(
        _dev_request(
            {
                "x-elbysodic-community": community.slug,
                "x-elbysodic-user-id": str(user_id),
            }
        )
    )

    with pytest.raises(PermissionError, match="is not active"):
        scoped.viewer()


def test_request_scoped_page_renders_selected_community_membership() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        community, user_id, _membership_id, _character_id = _add_hosted_membership(
            services,
            user_id=services.seed.user.id,
        )

        async with TestClient(app) as client:
            default_members = await client.get("/members")
            hosted_members = await client.get(
                "/members",
                headers={
                    "x-elbysodic-community": community.slug,
                    "x-elbysodic-user-id": str(user_id),
                },
            )

        assert default_members.status == 200
        assert hosted_members.status == 200
        assert "X-Men Apocalypse" in default_members.text
        assert "Hosted Program" in hosted_members.text
        assert "Hosted Lane" in hosted_members.text
        assert "Hosted Face" in hosted_members.text
        assert "Cyclops" not in hosted_members.text

    asyncio.run(run())


def test_tenant_prefixed_route_resolves_community_before_local_slug() -> None:
    async def run() -> None:
        app = _app()

        async with TestClient(app) as client:
            response = await client.get("/c/jurassic-park-universe/boards/paddock-twelve")

        assert response.status == 200
        assert "Jurassic Park Universe" in response.text
        assert "Paddock Twelve" in response.text
        assert (
            'class="elbysodic-community-brand__name">Jurassic Park Universe</span>' in response.text
        )

    asyncio.run(run())


def test_tenant_prefixed_route_overrides_development_community_header() -> None:
    async def run() -> None:
        app = _app()

        async with TestClient(app) as client:
            response = await client.get(
                "/c/jurassic-park-universe/world/paddock-twelve-incident",
                headers={"x-elbysodic-community": "x-men-apocalypse"},
            )

        assert response.status == 200
        assert "Jurassic Park Universe" in response.text
        assert "Current Event: Paddock Twelve" in response.text
        assert (
            'class="elbysodic-community-brand__name">Jurassic Park Universe</span>' in response.text
        )

    asyncio.run(run())


def test_tenant_prefixed_route_keeps_scoped_links_inside_prefix() -> None:
    async def run() -> None:
        app = _app()

        async with TestClient(app) as client:
            response = await client.get("/c/jurassic-park-universe/boards/paddock-twelve")

        assert response.status == 200
        assert 'href="/c/jurassic-park-universe"' in response.text
        assert 'href="/c/jurassic-park-universe/world"' in response.text
        assert 'href="/c/jurassic-park-universe/boards/paddock-twelve/threads/new"' in response.text
        assert (
            'name="next" value="/c/jurassic-park-universe/boards/paddock-twelve"' in response.text
        )
        assert (
            "/login?next=%2Fc%2Fjurassic-park-universe%2Fboards%2Fpaddock-twelve" in response.text
        )
        assert 'href="/elbysodic-static/elbysodic-theme.css' in response.text
        assert 'href="/c/jurassic-park-universe/elbysodic-static' not in response.text

    asyncio.run(run())


def test_tenant_scoping_preserves_authored_form_values() -> None:
    response = Response(
        """
        <a href="/world">World</a>
        <form action="/boards/danger-room/threads/new">
          <input name="title" value="/not-a-route">
          <input name="next" value="/boards/danger-room">
        </form>
        """,
        content_type="text/html",
    )

    scoped = scope_response_urls(response, "x-men-apocalypse")

    assert isinstance(scoped.body, str)
    assert 'href="/c/x-men-apocalypse/world"' in scoped.body
    assert 'action="/c/x-men-apocalypse/boards/danger-room/threads/new"' in scoped.body
    assert 'name="title" value="/not-a-route"' in scoped.body
    assert 'name="next" value="/c/x-men-apocalypse/boards/danger-room"' in scoped.body


def test_composer_forms_save_drafts_on_submit_instead_of_clearing_early() -> None:
    composer_paths = [
        Path("src/elbysodic/web/pages/boards/{board_slug}/threads/new/page.html"),
        Path("src/elbysodic/web/pages/boards/{board_slug}/threads/{thread_slug}/page.html"),
        Path(
            "src/elbysodic/web/pages/boards/{board_slug}/threads/{thread_slug}/posts/"
            "{post_id}/edit/page.html"
        ),
    ]

    for path in composer_paths:
        template = path.read_text(encoding="utf-8")
        assert '@submit="clearDraft()"' not in template
        assert '@submit="submitDraft()"' in template


def test_unknown_tenant_prefix_returns_not_found() -> None:
    async def run() -> None:
        app = _app()

        async with TestClient(app) as client:
            response = await client.get("/c/not-a-program/world")

        assert response.status == 404
        assert "We could not find that realm." in response.text
        assert "not-a-program is not a program on this studio network" in response.text
        assert "Open Studio Network" in response.text

    asyncio.run(run())


def test_tenant_prefix_does_not_wrap_app_global_routes() -> None:
    async def run() -> None:
        app = _app()

        async with TestClient(app) as client:
            login = await client.get("/c/x-men-apocalypse/login")
            health = await client.get("/c/x-men-apocalypse/health")
            static = await client.get("/c/x-men-apocalypse/elbysodic-static/elbysodic-theme.css")

        assert login.status == 404
        assert health.status == 404
        assert static.status == 404

    asyncio.run(run())


def test_boosted_main_navigation_uses_chirp_shell_outlet() -> None:
    async def run() -> None:
        app = _app()

        async with TestClient(app) as client:
            response = await client.get(
                "/wanted/brotherhood-rival-for-rogue",
                headers={
                    "HX-Request": "true",
                    "HX-Boosted": "true",
                    "HX-Target": "main",
                },
            )

        assert response.status == 200
        assert 'id="page-content"' in response.text
        assert 'id="page-root"' in response.text
        assert "HX-Reselect" not in response.headers

    asyncio.run(run())


def test_shell_brand_navigation_uses_full_boundary_navigation() -> None:
    async def run() -> None:
        app = _app()

        async with TestClient(app) as client:
            response = await client.get("/boards/cerebro")

        assert response.status == 200
        brand_link = re.search(
            r'<a href="/"[^>]*class="[^"]*elbysodic-community-brand[^"]*"[^>]*>',
            response.text,
        )
        assert brand_link is not None
        assert 'hx-boost="false"' in brand_link.group(0)

    asyncio.run(run())


def test_tenant_prefixed_boosted_main_navigation_keeps_links_in_chirp_shell_outlet() -> None:
    async def run() -> None:
        app = _app()

        async with TestClient(app) as client:
            response = await client.get(
                "/c/jurassic-park-universe/boards/paddock-twelve",
                headers={
                    "HX-Request": "true",
                    "HX-Boosted": "true",
                    "HX-Target": "main",
                },
            )

        assert response.status == 200
        assert 'id="page-content"' in response.text
        assert 'id="page-root"' in response.text
        assert 'href="/c/jurassic-park-universe/boards/paddock-twelve/threads/new"' in response.text
        assert "HX-Reselect" not in response.headers

    asyncio.run(run())


def test_tenant_prefixed_identity_and_casting_routes_scope_rendered_links() -> None:
    async def run() -> None:
        app = _app()
        community_slug = get_services().seed.community.slug

        async with TestClient(app) as client:
            character = await client.get(f"/c/{community_slug}/characters/rogue")
            wanted = await client.get(f"/c/{community_slug}/wanted/brotherhood-rival-for-rogue")
            application = await client.get(f"/c/{community_slug}/applications/new")

        assert character.status == 200
        assert "Rogue" in character.text
        assert f'href="/c/{community_slug}/my/threads?character=rogue"' in character.text
        assert f'href="/c/{community_slug}/wanted/brotherhood-rival-for-rogue"' in character.text

        assert wanted.status == 200
        assert "Brotherhood rival from Rogue" in wanted.text
        assert f'href="/c/{community_slug}/characters/rogue"' in wanted.text
        assert (
            f'name="next" value="/c/{community_slug}/wanted/brotherhood-rival-for-rogue"'
            in wanted.text
        )

        assert application.status == 200
        assert "Start Application" in application.text
        assert "Create draft face" in application.text
        assert f'href="/c/{community_slug}/applications"' in application.text
        assert 'href="/elbysodic-static/elbysodic-theme.css' in application.text
        assert f'href="/c/{community_slug}/elbysodic-static' not in application.text

    asyncio.run(run())


def test_tenant_prefixed_thread_routes_scope_composer_redirects() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        community_slug = services.seed.community.slug
        character = services.viewer().current_character
        assert character is not None

        async with TestClient(app) as client:
            thread = await client.get(
                f"/c/{community_slug}/boards/danger-room/threads/sentinel-drill"
            )
            composer = await client.get(f"/c/{community_slug}/boards/danger-room/threads/new")
            created = await client.post(
                f"/c/{community_slug}/boards/danger-room/threads/new",
                body=urlencode(
                    {
                        "character_id": str(character.id),
                        "title": "Tenant Prefix Drill",
                        "status": "active",
                        "location": "Danger Room",
                        "timeline": "After class",
                        "summary": "A prefixed composer regression.",
                        "posting_mode": "freeform",
                        "body": "Opening from a tenant-prefixed composer.",
                    }
                ).encode(),
                headers=_FORM,
            )

        assert thread.status == 200
        assert "Sentinel drill after midnight" in thread.text
        assert f'href="/c/{community_slug}/boards/danger-room"' in thread.text
        assert (
            f'name="next" value="/c/{community_slug}/boards/danger-room/threads/sentinel-drill"'
            in thread.text
        )

        assert composer.status == 200
        assert "Start thread" in composer.text
        assert f'href="/c/{community_slug}/boards/danger-room"' in composer.text
        assert f"/c/{community_slug}/mentionables/search" in composer.text

        assert created.status == 302
        assert _response_header(created, "location").startswith(
            f"/c/{community_slug}/boards/danger-room/threads/tenant-prefix-drill#post-"
        )

    asyncio.run(run())


def test_identity_switcher_persists_dev_membership_cookie() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        network_option = next(
            option
            for option in services.viewer().identity_options
            if option.community.slug == "hp-universe"
        )

        async with TestClient(app) as client:
            before = await client.get("/notifications")
            switch = await client.post(
                "/identity",
                body=urlencode(
                    {
                        "intent": "switch_membership",
                        "membership_id": str(network_option.membership.id),
                        "character_id": "0",
                        "next": "/notifications",
                    }
                ).encode(),
                headers=_FORM,
            )
            set_cookie = _response_header(switch, "set-cookie")
            cookie = set_cookie.split(";", 1)[0]
            after = await client.get("/notifications", headers={"Cookie": cookie})

        assert before.status == 200
        assert "X-Men Universe" not in before.text
        assert "HP Universe" in before.text
        assert "Jurassic Park Universe" in before.text
        assert "RL NYC" in before.text
        assert "RL Small Town" in before.text
        assert switch.status == 302
        assert "elbysodic_dev_identity=" in set_cookie
        assert after.status == 200
        assert '<span class="elbysodic-community-brand__name">HP Universe</span>' in after.text
        assert "Director in HP Universe" in after.text
        assert "playing as Rowan Ash" in after.text
        assert '<style id="elbysodic-program-theme">' in after.text
        assert "--chirpui-accent: #c8a6ff;" in after.text
        assert "--chirpui-ui-font-family: Georgia, serif;" in after.text

    asyncio.run(run())


def test_dev_personas_are_gated_by_development_tools() -> None:
    async def run() -> None:
        disabled_app = create_app(
            debug=False,
            services=create_services(path=":memory:"),
            dev_tools=False,
        )

        async with TestClient(disabled_app) as client:
            disabled = await client.get("/dev/personas")
        enabled_app = create_app(
            debug=False,
            services=create_services(path=":memory:"),
            dev_tools=True,
        )
        async with TestClient(enabled_app) as client:
            enabled = await client.get("/dev/personas")

        assert disabled.status == 404
        assert enabled.status == 200
        assert "Dev Personas" in enabled.text
        assert "xmen_staff" in enabled.text
        assert "HP director" in enabled.text
        assert "inactive" in enabled.text

    asyncio.run(run())


def test_seed_persona_matrix_names_multi_community_role_differences() -> None:
    services = create_services(path=":memory:")
    xmen_writer = resolve_seed_persona(services.repo, "xmen_writer")
    hp_director = resolve_seed_persona(services.repo, "hp_director")
    nyc_writer = resolve_seed_persona(services.repo, "nyc_writer")
    inactive = resolve_seed_persona(services.repo, "xmen_inactive")

    assert xmen_writer.user.id == hp_director.user.id == nyc_writer.user.id
    assert xmen_writer.community.slug == "x-men-apocalypse"
    assert xmen_writer.role.name == "Member"
    assert not xmen_writer.role.is_admin
    assert hp_director.community.slug == "hp-universe"
    assert hp_director.role.name == "Director"
    assert hp_director.role.is_admin
    assert nyc_writer.community.slug == "rl-nyc"
    assert nyc_writer.role.name == "Member"
    assert not nyc_writer.role.is_admin
    assert inactive.membership.username == "sleepingstar"
    assert not inactive.membership.is_active
    assert inactive.character is not None
    assert inactive.character.name == "Sleeping Star"


def test_dev_persona_switcher_can_change_seeded_user_and_membership() -> None:
    async def run() -> None:
        app = create_app(
            debug=False,
            services=create_services(path=":memory:"),
            dev_tools=True,
        )

        async with TestClient(app) as client:
            page = await client.get("/dev/personas")
            switch = await client.post(
                "/dev/personas",
                body=urlencode(
                    {
                        "persona_key": "xmen_staff",
                        "next": "/studio",
                    }
                ).encode(),
                headers=_FORM,
            )
            set_cookie = _response_header(switch, "set-cookie")
            cookie = set_cookie.split(";", 1)[0]
            studio = await client.get("/studio", headers={"Cookie": cookie})

        assert page.status == 200
        assert "X-Men staff" in page.text
        assert switch.status == 302
        assert _response_header(switch, "location") == "/studio"
        assert "elbysodic_dev_identity=" in set_cookie
        assert "HttpOnly" in set_cookie
        assert "SameSite=lax" in set_cookie
        assert studio.status == 200
        assert "Staff in X-Men Apocalypse" in studio.text
        assert "playing as Moira MacTaggert" in studio.text
        assert "Save theme tokens" in studio.text
        assert "Director Studio is visible as a preview" not in studio.text

    asyncio.run(run())


def test_dev_persona_switcher_refuses_inactive_seed_persona() -> None:
    async def run() -> None:
        app = create_app(
            debug=False,
            services=create_services(path=":memory:"),
            dev_tools=True,
        )

        async with TestClient(app) as client:
            response = await client.post(
                "/dev/personas",
                body=urlencode(
                    {
                        "persona_key": "xmen_inactive",
                        "next": "/members",
                    }
                ).encode(),
                headers=_FORM,
            )

        assert response.status == 403

    asyncio.run(run())


def test_login_route_creates_account_session_and_membership_context() -> None:
    async def run() -> None:
        app = create_app(
            debug=False,
            services=create_services(path=":memory:"),
            dev_tools=True,
        )

        async with TestClient(app) as client:
            page = await client.get("/login?next=/studio")
            login = await client.post(
                "/login",
                body=urlencode(
                    {
                        "email": "moira@example.com",
                        "password": "password",
                        "next": "/studio",
                    }
                ).encode(),
                headers=_FORM,
            )
            set_cookies = _response_headers(login, "set-cookie")
            cookie_header = "; ".join(cookie.split(";", 1)[0] for cookie in set_cookies)
            studio = await client.get("/studio", headers={"Cookie": cookie_header})

        assert page.status == 200
        assert "Seed accounts use password" in page.text
        assert login.status == 302
        assert _response_header(login, "location") == "/studio"
        assert any(cookie.startswith("elbysodic_session=") for cookie in set_cookies)
        assert any(cookie.startswith("elbysodic_dev_identity=") for cookie in set_cookies)
        assert studio.status == 200
        assert "Staff in X-Men Apocalypse" in studio.text
        assert "Save theme tokens" in studio.text

    asyncio.run(run())


def test_session_user_overrides_forged_dev_identity_cookie() -> None:
    async def run() -> None:
        app = create_app(
            debug=False,
            services=create_services(path=":memory:"),
            dev_tools=True,
        )
        services = get_services()
        community = services.seed.community
        moira = services.repo.get_membership_by_username(community.id, "moira")

        async with TestClient(app) as client:
            login = await client.post(
                "/login",
                body=urlencode(
                    {
                        "email": "writer@example.com",
                        "password": "password",
                        "next": "/studio",
                    }
                ).encode(),
                headers=_FORM,
            )
            session_cookie = next(
                cookie.split(";", 1)[0]
                for cookie in _response_headers(login, "set-cookie")
                if cookie.startswith("elbysodic_session=")
            )
            forged_identity = f"elbysodic_dev_identity={community.id}:{moira.user_id}:{moira.id}"
            studio = await client.get(
                "/studio",
                headers={"Cookie": f"{session_cookie}; {forged_identity}"},
            )

        assert studio.status == 200
        assert "Member in X-Men Apocalypse" in studio.text
        assert "Director Studio is visible as a preview" in studio.text
        assert "Staff in X-Men Apocalypse" not in studio.text

    asyncio.run(run())


def test_logout_revokes_session_and_clears_identity_cookies() -> None:
    async def run() -> None:
        app = create_app(
            debug=False,
            services=create_services(path=":memory:"),
            dev_tools=True,
        )

        async with TestClient(app) as client:
            login = await client.post(
                "/login",
                body=urlencode(
                    {
                        "email": "moira@example.com",
                        "password": "password",
                        "next": "/studio",
                    }
                ).encode(),
                headers=_FORM,
            )
            cookie_header = "; ".join(
                cookie.split(";", 1)[0] for cookie in _response_headers(login, "set-cookie")
            )
            logout = await client.get("/logout", headers={"Cookie": cookie_header})

        set_cookies = _response_headers(logout, "set-cookie")
        assert logout.status == 302
        assert _response_header(logout, "location") == "/login"
        assert any(
            cookie.startswith("elbysodic_session=") and "Max-Age=0" in cookie
            for cookie in set_cookies
        )
        assert any(
            cookie.startswith("elbysodic_dev_identity=") and "Max-Age=0" in cookie
            for cookie in set_cookies
        )

    asyncio.run(run())


def test_stale_dev_identity_cookie_falls_back_to_membership_for_program() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        community = services.repo.get_community_by_slug("jurassic-park-universe")
        stale_cookie = f"elbysodic_dev_identity={community.id}:1:999999"

        async with TestClient(app) as client:
            response = await client.get("/applications", headers={"Cookie": stale_cookie})

        assert response.status == 200
        assert (
            '<span class="elbysodic-community-brand__name">Jurassic Park Universe</span>'
            in response.text
        )
        assert '<style id="elbysodic-program-theme">' in response.text
        assert "--chirpui-accent: #6bbf7a;" in response.text

    asyncio.run(run())


def test_product_shell_does_not_inherit_current_program_theme() -> None:
    async def run() -> None:
        app = create_app(
            debug=False,
            services=create_services(path=":memory:"),
            dev_tools=True,
        )
        services = get_services()
        hp = services.repo.get_community_by_slug("hp-universe")
        hp_membership = services.repo.get_membership_for_user(hp.id, 1)
        cookie = f"elbysodic_dev_identity={hp.id}:1:{hp_membership.id}"

        async with TestClient(app) as client:
            network = await client.get("/network", headers={"Cookie": cookie})
            community = await client.get("/notifications", headers={"Cookie": cookie})

        assert network.status == 200
        assert community.status == 200
        assert "--chirpui-accent: #c8a6ff;" not in _style_block(
            network.text, "elbysodic-program-theme"
        )
        assert "--chirpui-sidebar-width: 0rem;" in _style_block(
            network.text, "elbysodic-product-shell"
        )
        assert "--chirpui-accent: #c8a6ff;" in _style_block(
            community.text, "elbysodic-program-theme"
        )
        assert "--chirpui-sidebar-width: 0rem;" not in _style_block(
            community.text, "elbysodic-product-shell"
        )

    asyncio.run(run())


def test_boosted_shell_navigation_carries_theme_boundary_oob() -> None:
    async def run() -> None:
        app = create_app(
            debug=False,
            services=create_services(path=":memory:"),
            dev_tools=True,
        )
        services = get_services()
        hp = services.repo.get_community_by_slug("hp-universe")
        hp_membership = services.repo.get_membership_for_user(hp.id, 1)
        cookie = f"elbysodic_dev_identity={hp.id}:1:{hp_membership.id}"
        hx_headers = {
            "Cookie": cookie,
            "HX-Request": "true",
            "HX-Boosted": "true",
            "HX-Target": "main",
        }

        async with TestClient(app) as client:
            network = await client.get("/network", headers=hx_headers)
            community = await client.get("/notifications", headers=hx_headers)

        assert network.status == 200
        assert community.status == 200
        assert "--chirpui-accent: #c8a6ff;" not in _oob_block(
            network.text, "elbysodic-program-theme"
        )
        assert "--chirpui-sidebar-width: 0rem;" in _oob_block(
            network.text, "elbysodic-product-shell"
        )
        assert 'id="page-root" hx-boost="false"' in network.text
        assert "--chirpui-accent: #c8a6ff;" in _oob_block(community.text, "elbysodic-program-theme")
        assert "--chirpui-sidebar-width: 0rem;" not in _oob_block(
            community.text, "elbysodic-product-shell"
        )

    asyncio.run(run())


def test_application_room_for_other_program_renders_realm_recovery() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        hp = services.repo.get_community_by_slug("hp-universe")
        hp_membership = services.repo.get_membership_for_user(hp.id, 1)
        cookie = f"elbysodic_dev_identity={hp.id}:1:{hp_membership.id}"

        async with TestClient(app) as client:
            response = await client.get(
                "/applications/asha-bennett",
                headers={"Cookie": cookie},
            )

        assert response.status == 200
        assert '<span class="elbysodic-community-brand__name">HP Universe</span>' in response.text
        assert "That face lives in Jurassic Park Universe." in response.text
        assert "Switch to Jurassic Park Universe" in response.text
        assert 'name="next" value="/applications/asha-bennett"' in response.text
        assert 'href="/applications"' in response.text

    asyncio.run(run())


def test_cross_realm_character_url_renders_switchable_recovery() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        hp = services.repo.get_community_by_slug("hp-universe")
        hp_membership = services.repo.get_membership_for_user(hp.id, 1)
        cookie = f"elbysodic_dev_identity={hp.id}:1:{hp_membership.id}"

        async with TestClient(app) as client:
            response = await client.get(
                "/characters/asha-bennett",
                headers={"Cookie": cookie},
            )

        assert response.status == 200
        assert "That face lives in Jurassic Park Universe." in response.text
        assert 'name="next" value="/characters/asha-bennett"' in response.text
        assert "Open Roster" in response.text

    asyncio.run(run())


def test_cross_realm_character_recovery_ignores_inactive_faces() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        hosted, _user_id, inactive_membership_id, _character_id = _add_hosted_membership(
            services,
            slug="retired-program",
            user_id=services.seed.user.id,
            username="retired-realm",
        )
        services.repo.create_character(
            hosted.id,
            inactive_membership_id,
            "retired-cross-face",
            "Retired Cross Face",
        )
        services.repo.connection.execute(
            "UPDATE community_memberships SET is_active = 0 WHERE community_id = ? AND id = ?",
            (hosted.id, inactive_membership_id),
        )
        services.repo.connection.commit()

        async with TestClient(app) as client:
            response = await client.get("/characters/retired-cross-face")

        assert response.status == 200
        assert "That face is not in X-Men Apocalypse." in response.text
        assert "That face lives in Hosted Program." not in response.text
        assert "Switch to Hosted Program" not in response.text

    asyncio.run(run())


def test_cross_realm_material_url_renders_switchable_recovery() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        hp = services.repo.get_community_by_slug("hp-universe")
        hp_membership = services.repo.get_membership_for_user(hp.id, 1)
        cookie = f"elbysodic_dev_identity={hp.id}:1:{hp_membership.id}"

        async with TestClient(app) as client:
            response = await client.get(
                "/world/paddock-twelve-incident",
                headers={"Cookie": cookie},
            )

        assert response.status == 200
        assert "That world material lives in Jurassic Park Universe." in response.text
        assert 'name="next" value="/world/paddock-twelve-incident"' in response.text
        assert "Open Guidebook" in response.text

    asyncio.run(run())


def test_prefixed_cross_realm_recovery_switches_to_target_tenant() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        jurassic = services.repo.get_community_by_slug("jurassic-park-universe")
        jurassic_membership = services.repo.get_membership_for_user(
            jurassic.id,
            services.seed.user.id,
        )

        async with TestClient(app) as client:
            recovery = await client.get(
                f"/c/{services.seed.community.slug}/world/paddock-twelve-incident",
            )
            switch = await client.post(
                "/identity",
                body=urlencode(
                    {
                        "intent": "switch_membership",
                        "membership_id": str(jurassic_membership.id),
                        "character_id": "0",
                        "next": "/c/jurassic-park-universe/world/paddock-twelve-incident",
                    }
                ).encode(),
                headers=_FORM,
            )

        assert recovery.status == 200
        assert "That world material lives in Jurassic Park Universe." in recovery.text
        assert (
            'name="next" value="/c/jurassic-park-universe/world/paddock-twelve-incident"'
            in recovery.text
        )
        assert f'href="/c/{services.seed.community.slug}/world"' in recovery.text
        assert switch.status == 302
        assert (
            _response_header(switch, "location")
            == "/c/jurassic-park-universe/world/paddock-twelve-incident"
        )

    asyncio.run(run())


def test_identity_switch_sanitizes_cross_realm_next_url() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        hp = services.repo.get_community_by_slug("hp-universe")
        hp_membership = services.repo.get_membership_for_user(hp.id, 1)

        async with TestClient(app) as client:
            response = await client.post(
                "/identity",
                body=urlencode(
                    {
                        "intent": "switch_membership",
                        "membership_id": str(hp_membership.id),
                        "character_id": "0",
                        "next": "/applications/asha-bennett",
                    }
                ).encode(),
                headers=_FORM,
            )

        assert response.status == 302
        assert _response_header(response, "location") == "/applications"

    asyncio.run(run())


def test_network_directory_lists_programs_and_realm_entry_actions() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            response = await client.get("/network")

        assert response.status == 200
        assert "Explore Elbysodic" in response.text
        assert "Search worlds, wanted hooks, and writing lanes." in response.text
        assert "X-Men Apocalypse" in response.text
        assert "HP Universe" in response.text
        assert "Jurassic Park Universe" in response.text
        assert "RL NYC" in response.text
        assert "RL Small Town" in response.text
        assert "current realm" in response.text
        assert "playing as Rogue" in response.text
        assert response.text.count('name="intent" value="switch_membership"') >= 4
        assert 'name="next" value="/c/hp-universe"' in response.text
        assert "/applications/new" not in response.text
        assert "Start application" not in response.text
        assert 'name="next" value="/c/jurassic-park-universe"' in response.text
        assert 'class="elbysodic-network-card__realm-link"' in response.text
        assert 'aria-label="Enter Jurassic Park Universe"' in response.text
        assert 'class="elbysodic-network-card__icon-action' in response.text
        assert 'aria-label="Current event"' in response.text
        assert 'aria-label="Wanted hooks"' in response.text
        assert "elbysodic-network-card__tooltip" in response.text
        assert 'title="Wanted hooks"' not in response.text
        assert "elbysodic-network-search__control" in response.text
        assert "face you want to play next" in response.text
        assert "face you want to wear next" not in response.text
        assert "elbysodic-network-card__mark" in response.text
        assert "XMA" in response.text
        assert 'href="/c/jurassic-park-universe/characters" aria-label="3 faces"' in response.text
        assert 'href="/c/jurassic-park-universe/wanted" aria-label="2 wanted"' in response.text
        assert 'href="/c/jurassic-park-universe/plotting" aria-label="0 rooms"' in response.text
        assert 'href="/c/jurassic-park-universe/world/paddock-twelve-incident"' in response.text

    asyncio.run(run())


def test_network_explore_search_filters_programs() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            response = await client.get("/network?q=magic")

        assert response.status == 200
        assert 'value="magic"' in response.text
        assert "1</strong>\n  <span>realms found</span>" in response.text
        assert "HP Universe" in response.text

    asyncio.run(run())


def test_network_directory_enter_realm_sets_identity_cookie() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        hp = services.repo.get_community_by_slug("hp-universe")
        hp_membership = services.repo.get_membership_for_user(hp.id, 1)

        async with TestClient(app) as client:
            response = await client.post(
                "/identity",
                body=urlencode(
                    {
                        "intent": "switch_membership",
                        "membership_id": str(hp_membership.id),
                        "character_id": "0",
                        "next": "/c/hp-universe",
                    }
                ).encode(),
                headers=_FORM,
            )

        assert response.status == 302
        assert _response_header(response, "location") == "/c/hp-universe"
        assert "elbysodic_dev_identity=" in _response_header(response, "set-cookie")

    asyncio.run(run())


def test_identity_dropdown_switches_to_canonical_community_path() -> None:
    async def run() -> None:
        app = _app()
        community_slug = get_services().seed.community.slug

        async with TestClient(app) as client:
            response = await client.get(f"/c/{community_slug}")

        assert response.status == 200
        assert f'name="next" value="/c/{community_slug}"' in response.text
        assert 'name="next" value="/c/hp-universe"' in response.text
        assert 'name="next" value="/c/jurassic-park-universe"' in response.text
        assert 'name="next" value="/boards/' not in response.text

    asyncio.run(run())


def test_forum_pages_render_seeded_boards_and_thread() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            index = await client.get("/c/x-men-apocalypse")
            assert index.status == 200
            assert "X-Men Apocalypse" in index.text
            assert "Announcements" in index.text
            assert "Danger Room" in index.text
            assert "Staff Room" not in index.text
            assert "Latest" in index.text
            assert "Recent activity" in index.text
            assert "#post-" in index.text
            assert "/members/starlane" in index.text
            assert "Latest details:" in index.text
            assert "Relevant for Rogue:" in index.text
            assert "elbysodic-board-poster__face-signal-hint" in index.text
            assert "elbysodic-identity-menu" in index.text
            assert "elbysodic-identity-menu__notification-link" in index.text
            assert "elbysodic-identity-menu__theme-row" in index.text
            assert "playing as Rogue" in index.text
            assert "elbysodic-community-table" in index.text
            assert "elbysodic-community-row" in index.text
            assert "✉" in index.text
            assert "✏" in index.text
            assert "◉" in index.text
            assert "⟳" in index.text
            assert "elbysodic-activity-log" in index.text
            assert "elbysodic-activity-log-item" in index.text
            assert re.search(
                r">\s*(?:Today|Yesterday), \d{1,2}:\d{2} [AP]M\s*</time>",
                index.text,
            )
            assert re.search(
                r'<time class="elbysodic-activity-log-item__time"\s+datetime="[^"]+"\s+title="[A-Z][a-z]{2} \d{1,2}, 2026 \d{1,2}:\d{2} [AP]M UTC">',
                index.text,
            )
            assert _sidebar_board_count(index.text, "plotting") == 1

            board = await client.get("/boards/plotting")
            assert board.status == 200
            assert "Open thread roster" in board.text
            assert "Started by" in board.text
            assert "Latest" in board.text
            assert 'id="board-thread-region"' in board.text
            assert 'hx-target="#board-thread-region"' in board.text
            assert 'hx-swap="outerHTML show:none"' in board.text
            assert "chirpui-breadcrumbs" in board.text
            assert "chirpui-saved-view-strip" in board.text
            assert "chirpui-facet-chip" in board.text
            assert "First unread" in board.text
            assert "#post-" in board.text
            assert "new replies" in board.text
            assert "min read" in board.text
            assert "written by" in board.text
            assert "Next unread" in board.text
            assert "Magneto" in board.text

            thread = await client.get("/boards/plotting/threads/open-thread-roster")
            assert thread.status == 200
            assert 'id="post-' in thread.text
            assert "chirpui-thread-reader-layout" in thread.text
            assert "chirpui-breadcrumbs" in thread.text
            assert "Runtime" in thread.text
            assert "Credits" in thread.text
            assert "min read" in thread.text
            assert "Drop your available characters here" in thread.text
            assert "Rogue" in thread.text
            assert "Magneto" in thread.text
            assert "/members/starlane" in thread.text
            assert "caught up" in thread.text
            assert _sidebar_board_count(thread.text, "plotting") == 0

    asyncio.run(run())


def test_seeded_world_surfaces_place_hierarchy() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            index = await client.get("/c/x-men-apocalypse")
            assert index.status == 200
            assert "/boards/xavier-institute" in index.text
            assert "/boards/med-bay" in index.text
            assert "Locations" in index.text

            academy = await client.get("/boards/xavier-institute")
            assert academy.status == 200
            assert "Sublocations" in academy.text
            assert "Med Bay" in academy.text
            assert "Cerebro" in academy.text
            assert "Danger Room" in academy.text

            med_bay = await client.get("/boards/med-bay")
            assert med_bay.status == 200
            assert "Xavier Institute" in med_bay.text
            assert "Nearby locations" in med_bay.text
            assert "The med-bay lights stay on" in med_bay.text

    asyncio.run(run())


def test_root_renders_elbysodic_network_home_not_default_community() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            root = await client.get("/")

        assert root.status == 200
        assert '<span class="elbysodic-community-brand__name">Elbysodic</span>' in root.text
        assert "Studio Network" in root.text
        assert "Choose the realm you are writing in." in root.text
        assert 'aria-label="Community"' not in root.text
        assert 'class="chirpui-sidebar elbysodic-sidebar"' not in root.text
        assert 'href="/c/x-men-apocalypse"' in root.text
        assert "/elbysodic-static/seed-media/xmen-mark.svg" in root.text
        assert "/elbysodic-static/seed-media/xmen-hero.svg" in root.text

    asyncio.run(run())


def test_shell_groups_community_modes_in_topbar_and_context_in_sidebar() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            index = await client.get("/c/x-men-apocalypse")

            assert index.status == 200
            assert "/elbysodic-static/seed-media/xmen-mark.svg" in index.text
            assert 'alt="X-Men Apocalypse academy signal mark"' in index.text
            assert (
                '<span class="elbysodic-community-brand__name">X-Men Apocalypse</span>'
                in index.text
            )
            assert "Built on" in index.text
            assert "<strong>Elbysodic</strong>" in index.text
            assert 'href="/c/x-men-apocalypse"' in index.text
            assert 'href="/c/x-men-apocalypse/desk"' in index.text
            assert 'aria-label="Community"' in index.text
            assert 'aria-label="Global"' in index.text
            assert re.search(
                r'<nav class="elbysodic-topnav elbysodic-topnav--community"'
                r"[^>]*>(?P<body>.*?)</nav>",
                index.text,
                re.S,
            )
            assert ">Home</a>" not in index.text
            assert re.search(
                r'<a class="elbysodic-topnav__link"\s+href="/c/x-men-apocalypse/locations"[^>]*>World</a>',
                index.text,
            )
            assert re.search(
                r'<a class="elbysodic-topnav__link"\s+href="/network"[^>]*>Explore</a>',
                index.text,
            )
            topbar = re.search(
                r'<nav class="elbysodic-topnav elbysodic-topnav--global"[^>]*>(?P<body>.*?)</nav>',
                index.text,
                re.S,
            )
            assert topbar is not None
            assert 'href="/"' not in topbar.group("body")
            assert 'href="/world"' not in topbar.group("body")
            assert 'href="/wanted"' not in topbar.group("body")
            assert 'href="/desk"' not in topbar.group("body")
            assert 'href="/studio"' not in topbar.group("body")
            assert '<span class="chirpui-sidebar__section-title">In World</span>' in index.text
            assert '<span class="chirpui-sidebar__label">Locations</span>' in index.text
            assert '<span class="chirpui-sidebar__label">Guidebook</span>' in index.text
            assert '<span class="chirpui-sidebar__label">Community</span>' in index.text
            assert "elbysodic-mobile-realm-nav" not in index.text
            assert 'class="elbysodic-topnav__link" href="/notifications"' not in index.text

    asyncio.run(run())


def test_seeded_program_homepage_uses_community_media_and_world_status() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        hp = services.repo.get_community_by_slug("hp-universe")
        hp_membership = services.repo.get_membership_for_user(hp.id, 1)
        cookie = f"elbysodic_dev_identity={hp.id}:1:{hp_membership.id}"

        async with TestClient(app) as client:
            xmen = await client.get("/c/x-men-apocalypse")
            hp_home = await client.get("/c/hp-universe", headers={"Cookie": cookie})

        assert xmen.status == 200
        assert "elbysodic-world-hero--split" in xmen.text
        assert "/elbysodic-static/seed-media/xmen-hero.svg" in xmen.text
        assert 'alt="Snow-lit academy and B-24 signal lines"' in xmen.text
        assert "Current Event: B-24 Winter" in xmen.text
        assert "Iceman is infected with B-24" in xmen.text

        assert hp_home.status == 200
        assert "elbysodic-world-hero--poster" in hp_home.text
        assert "elbysodic-world-hero--focal-top" in hp_home.text
        assert "/elbysodic-static/seed-media/hp-mark.svg" in hp_home.text
        assert "/elbysodic-static/seed-media/hp-hero.svg" in hp_home.text
        assert 'alt="Glass staircase rising through castle stacks"' in hp_home.text
        assert "Current Event: No Reflection" in hp_home.text
        assert (
            "One student has gone missing, and every portrait remembers a different last sighting."
            in hp_home.text
        )
        assert "The school has reopened under a fragile truce" not in hp_home.text

    asyncio.run(run())


def test_new_realm_homepage_uses_quiet_sections_and_actionable_empty_states() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            response = await client.get("/c/rl-nyc")

        assert response.status == 200
        content = _page_content(response.text)
        assert "elbysodic-home-section-header" in content
        assert "chirpui-section-header" not in content
        assert "elbysodic-quiet-empty" in content
        assert "Your roster is caught up for now." in content
        assert "No scenes have opened here yet." in content
        assert 'href="/c/rl-nyc/boards/brooklyn/threads/new"' in content
        assert 'href="/c/rl-nyc/boards/queens-night-market/threads/new"' in content
        assert "Community Table" not in content
        assert "Recent activity" not in content

    asyncio.run(run())


def test_seeded_location_boards_have_media_throughlines() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        expected = {
            services.seed.community.slug: 6,
            "hp-universe": 3,
            "jurassic-park-universe": 4,
            "rl-nyc": 3,
            "rl-small-town": 4,
        }

        for community_slug, minimum in expected.items():
            community = repo.get_community_by_slug(community_slug)
            location_boards = [
                board
                for board in repo.list_boards(community.id)
                if board.board_kind == "location" and board.image_url
            ]
            assert len(location_boards) >= minimum
            assert all(board.image_alt for board in location_boards)
            assert all(
                board.image_url is not None
                and board.image_url.startswith("/elbysodic-static/seed-media/locations/")
                for board in location_boards
            )

        hp = repo.get_community_by_slug("hp-universe")
        hp_membership = repo.get_membership_for_user(hp.id, 1)
        hp_cookie = f"elbysodic_dev_identity={hp.id}:1:{hp_membership.id}"

        async with TestClient(app) as client:
            home = await client.get("/c/x-men-apocalypse")
            hp_home = await client.get("/c/hp-universe", headers={"Cookie": hp_cookie})
            xavier = await client.get("/boards/xavier-institute")

        assert home.status == 200
        assert "/elbysodic-static/seed-media/locations/xmen-xavier-institute.svg" in home.text
        assert 'alt="Snowbound academy windows under B-24 signal arcs"' in home.text
        assert hp_home.status == 200
        assert "/elbysodic-static/seed-media/locations/hp-castle-corridors.svg" in hp_home.text
        assert 'alt="Castle corridor with shifting stairs and portrait light"' in hp_home.text
        assert xavier.status == 200
        assert "/elbysodic-static/seed-media/locations/xmen-xavier-institute.svg" in xavier.text

    asyncio.run(run())


def test_seeded_location_media_does_not_overwrite_custom_board_media() -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    community = services.seed.community
    board = repo.get_board_by_slug(community.id, "xavier-institute")

    repo.update_board(
        community.id,
        board.id,
        name=board.name,
        description=board.description,
        sort_order=board.sort_order,
        parent_board_id=board.parent_board_id,
        board_kind=board.board_kind,
        sidebar_section=board.sidebar_section,
        tagline=board.tagline,
        image_url="https://example.test/custom-academy.jpg",
        image_alt="Custom academy image",
        is_private=board.is_private,
        navigation_order=board.navigation_order,
        show_in_navigation=board.show_in_navigation,
    )

    seed_demo_forum(repo)

    updated = repo.get_board_by_slug(community.id, "xavier-institute")
    assert updated.image_url == "https://example.test/custom-academy.jpg"
    assert updated.image_alt == "Custom academy image"


def test_text_first_board_media_treatment_keeps_image_out_of_public_stage() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        board = repo.get_board_by_slug(community.id, "xavier-institute")
        repo.update_board(
            community.id,
            board.id,
            name=board.name,
            description=board.description,
            sort_order=board.sort_order,
            parent_board_id=board.parent_board_id,
            board_kind=board.board_kind,
            sidebar_section=board.sidebar_section,
            tagline=board.tagline,
            image_url="https://example.test/text-first.jpg",
            image_alt="Text first image",
            image_treatment="text",
            image_focal_point="right",
            image_overlay="light",
            is_private=board.is_private,
            navigation_order=board.navigation_order,
            show_in_navigation=board.show_in_navigation,
        )

        async with TestClient(app) as client:
            page = await client.get("/boards/xavier-institute")

        assert page.status == 200
        assert "elbysodic-board-media-treatment--text" in page.text
        assert "elbysodic-board-media-focal--right" in page.text
        assert "elbysodic-board-media-overlay--light" in page.text
        assert 'src="https://example.test/text-first.jpg"' not in page.text

    asyncio.run(run())


def test_writer_desk_hub_keeps_meta_tools_reachable() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            desk = await client.get("/desk")

            assert desk.status == 200
            assert "Writer Desk" in desk.text
            assert "Lane's operating room" in desk.text
            assert "Writing as Rogue" in desk.text
            assert "What needs you" in desk.text
            assert "Face lanes" in desk.text
            assert "Work lanes" in desk.text
            assert "Needs reply" in desk.text
            assert "Unread watched" in desk.text
            assert "Waiting on others" in desk.text
            assert "Plotting rooms" in desk.text
            assert "playing as Rogue" in desk.text
            assert "Queue" in desk.text
            assert "Inbox" in desk.text
            assert "Roster" in desk.text
            assert "Discovery" in desk.text
            assert "/my/threads" in desk.text
            assert "/notifications" in desk.text
            assert "/characters" in desk.text
            assert "/applications" in desk.text
            assert "/casting" in desk.text
            assert "/discover" in desk.text

    asyncio.run(run())


def test_director_studio_surfaces_community_production_work() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            studio = await client.get("/studio")
            operations = await client.get("/studio/operations")

            assert studio.status == 200
            assert "Director Studio" in studio.text
            assert "Shape X-Men Apocalypse" in studio.text
            assert "Studio rooms" in studio.text
            assert 'href="/studio/operations"' in studio.text
            assert "Daily director console" in studio.text
            assert 'href="#world-structure"' in studio.text
            assert 'href="#navigation"' in studio.text
            assert 'href="#identity-appearance"' in studio.text
            assert 'href="#casting-applications"' in studio.text
            assert 'href="#continuity-events"' in studio.text
            assert 'id="world-structure"' in studio.text
            assert 'id="navigation"' in studio.text
            assert 'id="identity-appearance"' in studio.text
            assert 'id="casting-applications"' in studio.text
            assert 'id="continuity-events"' in studio.text
            assert "Boards and places" in studio.text
            assert "Sidebar composer" in studio.text
            assert "Appearance vocabulary" in studio.text
            assert "World Bible" in studio.text
            assert "Location Studio" in studio.text
            assert "Event Studio" in studio.text
            assert "Applications and hooks" in studio.text
            assert "Board taxonomy" in studio.text
            assert "Navigation composer" in studio.text
            assert "Sidebar section settings" in studio.text
            assert "Navigation Health" in studio.text
            assert "Navigation is coherent right now." in studio.text
            assert "World sidebar" in studio.text
            assert "Desk sidebar" in studio.text
            assert "Studio sidebar" in studio.text
            assert "Casting sidebar" in studio.text
            assert "App-owned" in studio.text
            assert "Board-derived" in studio.text
            assert "Material-derived" in studio.text
            assert "Identity-derived" in studio.text
            assert "Wanted-derived" in studio.text
            assert "Community board" in studio.text
            assert "Sublocation" in studio.text
            assert "Announcements" in studio.text
            assert "Classify each board" in studio.text
            assert 'href="/studio#board-taxonomy"' in studio.text
            assert 'href="/studio#navigation-composer"' in studio.text
            assert 'href="/studio/boards/announcements"' in studio.text
            assert 'href="/world/b-24-winter"' in studio.text
            assert 'href="/applications"' in studio.text
            assert 'href="/wanted"' in studio.text
            assert "Current Event" in studio.text
            assert operations.status == 200
            assert "Director Operations" in operations.text
            assert "What needs a director?" in operations.text
            assert "Review queue" in operations.text
            assert "Claim conflicts" in operations.text
            assert "Active reserves" in operations.text
            assert "Hooks with movement" in operations.text
            assert "Staff notifications" in operations.text
            assert "Production health" in operations.text
            assert "Draft materials" in operations.text
            assert "Dry-run intake" in operations.text
            assert "Release smoke" in operations.text
            assert "Log in, enter a realm, and switch memberships." in operations.text
            assert 'href="/studio/intake#program-blueprint-preview"' in operations.text
            assert 'href="/network"' in operations.text
            assert "Application Triage" in operations.text
            assert 'href="/applications"' in operations.text
            assert 'href="/casting"' in operations.text
            assert 'href="/notifications"' in operations.text

    asyncio.run(run())


def test_studio_operations_hides_review_queue_from_non_staff_members() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        community = services.seed.community
        member_role = repo.get_role_by_slug(community.id, "member")
        applicant_user = repo.create_user("privacy-applicant@example.com", "hash")
        applicant_membership = repo.create_membership(
            community.id,
            applicant_user.id,
            member_role.id,
            "privacy-applicant",
            "Privacy Applicant",
        )
        applicant_face = repo.create_character(
            community.id,
            applicant_membership.id,
            "privacy-queue-face",
            "Privacy Queue Face",
            summary="A submitted face that only staff should triage.",
            application_status="draft",
        )
        application = repo.ensure_character_application(community.id, applicant_face.id)
        repo.update_character_application_draft(
            community.id,
            application.id,
            title="Privacy Queue Face",
            summary="A submitted face that only staff should triage.",
            body="Private application body should not leak through Studio operations.",
        )
        repo.transition_character_application_status(
            community.id,
            application.id,
            status="submitted",
            actor_membership_id=applicant_membership.id,
            actor_character_id=applicant_face.id,
            note="Submitted for director review.",
        )

        member_services, _character_id = _outsider_services(
            services,
            prefix="studio-operations-member",
        )
        member_app = create_app(debug=False, services=member_services)
        async with TestClient(member_app) as member_client:
            member_operations = await member_client.get("/studio/operations")

        alex_membership = repo.get_membership_by_username(community.id, "alex")
        alex_user = repo.get_user(alex_membership.user_id)
        cyclops = repo.get_character_by_slug(community.id, "cyclops")
        staff_app = create_app(
            debug=False,
            services=AppServices(repo, DemoSeed(community, alex_user, alex_membership, cyclops)),
        )
        async with TestClient(staff_app) as staff_client:
            staff_operations = await staff_client.get("/studio/operations")

        assert member_operations.status == 200
        assert "read-only" in member_operations.text
        assert "Privacy Queue Face" not in member_operations.text
        assert "Private application body should not leak" not in member_operations.text
        assert "0 ready apps" in member_operations.text
        assert staff_operations.status == 200
        assert "Privacy Queue Face - ready" in staff_operations.text
        assert "ready apps" in staff_operations.text

    asyncio.run(run())


def test_studio_intake_previews_program_blueprint_yaml_without_hydration() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        community = repo.get_community(services.seed.community.id)
        user = repo.get_user_by_email("moira@example.com")
        membership = repo.get_membership_by_username(community.id, "moira")
        character = repo.get_character_by_slug(community.id, "moira-mactaggert")
        admin_services = AppServices(
            repo,
            DemoSeed(community, user, membership, character),
        )
        app = create_app(debug=False, services=admin_services)
        before_count = repo.connection.execute(
            "SELECT COUNT(*) FROM communities",
        ).fetchone()[0]
        blueprint_yaml = """
elbysodic_blueprint: 1
program:
  slug: rl-small-town-preview
  name: RL Small Town Preview
  role:
    slug: director
    name: Director
    is_admin: true
characters:
  - slug: june-calloway
    name: June Calloway
    summary: Florist and town council note-taker.
boards:
  - slug: main-street
    name: Main Street
    kind: location
    tagline: One stoplight, twelve opinions.
    description: The town's public spine.
materials:
  - slug: premise
    title: Premise
    type: premise
    summary: A small-town ensemble.
    body: Founder's Week should be a cozy pressure cooker.
wanted:
  - slug: returning-sibling
    title: Returning sibling
    type: relationship
    related_material: premise
    summary: A homecoming character with history.
    body: Someone left, came back, and knows where the deed is hidden.
appearance:
  post_style:
    profile_variant: poster
    accent_style: line
    border_style: hairline
    title_style: serif
    density: calm
  material_variants:
    premise: chapter
"""

        async with TestClient(app) as client:
            page = await client.get("/studio/intake")
            response = await client.post(
                "/studio/intake",
                body=urlencode(
                    {
                        "intent": "preview_blueprint",
                        "blueprint_yaml": blueprint_yaml,
                    }
                ).encode(),
                headers=_FORM,
            )

        assert page.status == 200
        assert "Dry-run YAML intake" in page.text
        assert response.status == 200
        assert "valid dry run" in response.text
        assert "1 program" in response.text
        assert "1 starter faces" in response.text
        assert "1 scene hubs" in response.text
        assert "1 materials" in response.text
        assert "1 wanted hooks" in response.text
        assert "1 appearance" in response.text
        assert "postbit: poster rail, hairline frame; 1 guidebook variants" in response.text
        assert "Hydration diff preview" in response.text
        assert "create</strong> program: RL Small Town Preview" in response.text
        assert "create</strong> scene hub: Main Street" in response.text
        assert "create</strong> wanted hook: Returning sibling" in response.text
        assert "Hydration gate: nothing has been applied." in response.text
        assert "duplicate handling, ownership defaults, rollback behavior" in response.text
        after_count = repo.connection.execute(
            "SELECT COUNT(*) FROM communities",
        ).fetchone()[0]
        assert after_count == before_count

    asyncio.run(run())


def test_director_studio_updates_sidebar_section_language() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        community = repo.get_community(services.seed.community.id)
        user = repo.get_user_by_email("moira@example.com")
        membership = repo.get_membership_by_username(community.id, "moira")
        character = repo.get_character_by_slug(community.id, "moira-mactaggert")
        admin_services = AppServices(
            repo,
            DemoSeed(community, user, membership, character),
        )
        app = create_app(debug=False, services=admin_services)

        async with TestClient(app) as client:
            response = await client.post(
                "/studio",
                body=urlencode(
                    {
                        "intent": "sidebar_section",
                        "section_key": "locations",
                        "label": "Realms",
                        "description": "The board's playable map language.",
                        "sort_order": 3,
                        "show_label": "on",
                    }
                ).encode(),
                headers=_FORM,
            )

            assert response.status == 302
            section = repo.get_sidebar_section(community.id, "locations")
            assert section.label == "Realms"
            assert section.description == "The board's playable map language."
            assert section.sort_order == 3
            assert section.show_label is True

            locations = await client.get("/locations")
            assert locations.status == 200
            assert 'class="chirpui-sidebar__section-title">Realms</span>' in locations.text
            assert re.search(
                r'<a class="[^"]*elbysodic-sidebar-destination[^"]*"'
                r'[^>]*href="/locations"[^>]*>\s*'
                r'<span class="chirpui-sidebar__icon">[^<]+</span>\s*'
                r'<span class="chirpui-sidebar__label">Realms</span>',
                locations.text,
            )

            studio = await client.get("/studio")
            assert studio.status == 200
            assert "playable map language" in studio.text
            assert "Realms" in studio.text

    asyncio.run(run())


def test_navigation_health_flags_confusing_sidebar_shapes() -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    community = repo.get_community(services.seed.community.id)
    xavier = repo.get_board_by_slug(community.id, "xavier-institute")
    med_bay = repo.get_board_by_slug(community.id, "med-bay")
    announcements = repo.get_board_by_slug(community.id, "announcements")
    staff_room = repo.get_board_by_slug(community.id, "staff-room")

    repo.update_board(
        community.id,
        xavier.id,
        name=xavier.name,
        description=xavier.description,
        sort_order=xavier.sort_order,
        parent_board_id=xavier.parent_board_id,
        board_kind=xavier.board_kind,
        sidebar_section=xavier.sidebar_section,
        tagline=xavier.tagline,
        image_url=xavier.image_url,
        image_alt=xavier.image_alt,
        is_private=xavier.is_private,
        navigation_order=xavier.navigation_order,
        show_in_navigation=False,
    )
    repo.update_board(
        community.id,
        med_bay.id,
        name=med_bay.name,
        description=med_bay.description,
        sort_order=med_bay.sort_order,
        parent_board_id=med_bay.parent_board_id,
        board_kind=med_bay.board_kind,
        sidebar_section="community",
        tagline=med_bay.tagline,
        image_url=med_bay.image_url,
        image_alt=med_bay.image_alt,
        is_private=med_bay.is_private,
        navigation_order=med_bay.navigation_order,
        show_in_navigation=True,
    )
    repo.update_board(
        community.id,
        announcements.id,
        name=announcements.name,
        description=announcements.description,
        sort_order=announcements.sort_order,
        parent_board_id=announcements.parent_board_id,
        board_kind=announcements.board_kind,
        sidebar_section="locations",
        tagline=announcements.tagline,
        image_url=announcements.image_url,
        image_alt=announcements.image_alt,
        is_private=True,
        navigation_order=announcements.navigation_order,
        show_in_navigation=True,
    )
    repo.update_board(
        community.id,
        staff_room.id,
        name=staff_room.name,
        description=staff_room.description,
        sort_order=staff_room.sort_order,
        parent_board_id=staff_room.parent_board_id,
        board_kind=staff_room.board_kind,
        sidebar_section="studio",
        tagline=staff_room.tagline,
        image_url=staff_room.image_url,
        image_alt=staff_room.image_alt,
        is_private=False,
        navigation_order=staff_room.navigation_order,
        show_in_navigation=True,
    )
    repo.update_sidebar_section(
        community.id,
        "studio",
        label="Director Studio",
        description="Director lanes.",
        sort_order=20,
        show_label=True,
    )

    user = repo.get_user_by_email("moira@example.com")
    membership = repo.get_membership_by_username(community.id, "moira")
    character = repo.get_character_by_slug(community.id, "moira-mactaggert")
    admin_services = AppServices(
        repo,
        DemoSeed(community, user, membership, character),
    )
    studio = admin_services.director_studio()
    titles = {warning.title for warning in studio.navigation_warnings}

    assert "Hidden parent with visible children" in titles
    assert "Visible child under hidden parent" in titles
    assert "Place outside the map" in titles
    assert "Community board in the location map" in titles
    assert "Private board in a public-facing section" in titles
    assert "Public board in Studio" in titles
    assert studio.navigation_attention_count == 1
    assert studio.navigation_warning_count >= 4
    assert studio.navigation_note_count >= 1


def test_director_studio_updates_board_taxonomy() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        community = repo.get_community(services.seed.community.id)
        user = repo.get_user_by_email("moira@example.com")
        membership = repo.get_membership_by_username(community.id, "moira")
        character = repo.get_character_by_slug(community.id, "moira-mactaggert")
        admin_services = AppServices(
            repo,
            DemoSeed(community, user, membership, character),
        )
        app = create_app(debug=False, services=admin_services)
        announcements = repo.get_board_by_slug(community.id, "announcements")
        xavier = repo.get_board_by_slug(community.id, "xavier-institute")

        async with TestClient(app) as client:
            response = await client.post(
                "/studio",
                body=urlencode(
                    {
                        "intent": "board_taxonomy",
                        "board_id": announcements.id,
                        "board_kind": "sublocation",
                        "parent_board_id": xavier.id,
                        "navigation_order": 99,
                        "show_in_navigation": "on",
                    }
                ).encode(),
                headers=_FORM,
            )

            assert response.status == 302
            updated = repo.get_board(community.id, announcements.id)
            assert updated.board_kind == "sublocation"
            assert updated.parent_board_id == xavier.id
            assert updated.sidebar_section == "locations"
            assert updated.navigation_order == 99
            assert updated.show_in_navigation is True

            invalid = await client.post(
                "/studio",
                body=urlencode(
                    {
                        "intent": "board_taxonomy",
                        "board_id": announcements.id,
                        "board_kind": "sublocation",
                        "parent_board_id": "",
                        "navigation_order": 99,
                        "show_in_navigation": "on",
                    }
                ).encode(),
                headers=_FORM,
            )

            assert invalid.status == 200
            assert "choose a parent location for sublocations" in invalid.text

    asyncio.run(run())


def test_director_studio_hides_board_from_navigation_without_hiding_route() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        community = repo.get_community(services.seed.community.id)
        user = repo.get_user_by_email("moira@example.com")
        membership = repo.get_membership_by_username(community.id, "moira")
        character = repo.get_character_by_slug(community.id, "moira-mactaggert")
        admin_services = AppServices(
            repo,
            DemoSeed(community, user, membership, character),
        )
        app = create_app(debug=False, services=admin_services)
        announcements = repo.get_board_by_slug(community.id, "announcements")

        async with TestClient(app) as client:
            response = await client.post(
                "/studio",
                body=urlencode(
                    {
                        "intent": "board_taxonomy",
                        "board_id": announcements.id,
                        "board_kind": "community",
                        "parent_board_id": "",
                        "navigation_order": 40,
                    }
                ).encode(),
                headers=_FORM,
            )

            assert response.status == 302
            updated = repo.get_board(community.id, announcements.id)
            assert updated.show_in_navigation is False
            assert updated.navigation_order == 40
            assert updated.sidebar_section == "community"

            community_page = await client.get("/community")
            assert community_page.status == 200
            assert not re.search(
                r'<a class="[^"]*elbysodic-sidebar-link[^"]*"'
                r' href="/boards/announcements"',
                community_page.text,
            )

            board_page = await client.get("/boards/announcements")
            assert board_page.status == 200
            assert "Announcements" in board_page.text

    asyncio.run(run())


def test_studio_board_editor_updates_board_identity_and_navigation() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        community = repo.get_community(services.seed.community.id)
        user = repo.get_user_by_email("moira@example.com")
        membership = repo.get_membership_by_username(community.id, "moira")
        character = repo.get_character_by_slug(community.id, "moira-mactaggert")
        admin_services = AppServices(
            repo,
            DemoSeed(community, user, membership, character),
        )
        app = create_app(debug=False, services=admin_services)
        xavier = repo.get_board_by_slug(community.id, "xavier-institute")

        async with TestClient(app) as client:
            editor = await client.get("/studio/boards/announcements")
            assert editor.status == 200
            assert "Board editor" in editor.text
            assert "Edit Announcements" in editor.text
            assert "Show in sidebar navigation" in editor.text
            assert "Sidebar placement" in editor.text
            assert "Image treatment" in editor.text
            assert "Image focal point" in editor.text
            assert "Overlay strength" in editor.text
            assert "Composer effect" in editor.text

            response = await client.post(
                "/studio/boards/announcements",
                body=urlencode(
                    {
                        "name": "Director Notices",
                        "board_kind": "sublocation",
                        "parent_board_id": xavier.id,
                        "tagline": "What changed, and why.",
                        "description": "Formal staff notices for the current continuity.",
                        "image_url": "https://example.test/notices.jpg",
                        "image_alt": "Notice board under red light",
                        "image_treatment": "background",
                        "image_focal_point": "top",
                        "image_overlay": "heavy",
                        "sort_order": 12,
                        "navigation_order": 7,
                        "sidebar_section": "locations",
                        "show_in_navigation": "on",
                        "is_private": "on",
                    }
                ).encode(),
                headers=_FORM,
            )
            board_page = await client.get("/boards/announcements")
            parent_page = await client.get("/boards/xavier-institute")
            editor_after = await client.get("/studio/boards/announcements")

            assert response.status == 302
            assert dict(response.headers)["location"] == "/studio/boards/announcements"
            updated = repo.get_board_by_slug(community.id, "announcements")
            assert updated.name == "Director Notices"
            assert updated.board_kind == "sublocation"
            assert updated.parent_board_id == xavier.id
            assert updated.tagline == "What changed, and why."
            assert updated.description == "Formal staff notices for the current continuity."
            assert updated.image_url == "https://example.test/notices.jpg"
            assert updated.image_alt == "Notice board under red light"
            assert updated.image_treatment == "background"
            assert updated.image_focal_point == "top"
            assert updated.image_overlay == "heavy"
            assert updated.sort_order == 12
            assert updated.navigation_order == 7
            assert updated.sidebar_section == "locations"
            assert updated.show_in_navigation is True
            assert updated.is_private is True
            assert board_page.status == 200
            assert 'src="https://example.test/notices.jpg"' in board_page.text
            assert 'alt="Notice board under red light"' in board_page.text
            assert "elbysodic-board-media-treatment--background" in board_page.text
            assert "elbysodic-board-media-focal--top" in board_page.text
            assert "elbysodic-board-media-overlay--heavy" in board_page.text
            assert "url('https://example.test/notices.jpg')" not in board_page.text
            assert parent_page.status == 200
            assert 'src="https://example.test/notices.jpg"' in parent_page.text
            assert 'alt="Notice board under red light"' in parent_page.text
            assert editor_after.status == 200
            assert 'src="https://example.test/notices.jpg"' in editor_after.text
            assert 'alt="Notice board under red light"' in editor_after.text
            assert 'option value="background" selected' in editor_after.text
            assert 'option value="top" selected' in editor_after.text
            assert 'option value="heavy" selected' in editor_after.text

    asyncio.run(run())


def test_studio_board_editor_requires_alt_text_for_board_media() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        community = repo.get_community(services.seed.community.id)
        user = repo.get_user_by_email("moira@example.com")
        membership = repo.get_membership_by_username(community.id, "moira")
        character = repo.get_character_by_slug(community.id, "moira-mactaggert")
        admin_services = AppServices(
            repo,
            DemoSeed(community, user, membership, character),
        )
        app = create_app(debug=False, services=admin_services)

        async with TestClient(app) as client:
            response = await client.post(
                "/studio/boards/announcements",
                body=urlencode(
                    {
                        "name": "Announcements",
                        "board_kind": "community",
                        "parent_board_id": "",
                        "tagline": "Staff notes.",
                        "description": "Formal staff notices for the current continuity.",
                        "image_url": "https://example.test/notices.jpg",
                        "image_alt": "",
                        "image_treatment": "poster",
                        "image_focal_point": "center",
                        "image_overlay": "medium",
                        "sort_order": 10,
                        "navigation_order": 10,
                        "sidebar_section": "community",
                        "show_in_navigation": "on",
                    }
                ).encode(),
                headers=_FORM,
            )

        updated = repo.get_board_by_slug(community.id, "announcements")
        assert response.status == 200
        assert "board image alt text is required when an image URL is set" in response.text
        assert updated.image_url is None
        assert updated.image_alt == ""

    asyncio.run(run())


def test_studio_board_editor_rejects_unsupported_board_media_controls() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        community = repo.get_community(services.seed.community.id)
        user = repo.get_user_by_email("moira@example.com")
        membership = repo.get_membership_by_username(community.id, "moira")
        character = repo.get_character_by_slug(community.id, "moira-mactaggert")
        admin_services = AppServices(
            repo,
            DemoSeed(community, user, membership, character),
        )
        app = create_app(debug=False, services=admin_services)

        async with TestClient(app) as client:
            response = await client.post(
                "/studio/boards/announcements",
                body=urlencode(
                    {
                        "name": "Announcements",
                        "board_kind": "community",
                        "parent_board_id": "",
                        "tagline": "Staff notes.",
                        "description": "Formal staff notices for the current continuity.",
                        "image_url": "https://example.test/notices.jpg",
                        "image_alt": "Notice board under red light",
                        "image_treatment": "raw-css",
                        "image_focal_point": "center",
                        "image_overlay": "medium",
                        "sort_order": 10,
                        "navigation_order": 10,
                        "sidebar_section": "community",
                        "show_in_navigation": "on",
                    }
                ).encode(),
                headers=_FORM,
            )

        updated = repo.get_board_by_slug(community.id, "announcements")
        assert response.status == 200
        assert "choose a supported board image treatment" in response.text
        assert updated.image_url is None
        assert updated.image_treatment == "poster"

    asyncio.run(run())


def test_studio_board_editor_validates_sublocation_parent() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        community = repo.get_community(services.seed.community.id)
        user = repo.get_user_by_email("moira@example.com")
        membership = repo.get_membership_by_username(community.id, "moira")
        character = repo.get_character_by_slug(community.id, "moira-mactaggert")
        admin_services = AppServices(
            repo,
            DemoSeed(community, user, membership, character),
        )
        app = create_app(debug=False, services=admin_services)

        async with TestClient(app) as client:
            response = await client.post(
                "/studio/boards/announcements",
                body=urlencode(
                    {
                        "name": "Announcements",
                        "board_kind": "sublocation",
                        "parent_board_id": "",
                        "tagline": "",
                        "description": "Needs a parent.",
                        "image_url": "",
                        "image_alt": "",
                        "image_treatment": "poster",
                        "image_focal_point": "center",
                        "image_overlay": "medium",
                        "sort_order": 10,
                        "navigation_order": 10,
                        "sidebar_section": "locations",
                        "show_in_navigation": "on",
                    }
                ).encode(),
                headers=_FORM,
            )

            assert response.status == 200
            assert "choose a parent location for sublocations" in response.text
            assert "Board editor" in response.text

    asyncio.run(run())


def test_board_sidebar_section_controls_direct_board_sidebar_realm() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        community = repo.get_community(services.seed.community.id)
        user = repo.get_user_by_email("moira@example.com")
        membership = repo.get_membership_by_username(community.id, "moira")
        character = repo.get_character_by_slug(community.id, "moira-mactaggert")
        admin_services = AppServices(
            repo,
            DemoSeed(community, user, membership, character),
        )
        applications = repo.get_board_by_slug(community.id, "applications")
        repo.update_board(
            community.id,
            applications.id,
            name=applications.name,
            description=applications.description,
            sort_order=applications.sort_order,
            parent_board_id=applications.parent_board_id,
            board_kind=applications.board_kind,
            sidebar_section="studio",
            tagline=applications.tagline,
            image_url=applications.image_url,
            image_alt=applications.image_alt,
            is_private=applications.is_private,
            navigation_order=applications.navigation_order,
            show_in_navigation=applications.show_in_navigation,
        )
        app = create_app(debug=False, services=admin_services)

        async with TestClient(app) as client:
            board_page = await client.get("/boards/applications")

            assert board_page.status == 200
            assert 'href="/studio#board-taxonomy"' in board_page.text
            assert re.search(
                r'<a class="[^"]*elbysodic-sidebar-link[^"]*"'
                r'[^>]*href="/boards/applications"[^>]*aria-current="page"',
                board_page.text,
            )
            assert "Board taxonomy" in board_page.text

    asyncio.run(run())


def test_sidebar_modes_follow_major_product_paths() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            world = await client.get("/boards/xavier-institute")
            assert world.status == 200
            assert "World Map" not in world.text
            assert "Locations" in world.text
            assert "Sublocations" in world.text
            assert "Wanted board" not in world.text
            assert "data-elbysodic-sidebar-toggle" in world.text
            assert "chirpui-app-shell__sidebar-resize" in world.text
            assert "elbysodic-sidebar-destination" in world.text
            assert 'href="/locations"' in world.text
            assert 'href="/community"' in world.text
            assert 'class="chirpui-sidebar elbysodic-sidebar"' in world.text
            assert "elbysodic-mobile-nav-trigger" in world.text
            assert "elbysodic-mobile-shell-drawer" in world.text
            assert '<h2 class="chirpui-drawer__title">Navigation</h2>' in world.text
            assert "elbysodic-mobile-realm-nav" not in world.text

            locations = await client.get("/locations")
            assert locations.status == 200
            assert "Playable world map" in locations.text
            assert "Major locations" in locations.text
            assert "/boards/xavier-institute" in locations.text
            assert "Community table" not in locations.text

            community = await client.get("/community")
            assert community.status == 200
            assert "Writer room and record" in community.text
            assert "Community table" in community.text
            assert "Announcements" in community.text
            assert "Playable world map" not in community.text

            guidebook = await client.get("/world")
            assert guidebook.status == 200
            assert "Guidebook" in guidebook.text
            assert "Start Here" in guidebook.text
            assert "World Map" not in guidebook.text
            assert 'class="chirpui-sidebar__section-title">In World</span>' in guidebook.text
            assert 'class="chirpui-sidebar__section-title">Guidebook Index</span>' in guidebook.text
            assert 'class="chirpui-sidebar__section-title">Start Here</span>' not in guidebook.text
            assert 'class="chirpui-sidebar__section-title">Guides</span>' in guidebook.text
            assert 'class="chirpui-sidebar__section-title">Events</span>' in guidebook.text
            assert '<h2 class="chirpui-drawer__title">Navigation</h2>' in guidebook.text

            desk = await client.get("/desk")
            assert desk.status == 200
            assert "Writer Desk" in desk.text
            assert "Queue" in desk.text
            assert "Inbox" in desk.text
            assert "Roster" in desk.text
            assert "World Map" not in desk.text
            assert 'class="chirpui-sidebar__section-title">On Your Desk</span>' in desk.text
            assert '<h2 class="chirpui-drawer__title">Navigation</h2>' in desk.text

            studio = await client.get("/studio")
            assert studio.status == 200
            assert "Director Studio" in studio.text
            assert "Production" in studio.text
            assert "Wanted board" in studio.text
            assert "World Map" not in studio.text
            assert 'class="chirpui-sidebar__section-title">In Studio</span>' in studio.text
            assert 'class="chirpui-sidebar__section-title">Production</span>' in studio.text
            assert '<h2 class="chirpui-drawer__title">Navigation</h2>' in studio.text

            wanted = await client.get("/wanted")
            assert wanted.status == 200
            assert "Casting" in wanted.text
            assert "Wanted board" not in wanted.text
            assert "Open Wants" in wanted.text
            assert "World Map" not in wanted.text
            assert 'class="chirpui-sidebar__section-title">In Play</span>' in wanted.text
            assert '<h2 class="chirpui-drawer__title">Navigation</h2>' in wanted.text

    asyncio.run(run())


def test_sidebar_hidden_preference_is_cookie_backed_and_server_rendered() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            world = await client.get("/boards/xavier-institute")
            assert world.status == 200
            assert 'var cookieName = "elbysodic_sidebar_hidden_v2";' in world.text
            assert "elbysodic-theme.css?v=sidebar-cookie-1" in world.text
            assert "elbysodic-shell.js?v=sidebar-cookie-2" in world.text
            assert "elbysodic-composer.js?v=sidebar-cookie-1" in world.text
            assert 'id="elbysodic-sidebar-cookie-state"' not in world.text
            assert 'aria-label="Hide navigation"' in world.text
            assert 'aria-expanded="true"' in world.text

            hidden_world = await client.get(
                "/boards/xavier-institute",
                headers={"Cookie": "elbysodic_sidebar_hidden_v2=true"},
            )
            assert hidden_world.status == 200
            assert 'id="elbysodic-sidebar-cookie-state"' in hidden_world.text
            assert 'aria-label="Show navigation"' in hidden_world.text
            assert 'aria-expanded="false"' in hidden_world.text

            stylesheet = await client.get("/elbysodic-static/elbysodic-theme.css")
            assert stylesheet.status == 200
            assert ".elbysodic-app-shell--sidebar-hidden .chirpui-app-shell" in stylesheet.text

            script = await client.get("/elbysodic-static/elbysodic-shell.js")
            assert script.status == 200
            assert 'const COOKIE_NAME = "elbysodic_sidebar_hidden_v2";' in script.text
            assert 'document.getElementById("elbysodic-sidebar-cookie-state")' in script.text
            assert "serverStyle.disabled = !hidden" in script.text
            assert "document.documentElement.classList.toggle(HIDDEN_CLASS, hidden)" in script.text
            assert 'window.localStorage.removeItem("chirpui-sidebar-collapsed")' in script.text

            composer = await client.get("/elbysodic-static/elbysodic-composer.js")
            assert composer.status == 200
            assert "data-elbysodic-sidebar-toggle" not in composer.text

    asyncio.run(run())


def test_world_map_sidebar_anchors_current_location_branch() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            parent = await client.get("/boards/new-york-city")
            assert parent.status == 200
            assert re.search(
                r'class="[^"]*elbysodic-sidebar-tree__link--active[^"]*"'
                r'[^>]*href="/boards/new-york-city"',
                parent.text,
            )
            assert "/boards/frozen-midtown" in parent.text

            child = await client.get("/boards/frozen-midtown")
            assert child.status == 200
            assert re.search(
                r'class="[^"]*elbysodic-sidebar-tree__link--branch[^"]*"'
                r'[^>]*href="/boards/new-york-city"',
                child.text,
            )
            assert re.search(
                r'class="[^"]*elbysodic-sidebar-tree__link--active[^"]*"'
                r'[^>]*href="/boards/frozen-midtown"',
                child.text,
            )
            frozen_link = re.search(
                r'<a class="[^"]*elbysodic-sidebar-tree__link[^"]*"'
                r'[^>]*href="/boards/frozen-midtown"[^>]*>',
                child.text,
            )
            assert frozen_link is not None
            assert "hx-target" not in frozen_link.group(0)
            assert 'aria-label="Place path"' in child.text

    asyncio.run(run())


def test_board_pages_render_location_stage_and_place_tiles() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            academy = await client.get("/boards/xavier-institute")

            assert academy.status == 200
            assert "elbysodic-board-stage" in academy.text
            assert "elbysodic-board-media--xavier-institute" in academy.text
            assert "elbysodic-location-compass" in academy.text
            assert "What is playable here" in academy.text
            assert "Relevant for Rogue" in academy.text
            assert "Plot pressure" in academy.text
            assert "No scene spotlight yet" in academy.text
            assert "Total" in academy.text
            assert (
                "Event boosts, location pins, or first direct scenes can surface here."
                in academy.text
            )
            assert "Doors" in academy.text
            assert "Nearby" in academy.text
            assert 'id="sublocations"' in academy.text
            assert 'id="nearby"' in academy.text
            assert "Choose a door inside Xavier Institute" in academy.text
            assert "Xavier Institute threads" in academy.text
            assert "No scenes have opened directly here yet." in academy.text
            assert "Sublocations" in academy.text
            assert "elbysodic-board-poster--tile" in academy.text

            midtown = await client.get("/boards/frozen-midtown")

            assert midtown.status == 200
            assert "elbysodic-board-media--frozen-midtown" in midtown.text
            assert "Nearby" in midtown.text
            assert "New York City" in midtown.text
            assert "/boards/transit-tunnels" in midtown.text

    asyncio.run(run())


def test_quiet_location_page_keeps_actions_visible_without_empty_door_sections() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        community = services.seed.community
        repo.create_board(
            community.id,
            "quiet-courtyard",
            "Quiet Courtyard",
            "A low-pressure place for slower scenes and first meetings.",
            board_kind="location",
            tagline="A softer corner of the grounds.",
            sort_order=999,
        )
        app = create_app(debug=False, services=services)

        async with TestClient(app) as client:
            page = await client.get("/boards/quiet-courtyard")

        assert page.status == 200
        assert "elbysodic-location-compass" in page.text
        assert "Open for scenes" in page.text
        assert "No scene spotlight yet" in page.text
        assert "Event boosts, location pins, or first direct scenes can surface here." in page.text
        assert 'href="#sublocations"' not in page.text
        assert 'id="sublocations"' not in page.text
        assert "No scenes have opened directly here yet." in page.text

    asyncio.run(run())


def test_community_board_pages_use_community_language_and_sidebar_state() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            announcements = await client.get("/boards/announcements")

            assert announcements.status == 200
            assert "Community board" in announcements.text
            assert "Threads here" in announcements.text
            assert "Direct threads in this board." in announcements.text
            assert "Location hub" not in announcements.text
            assert "Other major locations" not in announcements.text
            assert "Current event in this location" not in announcements.text
            assert "World Map" not in announcements.text
            assert re.search(
                r'<a class="[^"]*elbysodic-sidebar-destination[^"]*"'
                r'[^>]*href="/community"[^>]*aria-current="page"',
                announcements.text,
            )

    asyncio.run(run())


def test_topbar_marks_active_community_mode() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            world = await client.get("/boards/xavier-institute")
            assert world.status == 200
            assert re.search(
                r'<a class="[^"]*elbysodic-topnav__link--active[^"]*"'
                r'\s+href="/locations"[^>]*>World</a>',
                world.text,
            )

            guidebook = await client.get("/world")
            assert guidebook.status == 200
            assert re.search(
                r'<a class="[^"]*elbysodic-topnav__link--active[^"]*"'
                r'\s+href="/locations"[^>]*>World</a>',
                guidebook.text,
            )

            desk = await client.get("/desk")
            assert desk.status == 200
            assert re.search(
                r'<a class="[^"]*elbysodic-topnav__link--active[^"]*"'
                r'\s+href="/desk"[^>]*>Desk</a>',
                desk.text,
            )

            wanted = await client.get("/wanted")
            assert wanted.status == 200
            assert re.search(
                r'<a class="[^"]*elbysodic-topnav__link--active[^"]*"'
                r'\s+href="/wanted"[^>]*>Play</a>',
                wanted.text,
            )

            studio = await client.get("/studio")
            assert studio.status == 200
            assert re.search(
                r'<a class="[^"]*elbysodic-topnav__link--active[^"]*"'
                r'\s+href="/studio"[^>]*>Studio</a>',
                studio.text,
            )

            notifications = await client.get("/notifications")
            assert notifications.status == 200
            assert re.search(
                r'<a class="[^"]*elbysodic-topnav__link--active[^"]*"'
                r'\s+href="/desk"[^>]*>Desk</a>',
                notifications.text,
            )
            assert re.search(
                r'class="[^"]*elbysodic-identity-menu__notification-link--active[^"]*"'
                r'[^>]*href="/notifications"',
                notifications.text,
            )

    asyncio.run(run())


def test_parent_board_summaries_roll_up_child_activity_but_thread_lists_stay_direct() -> None:
    connection = connect(check_same_thread=False)
    create_schema(connection)
    repo = ForumRepository(connection)
    community = repo.seed_default_community("Hierarchy Test")
    role = repo.create_role(community.id, "member", "Member")
    user = repo.create_user("writer@example.com", "hash")
    membership = repo.create_membership(community.id, user.id, role.id, "writer", "Writer")
    character = repo.create_character(
        community.id,
        membership.id,
        "active-face",
        "Active Face",
        make_default=True,
    )
    parent = repo.create_board(community.id, "academy", "Academy", board_kind="location")
    child = repo.create_board(
        community.id,
        "med-bay",
        "Med Bay",
        parent_board_id=parent.id,
        board_kind="sublocation",
    )
    parent_thread = repo.create_thread(
        community.id,
        parent.id,
        character.id,
        "hallway-scene",
        "Hallway Scene",
    )
    repo.create_post(community.id, parent_thread.id, character.id, "A direct academy scene.")
    child_thread = repo.create_thread(
        community.id,
        child.id,
        character.id,
        "med-bay-scene",
        "Med Bay Scene",
    )
    repo.create_post(community.id, child_thread.id, character.id, "A child-location scene.")
    services = AppServices(
        repo,
        DemoSeed(
            community=community,
            user=user,
            membership=repo.get_membership(community.id, membership.id),
            default_character=character,
        ),
    )

    summaries = {summary.board.slug: summary for summary in services.list_boards()}
    _, direct_threads = services.board_threads("academy")

    assert summaries["academy"].thread_count == 2
    assert summaries["academy"].post_count == 2
    assert summaries["academy"].has_children is True
    assert summaries["academy"].latest_thread == child_thread
    assert [item.thread.title for item in direct_threads] == ["Hallway Scene"]


def test_discovery_defaults_to_active_face_lens_and_filters_facets() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            discover = await client.get("/discover")
            assert discover.status == 200
            assert "Plot discovery" in discover.text
            assert "chirpui-facet-chip" in discover.text
            assert "For Rogue" in discover.text
            assert "Mutant" in discover.text
            assert "X-Men" in discover.text
            assert "Academy" in discover.text
            assert "Rogue" in discover.text
            assert "Bolivar Trask" not in discover.text

            human_un = await client.get("/discover?facets=human,united-nations")
            assert human_un.status == 200
            assert "Bolivar Trask" in human_un.text
            assert "Moira MacTaggert" in human_un.text
            assert 'href="/characters/rogue">Rogue' not in human_un.text

    asyncio.run(run())


def test_world_materials_render_pillars_events_and_application_guides() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            world = await client.get("/world")
            assert world.status == 200
            assert "World studio" in world.text
            assert "Premise" in world.text
            assert "Application Guide" in world.text
            assert "Current Event: B-24 Winter" in world.text
            assert "Guidebook pulse" in world.text
            assert 'href="/world/premise"' in world.text
            assert 'href="/world/b-24-winter"' in world.text
            assert "United Nations" in world.text
            assert "elbysodic-material-card--premise" in world.text
            assert "elbysodic-material-card--application" in world.text
            assert "elbysodic-current-event-card--event" in world.text

            event = await client.get("/world/b-24-winter")
            assert event.status == 200
            assert "elbysodic-material-hero--event" in event.text
            assert "chirpui-detail-header" in event.text
            assert "chirpui-saved-view-strip" in event.text
            assert "elbysodic-material-detail-shell--event" in event.text
            assert "Iceman is infected with B-24" in event.text
            assert "Evil Lab" in event.text
            assert "Wanted hooks" in event.text
            assert "Active scenes" in event.text
            assert "Locations" in event.text
            assert "Related materials" in event.text
            assert "elbysodic-studio-facts" in event.text
            assert "Featured" in event.text
            assert "Carry this event into play" in event.text
            assert 'aria-label="Material sections"' in event.text
            assert 'href="#event-actions"' in event.text
            assert 'id="canon"' in event.text
            assert "Enter scene" in event.text
            assert "Answer hook" in event.text
            assert "Explore location" in event.text
            assert "Open discovery" in event.text
            assert "Event progression" in event.text
            assert "elbysodic-continuity-timeline" in event.text
            assert "elbysodic-continuity-timeline__title-link" in event.text
            assert "Event opened" in event.text
            assert "elbysodic-counter__label chirpui-visually-hidden" in event.text

            location = await client.get("/boards/frozen-midtown")
            assert location.status == 200
            assert "Current event in this location" in location.text
            assert 'href="/world/b-24-winter"' in location.text

            scene = await client.get("/boards/frozen-midtown/threads/frozen-avenue-evacuation")
            assert scene.status == 200
            assert "Current event shaping this scene" in scene.text
            assert 'href="/world/b-24-winter"' in scene.text

            missing = await client.get("/world/not-a-material")
            assert missing.status == 200
            assert "That world material is not in X-Men Apocalypse." in missing.text
            assert "Open Guidebook" in missing.text

    asyncio.run(run())


def test_draft_world_materials_are_staff_only_on_rendered_routes() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        community = services.seed.community
        services.repo.create_material(
            community.id,
            "director-only-event",
            "Director Only Event",
            material_type="event",
            summary="This draft should stay inside Studio.",
            body="Private director continuity that should not leak.",
            status="draft",
        )
        member_services, _member_character_id = _outsider_services(
            services,
            prefix="draft-material-member",
        )
        member_app = create_app(debug=False, services=member_services)
        async with TestClient(member_app) as member_client:
            member_world = await member_client.get("/world")
            member_direct = await member_client.get("/world/director-only-event")

        alex_membership = services.repo.get_membership_by_username(community.id, "alex")
        alex_user = services.repo.get_user(alex_membership.user_id)
        cyclops = services.repo.get_character_by_slug(community.id, "cyclops")
        alex_services = AppServices(
            services.repo,
            DemoSeed(community, alex_user, alex_membership, cyclops),
        )
        staff_app = create_app(debug=False, services=alex_services)
        async with TestClient(staff_app) as staff_client:
            staff_studio = await staff_client.get("/studio")
            staff_direct = await staff_client.get("/world/director-only-event")

        assert member_world.status == 200
        assert "Director Only Event" not in member_world.text
        assert "Private director continuity that should not leak." not in member_direct.text
        assert "That world material is not in X-Men Apocalypse." in member_direct.text
        assert staff_studio.status == 200
        assert "Director Only Event" in staff_studio.text
        assert staff_direct.status == 200
        assert "Director Only Event" in staff_direct.text
        assert "Private director continuity that should not leak." in staff_direct.text
        assert "Material studio" in staff_direct.text

    asyncio.run(run())


def test_directors_can_publish_draft_materials_from_studio_queue() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        community = repo.get_community(services.seed.community.id)
        draft_event = repo.create_material(
            community.id,
            "new-canon-pulse",
            "New Canon Pulse",
            material_type="event",
            summary="Director draft for the next canon beat.",
            body="A production note waiting for publication.",
            status="draft",
        )
        member_services, _member_character_id = _outsider_services(
            services,
            prefix="studio-material-member",
        )
        member_app = create_app(debug=False, services=member_services)
        async with TestClient(member_app) as member_client:
            forbidden = await member_client.post(
                "/studio",
                body=urlencode(
                    {
                        "intent": "material_status",
                        "material_slug": draft_event.slug,
                        "status": "published",
                    }
                ).encode(),
                headers=_FORM,
            )

        assert forbidden.status == 403
        assert repo.get_material_by_slug(community.id, draft_event.slug).status == "draft"

        user = repo.get_user_by_email("moira@example.com")
        membership = repo.get_membership_by_username(community.id, "moira")
        character = repo.get_character_by_slug(community.id, "moira-mactaggert")
        admin_services = AppServices(
            repo,
            DemoSeed(community, user, membership, character),
        )
        app = create_app(debug=False, services=admin_services)
        async with TestClient(app) as client:
            studio = await client.get("/studio")
            assert studio.status == 200
            assert "New Canon Pulse" in studio.text
            assert "Publish as current" in studio.text

            response = await client.post(
                "/studio",
                body=urlencode(
                    {
                        "intent": "material_status",
                        "material_slug": draft_event.slug,
                        "status": "published",
                        "is_featured": "on",
                    }
                ).encode(),
                headers=_FORM,
            )
            assert response.status == 302
            assert _response_header(response, "location") == "/studio#continuity-events"

            world = await client.get("/world/new-canon-pulse")
            studio_after = await client.get("/studio")

        updated = repo.get_material_by_slug(community.id, draft_event.slug)
        old_event = repo.get_material_by_slug(community.id, "b-24-winter")
        assert updated.status == "published"
        assert updated.is_featured is True
        assert old_event.is_featured is False
        current_event = admin_services.director_studio().current_event
        assert current_event is not None
        assert current_event.material.slug == draft_event.slug
        assert world.status == 200
        assert "New Canon Pulse" in world.text
        assert studio_after.status == 200
        assert "New Canon Pulse" in studio_after.text

    asyncio.run(run())


def test_applications_desk_tracks_character_statuses() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            applications = await client.get("/applications")
            assert applications.status == 200
            assert "Applications" in applications.text
            assert "Application pipeline" in applications.text
            assert "Rogue" in applications.text
            assert "Accepted" in applications.text
            assert "Application Guide" in applications.text
            assert 'href="/world/application-guide"' in applications.text

            roster = await client.get("/characters")
            assert roster.status == 200
            assert "Accepted" in roster.text
            assert "Start a draft application" in roster.text

            response = await client.post(
                "/characters",
                body=urlencode(
                    {
                        "name": "Jubilee",
                        "summary": "Fireworks, mall instincts, and a very loud jacket.",
                        "avatar_url": "",
                    }
                ).encode(),
                headers=_FORM,
            )
            assert response.status == 302

            services = get_services()
            character = services.repo.get_character_by_slug(
                services.seed.community.id,
                "jubilee",
            )
            assert character.application_status == "draft"

            draft_view = await client.get("/applications")
            assert draft_view.status == 200
            assert "Jubilee" in draft_view.text
            assert "Draft" in draft_view.text
            assert "Submit application" in draft_view.text
            assert 'href="/applications/jubilee"' in draft_view.text

            room = await client.get("/applications/jubilee")
            assert room.status == 200
            assert "Application Review Room" in room.text
            assert "Applicant Notes" in room.text
            assert "Save notes" in room.text

            save_room = await client.post(
                "/applications/jubilee",
                body=urlencode(
                    {
                        "intent": "save_application",
                        "summary": "Fireworks, mall instincts, and a very loud jacket.",
                        "body": "Jubilee is looking for a found-family first scene.",
                    }
                ).encode(),
                headers=_FORM,
            )
            assert save_room.status == 302
            application = services.repo.get_character_application_for_character(
                services.seed.community.id,
                character.id,
            )
            assert application.body == "Jubilee is looking for a found-family first scene."

            submit_response = await client.post(
                "/applications",
                body=urlencode(
                    {
                        "intent": "submit_application",
                        "character_slug": "jubilee",
                    }
                ).encode(),
                headers=_FORM,
            )
            assert submit_response.status == 302
            assert (
                services.repo.get_character_by_slug(
                    services.seed.community.id,
                    "jubilee",
                ).application_status
                == "submitted"
            )

            alex_membership = services.repo.get_membership_by_username(
                services.seed.community.id,
                "alex",
            )
            alex_user = services.repo.get_user(alex_membership.user_id)
            cyclops = services.repo.get_character_by_slug(
                services.seed.community.id,
                "cyclops",
            )
            alex_services = AppServices(
                services.repo,
                DemoSeed(services.seed.community, alex_user, alex_membership, cyclops),
            )
            assert any(
                item.label == "Application submitted" and item.title == "Jubilee"
                for item in alex_services.notifications().items
            )

            alex_app = create_app(debug=False, services=alex_services)
            async with TestClient(alex_app) as alex_client:
                review = await alex_client.get("/applications")
                assert review.status == 200
                assert "Review Queue" in review.text
                assert "Jubilee" in review.text
                assert "Accept" in review.text
                assert "Request revisions" in review.text
                assert 'name="intent" value="request_revision"' not in review.text

                review_room = await alex_client.get("/applications/jubilee")
                assert review_room.status == 200
                assert "Director Review" in review_room.text
                assert "Jubilee is looking for a found-family first scene." in review_room.text

                save_review = await alex_client.post(
                    "/applications/jubilee",
                    body=urlencode(
                        {
                            "intent": "save_review",
                            "revision_notes": "",
                            "staff_notes": "Voice is clear.",
                            "checklist": "Starter hook\nCast tie",
                        }
                    ).encode(),
                    headers=_FORM,
                )
                assert save_review.status == 302

                accept_response = await alex_client.post(
                    "/applications/jubilee",
                    body=urlencode(
                        {
                            "intent": "accept_application",
                        }
                    ).encode(),
                    headers=_FORM,
                )
                assert accept_response.status == 302

                revision_response = await alex_client.post(
                    "/applications/kitty-pryde",
                    body=urlencode(
                        {
                            "intent": "request_revision",
                            "revision_notes": "Add one concrete school-life pressure point.",
                        }
                    ).encode(),
                    headers=_FORM,
                )
                assert revision_response.status == 302

            assert (
                services.repo.get_character_by_slug(
                    services.seed.community.id,
                    "jubilee",
                ).application_status
                == "accepted"
            )
            applicant_app = create_app(
                debug=False, services=AppServices(services.repo, services.seed)
            )
            async with TestClient(applicant_app) as applicant_client:
                accepted_room = await applicant_client.get("/applications/jubilee")
            assert accepted_room.status == 200
            assert "Jubilee is looking for a found-family first scene." in accepted_room.text
            assert "Director Review" not in accepted_room.text
            assert "Voice is clear." not in accepted_room.text
            assert "Starter hook" not in accepted_room.text
            assert "Cast tie" not in accepted_room.text
            assert any(
                item.label == "Application accepted" and item.title == "Jubilee"
                for item in services.notifications().items
            )
            accepted_application = services.repo.get_character_application_for_character(
                services.seed.community.id,
                character.id,
            )
            assert accepted_application.staff_notes == "Voice is clear."
            assert accepted_application.checklist == "Starter hook\nCast tie"
            assert [
                event.to_status
                for event in services.repo.list_character_application_events(
                    services.seed.community.id,
                    accepted_application.id,
                )
            ] == ["accepted", "submitted"]

            mira_membership = services.repo.get_membership_by_username(
                services.seed.community.id,
                "mira",
            )
            mira_user = services.repo.get_user(mira_membership.user_id)
            kitty = services.repo.get_character_by_slug(
                services.seed.community.id,
                "kitty-pryde",
            )
            assert kitty.application_status == "revision_requested"
            mira_services = AppServices(
                services.repo,
                DemoSeed(services.seed.community, mira_user, mira_membership, kitty),
            )
            assert any(
                item.label == "Revisions requested" and item.title == "Kitty Pryde"
                for item in mira_services.notifications().items
            )

            mira_app = create_app(debug=False, services=mira_services)
            async with TestClient(mira_app) as mira_client:
                mira_applications = await mira_client.get("/applications")
                assert mira_applications.status == 200
                assert "Resubmit application" in mira_applications.text
                kitty_room = await mira_client.get("/applications/kitty-pryde")
                assert kitty_room.status == 200
                assert "Add one concrete school-life pressure point." in kitty_room.text

                resubmit_response = await mira_client.post(
                    "/applications",
                    body=urlencode(
                        {
                            "intent": "submit_application",
                            "character_slug": "kitty-pryde",
                        }
                    ).encode(),
                    headers=_FORM,
                )
                assert resubmit_response.status == 302
            assert (
                services.repo.get_character_by_slug(
                    services.seed.community.id,
                    "kitty-pryde",
                ).application_status
                == "submitted"
            )

    asyncio.run(run())


def test_wanted_ads_render_board_detail_and_character_hub() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            wanted = await client.get("/wanted")
            assert wanted.status == 200
            assert "Wanted" in wanted.text
            assert "Brotherhood rival from Rogue" in wanted.text
            assert "Human UN liaison for B-24 talks" in wanted.text
            assert 'href="/wanted/brotherhood-rival-for-rogue"' in wanted.text
            assert "United Nations" in wanted.text

            detail = await client.get("/wanted/brotherhood-rival-for-rogue")
            assert detail.status == 200
            assert "chirpui-detail-header" in detail.text
            assert "chirpui-facet-chip" in detail.text
            assert "chirpui-scope-switcher" in detail.text
            assert "Rogue needs someone who remembers" in detail.text
            assert 'href="/characters/rogue"' in detail.text
            assert 'href="/world/factions"' in detail.text
            assert "Complicated Romance" in detail.text

            character = await client.get("/characters/rogue")
            assert character.status == 200
            assert "Plotter" in character.text
            assert "Tracker" in character.text
            assert "Brotherhood rival from Rogue" in character.text
            assert 'href="/wanted"' in character.text

            interest_response = await client.post(
                "/wanted/human-un-liaison-for-b24",
                body=b"intent=express_interest",
                headers=_FORM,
            )
            assert interest_response.status == 302

            interested = await client.get("/wanted/human-un-liaison-for-b24")
            assert interested.status == 200
            assert "Rogue is interested in this hook." in interested.text
            assert "Interested faces" in interested.text

            services = get_services()
            repo = services.repo
            community = services.seed.community
            wanted_ad = repo.get_wanted_ad_by_slug(community.id, "human-un-liaison-for-b24")
            rogue = repo.get_character_by_slug(community.id, "rogue")
            interest = repo.get_wanted_ad_interest_for_character(
                community.id,
                wanted_ad.id,
                rogue.id,
            )
            assert interest.character_id == rogue.id

            charlie_membership = repo.get_membership_by_username(community.id, "charlie")
            charlie_user = repo.get_user(charlie_membership.user_id)
            xavier = repo.get_character_by_slug(community.id, "charles-xavier")
            charlie_services = AppServices(
                repo,
                DemoSeed(community, charlie_user, charlie_membership, xavier),
            )
            inbox = charlie_services.notifications()
            assert inbox.unread_count == 1
            assert inbox.items[0].label == "Wanted interest"
            assert inbox.items[0].title == "Human UN liaison for B-24 talks"
            assert inbox.items[0].href == "/wanted/human-un-liaison-for-b24"

            charlie_app = create_app(debug=False, services=charlie_services)
            async with TestClient(charlie_app) as charlie_client:
                creator_view = await charlie_client.get("/wanted/human-un-liaison-for-b24")
                assert creator_view.status == 200
                assert "Reserve for Rogue" in creator_view.text

                reserve_response = await charlie_client.post(
                    "/wanted/human-un-liaison-for-b24",
                    body=f"intent=reserve_interest&interest_id={interest.id}".encode(),
                    headers=_FORM,
                )
                assert reserve_response.status == 302

                reserved_view = await charlie_client.get("/wanted/human-un-liaison-for-b24")
                assert reserved_view.status == 200
                assert "reserved" in reserved_view.text
                assert "Create reserve" in reserved_view.text
                assert "Reserve for Rogue" not in reserved_view.text

                reserve_create = await charlie_client.post(
                    "/wanted/human-un-liaison-for-b24",
                    body=f"intent=create_reserve&interest_id={interest.id}".encode(),
                    headers=_FORM,
                )
                assert reserve_create.status == 302

                reserve_view = await charlie_client.get("/wanted/human-un-liaison-for-b24")
                assert reserve_view.status == 200
                assert "Reserve created" in reserve_view.text
                assert "Reserves" in reserve_view.text
                assert (
                    "Reserved from wanted hook: Human UN liaison for B-24 talks"
                    in reserve_view.text
                )

            assert (
                repo.get_wanted_ad_interest_for_character(
                    community.id,
                    wanted_ad.id,
                    rogue.id,
                ).status
                == "reserved"
            )
            assert repo.get_wanted_ad(community.id, wanted_ad.id).status == "reserved"
            reserve = repo.get_character_reserve_for_wanted_interest(community.id, interest.id)
            assert reserve.character_id == rogue.id

            lane_inbox = AppServices(repo, services.seed).notifications()
            assert any(item.label == "Wanted reserved" for item in lane_inbox.items)
            assert any(item.label == "Reserve created" for item in lane_inbox.items)

            profile_app = create_app(debug=False, services=AppServices(repo, services.seed))
            async with TestClient(profile_app) as profile_client:
                profile = await profile_client.get("/characters/rogue")
                assert profile.status == 200
                assert "Reserves" in profile.text
                assert "Human UN liaison for B-24 talks" in profile.text
                casting = await profile_client.get("/casting")
                assert casting.status == 200
                assert "Casting Desk" in casting.text
                assert "Browsing as Rogue" in casting.text
                assert "Wanted With Interest" in casting.text
                assert "Active Reserves" in casting.text
                assert "Human UN liaison for B-24 talks" in casting.text
                assert "Rogue&#39;s Reserves" in casting.text

            charlie_app = create_app(debug=False, services=charlie_services)
            async with TestClient(charlie_app) as charlie_client:
                filled_response = await charlie_client.post(
                    "/wanted/human-un-liaison-for-b24",
                    body=urlencode(
                        {
                            "intent": "update_lifecycle_status",
                            "status": "filled",
                        }
                    ).encode(),
                    headers=_FORM,
                )
                filled_view = await charlie_client.get("/wanted/human-un-liaison-for-b24")

                archive_response = await charlie_client.post(
                    "/wanted/human-un-liaison-for-b24",
                    body=urlencode(
                        {
                            "intent": "update_lifecycle_status",
                            "status": "archived",
                        }
                    ).encode(),
                    headers=_FORM,
                )
                archived_manager_view = await charlie_client.get("/wanted/human-un-liaison-for-b24")

                reopen_response = await charlie_client.post(
                    "/wanted/human-un-liaison-for-b24",
                    body=urlencode(
                        {
                            "intent": "update_lifecycle_status",
                            "status": "open",
                        }
                    ).encode(),
                    headers=_FORM,
                )

            outsider_services, _outsider_character_id = _outsider_services(
                services,
                prefix="wanted-archive-outsider",
            )
            archived_wanted = services.repo.update_wanted_ad_status(
                community.id,
                wanted_ad.id,
                "archived",
            )
            outsider_app = create_app(debug=False, services=outsider_services)
            async with TestClient(outsider_app) as outsider_client:
                archived_outsider_view = await outsider_client.get(
                    "/wanted/human-un-liaison-for-b24"
                )
                archived_wanted_board = await outsider_client.get("/wanted")

            reopened = services.repo.update_wanted_ad_status(
                community.id,
                wanted_ad.id,
                "open",
            )

            assert filled_response.status == 302
            assert "Manage hook lifecycle" in filled_view.text
            assert '<option value="filled" selected>Filled</option>' in filled_view.text
            assert archive_response.status == 302
            assert archived_manager_view.status == 200
            assert (
                '<option value="archived" selected>Archived</option>' in archived_manager_view.text
            )
            assert reopen_response.status == 302
            assert archived_wanted.status == "archived"
            assert archived_outsider_view.status == 200
            assert "That wanted hook is not in X-Men Apocalypse." in archived_outsider_view.text
            assert "Human UN liaison for B-24 talks" not in archived_wanted_board.text
            assert reopened.status == "open"

            missing = await client.get("/wanted/not-a-hook")
            assert missing.status == 200
            assert "That wanted hook is not in X-Men Apocalypse." in missing.text
            assert "Open Wanted" in missing.text

    asyncio.run(run())


def test_application_start_form_creates_draft_face_and_review_room() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        community = services.seed.community
        facet = services.repo.get_facet_by_slug(community.id, "x-men")
        fields = {
            field.field_key: field
            for field in services.repo.list_application_template_fields(community.id)
        }

        async with TestClient(app) as client:
            form = await client.get("/applications/new")
            response = await client.post(
                "/applications/new",
                body=urlencode(
                    {
                        "name": "Jean Grey",
                        "summary": "A powerful telepath trying to stay gentle.",
                        "body": "Looking for school pressure, found family, and dangerous rescue work.",
                        "facet_slugs": [facet.slug],
                        f"application_field_{fields['face_claim'].id}": "Famke Janssen",
                        f"application_field_{fields['faction_claim'].id}": "X-Men",
                        f"application_field_{fields['power_claim'].id}": "Telepathy",
                    },
                    doseq=True,
                ).encode(),
                headers=_FORM,
            )
            room = await client.get("/applications/jean-grey")
            applications = await client.get("/applications")

        character = services.repo.get_character_by_slug(community.id, "jean-grey")
        application = services.repo.get_character_application_for_character(
            community.id,
            character.id,
        )
        field_values = services.repo.list_application_field_values(community.id, application.id)
        facets = services.repo.list_character_facets(community.id, character.id)

        assert form.status == 200
        assert "Begin a new face for this realm." in form.text
        assert "Application Guide" in form.text
        assert "Director fields" in form.text
        assert "Face claim" in form.text
        assert response.status == 302
        assert _response_header(response, "location") == "/applications/jean-grey"
        assert character.application_status == "draft"
        assert application.summary == "A powerful telepath trying to stay gentle."
        assert "dangerous rescue work" in application.body
        assert "Application fields" in application.body
        assert "Face claim: Famke Janssen" in application.body
        assert "Primary faction: X-Men" in application.body
        assert {value.value for value in field_values} == {
            "Famke Janssen",
            "Telepathy",
            "X-Men",
        }
        assert [assigned.slug for assigned in facets] == ["x-men"]
        assert room.status == 200
        assert "Jean Grey" in room.text
        assert "Director fields" in room.text
        assert "Famke Janssen" in room.text
        assert "Draft" in room.text
        assert applications.status == 200
        assert "Jean Grey" in applications.text

        async with TestClient(app) as client:
            conflict_save_response = await client.post(
                "/applications/jean-grey",
                body=urlencode(
                    {
                        "intent": "save_application",
                        "summary": "A powerful telepath trying to stay gentle.",
                        "body": "Trying a visual that directors should catch.",
                        f"application_field_{fields['face_claim'].id}": "Magneto Visual",
                        f"application_field_{fields['faction_claim'].id}": "X-Men",
                        f"application_field_{fields['power_claim'].id}": "Telekinesis",
                    }
                ).encode(),
                headers=_FORM,
            )
            conflict_room = await client.get("/applications/jean-grey")
            conflict_applications = await client.get("/applications")
            conflict_submit_response = await client.post(
                "/applications",
                body=urlencode(
                    {
                        "intent": "submit_application",
                        "character_slug": "jean-grey",
                    }
                ).encode(),
                headers=_FORM,
            )
            save_response = await client.post(
                "/applications/jean-grey",
                body=urlencode(
                    {
                        "intent": "save_application",
                        "summary": "A powerful telepath trying to stay gentle.",
                        "body": "Updated notes for school pressure and rescue work.",
                        f"application_field_{fields['face_claim'].id}": "Sophie Turner",
                        f"application_field_{fields['faction_claim'].id}": "X-Men",
                        f"application_field_{fields['power_claim'].id}": "Telekinesis",
                    }
                ).encode(),
                headers=_FORM,
            )
            submit_response = await client.post(
                "/applications",
                body=urlencode(
                    {
                        "intent": "submit_application",
                        "character_slug": "jean-grey",
                    }
                ).encode(),
                headers=_FORM,
            )
        assert save_response.status == 302
        assert conflict_save_response.status == 302
        assert conflict_room.status == 200
        assert "Already claimed" in conflict_room.text
        assert 'href="/characters/magneto"' in conflict_room.text
        assert conflict_applications.status == 200
        assert "1 claim conflict" in conflict_applications.text
        assert "First conflict is held by Magneto." in conflict_applications.text
        assert conflict_submit_response.status == 400
        assert "Face claim is already claimed: Magneto Visual" in conflict_submit_response.text
        updated_field_values = services.repo.list_application_field_values(
            community.id,
            application.id,
        )
        assert {value.value for value in updated_field_values} == {
            "Sophie Turner",
            "Telekinesis",
            "X-Men",
        }
        assert submit_response.status == 302

        alex_membership = services.repo.get_membership_by_username(community.id, "alex")
        alex_user = services.repo.get_user(alex_membership.user_id)
        cyclops = services.repo.get_character_by_slug(community.id, "cyclops")
        alex_services = AppServices(
            services.repo,
            DemoSeed(community, alex_user, alex_membership, cyclops),
        )
        alex_app = create_app(debug=False, services=alex_services)
        async with TestClient(alex_app) as alex_client:
            review_room = await alex_client.get("/applications/jean-grey")
            accept_response = await alex_client.post(
                "/applications/jean-grey",
                body=urlencode({"intent": "accept_application"}).encode(),
                headers=_FORM,
            )
            claims = await alex_client.get("/claims")

        accepted_claims = services.repo.list_character_claims_for_character(
            community.id,
            character.id,
            status=None,
        )
        assert review_room.status == 200
        assert "Intake Fields" in review_room.text
        assert accept_response.status == 302
        assert {claim.label for claim in accepted_claims} == {
            "Sophie Turner",
            "Telekinesis",
            "X-Men",
        }
        assert {claim.value for claim in accepted_claims} == {
            "sophie-turner",
            "telekinesis",
            "x-men",
        }
        assert claims.status == 200
        assert "Sophie Turner" in claims.text

    asyncio.run(run())


def test_application_review_flags_mapped_claim_conflicts_before_accept() -> None:
    async def run() -> None:
        _app()
        services = get_services()
        community = services.seed.community
        fields = {
            field.field_key: field
            for field in services.repo.list_application_template_fields(community.id)
        }
        expected_revision_note = (
            "Please revise the mapped claim details before we can accept this face.\n"
            "- Face claim: Magneto Visual is already held by Magneto."
        )
        character = services.create_character(
            name="Duplicate Face",
            summary="A test applicant with a taken visual reference.",
            application_body="Staff should see the collision before accepting.",
            application_field_values={
                fields["face_claim"].id: "Magneto Visual",
                fields["faction_claim"].id: "X-Men",
            },
        )
        application = services.repo.get_character_application_for_character(
            community.id,
            character.id,
        )
        services.repo.transition_character_application_status(
            community.id,
            application.id,
            status="submitted",
            actor_membership_id=services.seed.membership.id,
            actor_character_id=character.id,
            note="Imported submitted application.",
        )

        alex_membership = services.repo.get_membership_by_username(community.id, "alex")
        alex_user = services.repo.get_user(alex_membership.user_id)
        cyclops = services.repo.get_character_by_slug(community.id, "cyclops")
        alex_services = AppServices(
            services.repo,
            DemoSeed(community, alex_user, alex_membership, cyclops),
        )
        alex_app = create_app(debug=False, services=alex_services)
        async with TestClient(alex_app) as alex_client:
            applications = await alex_client.get("/applications")
            review_room = await alex_client.get("/applications/duplicate-face")
            accept_response = await alex_client.post(
                "/applications/duplicate-face",
                body=urlencode({"intent": "accept_application"}).encode(),
                headers=_FORM,
            )
            revision_response = await alex_client.post(
                "/applications/duplicate-face",
                body=urlencode(
                    {
                        "intent": "request_revision",
                        "revision_notes": expected_revision_note,
                    }
                ).encode(),
                headers=_FORM,
            )

        duplicate = services.repo.get_character_by_slug(community.id, "duplicate-face")
        duplicate_application = services.repo.get_character_application_for_character(
            community.id,
            duplicate.id,
        )

        assert review_room.status == 200
        assert applications.status == 200
        assert "1 claim conflict" in applications.text
        assert "First conflict is held by Magneto." in applications.text
        assert "Already claimed" in review_room.text
        assert "Resolve exclusive claims before accepting" in review_room.text
        assert "Please revise the mapped claim details" in review_room.text
        assert "Review claims" in review_room.text
        assert (
            '<button type="submit"\n                class="chirpui-btn chirpui-btn--primary"\n                disabled>'
            in review_room.text
        )
        assert "Held by" in review_room.text
        assert 'href="/characters/magneto"' in review_room.text
        assert "Shared lane" in review_room.text
        assert accept_response.status == 400
        assert "Face claim is already claimed: Magneto Visual" in accept_response.text
        assert revision_response.status == 302
        assert duplicate.application_status == "revision_requested"
        assert duplicate_application.revision_notes == expected_revision_note

    asyncio.run(run())


def test_application_start_form_preserves_validation_errors_and_unique_slugs() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        community = services.seed.community
        fields = {
            field.field_key: field
            for field in services.repo.list_application_template_fields(community.id)
        }
        dynamic_fields = {
            f"application_field_{fields['face_claim'].id}": "Echo Visual",
            f"application_field_{fields['faction_claim'].id}": "X-Men",
        }

        async with TestClient(app) as client:
            invalid = await client.post(
                "/applications/new",
                body=urlencode({"name": "", "summary": "A concept"}).encode(),
                headers=_FORM,
            )
            missing_required_field = await client.post(
                "/applications/new",
                body=urlencode(
                    {
                        "name": "Missing Claim",
                        "summary": "A concept",
                    }
                ).encode(),
                headers=_FORM,
            )
            duplicate_claim = await client.post(
                "/applications/new",
                body=urlencode(
                    {
                        "name": "Duplicate Face",
                        "summary": "A concept with a taken face claim.",
                        f"application_field_{fields['face_claim'].id}": "Magneto Visual",
                        f"application_field_{fields['faction_claim'].id}": "X-Men",
                    }
                ).encode(),
                headers=_FORM,
            )
            first = await client.post(
                "/applications/new",
                body=urlencode(
                    {
                        "name": "Echo",
                        "summary": "First draft",
                        **dynamic_fields,
                    }
                ).encode(),
                headers=_FORM,
            )
            second = await client.post(
                "/applications/new",
                body=urlencode(
                    {
                        "name": "Echo",
                        "summary": "Second draft",
                        **dynamic_fields,
                    }
                ).encode(),
                headers=_FORM,
            )

        assert invalid.status == 200
        assert "character name is required" in invalid.text
        assert missing_required_field.status == 200
        assert "Face claim is required" in missing_required_field.text
        assert duplicate_claim.status == 200
        assert (
            "Some claims need another choice before you create this draft." in duplicate_claim.text
        )
        assert "Already claimed" in duplicate_claim.text
        assert "Held by" in duplicate_claim.text
        assert 'href="/characters/magneto"' in duplicate_claim.text
        assert "Shared lane" in duplicate_claim.text
        assert first.status == 302
        assert _response_header(first, "location") == "/applications/echo"
        assert second.status == 302
        assert _response_header(second, "location") == "/applications/echo-2"
        assert services.repo.get_character_by_slug(community.id, "echo").name == "Echo"
        assert services.repo.get_character_by_slug(community.id, "echo-2").name == "Echo"
        assert "duplicate-face" not in [
            character.slug for character in services.repo.list_community_characters(community.id)
        ]

    asyncio.run(run())


def test_direct_application_path_switches_to_realm_form() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        hp = services.repo.get_community_by_slug("hp-universe")
        hp_membership = services.repo.get_membership_for_user(hp.id, 1)

        async with TestClient(app) as client:
            network = await client.get("/network")
            response = await client.post(
                "/identity",
                body=urlencode(
                    {
                        "intent": "switch_membership",
                        "membership_id": str(hp_membership.id),
                        "character_id": "0",
                        "next": "/c/hp-universe/applications/new",
                    }
                ).encode(),
                headers=_FORM,
            )
            set_cookie = _response_header(response, "set-cookie").split(";", 1)[0]
            form = await client.get(
                "/c/hp-universe/applications/new", headers={"Cookie": set_cookie}
            )

        assert network.status == 200
        assert "/applications/new" not in network.text
        assert "Start application" not in network.text
        assert response.status == 302
        assert _response_header(response, "location") == "/c/hp-universe/applications/new"
        assert form.status == 200
        assert '<span class="elbysodic-community-brand__name">HP Universe</span>' in form.text
        assert "Begin a new face for this realm." in form.text

    asyncio.run(run())


def test_claims_directory_renders_seeded_claims_and_studio_summary() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            claims = await client.get("/claims")
            open_claims = await client.get("/claims?status=available")
            magneto_claims = await client.get("/claims?q=magneto")
            claimed_brotherhood = await client.get("/claims?status=claimed&q=brotherhood")
            no_results = await client.get("/claims?q=not-a-real-claim")
            studio = await client.get("/studio")

        assert claims.status == 200
        assert "What is taken, open, and expected." in claims.text
        assert "Claimed" in claims.text
        assert "Reserved" in claims.text
        assert "Open slots" in claims.text
        assert "Face Claim" in claims.text
        assert "Faction Claim" in claims.text
        assert "Magneto visual reference" in claims.text
        assert "Brotherhood" in claims.text
        assert "Collected by Face claim on the application template." in claims.text
        assert open_claims.status == 200
        assert "What is taken, open, and expected." in open_claims.text
        assert "X-Men" in open_claims.text
        assert "Magneto visual reference" not in open_claims.text
        assert "No available claims match this type yet." in open_claims.text
        assert magneto_claims.status == 200
        assert "Magneto visual reference" in magneto_claims.text
        assert "Rogue visual reference" not in magneto_claims.text
        assert 'href="/claims?status=claimed&amp;q=magneto"' in magneto_claims.text
        assert claimed_brotherhood.status == 200
        assert "Brotherhood" in claimed_brotherhood.text
        assert "Rogue visual reference" not in claimed_brotherhood.text
        assert no_results.status == 200
        assert 'value="not-a-real-claim"' in no_results.text
        assert 'No claims match "not-a-real-claim" in this type.' in no_results.text
        assert studio.status == 200
        assert "Claims and fields" in studio.text
        assert 'href="/claims"' in studio.text

    asyncio.run(run())


def test_director_can_record_manual_claims_from_claims_directory() -> None:
    async def run() -> None:
        _app()
        services = get_services()
        community = services.seed.community
        face_claim = services.repo.get_claim_type_by_slug(community.id, "face")
        alex_membership = services.repo.get_membership_by_username(community.id, "alex")
        alex_user = services.repo.get_user(alex_membership.user_id)
        cyclops = services.repo.get_character_by_slug(community.id, "cyclops")
        alex_services = AppServices(
            services.repo,
            DemoSeed(community, alex_user, alex_membership, cyclops),
        )
        alex_app = create_app(debug=False, services=alex_services)

        async with TestClient(alex_app) as client:
            directory = await client.get("/claims")
            response = await client.post(
                "/claims",
                body=urlencode(
                    {
                        "intent": "create_claim",
                        "claim_type_id": str(face_claim.id),
                        "label": "Cyclops tactical visor",
                        "status": "claimed",
                        "character_id": str(cyclops.id),
                        "notes": "Manual director correction after importing old claims.",
                    }
                ).encode(),
                headers=_FORM,
            )
            created_claim = next(
                claim
                for claim in services.repo.list_character_claims_for_character(
                    community.id,
                    cyclops.id,
                    status=None,
                )
                if claim.label == "Cyclops tactical visor"
            )
            update_response = await client.post(
                "/claims",
                body=urlencode(
                    {
                        "intent": "update_claim",
                        "claim_id": str(created_claim.id),
                        "label": "Cyclops visor reserve",
                        "status": "reserved",
                        "character_id": "",
                        "notes": "Holding the visual slot during a costume refresh.",
                    }
                ).encode(),
                headers=_FORM,
            )
            updated_directory = await client.get("/claims")
            reserved_directory = await client.get("/claims?status=reserved")

        manual_claim = services.repo.get_character_claim(
            community.id,
            created_claim.id,
        )
        cyclops_claims = services.repo.list_character_claims_for_character(
            community.id,
            cyclops.id,
            status=None,
        )

        assert directory.status == 200
        assert "Record claim" in directory.text
        assert "Cyclops" in directory.text
        assert response.status == 302
        assert update_response.status == 302
        assert manual_claim.label == "Cyclops visor reserve"
        assert manual_claim.value == "cyclops-visor-reserve"
        assert manual_claim.status == "reserved"
        assert manual_claim.character_id is None
        assert manual_claim.notes == "Holding the visual slot during a costume refresh."
        assert all(claim.id != created_claim.id for claim in cyclops_claims)
        assert updated_directory.status == 200
        assert "Edit claim" in updated_directory.text
        assert "Cyclops visor reserve" in updated_directory.text
        assert "Holding the visual slot during a costume refresh." in updated_directory.text
        assert "Save claim" in updated_directory.text
        assert reserved_directory.status == 200
        assert "Cyclops visor reserve" in reserved_directory.text
        assert "Cyclops tactical visor" not in reserved_directory.text

    asyncio.run(run())


def test_studio_intake_editor_updates_claims_and_application_fields() -> None:
    async def run() -> None:
        _app()
        services = get_services()
        community = services.seed.community
        face_claim = services.repo.get_claim_type_by_slug(community.id, "face")
        faction_field = services.repo.get_application_template_field_by_key(
            community.id,
            "faction_claim",
        )
        alex_membership = services.repo.get_membership_by_username(community.id, "alex")
        alex_user = services.repo.get_user(alex_membership.user_id)
        cyclops = services.repo.get_character_by_slug(community.id, "cyclops")
        alex_services = AppServices(
            services.repo,
            DemoSeed(community, alex_user, alex_membership, cyclops),
        )
        alex_app = create_app(debug=False, services=alex_services)

        async with TestClient(alex_app) as client:
            editor = await client.get("/studio/intake")
            create_claim_response = await client.post(
                "/studio/intake",
                body=urlencode(
                    {
                        "intent": "create_claim_type",
                        "name": "Birthright Claim",
                        "claim_kind": "lineage",
                        "description": "Legacy, family, or inheritance pressure.",
                        "sort_order": "25",
                        "is_required": "on",
                        "is_exclusive": "on",
                        "visibility": "public",
                    }
                ).encode(),
                headers=_FORM,
            )
            created_claim = services.repo.get_claim_type_by_slug(community.id, "birthright-claim")
            create_field_response = await client.post(
                "/studio/intake",
                body=urlencode(
                    {
                        "intent": "create_template_field",
                        "label": "Birthright",
                        "field_type": "text",
                        "maps_to_claim_type_id": str(created_claim.id),
                        "sort_order": "35",
                        "help_text": "Name the legacy pressure this face brings into play.",
                        "placeholder": "Summers family, royal line, inherited title...",
                        "options": "",
                        "is_required": "on",
                    }
                ).encode(),
                headers=_FORM,
            )
            claim_response = await client.post(
                "/studio/intake",
                body=urlencode(
                    {
                        "intent": "claim_type",
                        "claim_type_id": str(face_claim.id),
                        "name": "Visual Claim",
                        "claim_kind": "face",
                        "description": "The visual reference directors reserve.",
                        "sort_order": "5",
                        "is_required": "on",
                        "is_exclusive": "on",
                        "visibility": "public",
                    }
                ).encode(),
                headers=_FORM,
            )
            field_response = await client.post(
                "/studio/intake",
                body=urlencode(
                    {
                        "intent": "template_field",
                        "field_id": str(faction_field.id),
                        "label": "Story lane",
                        "field_type": "select",
                        "maps_to_claim_type_id": str(faction_field.maps_to_claim_type_id),
                        "sort_order": "15",
                        "help_text": "Choose the pressure lane directors should route first.",
                        "placeholder": "",
                        "options": "X-Men\nBrotherhood\nCivilian\nOther",
                        "is_required": "on",
                    }
                ).encode(),
                headers=_FORM,
            )
            updated_editor = await client.get("/studio/intake")
            studio = await client.get("/studio")
            claims = await client.get("/claims")
            application_form = await client.get("/applications/new")

        updated_face_claim = services.repo.get_claim_type(community.id, face_claim.id)
        updated_faction_field = services.repo.get_application_template_field(
            community.id,
            faction_field.id,
        )
        created_field = services.repo.get_application_template_field_by_key(
            community.id,
            "birthright",
        )

        assert editor.status == 200
        assert "Claims and application fields" in editor.text
        assert create_claim_response.status == 302
        assert create_field_response.status == 302
        assert claim_response.status == 302
        assert field_response.status == 302
        assert created_claim.name == "Birthright Claim"
        assert created_claim.claim_kind == "lineage"
        assert created_claim.is_exclusive
        assert created_field.label == "Birthright"
        assert created_field.maps_to_claim_type_id == created_claim.id
        assert updated_face_claim.name == "Visual Claim"
        assert updated_face_claim.sort_order == 5
        assert updated_faction_field.label == "Story lane"
        assert updated_faction_field.options_json == '["X-Men","Brotherhood","Civilian","Other"]'
        assert updated_editor.status == 200
        assert "Add claim type" in updated_editor.text
        assert "Add application field" in updated_editor.text
        assert "Birthright Claim" in updated_editor.text
        assert "Birthright" in updated_editor.text
        assert "Visual Claim" in updated_editor.text
        assert "Story lane" in updated_editor.text
        assert studio.status == 200
        assert 'href="/studio/intake"' in studio.text
        assert claims.status == 200
        assert "Birthright Claim" in claims.text
        assert "Visual Claim" in claims.text
        assert application_form.status == 200
        assert "Story lane" in application_form.text
        assert "Birthright" in application_form.text
        assert "Other" in application_form.text

    asyncio.run(run())


def test_realm_interactions_render_submit_and_link_from_applications() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        community = services.seed.community
        interaction = services.repo.get_realm_interaction_by_slug(
            community.id,
            "pressure-lane-finder",
        )
        question = services.repo.list_realm_interaction_questions(
            community.id,
            interaction.id,
        )[0]
        option = services.repo.list_realm_interaction_options(
            community.id,
            question.id,
        )[0]

        async with TestClient(app) as client:
            hub = await client.get("/interactions")
            detail = await client.get("/interactions/pressure-lane-finder")
            application = await client.get("/applications/new")
            response = await client.post(
                "/interactions/pressure-lane-finder",
                body=urlencode({f"question_{question.id}": str(option.id)}).encode(),
                headers=_FORM,
            )
            updated = await client.get("/interactions/pressure-lane-finder")

        stored = services.repo.get_realm_interaction_response_for_membership(
            community.id,
            interaction.id,
            services.seed.membership.id,
        )

        assert hub.status == 200
        assert "Realm Artifacts" in hub.text
        assert "Pressure Lane Finder" in hub.text
        assert detail.status == 200
        assert "When the world turns against mutants" in detail.text
        assert application.status == 200
        assert "Optional realm quizzes" in application.text
        assert "Pressure Lane Finder" in application.text
        assert response.status == 302
        assert _response_header(response, "location") == "/interactions/pressure-lane-finder"
        assert stored is not None
        assert updated.status == 200
        assert "You responded" in updated.text

    asyncio.run(run())


def test_character_plot_hooks_render_create_and_notify_interest() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            character = await client.get("/characters/rogue")
            assert character.status == 200
            assert "Old ghosts, new lines" in character.text
            assert "New plot hook" in character.text

            response = await client.post(
                "/characters/rogue",
                body=urlencode(
                    {
                        "intent": "create_plot_hook",
                        "plot_hook_title": "Coffee before the crisis",
                        "plot_hook_type": "scene",
                        "plot_hook_summary": "A quieter beat before the event pressure.",
                        "plot_hook_body": "Rogue wants a low-stakes conversation before B-24.",
                        "plot_hook_facets": "x-men",
                    }
                ).encode(),
                headers=_FORM,
            )
            assert response.status == 302

            detail = await client.get("/characters/rogue/hooks/coffee-before-the-crisis")
            assert detail.status == 200
            assert "Coffee before the crisis" in detail.text
            assert "You created this hook." in detail.text

            discover = await client.get("/discover?facets=x-men")
            assert discover.status == 200
            assert "Plot hooks" in discover.text
            assert "Coffee before the crisis" in discover.text

            services = get_services()
            outsider_services, _character_id = _outsider_services(services, prefix="hookfan")
            outsider_app = create_app(debug=False, services=outsider_services)
            async with TestClient(outsider_app) as outsider_client:
                outsider_detail = await outsider_client.get(
                    "/characters/rogue/hooks/coffee-before-the-crisis"
                )
                assert outsider_detail.status == 200
                assert "I'm interested as Hookfan Face" in outsider_detail.text

                interest = await outsider_client.post(
                    "/characters/rogue/hooks/coffee-before-the-crisis",
                    body=b"intent=express_interest",
                    headers=_FORM,
                )
                assert interest.status == 302

            owner_inbox = AppServices(services.repo, services.seed).notifications()
            assert any(item.label == "Plot hook interest" for item in owner_inbox.items)

            repo = services.repo
            community = services.seed.community
            hook = repo.get_character_plot_hook_by_slug(
                community.id,
                repo.get_character_by_slug(community.id, "rogue").id,
                "coffee-before-the-crisis",
            )
            interest = repo.list_character_plot_hook_interests(community.id, hook.id)[0]

            owner_app = create_app(debug=False, services=AppServices(repo, services.seed))
            async with TestClient(owner_app) as owner_client:
                creator_detail = await owner_client.get(
                    "/characters/rogue/hooks/coffee-before-the-crisis"
                )
                assert creator_detail.status == 200
                assert "Start plotting room" in creator_detail.text

                room_response = await owner_client.post(
                    "/characters/rogue/hooks/coffee-before-the-crisis",
                    body=f"intent=start_plotting_room&interest_id={interest.id}".encode(),
                    headers=_FORM,
                )
                assert room_response.status == 302

                room = repo.get_plotting_room_for_plot_hook_interest(community.id, interest.id)
                room_page = await owner_client.get(f"/plotting/{room.id}")
                assert room_page.status == 200
                assert "Coffee before the crisis: Hookfan Face" in room_page.text
                assert "Hookfan Face" in room_page.text

                plotting = await owner_client.get("/plotting")
                assert plotting.status == 200
                assert "Plotting Rooms" in plotting.text
                assert "Open plotting room" in plotting.text

                profile = await owner_client.get("/characters/rogue")
                assert profile.status == 200
                assert "Plotting Now" in profile.text
                assert "Coffee before the crisis: Hookfan Face" in profile.text

            assert (
                repo.get_character_plot_hook_interest(community.id, interest.id).status
                == "plotting"
            )

            outsider_inbox = outsider_services.notifications()
            assert any(item.label == "Plotting room" for item in outsider_inbox.items)

    asyncio.run(run())


def test_unaccepted_faces_cannot_take_story_actions() -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    community = services.seed.community
    assert services.seed.default_character is not None
    character = repo.update_character_application_status(
        community.id,
        services.seed.default_character.id,
        "submitted",
    )
    thread = repo.get_thread_by_slug(
        community.id,
        repo.get_board_by_slug(community.id, "danger-room").id,
        "sentinel-drill",
    )
    role = repo.get_role_by_slug(community.id, "member")
    other_user = repo.create_user("story-counterparty@example.com", "hash")
    other_membership = repo.create_membership(
        community.id,
        other_user.id,
        role.id,
        "storycounter",
        "Story Counter",
    )
    other_character = repo.create_character(
        community.id,
        other_membership.id,
        "story-counter-face",
        "Story Counter Face",
    )
    repo.create_character_plot_hook(
        community.id,
        other_membership.id,
        other_character.id,
        "outside-hook",
        "Outside hook",
        summary="A hook for someone else.",
    )
    repo.create_wanted_ad(
        community.id,
        other_membership.id,
        "outside-wanted",
        "Outside wanted",
        summary="A wanted hook for someone else.",
    )

    with pytest.raises(PermissionError):
        services.start_thread(
            board_slug="danger-room",
            character_id=character.id,
            title="Submitted face scene",
            body="This should wait for acceptance.",
        )
    with pytest.raises(PermissionError):
        services.reply_to_thread("danger-room", thread.slug, character.id, "Not yet.")
    with pytest.raises(PermissionError):
        services.create_plot_hook(
            character.slug,
            title="Submitted face hook",
            hook_type="scene",
            summary="This should wait.",
            body="This should wait for acceptance.",
            facet_slugs=[],
        )
    with pytest.raises(PermissionError):
        services.express_plot_hook_interest("story-counter-face", "outside-hook")
    with pytest.raises(PermissionError):
        services.express_wanted_interest("outside-wanted")


def test_wanted_hooks_accept_prospective_character_interest() -> None:
    async def run() -> None:
        _app()
        services = get_services()
        faceless_services = _faceless_services(services, prefix="newface")
        faceless_app = create_app(debug=False, services=faceless_services)
        async with TestClient(faceless_app) as faceless_client:
            wanted = await faceless_client.get("/wanted/human-un-liaison-for-b24")
            assert wanted.status == 200
            assert "I'd create a new character for this" in wanted.text

            response = await faceless_client.post(
                "/wanted/human-un-liaison-for-b24",
                body=urlencode(
                    {
                        "intent": "express_prospective_interest",
                        "prospective_character_name": "Val Cooper",
                        "note": "I would app her as a UN pressure point.",
                    }
                ).encode(),
                headers=_FORM,
            )
            assert response.status == 302

        repo = services.repo
        community = services.seed.community
        wanted_ad = repo.get_wanted_ad_by_slug(community.id, "human-un-liaison-for-b24")
        newface_membership = repo.get_membership_by_username(community.id, "newface")
        prospective = repo.get_prospective_wanted_ad_interest_for_membership(
            community.id,
            wanted_ad.id,
            newface_membership.id,
        )
        assert prospective.character_id is None
        assert prospective.prospective_character_name == "Val Cooper"

        outsider_services, _outsider_character_id = _outsider_services(
            services,
            prefix="wanted-note-outsider",
        )
        outsider_app = create_app(debug=False, services=outsider_services)
        async with TestClient(outsider_app) as outsider_client:
            outsider_view = await outsider_client.get("/wanted/human-un-liaison-for-b24")
            assert outsider_view.status == 200
            assert "Val Cooper" in outsider_view.text
            assert "I would app her as a UN pressure point." not in outsider_view.text

        charlie_membership = repo.get_membership_by_username(community.id, "charlie")
        charlie_user = repo.get_user(charlie_membership.user_id)
        xavier = repo.get_character_by_slug(community.id, "charles-xavier")
        charlie_services = AppServices(
            repo,
            DemoSeed(community, charlie_user, charlie_membership, xavier),
        )
        creator_app = create_app(debug=False, services=charlie_services)
        async with TestClient(creator_app) as creator_client:
            creator_view = await creator_client.get("/wanted/human-un-liaison-for-b24")
            assert creator_view.status == 200
            assert "Val Cooper" in creator_view.text
            assert "I would app her as a UN pressure point." in creator_view.text
            assert "Reserve for Val Cooper" in creator_view.text

            reserve = await creator_client.post(
                "/wanted/human-un-liaison-for-b24",
                body=f"intent=reserve_interest&interest_id={prospective.id}".encode(),
                headers=_FORM,
            )
            assert reserve.status == 302

            reserved_view = await creator_client.get("/wanted/human-un-liaison-for-b24")
            assert reserved_view.status == 200
            assert "Create the character before making a reserve record." in reserved_view.text

        inbox = charlie_services.notifications()
        assert any(item.label == "Wanted interest" for item in inbox.items)

    asyncio.run(run())


def test_plotting_rooms_start_from_wanted_interest() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            response = await client.post(
                "/wanted/human-un-liaison-for-b24",
                body=b"intent=express_interest",
                headers=_FORM,
            )
            assert response.status == 302

        services = get_services()
        repo = services.repo
        community = services.seed.community
        wanted_ad = repo.get_wanted_ad_by_slug(community.id, "human-un-liaison-for-b24")
        rogue = repo.get_character_by_slug(community.id, "rogue")
        interest = repo.get_wanted_ad_interest_for_character(community.id, wanted_ad.id, rogue.id)
        charlie_membership = repo.get_membership_by_username(community.id, "charlie")
        charlie_user = repo.get_user(charlie_membership.user_id)
        xavier = repo.get_character_by_slug(community.id, "charles-xavier")
        charlie_services = AppServices(
            repo,
            DemoSeed(community, charlie_user, charlie_membership, xavier),
        )
        charlie_app = create_app(debug=False, services=charlie_services)
        async with TestClient(charlie_app) as charlie_client:
            creator_view = await charlie_client.get("/wanted/human-un-liaison-for-b24")
            assert creator_view.status == 200
            assert "Start plotting room" in creator_view.text

            room_response = await charlie_client.post(
                "/wanted/human-un-liaison-for-b24",
                body=f"intent=start_plotting_room&interest_id={interest.id}".encode(),
                headers=_FORM,
            )
            assert room_response.status == 302

            room = repo.get_plotting_room_for_wanted_interest(community.id, interest.id)
            room_page = await charlie_client.get(f"/plotting/{room.id}")
            assert room_page.status == 200
            assert "Human UN liaison for B-24 talks: Rogue" in room_page.text
            assert "Charles Xavier" in room_page.text
            assert "Rogue" in room_page.text

            plotting = await charlie_client.get("/plotting")
            assert plotting.status == 200
            assert "Interest Inbox" in plotting.text
            assert "Open plotting room" in plotting.text

        lane_inbox = AppServices(repo, services.seed).notifications()
        assert any(item.label == "Plotting room" for item in lane_inbox.items)
        assert repo.get_wanted_ad_interest(community.id, interest.id).status == "plotting"

    asyncio.run(run())


def test_tenant_prefixed_plotting_room_scopes_live_and_plan_routes() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            response = await client.post(
                "/wanted/human-un-liaison-for-b24",
                body=b"intent=express_interest",
                headers=_FORM,
            )
            assert response.status == 302

        services = get_services()
        repo = services.repo
        community = services.seed.community
        wanted_ad = repo.get_wanted_ad_by_slug(community.id, "human-un-liaison-for-b24")
        rogue = repo.get_character_by_slug(community.id, "rogue")
        interest = repo.get_wanted_ad_interest_for_character(community.id, wanted_ad.id, rogue.id)
        charlie_membership = repo.get_membership_by_username(community.id, "charlie")
        charlie_user = repo.get_user(charlie_membership.user_id)
        xavier = repo.get_character_by_slug(community.id, "charles-xavier")
        charlie_services = AppServices(
            repo,
            DemoSeed(community, charlie_user, charlie_membership, xavier),
        )
        charlie_app = create_app(debug=False, services=charlie_services)
        async with TestClient(charlie_app) as charlie_client:
            room_response = await charlie_client.post(
                "/wanted/human-un-liaison-for-b24",
                body=f"intent=start_plotting_room&interest_id={interest.id}".encode(),
                headers=_FORM,
            )
            assert room_response.status == 302

            room = repo.get_plotting_room_for_wanted_interest(community.id, interest.id)
            room_page = await charlie_client.get(f"/c/{community.slug}/plotting/{room.id}")
            saved = await charlie_client.post(
                f"/c/{community.slug}/plotting/{room.id}",
                body=urlencode(
                    {
                        "intent": "save_plan",
                        "notes": "Talk through the UN pressure point.",
                        "next_step": "Pick the first scene.",
                        "status": "brainstorming",
                    }
                ).encode(),
                headers=_FORM,
            )

        assert room_page.status == 200
        assert "Human UN liaison for B-24 talks: Rogue" in room_page.text
        assert f'href="/c/{community.slug}/plotting"' in room_page.text
        assert f'sse-connect="/c/{community.slug}/plotting/{room.id}/stream"' in room_page.text
        assert f'hx-post="/c/{community.slug}/plotting/{room.id}"' in room_page.text
        assert saved.status == 302
        assert _response_header(saved, "location") == f"/c/{community.slug}/plotting/{room.id}"

    asyncio.run(run())


def test_plotting_room_plan_can_turn_into_scene() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            response = await client.post(
                "/wanted/human-un-liaison-for-b24",
                body=b"intent=express_interest",
                headers=_FORM,
            )
            assert response.status == 302

        services = get_services()
        repo = services.repo
        community = services.seed.community
        wanted_ad = repo.get_wanted_ad_by_slug(community.id, "human-un-liaison-for-b24")
        rogue = repo.get_character_by_slug(community.id, "rogue")
        interest = repo.get_wanted_ad_interest_for_character(community.id, wanted_ad.id, rogue.id)
        charlie_membership = repo.get_membership_by_username(community.id, "charlie")
        charlie_user = repo.get_user(charlie_membership.user_id)
        xavier = repo.get_character_by_slug(community.id, "charles-xavier")
        charlie_services = AppServices(
            repo,
            DemoSeed(community, charlie_user, charlie_membership, xavier),
        )
        charlie_app = create_app(debug=False, services=charlie_services)
        async with TestClient(charlie_app) as charlie_client:
            room_response = await charlie_client.post(
                "/wanted/human-un-liaison-for-b24",
                body=f"intent=start_plotting_room&interest_id={interest.id}".encode(),
                headers=_FORM,
            )
            assert room_response.status == 302

        room = repo.get_plotting_room_for_wanted_interest(community.id, interest.id)
        plotting_board = repo.get_board_by_slug(community.id, "plotting")
        lane_app = create_app(debug=False, services=services)
        async with TestClient(lane_app) as lane_client:
            room_page = await lane_client.get(f"/plotting/{room.id}")
            assert room_page.status == 200
            assert "Room notes" in room_page.text
            assert "Start scene" not in room_page.text

            save_plan = await lane_client.post(
                f"/plotting/{room.id}",
                body=urlencode(
                    {
                        "intent": "save_plan",
                        "status": "ready",
                        "target_board_id": plotting_board.id,
                        "next_step": "Charles opens with the invitation.",
                        "notes": "Rogue arrives with a guarded yes.",
                    }
                ).encode(),
                headers=_FORM,
            )
            assert save_plan.status == 302

            message_response = await lane_client.post(
                f"/plotting/{room.id}",
                body=urlencode(
                    {
                        "intent": "post_message",
                        "body": "I can play Rogue guarded but curious.",
                    }
                ).encode(),
                headers={**_FORM, "HX-Request": "true"},
            )
            assert message_response.status == 200
            assert "plotting-room-composer" in message_response.text

        updated_room = repo.get_plotting_room(community.id, room.id)
        assert updated_room.status == "ready"
        assert updated_room.target_board_id == plotting_board.id
        assert updated_room.next_step == "Charles opens with the invitation."
        assert updated_room.notes == "Rogue arrives with a guarded yes."
        messages = repo.list_plotting_room_messages(community.id, room.id)
        assert len(messages) == 1
        assert messages[0].body == "I can play Rogue guarded but curious."

        outsider_services, _character_id = _outsider_services(services, prefix="roomcrasher")
        outsider_app = create_app(debug=False, services=outsider_services)
        async with TestClient(outsider_app) as outsider_client:
            denied = await outsider_client.get(f"/plotting/{room.id}")
            assert denied.status == 403

        charlie_app = create_app(debug=False, services=charlie_services)
        async with TestClient(charlie_app) as charlie_client:
            refreshed = await charlie_client.get(f"/plotting/{room.id}")
            assert refreshed.status == 200
            assert "Rogue arrives with a guarded yes." in refreshed.text
            assert "I can play Rogue guarded but curious." in refreshed.text
            assert f'sse-connect="/plotting/{room.id}/stream"' in refreshed.text
            assert "Start scene" in refreshed.text

            stream = await charlie_client.sse(
                f"/plotting/{room.id}/stream",
                max_events=1,
                timeout=1.0,
            )
            assert stream.status == 200
            assert stream.events[0].event == "plotting-room-ready"

            scene = await charlie_client.post(
                f"/plotting/{room.id}",
                body=urlencode(
                    {
                        "intent": "start_scene",
                        "board_id": plotting_board.id,
                        "character_id": xavier.id,
                        "title": "B-24 Liaison Debrief",
                        "summary": "Charles and Rogue turn the liaison hook into a scene.",
                        "location": "Xavier Institute",
                        "timeline": "After B-24",
                        "body": "Charles sets tea down and waits for Rogue to decide.",
                    }
                ).encode(),
                headers=_FORM,
            )
            assert scene.status == 302

            threaded_room = repo.get_plotting_room(community.id, room.id)
            assert threaded_room.status == "threaded"
            assert threaded_room.target_thread_id is not None
            created_thread = repo.get_thread(community.id, threaded_room.target_thread_id)
            assert created_thread.title == "B-24 Liaison Debrief"
            assert created_thread.summary == "Charles and Rogue turn the liaison hook into a scene."
            assert created_thread.location == "Xavier Institute"
            assert created_thread.timeline == "After B-24"
            assert {
                character.slug
                for character in repo.list_thread_participants(
                    community.id,
                    created_thread.id,
                )
            } == {"charles-xavier", "rogue"}

            threaded_page = await charlie_client.get(f"/plotting/{room.id}")
            assert threaded_page.status == 200
            assert "Open scene" in threaded_page.text
            assert f"/boards/plotting/threads/{created_thread.slug}" in threaded_page.text
            assert "Start scene" not in threaded_page.text

        lane_inbox = services.notifications()
        assert any(item.label == "Scene started" for item in lane_inbox.items)

    asyncio.run(run())


def test_plotting_room_notifications_do_not_leak_to_non_participants() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            response = await client.post(
                "/wanted/human-un-liaison-for-b24",
                body=b"intent=express_interest",
                headers=_FORM,
            )
            assert response.status == 302

        services = get_services()
        repo = services.repo
        community = services.seed.community
        wanted_ad = repo.get_wanted_ad_by_slug(community.id, "human-un-liaison-for-b24")
        rogue = repo.get_character_by_slug(community.id, "rogue")
        interest = repo.get_wanted_ad_interest_for_character(community.id, wanted_ad.id, rogue.id)
        charlie_membership = repo.get_membership_by_username(community.id, "charlie")
        charlie_user = repo.get_user(charlie_membership.user_id)
        xavier = repo.get_character_by_slug(community.id, "charles-xavier")
        charlie_services = AppServices(
            repo,
            DemoSeed(community, charlie_user, charlie_membership, xavier),
        )
        charlie_app = create_app(debug=False, services=charlie_services)
        async with TestClient(charlie_app) as charlie_client:
            room_response = await charlie_client.post(
                "/wanted/human-un-liaison-for-b24",
                body=f"intent=start_plotting_room&interest_id={interest.id}".encode(),
                headers=_FORM,
            )
            assert room_response.status == 302

        room = repo.get_plotting_room_for_wanted_interest(community.id, interest.id)
        outsider_services, _character_id = _outsider_services(services, prefix="room-notify")
        notification = repo.create_notification(
            community.id,
            outsider_services.seed.membership.id,
            kind="plotting_room_created",
            plotting_room_id=room.id,
            actor_membership_id=charlie_membership.id,
            actor_character_id=xavier.id,
        )
        outsider_app = create_app(debug=False, services=outsider_services)
        async with TestClient(outsider_app) as outsider_client:
            inbox = await outsider_client.get("/notifications")
            open_attempt = await outsider_client.post(
                "/notifications",
                body=urlencode(
                    {
                        "intent": "open",
                        "notification_id": str(notification.id),
                    }
                ).encode(),
                headers=_FORM,
            )
            room_attempt = await outsider_client.get(f"/plotting/{room.id}")

        assert outsider_services.viewer().unread_notification_count == 0
        assert outsider_services.notifications().unread_count == 0
        assert inbox.status == 200
        assert "No notifications are waiting on you." in inbox.text
        assert "Find hooks for Room-Notify Face" in inbox.text
        assert 'href="/characters/room-notify-face#plotter"' in inbox.text
        assert room.title not in inbox.text
        assert "Human UN liaison for B-24 talks: Rogue" not in inbox.text
        assert open_attempt.status == 404
        assert room_attempt.status == 403

    asyncio.run(run())


def test_thread_cards_jump_to_first_unread_then_latest() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        membership = services.seed.membership
        role = repo.get_role_by_slug(community.id, "member")
        outsider_user = repo.create_user("jump@example.com", "hash")
        outsider_membership = repo.create_membership(
            community.id,
            outsider_user.id,
            role.id,
            "jumpwriter",
            "Jump Writer",
        )
        outsider = repo.create_character(
            community.id,
            outsider_membership.id,
            "jump-face",
            "Jump Face",
        )
        board = repo.get_board_by_slug(community.id, "plotting")
        thread = repo.get_thread_by_slug(community.id, board.id, "open-thread-roster")
        repo.mark_thread_read(
            community.id,
            thread.id,
            membership.id,
            read_at="2026-01-01T00:00:00+00:00",
        )
        first_unread = repo.create_post(
            community.id,
            thread.id,
            outsider.id,
            "First unread beat.",
        )
        latest_unread = repo.create_post(
            community.id,
            thread.id,
            outsider.id,
            "Latest unread beat.",
        )
        repo.connection.execute(
            """
            UPDATE posts
            SET created_at = '2025-12-31T23:59:00+00:00',
                updated_at = '2025-12-31T23:59:00+00:00'
            WHERE community_id = ? AND thread_id = ? AND id NOT IN (?, ?)
            """,
            (community.id, thread.id, first_unread.id, latest_unread.id),
        )
        repo.connection.execute(
            """
            UPDATE posts
            SET created_at = '2026-01-01T00:00:01+00:00',
                updated_at = '2026-01-01T00:00:01+00:00'
            WHERE community_id = ? AND id = ?
            """,
            (community.id, first_unread.id),
        )
        repo.connection.execute(
            """
            UPDATE posts
            SET created_at = '2026-01-01T00:00:02+00:00',
                updated_at = '2026-01-01T00:00:02+00:00'
            WHERE community_id = ? AND id = ?
            """,
            (community.id, latest_unread.id),
        )
        repo.connection.execute(
            """
            UPDATE threads
            SET updated_at = '2026-01-01T00:00:02+00:00'
            WHERE community_id = ? AND id = ?
            """,
            (community.id, thread.id),
        )
        repo.connection.commit()

        async with TestClient(app) as client:
            board_response = await client.get("/boards/plotting")
            assert board_response.status == 200
            assert "First unread" in board_response.text
            assert (
                f"/boards/plotting/threads/open-thread-roster#post-{first_unread.post_number}"
                in board_response.text
            )
            assert (
                f"/boards/plotting/threads/open-thread-roster#post-{latest_unread.post_number}"
                not in board_response.text
            )

            thread_response = await client.get("/boards/plotting/threads/open-thread-roster")
            assert thread_response.status == 200

            board_after_read = await client.get("/boards/plotting")
            assert board_after_read.status == 200
            assert "Jump to latest" in board_after_read.text
            assert (
                f"/boards/plotting/threads/open-thread-roster#post-{latest_unread.post_number}"
                in board_after_read.text
            )

    asyncio.run(run())


def test_board_page_next_unread_jumps_to_first_unread_post() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        membership = services.seed.membership
        role = repo.get_role_by_slug(community.id, "member")
        outsider_user = repo.create_user("board-next@example.com", "hash")
        outsider_membership = repo.create_membership(
            community.id,
            outsider_user.id,
            role.id,
            "boardnext",
            "Board Next",
        )
        outsider = repo.create_character(
            community.id,
            outsider_membership.id,
            "board-next-face",
            "Board Next Face",
        )
        board = repo.create_board(community.id, "board-next", "Board Next")
        thread = repo.create_thread(
            community.id,
            board.id,
            outsider.id,
            "board-next-thread",
            "Board Next Thread",
        )
        repo.create_post(
            community.id,
            thread.id,
            outsider.id,
            "The board-level thread exists.",
        )
        repo.connection.execute(
            """
            UPDATE posts
            SET created_at = '2026-01-01T00:00:00+00:00',
                updated_at = '2026-01-01T00:00:00+00:00'
            WHERE community_id = ? AND thread_id = ?
            """,
            (community.id, thread.id),
        )
        repo.connection.execute(
            """
            UPDATE threads
            SET updated_at = '2026-01-01T00:00:00+00:00'
            WHERE community_id = ? AND id = ?
            """,
            (community.id, thread.id),
        )
        repo.connection.commit()
        repo.mark_thread_read(
            community.id,
            thread.id,
            membership.id,
            read_at="2026-01-01T00:00:00+00:00",
        )
        post = repo.create_post(
            community.id,
            thread.id,
            outsider.id,
            "The board-level next unread target.",
        )
        repo.connection.execute(
            """
            UPDATE posts
            SET created_at = '2026-01-01T00:00:01+00:00',
                updated_at = '2026-01-01T00:00:01+00:00'
            WHERE community_id = ? AND id = ?
            """,
            (community.id, post.id),
        )
        repo.connection.execute(
            """
            UPDATE threads
            SET updated_at = '2026-01-01T00:00:01+00:00'
            WHERE community_id = ? AND id = ?
            """,
            (community.id, thread.id),
        )
        repo.connection.commit()

        async with TestClient(app) as client:
            page = await client.get("/boards/board-next")
            assert page.status == 200
            assert "Next unread" in page.text
            assert (
                f"/boards/board-next/threads/board-next-thread#post-{post.post_number}" in page.text
            )

            thread_response = await client.get("/boards/board-next/threads/board-next-thread")
            assert thread_response.status == 200

            caught_up = await client.get("/boards/board-next")
            assert "Next unread" not in caught_up.text

    asyncio.run(run())


def test_reading_thread_clears_unread_marker_for_membership() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            board_before = await client.get("/boards/plotting")
            assert "new replies" in board_before.text

            thread = await client.get("/boards/plotting/threads/open-thread-roster")
            assert thread.status == 200

            board_after = await client.get("/boards/plotting")
            assert ">new replies<" not in board_after.text

    asyncio.run(run())


def test_thread_watch_toggle_controls_thread_notifications() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            thread = await client.get("/boards/plotting/threads/open-thread-roster")
            assert thread.status == 200
            assert "chirpui-thread-reader-layout" in thread.text
            assert "Watch thread" in thread.text

            watched = await client.post(
                "/boards/plotting/threads/open-thread-roster",
                body=b"intent=watch",
                headers=_FORM,
            )
            assert watched.status == 302

            watched_thread = await client.get("/boards/plotting/threads/open-thread-roster")
            assert "watching" in watched_thread.text
            assert "Unwatch thread" in watched_thread.text

            unwatched = await client.post(
                "/boards/plotting/threads/open-thread-roster",
                body=b"intent=unwatch",
                headers=_FORM,
            )
            assert unwatched.status == 302

            unwatched_thread = await client.get("/boards/plotting/threads/open-thread-roster")
            assert "Watch thread" in unwatched_thread.text
            assert "Unwatch thread" not in unwatched_thread.text

    asyncio.run(run())


def test_notifications_track_watched_thread_replies_and_open_read_state() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        services.watch_thread("plotting", "open-thread-roster")
        outsider_services, outsider_character_id = _outsider_services(services, prefix="notify")
        post = outsider_services.reply_to_thread(
            "plotting",
            "open-thread-roster",
            outsider_character_id,
            "A watched reply arrives.",
        )

        async with TestClient(app) as client:
            index = await client.get("/c/x-men-apocalypse")
            assert index.status == 200
            assert "Notifications" in index.text
            assert "elbysodic-sidebar-count" in index.text

            notifications = await client.get("/notifications")
            assert notifications.status == 200
            assert "Watched thread" in notifications.text
            assert "A watched reply arrives." in notifications.text
            assert "Notify Face" in notifications.text
            assert "new" in notifications.text

            item = services.notifications().items[0]
            opened = await client.post(
                "/notifications",
                body=f"intent=open&notification_id={item.notification.id}".encode(),
                headers=_FORM,
            )
            assert opened.status == 302
            assert dict(opened.headers)["location"] == (
                f"/boards/plotting/threads/open-thread-roster#post-{post.post_number}"
            )
            assert services.viewer().unread_notification_count == 0

    asyncio.run(run())


def test_mentions_notify_character_owner_without_thread_watch() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        outsider_services, outsider_character_id = _outsider_services(services, prefix="mention")
        outsider_services.reply_to_thread(
            "plotting",
            "open-thread-roster",
            outsider_character_id,
            "Hey @Rogue, the plotting board needs you.",
        )

        async with TestClient(app) as client:
            thread = await client.get("/boards/plotting/threads/open-thread-roster")
            assert thread.status == 200
            assert 'href="/characters/rogue"' in thread.text
            assert 'data-mention-kind="character"' in thread.text

            notifications = await client.get("/notifications")
            assert notifications.status == 200
            assert "Mention" in notifications.text
            assert "Hey @Rogue, the plotting board needs you." in notifications.text
            assert "Mention Face" in notifications.text

    asyncio.run(run())


def test_writer_mentions_notify_membership_without_thread_watch() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        outsider_services, outsider_character_id = _outsider_services(
            services,
            prefix="writermention",
        )
        outsider_services.reply_to_thread(
            "plotting",
            "open-thread-roster",
            outsider_character_id,
            "Looping in @starlane for the OOC planning bit.",
        )

        async with TestClient(app) as client:
            thread = await client.get("/boards/plotting/threads/open-thread-roster")
            assert thread.status == 200
            assert 'href="/members/starlane"' in thread.text
            assert 'data-mention-kind="writer"' in thread.text

            notifications = await client.get("/notifications")
            assert notifications.status == 200
            assert "Mention" in notifications.text
            assert "Looping in @starlane for the OOC planning bit." in notifications.text
            assert "Writermention Face" in notifications.text

    asyncio.run(run())


def test_members_directory_and_profile_show_visible_community_cast() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        viewer = services.viewer()
        character = viewer.current_character
        assert character is not None
        private_board = repo.create_board(
            community.id,
            "private-lab",
            "Private Lab",
            is_private=True,
        )
        private_thread = repo.create_thread(
            community.id,
            private_board.id,
            character.id,
            "private-notes",
            "Private notes",
        )
        repo.create_post(
            community.id,
            private_thread.id,
            character.id,
            "Private activity should stay private.",
        )
        role = repo.get_role_by_slug(community.id, "member")
        inactive_user = repo.create_user("retired@example.com", "hash")
        inactive_membership = repo.create_membership(
            community.id,
            inactive_user.id,
            role.id,
            "retiredlane",
            "Retired Lane",
        )
        repo.create_character(
            community.id,
            inactive_membership.id,
            "retired-face",
            "Retired Face",
            summary="Retired profile copy should not render.",
        )
        repo.connection.execute(
            "UPDATE community_memberships SET is_active = 0 WHERE community_id = ? AND id = ?",
            (community.id, inactive_membership.id),
        )
        repo.connection.commit()

        async with TestClient(app) as client:
            directory = await client.get("/members")
            assert directory.status == 200
            assert "Members" in directory.text
            assert "Lane" in directory.text
            assert "@starlane" in directory.text
            assert "Known for" in directory.text
            assert "Rogue" in directory.text
            assert "/members/starlane" in directory.text
            assert "Private activity should stay private." not in directory.text
            assert "Retired Lane" not in directory.text
            assert "Retired Face" not in directory.text

            profile = await client.get("/members/starlane")
            assert profile.status == 200
            assert "Current face: Rogue" in profile.text
            assert "Known For" in profile.text
            assert "Current Roles" in profile.text
            assert "Collaborators" in profile.text
            assert "Visible posts" in profile.text
            assert "Open thread roster" in profile.text
            assert "/characters/rogue" in profile.text
            assert "Private notes" not in profile.text
            assert "Private activity should stay private." not in profile.text

            missing = await client.get("/members/nope")
            assert missing.status == 404
            inactive_member = await client.get("/members/retiredlane")
            assert inactive_member.status == 404
            inactive_character = await client.get("/characters/retired-face")
            assert inactive_character.status == 200
            assert "That face is not in X-Men Apocalypse." in inactive_character.text
            assert "Retired profile copy should not render." not in inactive_character.text

    asyncio.run(run())


def test_external_character_profile_links_to_owning_member_without_edit_controls() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        outsider_services, outsider_character_id = _outsider_services(
            services,
            prefix="castmate",
        )
        assert outsider_services is not None
        assert outsider_character_id > 0

        async with TestClient(app) as client:
            profile = await client.get("/characters/castmate-face")
            assert profile.status == 200
            assert "Castmate Face" in profile.text
            assert "/members/castmate" in profile.text
            assert "Edit character" not in profile.text
            assert "Set current face" not in profile.text
            assert "View writer" in profile.text

    asyncio.run(run())


def test_thread_page_links_previous_next_and_next_unread_threads() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        membership = services.seed.membership
        viewer = services.viewer()
        character = viewer.current_character
        assert character is not None
        board = repo.create_board(community.id, "navigation", "Navigation")
        newer = repo.create_thread(community.id, board.id, character.id, "newer", "Newer thread")
        current = repo.create_thread(
            community.id, board.id, character.id, "middle", "Middle thread"
        )
        older = repo.create_thread(community.id, board.id, character.id, "older", "Older thread")
        repo.create_post(community.id, newer.id, character.id, "Newer post.")
        repo.create_post(community.id, current.id, character.id, "Middle post.")
        older_post = repo.create_post(community.id, older.id, character.id, "Older post.")
        repo.connection.execute(
            """
            UPDATE threads
            SET updated_at = CASE id
                WHEN ? THEN '2026-01-01T00:03:00+00:00'
                WHEN ? THEN '2026-01-01T00:02:00+00:00'
                WHEN ? THEN '2026-01-01T00:01:00+00:00'
                ELSE updated_at
            END
            WHERE community_id = ? AND board_id = ?
            """,
            (newer.id, current.id, older.id, community.id, board.id),
        )
        repo.connection.commit()
        repo.mark_thread_read(community.id, newer.id, membership.id)
        role = repo.get_role_by_slug(community.id, "member")
        attention_user = repo.create_user("nav-attention@example.com", "hash")
        attention_membership = repo.create_membership(
            community.id,
            attention_user.id,
            role.id,
            "navattention",
            "Nav Attention",
        )
        attention_character = repo.create_character(
            community.id,
            attention_membership.id,
            "nav-attention-face",
            "Nav Attention Face",
        )
        repo.create_post(
            community.id,
            newer.id,
            attention_character.id,
            "A nearby scene needs a reply.",
        )

        async with TestClient(app) as client:
            page = await client.get("/boards/navigation/threads/middle")
            assert page.status == 200
            assert "Thread navigation" in page.text
            assert "Previous" in page.text
            assert "Previous unreplied" in page.text
            assert "Newer thread" in page.text
            assert "/boards/navigation/threads/newer" in page.text
            assert "Next" in page.text
            assert "Older thread" in page.text
            assert "Next unread" in page.text
            assert f"/boards/navigation/threads/older#post-{older_post.post_number}" in page.text

    asyncio.run(run())


def test_thread_page_bottom_next_unread_uses_visible_community_queue() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        membership = services.seed.membership
        viewer = services.viewer()
        character = viewer.current_character
        assert character is not None
        for existing_thread in repo.list_threads(community.id):
            repo.mark_thread_read(community.id, existing_thread.id, membership.id)
        current_board = repo.create_board(community.id, "current-nav", "Current Nav")
        unread_board = repo.create_board(community.id, "unread-nav", "Unread Nav")
        current = repo.create_thread(
            community.id,
            current_board.id,
            character.id,
            "current-scene",
            "Current scene",
        )
        unread = repo.create_thread(
            community.id,
            unread_board.id,
            character.id,
            "elsewhere-scene",
            "Elsewhere scene",
        )
        repo.create_post(community.id, current.id, character.id, "Current post.")
        unread_post = repo.create_post(
            community.id,
            unread.id,
            character.id,
            "Unread elsewhere.",
        )

        async with TestClient(app) as client:
            page = await client.get("/boards/current-nav/threads/current-scene")
            assert page.status == 200
            assert "Next unread" in page.text
            assert (
                f"/boards/unread-nav/threads/elsewhere-scene#post-{unread_post.post_number}"
                in page.text
            )

    asyncio.run(run())


def test_board_thread_filters_use_roster_participation() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        role = repo.get_role_by_slug(community.id, "member")
        outsider_user = repo.create_user("outsider@example.com", "hash")
        outsider_membership = repo.create_membership(
            community.id,
            outsider_user.id,
            role.id,
            "outsider",
            "Outsider",
        )
        outsider = repo.create_character(
            community.id,
            outsider_membership.id,
            "outsider-face",
            "Outsider Face",
        )
        board = repo.get_board_by_slug(community.id, "plotting")
        outside_thread = repo.create_thread(
            community.id,
            board.id,
            outsider.id,
            "outsider-plot",
            "Outsider plot",
        )
        repo.create_post(
            community.id,
            outside_thread.id,
            outsider.id,
            "A visible thread from another writer.",
        )

        async with TestClient(app) as client:
            all_threads = await client.get("/boards/plotting")
            assert all_threads.status == 200
            assert "Outsider plot" in all_threads.text
            assert "?filter=mine" in all_threads.text
            assert "?filter=unread" in all_threads.text
            assert "?filter=attention" in all_threads.text

            mine = await client.get("/boards/plotting?filter=mine")
            assert mine.status == 200
            assert "Open thread roster" in mine.text
            assert "Outsider plot" not in mine.text
            assert "mine" in mine.text

            pinned = await client.get("/boards/plotting?filter=pinned")
            assert pinned.status == 200
            assert "No pinned threads are in this board yet." in pinned.text

            locked = await client.get("/boards/announcements?filter=locked")
            assert locked.status == 200
            assert "Welcome to the rebuild" in locked.text
            assert "locked" in locked.text

    asyncio.run(run())


def test_attention_surfaces_threads_where_someone_else_posted_last() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        role = repo.get_role_by_slug(community.id, "member")
        outsider_user = repo.create_user("attention@example.com", "hash")
        outsider_membership = repo.create_membership(
            community.id,
            outsider_user.id,
            role.id,
            "attention",
            "Attention",
        )
        outsider = repo.create_character(
            community.id,
            outsider_membership.id,
            "attention-face",
            "Attention Face",
        )
        board = repo.get_board_by_slug(community.id, "plotting")
        thread = repo.get_thread_by_slug(community.id, board.id, "open-thread-roster")
        repo.create_post(
            community.id,
            thread.id,
            outsider.id,
            "A different writer nudges the plot forward.",
        )

        async with TestClient(app) as client:
            index = await client.get("/c/x-men-apocalypse")
            assert index.status == 200
            assert "Needs reply" in index.text
            assert "Open thread roster" in index.text
            assert "Attention Face" in index.text
            assert "A different writer nudges the plot forward." in index.text

            board_attention = await client.get("/boards/plotting?filter=attention")
            assert board_attention.status == 200
            assert "Open thread roster" in board_attention.text
            assert "needs reply" in board_attention.text

            thread_response = await client.get("/boards/plotting/threads/open-thread-roster")
            assert thread_response.status == 200

            cleared = await client.get("/boards/plotting?filter=attention")
            assert cleared.status == 200
            assert "Nothing here needs your roster right now." in cleared.text

            index_after_read = await client.get("/c/x-men-apocalypse")
            assert "Your roster is caught up for now." in index_after_read.text

    asyncio.run(run())


def test_my_threads_tracks_obligations_after_threads_are_read() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        role = repo.get_role_by_slug(community.id, "member")
        outsider_user = repo.create_user("obligation@example.com", "hash")
        outsider_membership = repo.create_membership(
            community.id,
            outsider_user.id,
            role.id,
            "obligation",
            "Obligation",
        )
        outsider = repo.create_character(
            community.id,
            outsider_membership.id,
            "obligation-face",
            "Obligation Face",
        )
        board = repo.get_board_by_slug(community.id, "plotting")
        thread = repo.get_thread_by_slug(community.id, board.id, "open-thread-roster")
        repo.create_post(
            community.id,
            thread.id,
            outsider.id,
            "A different writer puts the ball back in your court.",
        )

        async with TestClient(app) as client:
            read_thread = await client.get("/boards/plotting/threads/open-thread-roster")
            assert read_thread.status == 200

            dashboard = await client.get("/my/threads?character=all")
            assert dashboard.status == 200
            assert "My threads" in dashboard.text
            assert "Needs reply" in dashboard.text
            assert "Waiting on others" in dashboard.text
            assert "Started by me" in dashboard.text
            assert "All participated" in dashboard.text
            assert "Open thread roster" in dashboard.text
            assert "Obligation Face" in dashboard.text
            assert "elbysodic-thread-card__poster" in dashboard.text
            assert "elbysodic-scene-cast--stacked" in dashboard.text
            assert "elbysodic-thread-card__metrics" in dashboard.text
            assert "elbysodic-queue-history" in dashboard.text
            assert "needs reply" in dashboard.text
            assert "Sentinel drill after midnight" in dashboard.text
            assert "waiting" in dashboard.text
            assert "Welcome to the rebuild" not in dashboard.text
            assert "/boards/plotting/threads/open-thread-roster#post-" in dashboard.text

    asyncio.run(run())


def test_my_threads_defaults_to_current_face_lens() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            dashboard = await client.get("/my/threads")
            whole_roster = await client.get("/my/threads?character=all")

        assert dashboard.status == 200
        assert "Character threads" in dashboard.text
        assert "Rogue" in dashboard.text
        assert "Queue lens: Rogue" in dashboard.text
        assert 'href="/my/threads?character=all"' in dashboard.text
        assert "Open thread roster" in dashboard.text
        assert "Welcome to the rebuild" not in dashboard.text
        assert whole_roster.status == 200
        assert "My threads" in whole_roster.text
        assert "Queue lens: whole roster" in whole_roster.text

    asyncio.run(run())


def test_locked_seed_thread_suppresses_reply_composer() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        storm = next(
            character for character in services.viewer().roster if character.name == "Storm"
        )

        async with TestClient(app) as client:
            thread = await client.get("/boards/announcements/threads/welcome-to-the-rebuild")
            assert thread.status == 200
            assert "locked" in thread.text
            assert "Thread locked" in thread.text
            assert "Post reply" not in thread.text

            response = await client.post(
                "/boards/announcements/threads/welcome-to-the-rebuild",
                body=f"character_id={storm.id}&body=Staff+update.".encode(),
                headers=_FORM,
            )
            assert response.status == 200
            assert "cannot reply" in response.text

    asyncio.run(run())


def test_identity_route_changes_default_character_face() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        storm = next(
            character for character in services.viewer().roster if character.name == "Storm"
        )

        async with TestClient(app) as client:
            response = await client.post(
                "/identity",
                body=f"character_id={storm.id}&next=/".encode(),
                headers=_FORM,
            )
            assert response.status == 302

            index = await client.get("/c/x-men-apocalypse")
            assert "Current face: Storm" in index.text

    asyncio.run(run())


def test_theme_stylesheet_is_loaded_and_theme_aware() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            index = await client.get("/c/x-men-apocalypse")
            assert index.status == 200
            assert "/elbysodic-static/elbysodic-theme.css" in index.text

            stylesheet = await client.get("/elbysodic-static/elbysodic-theme.css")
            assert stylesheet.status == 200
            assert '[data-theme="light"]' in stylesheet.text
            assert '[data-theme="system"]' in stylesheet.text

    asyncio.run(run())


def test_character_roster_and_profiles_are_community_scoped() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            roster = await client.get("/characters")
            assert roster.status == 200
            assert "Your roster" in roster.text
            assert "Rogue" in roster.text
            assert "Storm" in roster.text
            assert "Magneto" in roster.text

            profile = await client.get("/characters/rogue")
            assert profile.status == 200
            assert "Power-stealing brawler with a careful heart." in profile.text
            assert "Sentinel drill after midnight" in profile.text
            assert "#post-" in profile.text

    asyncio.run(run())


def test_character_activity_center_tracks_identity_specific_threads() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            roster = await client.get("/characters")
            assert roster.status == 200
            assert "Needs Rogue" in roster.text
            assert "Waiting on Magneto" in roster.text
            assert "/my/threads?character=rogue" in roster.text

            profile = await client.get("/characters/rogue")
            assert profile.status == 200
            assert "Next actions" in profile.text
            assert "active-face defaults on" in profile.text
            assert "Reply as Rogue" in profile.text
            assert "Find play for Rogue" in profile.text
            assert "Casting as Rogue" in profile.text
            assert "Tracker" in profile.text
            assert "Open filtered queue" in profile.text
            assert "Open thread roster" in profile.text
            assert "Sentinel drill after midnight" in profile.text
            assert "needs reply" in profile.text
            assert "waiting" in profile.text

            filtered = await client.get("/my/threads?character=rogue")
            assert filtered.status == 200
            assert "Character threads" in filtered.text
            assert "Rogue · 1" in filtered.text
            assert "Open thread roster" in filtered.text
            assert "Sentinel drill after midnight" in filtered.text
            assert "Welcome to the rebuild" not in filtered.text

    asyncio.run(run())


def test_character_roster_can_create_new_default_character() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            response = await client.post(
                "/characters",
                body=(b"name=Jean+Grey&summary=Telepath+with+a+plot-problem.&make_default=on"),
                headers=_FORM,
            )
            assert response.status == 302

            profile = await client.get("/characters/jean-grey")
            assert profile.status == 200
            assert "Jean Grey" in profile.text
            assert "Telepath with a plot-problem." in profile.text

            index = await client.get("/c/x-men-apocalypse")
            assert "Current face: Jean Grey" in index.text

    asyncio.run(run())


def test_character_profile_can_set_current_face() -> None:
    async def run() -> None:
        app = _app()

        async with TestClient(app) as client:
            pending_profile = await client.get("/characters/storm")
            assert pending_profile.status == 200
            assert "set current for discovery" in pending_profile.text
            assert "Make Storm current" in pending_profile.text

            response = await client.post(
                "/characters/storm",
                body=b"intent=set_default",
                headers=_FORM,
            )
            assert response.status == 302
            assert dict(response.headers)["location"] == "/characters/storm"

            profile = await client.get("/characters/storm")
            assert "current" in profile.text
            assert "active-face defaults on" in profile.text
            assert "Find play for Storm" in profile.text

            index = await client.get("/c/x-men-apocalypse")
            assert "Current face: Storm" in index.text

    asyncio.run(run())


def test_character_profile_can_edit_owned_character() -> None:
    async def run() -> None:
        app = _app()

        async with TestClient(app) as client:
            response = await client.post(
                "/characters/rogue",
                body=(
                    b"intent=save"
                    b"&name=Rogue+Prime"
                    b"&avatar_url=https%3A%2F%2Fexample.test%2Frogue.png"
                    b"&accent_source=custom"
                    b"&accent_color=%2379a889"
                    b"&post_profile_variant=poster"
                    b"&post_accent_style=line"
                    b"&post_border_style=double"
                    b"&post_title_style=mono"
                    b"&post_density=compact"
                    b"&summary=Still+carrying+the+whole+plot."
                ),
                headers=_FORM,
            )
            assert response.status == 302
            assert dict(response.headers)["location"] == "/characters/rogue-prime"

            profile = await client.get("/characters/rogue-prime")
            assert profile.status == 200
            assert "Rogue Prime" in profile.text
            assert "Still carrying the whole plot." in profile.text
            assert "https://example.test/rogue.png" in profile.text
            assert "Post preview" in profile.text
            assert "Custom accent" in profile.text

            thread = await client.get("/boards/danger-room/threads/sentinel-drill")
            assert "Rogue Prime" in thread.text
            assert "elbysodic-post-profile--poster" in thread.text
            assert "elbysodic-post-accent--line" in thread.text
            assert "elbysodic-post-border--double" in thread.text
            assert "elbysodic-post-title--mono" in thread.text
            assert "elbysodic-post-density--compact" in thread.text
            assert "Rogue drops from the observation gantry" in thread.text

    asyncio.run(run())


def test_character_style_preset_applies_approved_post_tokens() -> None:
    async def run() -> None:
        app = _app()

        async with TestClient(app) as client:
            response = await client.post(
                "/characters",
                body=urlencode(
                    {
                        "name": "Jean Grey",
                        "summary": "Telepath with a plot-problem.",
                        "post_style_preset": "faction-dossier",
                    }
                ).encode(),
                headers=_FORM,
            )

            assert response.status == 302
            profile = await client.get("/characters/jean-grey")
            assert profile.status == 200
            assert "Post preview" in profile.text
            assert 'value="crest" selected' in profile.text
            assert 'value="block" selected' in profile.text
            assert 'value="double" selected' in profile.text
            assert 'value="mono" selected' in profile.text
            assert 'value="compact" selected' in profile.text

    asyncio.run(run())


def test_post_shell_inherits_identity_accent_from_facet_group() -> None:
    async def run() -> None:
        app = _app()

        async with TestClient(app) as client:
            thread = await client.get("/boards/danger-room/threads/moonlight-skirmish")
            roster = await client.get("/characters")
            profile = await client.get("/characters/storm")

            assert thread.status == 200
            assert 'style="--elbysodic-character-accent: #60a5fa"' in thread.text
            assert 'style="--elbysodic-character-accent: #79a889"' in thread.text
            assert roster.status == 200
            assert "Affiliation: X-Men" in roster.text
            assert 'style="--elbysodic-character-accent: #60a5fa"' in roster.text
            assert profile.status == 200
            assert "Inherited accent" in profile.text
            assert "Affiliation: X-Men" in profile.text

    asyncio.run(run())


def test_studio_post_style_policy_filters_character_controls() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        community = repo.get_community(services.seed.community.id)
        user = repo.get_user_by_email("moira@example.com")
        membership = repo.get_membership_by_username(community.id, "moira")
        character = repo.get_character_by_slug(community.id, "moira-mactaggert")
        admin_services = AppServices(
            repo,
            DemoSeed(community, user, membership, character),
        )
        app = create_app(debug=False, services=admin_services)

        async with TestClient(app) as client:
            response = await client.post(
                "/studio",
                body=urlencode(
                    {
                        "intent": "post_style_policy",
                        "enabled_post_profile_variants": "bio",
                        "enabled_post_accent_styles": "soft",
                        "enabled_post_border_styles": "hairline",
                        "enabled_post_title_styles": "standard",
                        "enabled_post_densities": "calm",
                    }
                ).encode(),
                headers=_FORM,
            )

            assert response.status == 302
            roster = await client.get("/characters")
            assert roster.status == 200
            assert '<option value="bio" selected>' in roster.text
            assert '<option value="poster"' not in roster.text

            denied = await client.post(
                "/characters",
                body=urlencode(
                    {
                        "name": "Bobby Drake",
                        "summary": "Ice and bad timing.",
                        "post_profile_variant": "poster",
                        "post_accent_style": "soft",
                        "post_border_style": "hairline",
                        "post_title_style": "standard",
                        "post_density": "calm",
                    }
                ).encode(),
                headers=_FORM,
            )
            assert denied.status == 200
            assert "post profile variant is not available" in denied.text

    asyncio.run(run())


def test_studio_can_set_identity_accent_source() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        community = repo.get_community(services.seed.community.id)
        user = repo.get_user_by_email("moira@example.com")
        membership = repo.get_membership_by_username(community.id, "moira")
        character = repo.get_character_by_slug(community.id, "moira-mactaggert")
        admin_services = AppServices(
            repo,
            DemoSeed(community, user, membership, character),
        )
        app = create_app(debug=False, services=admin_services)
        species = repo.get_facet_group_by_slug(community.id, "species")

        async with TestClient(app) as client:
            response = await client.post(
                "/studio",
                body=f"identity_accent_facet_group_id={species.id}".encode(),
                headers=_FORM,
            )

            assert response.status == 302
            assert dict(response.headers)["location"] == "/studio"
            assert repo.get_community(community.id).identity_accent_facet_group_id == species.id

    asyncio.run(run())


def test_director_studio_updates_default_theme_tokens() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        community = repo.get_community(services.seed.community.id)
        user = repo.get_user_by_email("moira@example.com")
        membership = repo.get_membership_by_username(community.id, "moira")
        character = repo.get_character_by_slug(community.id, "moira-mactaggert")
        admin_services = AppServices(
            repo,
            DemoSeed(community, user, membership, character),
        )
        app = create_app(debug=False, services=admin_services)
        body = {
            "intent": "default_theme",
            "theme_slug": "gothic-folk-horror",
            "theme_name": "Gothic Folk Horror",
            "theme_typography_display": "serif",
            "theme_typography_body": "serif",
            "theme_typography_mono": "mono",
            "theme_radius": "square",
            "theme_density": "dramatic",
            "theme_texture": "scanline",
            "theme_light_bg": "#f7f0e8",
            "theme_light_bg_subtle": "#eadfd5",
            "theme_light_surface": "#fffaf4",
            "theme_light_surface_elevated": "#f1e4d9",
            "theme_light_border": "#c8a994",
            "theme_light_text": "#261b18",
            "theme_light_text_muted": "#705c54",
            "theme_light_accent": "#7a2639",
            "theme_light_accent_hover": "#5a1a29",
            "theme_light_accent_dim": "#b36a78",
            "theme_light_accent_secondary": "#315f55",
            "theme_light_success": "#3f7557",
            "theme_light_warning": "#94651d",
            "theme_light_error": "#963333",
            "theme_dark_bg": "#100d0f",
            "theme_dark_bg_subtle": "#1b1518",
            "theme_dark_surface": "#241b20",
            "theme_dark_surface_elevated": "#30242a",
            "theme_dark_border": "#6a4b55",
            "theme_dark_text": "#f7ece7",
            "theme_dark_text_muted": "#c9b2ac",
            "theme_dark_accent": "#d98aa0",
            "theme_dark_accent_hover": "#efafbf",
            "theme_dark_accent_dim": "#7c4050",
            "theme_dark_accent_secondary": "#8ec0a0",
            "theme_dark_success": "#8ec0a0",
            "theme_dark_warning": "#d7ad63",
            "theme_dark_error": "#ec8b8b",
        }

        async with TestClient(app) as client:
            response = await client.post(
                "/studio",
                body=urlencode(body).encode(),
                headers=_FORM,
            )
            index = await client.get("/c/x-men-apocalypse")

        theme = repo.get_default_theme(community.id)
        assert response.status == 302
        assert _response_header(response, "location") == "/studio#appearance-theme"
        assert theme is not None
        assert theme.slug == "gothic-folk-horror"
        assert theme.name == "Gothic Folk Horror"
        tokens = json.loads(theme.tokens_json)
        assert tokens["texture"] == "scanline"
        assert tokens["density"] == "dramatic"
        assert tokens["typography"]["display"] == "serif"
        assert tokens["dark"]["accent"] == "#d98aa0"
        assert index.status == 200
        assert "--chirpui-accent: #d98aa0;" in index.text
        assert "--elbysodic-program-density: dramatic;" in index.text

    asyncio.run(run())


def test_director_studio_surfaces_theme_health_warnings() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        community = repo.get_community(services.seed.community.id)
        user = repo.get_user_by_email("moira@example.com")
        membership = repo.get_membership_by_username(community.id, "moira")
        character = repo.get_character_by_slug(community.id, "moira-mactaggert")
        admin_services = AppServices(
            repo,
            DemoSeed(community, user, membership, character),
        )
        admin_services.update_default_theme(
            slug="low-contrast",
            name="Low Contrast",
            typography_display="system",
            typography_body="system",
            typography_mono="mono",
            radius="sm",
            density="calm",
            texture="none",
            light={
                "bg": "#f0f0f0",
                "bg_subtle": "#eeeeee",
                "surface": "#f2f2f2",
                "surface_elevated": "#f3f3f3",
                "border": "#dddddd",
                "text": "#f1f1f1",
                "text_muted": "#eeeeee",
                "accent": "#f0eeee",
                "accent_hover": "#e8e8e8",
                "accent_dim": "#eeeeee",
                "accent_secondary": "#eeeeee",
                "success": "#eeeeee",
                "warning": "#eeeeee",
                "error": "#eeeeee",
            },
            dark={
                "bg": "#101010",
                "bg_subtle": "#161616",
                "surface": "#181818",
                "surface_elevated": "#202020",
                "border": "#343434",
                "text": "#f8f8f8",
                "text_muted": "#bbbbbb",
                "accent": "#d98aa0",
                "accent_hover": "#efafbf",
                "accent_dim": "#7c4050",
                "accent_secondary": "#8ec0a0",
                "success": "#8ec0a0",
                "warning": "#d7ad63",
                "error": "#ec8b8b",
            },
        )
        app = create_app(debug=False, services=admin_services)

        async with TestClient(app) as client:
            studio = await client.get("/studio")

        assert studio.status == 200
        assert "Theme Health" in studio.text
        assert "Guidebook body text may be hard to read" in studio.text
        assert "Muted metadata may fade too far back" in studio.text
        assert "Accent actions may not stand out" in studio.text

    asyncio.run(run())


def test_director_studio_updates_world_hero_media() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        community = repo.get_community(services.seed.community.id)
        user = repo.get_user_by_email("moira@example.com")
        membership = repo.get_membership_by_username(community.id, "moira")
        character = repo.get_character_by_slug(community.id, "moira-mactaggert")
        admin_services = AppServices(
            repo,
            DemoSeed(community, user, membership, character),
        )
        app = create_app(debug=False, services=admin_services)

        async with TestClient(app) as client:
            response = await client.post(
                "/studio",
                body=urlencode(
                    {
                        "intent": "community_media",
                        "community_mark_url": "https://example.test/mark.png",
                        "community_mark_alt": "X-Men mark",
                        "world_hero_image_url": "https://example.test/world.jpg",
                        "world_hero_image_alt": "A fog-covered academy at night",
                        "world_hero_treatment": "background",
                        "world_hero_focal_point": "top",
                        "world_hero_overlay": "heavy",
                        "world_hero_height": "immersive",
                    }
                ).encode(),
                headers=_FORM,
            )
            home = await client.get("/c/x-men-apocalypse")
            studio = await client.get("/studio")

        updated = repo.get_community(community.id)
        assert response.status == 302
        assert _response_header(response, "location") == "/studio#appearance-media"
        assert updated.world_hero_image_url == "https://example.test/world.jpg"
        assert updated.world_hero_treatment == "background"
        assert updated.world_hero_focal_point == "top"
        assert updated.world_hero_overlay == "heavy"
        assert updated.world_hero_height == "immersive"
        assert home.status == 200
        assert "elbysodic-world-hero--with-media" in home.text
        assert "elbysodic-world-hero--background" in home.text
        assert "elbysodic-world-hero--height-immersive" in home.text
        assert "elbysodic-world-hero--overlay-heavy" in home.text
        assert "elbysodic-world-hero--focal-top" in home.text
        assert 'src="https://example.test/world.jpg"' in home.text
        assert 'alt="A fog-covered academy at night"' in home.text
        assert studio.status == 200
        assert "Community media" in studio.text
        assert "https://example.test/world.jpg" in studio.text
        assert '<option value="background" selected>Full background</option>' in studio.text

    asyncio.run(run())


def test_director_studio_rejects_unsupported_hero_treatment() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        community = repo.get_community(services.seed.community.id)
        user = repo.get_user_by_email("moira@example.com")
        membership = repo.get_membership_by_username(community.id, "moira")
        character = repo.get_character_by_slug(community.id, "moira-mactaggert")
        admin_services = AppServices(
            repo,
            DemoSeed(community, user, membership, character),
        )
        app = create_app(debug=False, services=admin_services)

        async with TestClient(app) as client:
            response = await client.post(
                "/studio",
                body=urlencode(
                    {
                        "intent": "community_media",
                        "community_mark_url": "",
                        "community_mark_alt": "",
                        "world_hero_image_url": "https://example.test/world.jpg",
                        "world_hero_image_alt": "A fog-covered academy at night",
                        "world_hero_treatment": "raw-css",
                        "world_hero_focal_point": "center",
                        "world_hero_overlay": "medium",
                        "world_hero_height": "standard",
                    }
                ).encode(),
                headers=_FORM,
            )

        updated = repo.get_community(community.id)
        assert response.status == 200
        assert "world hero treatment is not supported" in response.text
        assert updated.world_hero_treatment == "split"

    asyncio.run(run())


def test_reply_uses_selected_character() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        storm = next(
            character for character in services.viewer().roster if character.name == "Storm"
        )

        async with TestClient(app) as client:
            response = await client.post(
                "/boards/plotting/threads/open-thread-roster",
                body=f"character_id={storm.id}&body=Lightning+answers.".encode(),
                headers=_FORM,
            )
            assert response.status == 302
            assert dict(response.headers)["location"].startswith(
                "/boards/plotting/threads/open-thread-roster#post-"
            )

            thread = await client.get("/boards/plotting/threads/open-thread-roster")
            assert "Lightning answers." in thread.text
            assert "Storm" in thread.text
            assert 'role="toolbar"' in thread.text
            assert 'aria-label="Bold"' in thread.text

    asyncio.run(run())


def test_thread_posts_render_safe_markup() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        storm = next(
            character for character in services.viewer().roster if character.name == "Storm"
        )
        body = (
            "**Lightning** answers.\n\n"
            "> Hold the line.\n\n"
            "[Briefing](https://example.test/briefing) "
            '<script>alert("x")</script>'
        )

        async with TestClient(app) as client:
            response = await client.post(
                "/boards/plotting/threads/open-thread-roster",
                body=urlencode({"character_id": storm.id, "body": body}).encode(),
                headers=_FORM,
            )
            assert response.status == 302

            thread = await client.get("/boards/plotting/threads/open-thread-roster")
            assert "<strong>Lightning</strong> answers." in thread.text
            assert "<blockquote><p>Hold the line.</p></blockquote>" in thread.text
            assert 'href="https://example.test/briefing"' in thread.text
            assert '<script>alert("x")</script>' not in thread.text
            assert "&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;" in thread.text

    asyncio.run(run())


def test_writer_can_edit_own_post_with_safe_markup() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        storm = next(
            character for character in services.viewer().roster if character.name == "Storm"
        )

        async with TestClient(app) as client:
            created = await client.post(
                "/boards/plotting/threads/open-thread-roster",
                body=urlencode({"character_id": storm.id, "body": "Original typo."}).encode(),
                headers=_FORM,
            )
            assert created.status == 302
            post_number = dict(created.headers)["location"].split("#post-")[1]

            edit_form = await client.get(
                f"/boards/plotting/threads/open-thread-roster/posts/{post_number}/edit"
            )
            assert edit_form.status == 200
            assert "Edit post" in edit_form.text
            assert "Original typo." in edit_form.text
            assert "edit-post-composer-config" in edit_form.text
            assert 'role="toolbar"' in edit_form.text
            assert 'aria-label="Bold"' in edit_form.text

            edited = await client.post(
                f"/boards/plotting/threads/open-thread-roster/posts/{post_number}/edit",
                body=urlencode(
                    {
                        "body": (
                            '**Updated** line.\n\n> Edited safely.\n\n<script>alert("x")</script>'
                        )
                    }
                ).encode(),
                headers=_FORM,
            )
            assert edited.status == 302
            assert dict(edited.headers)["location"] == (
                f"/boards/plotting/threads/open-thread-roster#post-{post_number}"
            )

            thread = await client.get("/boards/plotting/threads/open-thread-roster")
            assert "Original typo." not in thread.text
            assert "<strong>Updated</strong> line." in thread.text
            assert "<blockquote><p>Edited safely.</p></blockquote>" in thread.text
            assert '<script>alert("x")</script>' not in thread.text
            assert "&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;" in thread.text
            assert "edited" in thread.text
            assert f"/posts/{post_number}/revisions" in thread.text
            assert f"/posts/{post_number}/edit" in thread.text

            revisions = await client.get(
                f"/boards/plotting/threads/open-thread-roster/posts/{post_number}/revisions"
            )
            assert revisions.status == 200
            assert "Post history" in revisions.text
            assert "Revision 1" in revisions.text
            assert "Original typo." in revisions.text
            assert "**Updated** line." in revisions.text
            assert "/members/starlane" in revisions.text

    asyncio.run(run())


def test_noop_post_edit_does_not_create_revision() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        storm = next(
            character for character in services.viewer().roster if character.name == "Storm"
        )

        async with TestClient(app) as client:
            created = await client.post(
                "/boards/plotting/threads/open-thread-roster",
                body=urlencode({"character_id": storm.id, "body": "Already polished."}).encode(),
                headers=_FORM,
            )
            assert created.status == 302
            post_number = int(dict(created.headers)["location"].split("#post-")[1])
            board = repo.get_board_by_slug(services.seed.community.id, "plotting")
            thread = repo.get_thread_by_slug(
                services.seed.community.id,
                board.id,
                "open-thread-roster",
            )
            original = repo.get_post_by_number(
                services.seed.community.id,
                thread.id,
                post_number,
            )

            edited = await client.post(
                f"/boards/plotting/threads/open-thread-roster/posts/{post_number}/edit",
                body=urlencode({"body": "Already polished."}).encode(),
                headers=_FORM,
            )
            assert edited.status == 302

            unchanged = repo.get_post(services.seed.community.id, original.id)
            assert unchanged.updated_at == original.updated_at
            assert repo.list_post_revisions(services.seed.community.id, original.id) == []

    asyncio.run(run())


def test_writer_cannot_edit_someone_elses_post() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        role = repo.get_role_by_slug(community.id, "member")
        outsider_user = repo.create_user("not-yours@example.com", "hash")
        outsider_membership = repo.create_membership(
            community.id,
            outsider_user.id,
            role.id,
            "notyours",
            "Not Yours",
        )
        outsider = repo.create_character(
            community.id,
            outsider_membership.id,
            "not-yours-face",
            "Not Yours Face",
        )
        board = repo.get_board_by_slug(community.id, "plotting")
        thread = repo.get_thread_by_slug(community.id, board.id, "open-thread-roster")
        outsider_post = repo.create_post(
            community.id,
            thread.id,
            outsider.id,
            "This belongs to another writer.",
        )

        async with TestClient(app) as client:
            edit_form = await client.get(
                "/boards/plotting/threads/open-thread-roster/posts/"
                f"{outsider_post.post_number}/edit"
            )
            assert edit_form.status == 403

            edited = await client.post(
                "/boards/plotting/threads/open-thread-roster/posts/"
                f"{outsider_post.post_number}/edit",
                body=urlencode({"body": "Trying to overwrite."}).encode(),
                headers=_FORM,
            )
            assert edited.status == 403
            assert repo.get_post(community.id, outsider_post.id).body == (
                "This belongs to another writer."
            )
            assert repo.list_post_revisions(community.id, outsider_post.id) == []

    asyncio.run(run())


def test_locked_threads_still_allow_editing_own_existing_post() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        board = repo.get_board_by_slug(community.id, "announcements")
        thread = repo.get_thread_by_slug(community.id, board.id, "welcome-to-the-rebuild")
        post = repo.list_posts(community.id, thread.id)[0]

        async with TestClient(app) as client:
            response = await client.post(
                "/boards/announcements/threads/welcome-to-the-rebuild/posts/"
                f"{post.post_number}/edit",
                body=urlencode({"body": "Updated staff note."}).encode(),
                headers=_FORM,
            )
            assert response.status == 302

            restored = await client.get("/boards/announcements/threads/welcome-to-the-rebuild")
            assert "Updated staff note." in restored.text
            assert "Thread locked" in restored.text

    asyncio.run(run())


def test_staff_can_pin_and_lock_threads() -> None:
    async def run() -> None:
        app, repo, community, thread = _moderation_app(is_admin=True)

        async with TestClient(app) as client:
            page = await client.get("/boards/ic/threads/moderation-queue")
            assert page.status == 200
            assert "Staff controls" in page.text
            assert "Pin thread" in page.text
            assert "Lock thread" in page.text
            assert "Move thread" in page.text

            pinned = await client.post(
                "/boards/ic/threads/moderation-queue",
                body=b"intent=pin",
                headers=_FORM,
            )
            assert pinned.status == 302
            assert repo.get_thread(community.id, thread.id).is_pinned is True

            locked = await client.post(
                "/boards/ic/threads/moderation-queue",
                body=b"intent=lock",
                headers=_FORM,
            )
            assert locked.status == 302
            assert repo.get_thread(community.id, thread.id).is_locked is True

            updated = await client.get("/boards/ic/threads/moderation-queue")
            assert "pinned" in updated.text
            assert "locked" in updated.text
            assert "Unpin thread" in updated.text
            assert "Unlock thread" in updated.text

            unpinned = await client.post(
                "/boards/ic/threads/moderation-queue",
                body=b"intent=unpin",
                headers=_FORM,
            )
            assert unpinned.status == 302
            assert repo.get_thread(community.id, thread.id).is_pinned is False

            unlocked = await client.post(
                "/boards/ic/threads/moderation-queue",
                body=b"intent=unlock",
                headers=_FORM,
            )
            assert unlocked.status == 302
            assert repo.get_thread(community.id, thread.id).is_locked is False

    asyncio.run(run())


def test_staff_can_move_thread_without_rewriting_thread_history() -> None:
    async def run() -> None:
        app, repo, community, thread = _moderation_app(is_admin=True)
        target_board = repo.get_board_by_slug(community.id, "archive")
        original = repo.get_thread(community.id, thread.id)
        post = repo.list_posts(community.id, thread.id)[0]
        repo.create_post_revision(
            community.id,
            post.id,
            post.author_membership_id,
            "Old wording.",
            post.body,
        )
        repo.mark_thread_read(
            community.id,
            thread.id,
            post.author_membership_id,
            read_at="2026-01-01T00:00:00+00:00",
        )

        async with TestClient(app) as client:
            response = await client.post(
                "/boards/ic/threads/moderation-queue",
                body=f"intent=move&target_board_id={target_board.id}".encode(),
                headers=_FORM,
            )
            assert response.status == 302
            assert dict(response.headers)["location"] == "/boards/archive/threads/moderation-queue"

            moved = repo.get_thread(community.id, thread.id)
            assert moved.board_id == target_board.id
            assert moved.slug == original.slug
            assert moved.title == original.title
            assert moved.updated_at == original.updated_at
            assert [restored.body for restored in repo.list_posts(community.id, moved.id)] == [
                "A thread ready for staff tools."
            ]
            assert len(repo.list_post_revisions(community.id, post.id)) == 1
            assert repo.get_thread_read_at(community.id, moved.id, post.author_membership_id) == (
                "2026-01-01T00:00:00+00:00"
            )

            new_page = await client.get("/boards/archive/threads/moderation-queue")
            assert new_page.status == 200
            assert "Archive" in new_page.text
            assert "A thread ready for staff tools." in new_page.text

    asyncio.run(run())


def test_regular_members_cannot_manage_thread_lifecycle() -> None:
    async def run() -> None:
        app, repo, community, thread = _moderation_app(is_admin=False)
        target_board = repo.get_board_by_slug(community.id, "archive")

        async with TestClient(app) as client:
            page = await client.get("/boards/ic/threads/moderation-queue")
            assert page.status == 200
            assert "Staff controls" not in page.text

            lock_response = await client.post(
                "/boards/ic/threads/moderation-queue",
                body=b"intent=lock",
                headers=_FORM,
            )
            assert lock_response.status == 403

            move_response = await client.post(
                "/boards/ic/threads/moderation-queue",
                body=f"intent=move&target_board_id={target_board.id}".encode(),
                headers=_FORM,
            )
            assert move_response.status == 403
            assert repo.get_thread(community.id, thread.id).is_locked is False
            assert repo.get_thread(community.id, thread.id).is_pinned is False
            assert repo.get_thread(community.id, thread.id).board_id != target_board.id

    asyncio.run(run())


def test_start_thread_creates_opening_post_as_selected_character() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        roster = services.viewer().roster
        magneto = next(character for character in roster if character.name == "Magneto")
        xavier = services.repo.get_character_by_slug(
            services.seed.community.id,
            "charles-xavier",
        )

        async with TestClient(app) as client:
            form = await client.get("/boards/danger-room/threads/new")
            assert form.status == 200
            assert "Start thread" in form.text
            assert "elbysodicComposer" in form.text
            assert "thread-composer-config" in form.text
            assert "Post as" in form.text
            assert "Scene summary" in form.text
            assert "Tag cast" in form.text
            assert "elbysodicMentionPicker" in form.text
            assert "/mentionables/search" in form.text
            assert (
                re.search(
                    rf'<input type="checkbox"\s+name="participant_ids"\s+value="{magneto.id}"',
                    form.text,
                )
                is None
            )
            assert "Open to join" in form.text
            assert "Posting order" in form.text
            assert 'role="toolbar"' in form.text
            assert 'aria-label="Bold"' in form.text
            assert 'aria-label="Italic"' in form.text
            assert 'aria-label="Quote"' in form.text
            assert 'aria-label="Link"' in form.text
            assert "Power-stealing brawler with a careful heart." in form.text

            response = await client.post(
                "/boards/danger-room/threads/new",
                body=urlencode(
                    {
                        "character_id": magneto.id,
                        "participant_ids": [xavier.id],
                        "title": "Metal and Memory",
                        "status": "open",
                        "location": "Sublevel 3",
                        "timeline": "Before breakfast",
                        "summary": "Magneto tags Xavier into an unreasonable simulation.",
                        "posting_mode": "posting_order",
                        "body": "Magneto sets the simulation to unfair.",
                    },
                    doseq=True,
                ).encode(),
                headers=_FORM,
            )
            assert response.status == 302
            assert dict(response.headers)["location"].startswith(
                "/boards/danger-room/threads/metal-and-memory#post-"
            )

            thread = await client.get("/boards/danger-room/threads/metal-and-memory")
            assert thread.status == 200
            assert "Metal and Memory" in thread.text
            assert "Magneto sets the simulation to unfair." in thread.text
            assert "Magneto" in thread.text
            assert "Scene details" in thread.text
            assert "open to join" in thread.text
            assert "Sublevel 3" in thread.text
            assert "Before breakfast" in thread.text
            assert "Magneto tags Xavier into an unreasonable simulation." in thread.text
            assert "/characters/charles-xavier" in thread.text

            board = await client.get("/boards/danger-room")
            assert "Metal and Memory" in board.text
            assert "Started by" in board.text
            assert "open to join" in board.text
            assert "Sublevel 3" in board.text
            assert "Latest" in board.text
            assert "/members/starlane" in board.text

    asyncio.run(run())


def test_mentionable_search_supports_character_and_writer_scopes() -> None:
    async def run() -> None:
        app = _app()

        async with TestClient(app) as client:
            cast = await client.get("/mentionables/search?q=char&scope=cast")
            assert cast.status == 200
            cast_payload = json.loads(cast.body)
            assert cast_payload["items"][0]["kind"] == "character"
            assert cast_payload["items"][0]["handle"] == "charles-xavier"

            own_roster = await client.get("/mentionables/search?q=rogue&scope=cast")
            assert own_roster.status == 200
            assert json.loads(own_roster.body)["items"] == []

            ooc = await client.get("/mentionables/search?q=star&scope=ooc")
            assert ooc.status == 200
            ooc_payload = json.loads(ooc.body)
            assert ooc_payload["items"][0]["kind"] == "writer"
            assert ooc_payload["items"][0]["handle"] == "starlane"

    asyncio.run(run())


def test_open_thread_can_be_joined_as_active_face() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        plotting = repo.get_board_by_slug(community.id, "plotting")
        xavier = repo.get_character_by_slug(community.id, "charles-xavier")
        thread = repo.create_thread(
            community.id,
            plotting.id,
            xavier.id,
            "telepathy-office-hours",
            "Telepathy office hours",
            status="open",
            summary="Charles opens the study for whoever needs to talk.",
        )
        repo.create_post(
            community.id,
            thread.id,
            xavier.id,
            "Charles leaves the study door open and waits.",
        )

        async with TestClient(app) as client:
            page = await client.get("/boards/plotting/threads/telepathy-office-hours")
            assert page.status == 200
            assert "Join as Rogue" in page.text
            assert "watching" not in page.text

            joined = await client.post(
                "/boards/plotting/threads/telepathy-office-hours",
                body=b"intent=join_scene",
                headers=_FORM,
            )
            assert joined.status == 302

            assert {
                character.slug
                for character in repo.list_thread_participants(community.id, thread.id)
            } == {"charles-xavier", "rogue"}
            assert repo.is_thread_watched(community.id, thread.id, services.seed.membership.id)

            joined_page = await client.get("/boards/plotting/threads/telepathy-office-hours")
            assert joined_page.status == 200
            assert "Join as Rogue" not in joined_page.text
            assert 'aria-label="Rogue"' in joined_page.text
            assert "watching" in joined_page.text

    asyncio.run(run())


def test_non_open_threads_do_not_show_join_action() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        danger_room = repo.get_board_by_slug(community.id, "danger-room")
        xavier = repo.get_character_by_slug(community.id, "charles-xavier")
        thread = repo.create_thread(
            community.id,
            danger_room.id,
            xavier.id,
            "closed-practice",
            "Closed practice",
            status="active",
        )
        repo.create_post(
            community.id,
            thread.id,
            xavier.id,
            "This practice has already started.",
        )

        async with TestClient(app) as client:
            page = await client.get("/boards/danger-room/threads/closed-practice")
            assert page.status == 200
            assert "Join as Rogue" not in page.text

    asyncio.run(run())


def test_thread_view_hides_unspecified_scene_metadata() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        role = repo.get_role_by_slug(community.id, "member")
        author_user = repo.create_user("quiet-scene-author@example.com", "hash")
        author_membership = repo.create_membership(
            community.id,
            author_user.id,
            role.id,
            "quietauthor",
            "Quiet Author",
        )
        author = repo.create_character(
            community.id,
            author_membership.id,
            "quiet-author-face",
            "Quiet Author Face",
        )
        board = repo.get_board_by_slug(community.id, "danger-room")
        thread = repo.create_thread(
            community.id,
            board.id,
            author.id,
            "quiet-default-scene",
            "Quiet default scene",
        )
        repo.create_post(
            community.id,
            thread.id,
            author.id,
            "Rogue waits for someone else to make the first bad decision.",
        )

        async with TestClient(app) as client:
            page = await client.get("/boards/danger-room/threads/quiet-default-scene")
            assert page.status == 200
            assert "Scene details" in page.text
            assert "Scene management" not in page.text
            assert "Unspecified" not in page.text
            assert "Freeform" not in page.text
            assert "open to join" not in page.text

    asyncio.run(run())


def test_thread_starter_can_manage_scene_cast() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        board = repo.get_board_by_slug(community.id, "danger-room")
        thread = repo.get_thread_by_slug(community.id, board.id, "sentinel-drill")
        kitty = repo.get_character_by_slug(community.id, "kitty-pryde")
        xavier = repo.get_character_by_slug(community.id, "charles-xavier")

        async with TestClient(app) as client:
            page = await client.get("/boards/danger-room/threads/sentinel-drill")
            assert page.status == 200
            assert "Scene management" in page.text
            assert "Tag cast" in page.text
            assert "Charles Xavier" in page.text

            response = await client.post(
                "/boards/danger-room/threads/sentinel-drill",
                body=urlencode(
                    {
                        "intent": "scene",
                        "status": "paused",
                        "posting_mode": "freeform",
                        "location": "West lawn",
                        "timeline": "After inspection",
                        "summary": "Rogue calls a timeout before the simulation gets personal.",
                        "participant_ids": str(kitty.id),
                    }
                ).encode(),
                headers=_FORM,
            )
            assert response.status in {302, 303}

            updated = repo.get_thread(community.id, thread.id)
            assert updated.status == "paused"
            assert updated.location == "West lawn"
            assert updated.timeline == "After inspection"
            assert updated.summary == "Rogue calls a timeout before the simulation gets personal."
            assert updated.posting_mode == "freeform"
            assert {
                character.slug
                for character in repo.list_thread_participants(community.id, thread.id)
            } == {"rogue", "kitty-pryde"}
            assert xavier.id not in repo.list_thread_participant_ids(community.id, thread.id)

            rendered = await client.get("/boards/danger-room/threads/sentinel-drill")
            assert rendered.status == 200
            assert "paused" in rendered.text
            assert "West lawn" in rendered.text
            assert "After inspection" in rendered.text
            assert "Rogue calls a timeout before the simulation gets personal." in rendered.text

    asyncio.run(run())


def test_file_backed_services_persist_created_threads(tmp_path: Path) -> None:
    db_path = tmp_path / "elbysodic.sqlite3"
    services = create_services(path=db_path)
    viewer = services.viewer()
    assert viewer.current_character is not None

    thread = services.start_thread(
        board_slug="danger-room",
        character_id=viewer.current_character.id,
        title="Persistent Moonlight",
        body="This scene survives the next service boot.",
    )

    restarted = create_services(path=db_path)
    restored = restarted.read_thread("danger-room", thread.slug)
    assert restored.thread.title == "Persistent Moonlight"
    assert [post.post.body for post in restored.posts] == [
        "This scene survives the next service boot."
    ]
    assert len(restarted.viewer().roster) == 3


def test_start_thread_rolls_back_when_late_write_fails(monkeypatch) -> None:
    services = create_services(path=":memory:")
    viewer = services.viewer()
    assert viewer.current_character is not None
    board = services.repo.get_board_by_slug(viewer.community.id, "danger-room")
    before = [thread.slug for thread in services.repo.list_threads(viewer.community.id, board.id)]

    def fail_mark_thread_read(
        community_id: int,
        thread_id: int,
        membership_id: int,
    ) -> None:
        raise RuntimeError("simulated read-state failure")

    monkeypatch.setattr(services.repo, "mark_thread_read", fail_mark_thread_read)

    with pytest.raises(RuntimeError, match="simulated read-state failure"):
        services.start_thread(
            board_slug="danger-room",
            character_id=viewer.current_character.id,
            title="Rollback Drill",
            body="This scene should not survive a failed read-state write.",
        )

    after = [thread.slug for thread in services.repo.list_threads(viewer.community.id, board.id)]
    assert after == before
    assert "rollback-drill" not in after


def test_startup_seed_preserves_director_edited_boards_and_materials(tmp_path: Path) -> None:
    db_path = tmp_path / "elbysodic.sqlite3"
    services = create_services(path=db_path)
    repo = services.repo
    community = services.viewer().community
    board = repo.get_board_by_slug(community.id, "danger-room")
    material = repo.get_material_by_slug(community.id, "b-24-winter")

    repo.update_board(
        community.id,
        board.id,
        name="Danger Room After Hours",
        description="A director-customized simulation wing.",
        sort_order=board.sort_order,
        parent_board_id=board.parent_board_id,
        board_kind=board.board_kind,
        sidebar_section=board.sidebar_section,
        tagline="Custom director pressure.",
        image_url="/custom-danger-room.webp",
        image_alt="Custom Danger Room art",
        image_treatment=board.image_treatment,
        image_focal_point=board.image_focal_point,
        image_overlay=board.image_overlay,
        is_private=board.is_private,
        navigation_order=board.navigation_order,
        show_in_navigation=board.show_in_navigation,
    )
    repo.update_material(
        community.id,
        material.id,
        title="B-24 Winter Custom Briefing",
        material_type=material.material_type,
        summary="Director-edited event summary.",
        body="Director-edited event body.",
        status=material.status,
        sort_order=material.sort_order,
        is_featured=material.is_featured,
    )

    restarted = create_services(path=db_path)
    restored_board = restarted.repo.get_board_by_slug(community.id, "danger-room")
    restored_material = restarted.repo.get_material_by_slug(community.id, "b-24-winter")

    assert restored_board.name == "Danger Room After Hours"
    assert restored_board.description == "A director-customized simulation wing."
    assert restored_board.tagline == "Custom director pressure."
    assert restored_board.image_url == "/custom-danger-room.webp"
    assert restored_board.image_alt == "Custom Danger Room art"
    assert restored_material.title == "B-24 Winter Custom Briefing"
    assert restored_material.summary == "Director-edited event summary."
    assert restored_material.body == "Director-edited event body."


def test_composer_pages_point_empty_roster_to_character_setup() -> None:
    async def run() -> None:
        connection = connect(check_same_thread=False)
        create_schema(connection)
        repo = ForumRepository(connection)
        community = repo.seed_default_community("Empty Roster")
        role = repo.create_role(community.id, "member", "Member")
        user = repo.create_user("empty@example.com", "hash")
        membership = repo.create_membership(
            community.id,
            user.id,
            role.id,
            "empty",
            "Empty",
        )
        author_user = repo.create_user("author@example.com", "hash")
        author_membership = repo.create_membership(
            community.id,
            author_user.id,
            role.id,
            "author",
            "Author",
        )
        author = repo.create_character(
            community.id,
            author_membership.id,
            "author-face",
            "Author Face",
        )
        board = repo.create_board(community.id, "ic", "In Character")
        thread = repo.create_thread(
            community.id,
            board.id,
            author.id,
            "open-scene",
            "Open Scene",
        )
        repo.create_post(community.id, thread.id, author.id, "A scene exists.")
        services = AppServices(
            repo,
            DemoSeed(
                community=community,
                user=user,
                membership=membership,
                default_character=None,
            ),
        )

        app = create_app(debug=False, services=services)
        async with TestClient(app) as client:
            index = await client.get("/c/x-men-apocalypse")
            assert index.status == 200
            assert "Create your first character" in index.text

            new_thread = await client.get(f"/boards/{board.slug}/threads/new")
            assert new_thread.status == 200
            assert "Create a character first" in new_thread.text
            assert "Open roster" in new_thread.text
            assert "elbysodicComposer" not in new_thread.text

            reply = await client.get(f"/boards/{board.slug}/threads/{thread.slug}")
            assert reply.status == 200
            assert "Create a character first" in reply.text
            assert "A scene exists." in reply.text

    asyncio.run(run())


def test_app_contract_check_passes() -> None:
    _app().check()


def test_chirp_ui_alpine_runtime_is_loaded_for_interactive_layouts() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            response = await client.get("/characters/storm")
            assert response.status == 200
            check = check_alpine_runtime(response.text)
            assert check.ok
            assert check.script_loaded

    asyncio.run(run())


def _moderation_app(
    *,
    is_admin: bool,
) -> tuple[App, ForumRepository, Community, Thread]:
    connection = connect(check_same_thread=False)
    create_schema(connection)
    repo = ForumRepository(connection)
    community = repo.seed_default_community("Moderation Test")
    role = repo.create_role(
        community.id,
        "staff" if is_admin else "member",
        "Staff" if is_admin else "Member",
        is_admin=is_admin,
    )
    user = repo.create_user("moderator@example.com", "hash")
    membership = repo.create_membership(
        community.id,
        user.id,
        role.id,
        "modlane" if is_admin else "memberlane",
        "Mod Lane" if is_admin else "Member Lane",
    )
    character = repo.create_character(
        community.id,
        membership.id,
        "moderator-face" if is_admin else "member-face",
        "Moderator Face" if is_admin else "Member Face",
        make_default=True,
    )
    board = repo.create_board(community.id, "ic", "In Character")
    repo.create_board(community.id, "archive", "Archive", sort_order=20)
    thread = repo.create_thread(
        community.id,
        board.id,
        character.id,
        "moderation-queue",
        "Moderation Queue",
    )
    repo.create_post(community.id, thread.id, character.id, "A thread ready for staff tools.")
    services = AppServices(
        repo,
        DemoSeed(
            community=community,
            user=user,
            membership=repo.get_membership(community.id, membership.id),
            default_character=character,
        ),
    )
    return create_app(debug=False, services=services), repo, community, thread
