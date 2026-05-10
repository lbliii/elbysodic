from __future__ import annotations

import asyncio
import re
from urllib.parse import urlencode

import pytest
from chirp.testing import TestClient

from elbysodic.services import create_services
from elbysodic.services.network import search_studio_network
from elbysodic.web import create_app
from elbysodic.web.state import get_services

_FORM = {"Content-Type": "application/x-www-form-urlencoded"}
_CSRF_RE = re.compile(r'name="_csrf_token" value="([^"]+)"')


def _response_headers(response, name: str) -> list[str]:
    headers = response.headers
    if isinstance(headers, dict):
        value = headers.get(name)
        return [] if value is None else [str(value)]
    return [str(value) for key, value in headers if str(key).lower() == name.lower()]


def _cookie_values(*responses) -> dict[str, str]:
    values: dict[str, str] = {}
    for response in responses:
        for cookie in _response_headers(response, "set-cookie"):
            pair = cookie.split(";", 1)[0]
            name, _, value = pair.partition("=")
            values[name] = value
    return values


def _cookie_header(cookies: dict[str, str]) -> str:
    return "; ".join(f"{name}={value}" for name, value in cookies.items())


def _csrf_token(html: str) -> str:
    match = _CSRF_RE.search(html)
    assert match is not None
    return match.group(1)


def _set_production_env(monkeypatch, *, demo_mode: bool = True) -> None:
    monkeypatch.setenv("ELBYSODIC_ENV", "production")
    monkeypatch.setenv("ELBYSODIC_SECRET_KEY", "x" * 32)
    monkeypatch.setenv("ELBYSODIC_ALLOWED_HOSTS", "*")
    if demo_mode:
        monkeypatch.setenv("ELBYSODIC_DEMO_MODE", "1")
    else:
        monkeypatch.delenv("ELBYSODIC_DEMO_MODE", raising=False)


async def _production_login(client: TestClient, *, email: str, next_url: str = "/studio"):
    page = await client.get(f"/login?next={next_url}")
    cookies = _cookie_values(page)
    login = await client.post(
        "/login",
        body=urlencode(
            {
                "email": email,
                "password": "password",
                "next": next_url,
                "_csrf_token": _csrf_token(page.text),
            }
        ).encode(),
        headers={**_FORM, "Cookie": _cookie_header(cookies)},
    )
    cookies.update(_cookie_values(login))
    return login, cookies


def test_production_config_requires_secret_key(monkeypatch) -> None:
    monkeypatch.setenv("ELBYSODIC_ENV", "production")
    monkeypatch.delenv("ELBYSODIC_SECRET_KEY", raising=False)

    with pytest.raises(RuntimeError, match="ELBYSODIC_SECRET_KEY"):
        create_app(debug=False, services=create_services(path=":memory:"))


def test_production_config_parses_allowed_hosts_and_hsts(monkeypatch) -> None:
    monkeypatch.setenv("ELBYSODIC_ENV", "production")
    monkeypatch.setenv("ELBYSODIC_SECRET_KEY", "x" * 32)
    monkeypatch.setenv("ELBYSODIC_ALLOWED_HOSTS", "example.com, .up.railway.app")
    monkeypatch.setenv("ELBYSODIC_HSTS", "max-age=31536000")

    app = create_app(debug=False, services=create_services(path=":memory:"))

    assert app.config.env == "production"
    assert app.config.secret_key == "x" * 32
    assert app.config.allowed_hosts == ("example.com", ".up.railway.app")
    assert app.config.strict_transport_security == "max-age=31536000"


def test_session_cookies_are_secure_in_production(monkeypatch) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch)
        app = create_app(debug=False, services=create_services(path=":memory:"))

        async with TestClient(app) as client:
            response, _cookies = await _production_login(client, email="moira@example.com")

        assert response.status == 302
        set_cookie = "\n".join(_response_headers(response, "set-cookie"))
        assert "elbysodic_session=" in set_cookie
        assert "elbysodic_dev_identity=" not in set_cookie
        assert "Secure" in set_cookie
        assert "HttpOnly" in set_cookie
        assert "SameSite=lax" in set_cookie

    asyncio.run(run())


def test_production_seed_password_requires_demo_mode(monkeypatch) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch, demo_mode=False)
        app = create_app(debug=False, services=create_services(path=":memory:"))

        async with TestClient(app) as client:
            page = await client.get("/login")
            response = await client.post(
                "/login",
                body=urlencode(
                    {
                        "email": "moira@example.com",
                        "password": "password",
                        "next": "/studio",
                        "_csrf_token": _csrf_token(page.text),
                    }
                ).encode(),
                headers={**_FORM, "Cookie": _cookie_header(_cookie_values(page))},
            )

        assert response.status == 200
        assert "Access is invite-only for this launch" in page.text
        assert "public registration is not open" in page.text
        assert "Invite/demo accounts use password" not in page.text
        assert "email or password is incorrect" in response.text
        assert "elbysodic_session=" not in "\n".join(_response_headers(response, "set-cookie"))

    asyncio.run(run())


def test_production_routes_require_session(monkeypatch) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch)
        app = create_app(debug=False, services=create_services(path=":memory:"), dev_tools=True)

        async with TestClient(app) as client:
            health = await client.get("/health")
            root = await client.get("/")
            network = await client.get("/network?q=magic")
            login = await client.get("/login")
            nested_login = await client.get("/login?next=/login%3Fnext%3D/")
            request_access = await client.get("/request-access")
            studio = await client.get("/studio")
            tenant = await client.get("/c/x-men-apocalypse")
            post = await client.post(
                "/identity",
                body=urlencode({"intent": "set_default_character", "character_id": "0"}).encode(),
                headers=_FORM,
            )
            personas = await client.get("/dev/personas")

        assert health.status == 200
        assert root.status == 200
        assert "Studio Network" in root.text
        assert "starlane" not in root.text
        assert "playing as Rogue" not in root.text
        assert "elbysodic-identity-menu" not in root.text
        assert "elbysodic-anonymous-actions" in root.text
        assert 'href="/request-access"' in root.text
        assert 'href="/login?next=/"' in root.text
        assert "chirpui-theme-toggle" in root.text
        assert network.status == 200
        assert "HP Universe" in network.text
        assert "starlane" not in network.text
        assert "current realm" not in network.text
        assert "Public preview" in network.text
        assert login.status == 200
        assert "_csrf_token" in login.text
        assert 'href="/request-access"' in login.text
        assert 'href="/login?next=/"' in login.text
        assert 'name="next" value="/"' in nested_login.text
        assert 'href="/login?next=/login' not in nested_login.text
        assert "chirpui-sidebar__section-title" not in login.text
        assert "Staff in X-Men Apocalypse" not in login.text
        assert request_access.status == 200
        assert "Access opens through a director invitation." in request_access.text
        assert "Public registration is not open yet." in request_access.text
        assert "_csrf_token" not in request_access.text
        assert "chirpui-sidebar__section-title" not in request_access.text
        assert studio.status == 302
        assert dict(studio.headers)["location"] == "/login?next=/studio"
        assert tenant.status == 302
        assert dict(tenant.headers)["location"] == "/login?next=%2Fc%2Fx-men-apocalypse"
        assert post.status == 403
        assert "Log in to keep writing." in post.text
        assert "/login?next=/identity" in post.text
        assert personas.status == 302

    asyncio.run(run())


def test_production_empty_network_renders_launch_state(monkeypatch) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch)
        app = create_app(debug=False, db_path=":memory:", seed_demo=False)

        async with TestClient(app) as client:
            root = await client.get("/")
            network = await client.get("/network")

        assert root.status == 200
        assert network.status == 200
        for response in (root, network):
            assert "Launch state" in response.text
            assert "The first realm is still backstage." in response.text
            assert "wanted hooks, faces, scenes, and current events" in response.text
            assert 'href="/request-access"' in response.text
            assert 'href="/login?next=/"' in response.text
            assert "No programs are available yet." not in response.text
            assert "elbysodic-identity-menu" not in response.text

    asyncio.run(run())


def test_public_network_catalog_hides_membership_and_staff_signals(monkeypatch) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch)
        app = create_app(debug=False, services=create_services(path=":memory:"))

        async with TestClient(app) as client:
            network = await client.get("/network?q=wanted")

        assert network.status == 200
        assert "Public preview" in network.text
        assert "Open Wanted" in network.text or "wanted hooks" in network.text
        assert "starlane" not in network.text
        assert "moira" not in network.text
        assert "Director in" not in network.text
        assert "Member in" not in network.text
        assert "playing as" not in network.text
        assert "current realm" not in network.text
        assert "unread" not in network.text
        assert "Application Review Room" not in network.text
        assert "Staff notes" not in network.text

    asyncio.run(run())


def test_public_network_search_contract_stays_service_owned() -> None:
    services = create_services(path=":memory:")

    directory = services.public_studio_network()
    magic_results = search_studio_network(directory, "magic")
    wanted_results = search_studio_network(directory, "wanted")

    assert [program.community.slug for program in magic_results] == ["hp-universe"]
    assert {program.community.slug for program in wanted_results}
    assert all(program.membership is None for program in wanted_results)
    assert all(program.current_character is None for program in wanted_results)
    assert all(program.unread_notification_count == 0 for program in wanted_results)
    assert all(program.plotting_room_count == 0 for program in wanted_results)


def test_production_login_preserves_tenant_prefixed_destination(monkeypatch) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch)
        app = create_app(debug=False, services=create_services(path=":memory:"))

        async with TestClient(app) as client:
            protected = await client.get("/c/jurassic-park-universe/boards/paddock-twelve")
            login, cookies = await _production_login(
                client,
                email="writer@example.com",
                next_url="/c/jurassic-park-universe/boards/paddock-twelve",
            )
            board = await client.get(
                "/c/jurassic-park-universe/boards/paddock-twelve",
                headers={"Cookie": _cookie_header(cookies)},
            )

        assert protected.status == 302
        assert dict(protected.headers)["location"] == (
            "/login?next=%2Fc%2Fjurassic-park-universe%2Fboards%2Fpaddock-twelve"
        )
        assert login.status == 302
        assert dict(login.headers)["location"] == (
            "/c/jurassic-park-universe/boards/paddock-twelve"
        )
        assert board.status == 200
        assert "Jurassic Park Universe" in board.text
        assert "Paddock Twelve" in board.text

    asyncio.run(run())


def test_production_security_headers_are_set(monkeypatch) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch)
        monkeypatch.setenv("ELBYSODIC_HSTS", "max-age=31536000")
        app = create_app(debug=False, services=create_services(path=":memory:"))

        async with TestClient(app) as client:
            response = await client.get("/login")

        headers = dict(response.headers)
        assert headers["x-frame-options"] == "DENY"
        assert headers["x-content-type-options"] == "nosniff"
        assert headers["referrer-policy"] == "strict-origin-when-cross-origin"
        assert headers["strict-transport-security"] == "max-age=31536000"
        csp = headers["content-security-policy"]
        assert "frame-ancestors 'none'" in csp
        assert "style-src 'self' 'unsafe-inline'" in csp
        assert "script-src 'self' 'unsafe-inline' 'unsafe-eval'" in csp
        assert "connect-src 'self'" in csp

    asyncio.run(run())


def test_production_login_rate_limit_blocks_repeated_posts(monkeypatch) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch)
        app = create_app(debug=False, services=create_services(path=":memory:"))

        async with TestClient(app) as client:
            responses = [
                await client.post("/login", body=b"", headers=_FORM) for _attempt in range(11)
            ]

        assert [response.status for response in responses[:10]] == [403] * 10
        assert responses[10].status == 429
        assert dict(responses[10].headers)["retry-after"] == "300"

    asyncio.run(run())


def test_production_release_smoke_core_user_flow(monkeypatch) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch)
        app = create_app(debug=False, services=create_services(path=":memory:"))
        services = get_services()
        hp = services.repo.get_community_by_slug("hp-universe")
        hp_membership = services.repo.get_membership_for_user(hp.id, services.seed.user.id)

        async with TestClient(app) as client:
            health = await client.get("/health")
            login, cookies = await _production_login(
                client,
                email="writer@example.com",
                next_url="/c/x-men-apocalypse",
            )
            cookies.update(_cookie_values(login))
            original_session = cookies["elbysodic_session"]
            xmen_home = await client.get(
                "/c/x-men-apocalypse",
                headers={"Cookie": _cookie_header(cookies)},
            )
            network = await client.get(
                "/network?q=magic",
                headers={"Cookie": _cookie_header(cookies)},
            )
            thread = await client.get(
                "/c/x-men-apocalypse/boards/danger-room/threads/sentinel-drill",
                headers={"Cookie": _cookie_header(cookies)},
            )
            wanted = await client.get(
                "/c/x-men-apocalypse/wanted",
                headers={"Cookie": _cookie_header(cookies)},
            )
            applications = await client.get(
                "/c/x-men-apocalypse/applications",
                headers={"Cookie": _cookie_header(cookies)},
            )
            plotting = await client.get(
                "/c/x-men-apocalypse/plotting",
                headers={"Cookie": _cookie_header(cookies)},
            )
            notifications = await client.get(
                "/c/x-men-apocalypse/notifications",
                headers={"Cookie": _cookie_header(cookies)},
            )
            studio = await client.get(
                "/c/x-men-apocalypse/studio",
                headers={"Cookie": _cookie_header(cookies)},
            )
            cookies.update(_cookie_values(thread))
            switch = await client.post(
                "/identity",
                body=urlencode(
                    {
                        "intent": "switch_membership",
                        "membership_id": str(hp_membership.id),
                        "next": "/c/hp-universe",
                        "_csrf_token": _csrf_token(thread.text),
                    }
                ).encode(),
                headers={**_FORM, "Cookie": _cookie_header(cookies)},
            )
            cookies.update(_cookie_values(switch))
            hp_home = await client.get(
                "/c/hp-universe",
                headers={"Cookie": _cookie_header(cookies)},
            )
            jurassic_board = await client.get(
                "/c/jurassic-park-universe/boards/paddock-twelve",
                headers={"Cookie": _cookie_header(cookies)},
            )
            logout = await client.get("/logout", headers={"Cookie": _cookie_header(cookies)})
            cookies.update(_cookie_values(logout))
            studio_after_logout = await client.get(
                "/studio",
                headers={"Cookie": _cookie_header(cookies)},
            )
            studio_with_stale_session = await client.get(
                "/studio",
                headers={"Cookie": f"elbysodic_session={original_session}"},
            )

        assert health.status == 200
        assert login.status == 302
        assert dict(login.headers)["location"] == "/c/x-men-apocalypse"
        assert xmen_home.status == 200
        assert "X-Men Apocalypse" in xmen_home.text
        assert network.status == 200
        assert "HP Universe" in network.text
        assert "playing as Rogue" in network.text
        assert thread.status == 200
        assert "Sentinel drill after midnight" in thread.text
        assert "Reply as Rogue" in thread.text
        assert wanted.status == 200
        assert "Wanted" in wanted.text
        assert applications.status == 200
        assert "Applications" in applications.text
        assert plotting.status == 200
        assert "Plotting" in plotting.text
        assert notifications.status == 200
        assert "Notifications" in notifications.text
        assert studio.status == 200
        assert "Studio" in studio.text
        assert switch.status == 302
        assert dict(switch.headers)["location"] == "/c/hp-universe"
        assert hp_home.status == 200
        assert "Director in HP Universe" in hp_home.text
        assert "playing as Rowan Ash" in hp_home.text
        assert jurassic_board.status == 200
        assert "Paddock Twelve" in jurassic_board.text
        assert logout.status == 302
        assert studio_after_logout.status == 302
        assert dict(studio_after_logout.headers)["location"] == "/login?next=/studio"
        assert studio_with_stale_session.status == 302
        assert dict(studio_with_stale_session.headers)["location"] == "/login?next=/studio"

    asyncio.run(run())


def test_production_ignores_forged_dev_identity(monkeypatch) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch)
        app = create_app(debug=False, services=create_services(path=":memory:"), dev_tools=True)
        services = get_services()
        community = services.seed.community
        moira = services.repo.get_membership_by_username(community.id, "moira")

        async with TestClient(app) as client:
            _login, cookies = await _production_login(client, email="writer@example.com")
            forged_identity = f"elbysodic_dev_identity={community.id}:{moira.user_id}:{moira.id}"
            studio = await client.get(
                "/studio",
                headers={
                    "Cookie": f"{_cookie_header(cookies)}; {forged_identity}",
                    "x-elbysodic-user-id": str(moira.user_id),
                    "x-elbysodic-membership-id": str(moira.id),
                },
            )

        assert studio.status == 200
        assert "Member in X-Men Apocalypse" in studio.text
        assert "Staff in X-Men Apocalypse" not in studio.text

    asyncio.run(run())


def test_production_membership_switch_is_session_bound(monkeypatch) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch)
        app = create_app(debug=False, services=create_services(path=":memory:"))
        services = get_services()
        hp = services.repo.get_community_by_slug("hp-universe")
        hp_membership = services.repo.get_membership_for_user(hp.id, services.seed.user.id)

        async with TestClient(app) as client:
            _login, cookies = await _production_login(client, email="writer@example.com")
            studio_form = await client.get("/studio", headers={"Cookie": _cookie_header(cookies)})
            cookies.update(_cookie_values(studio_form))
            missing_csrf = await client.post(
                "/identity",
                body=urlencode(
                    {
                        "intent": "switch_membership",
                        "membership_id": str(hp_membership.id),
                        "next": "/studio",
                    }
                ).encode(),
                headers={**_FORM, "Cookie": _cookie_header(cookies)},
            )
            switch = await client.post(
                "/identity",
                body=urlencode(
                    {
                        "intent": "switch_membership",
                        "membership_id": str(hp_membership.id),
                        "next": "/studio",
                        "_csrf_token": _csrf_token(studio_form.text),
                    }
                ).encode(),
                headers={**_FORM, "Cookie": _cookie_header(cookies)},
            )
            cookies.update(_cookie_values(switch))
            studio = await client.get("/studio", headers={"Cookie": _cookie_header(cookies)})

        assert missing_csrf.status == 403
        assert switch.status == 302
        assert "elbysodic_dev_identity=" not in "\n".join(_response_headers(switch, "set-cookie"))
        assert studio.status == 200
        assert "Director in HP Universe" in studio.text
        assert "Member in X-Men Apocalypse" not in studio.text

    asyncio.run(run())


def test_production_application_room_requires_csrf_and_accepts_rendered_token(
    monkeypatch,
) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch)
        app = create_app(debug=False, services=create_services(path=":memory:"))
        services = get_services()
        community = services.seed.community
        kitty = services.repo.get_character_by_slug(community.id, "kitty-pryde")

        async with TestClient(app) as client:
            _login, cookies = await _production_login(
                client,
                email="alex@example.com",
                next_url="/applications/kitty-pryde",
            )
            room = await client.get(
                "/applications/kitty-pryde",
                headers={"Cookie": _cookie_header(cookies)},
            )
            cookies.update(_cookie_values(room))
            missing_csrf = await client.post(
                "/applications/kitty-pryde",
                body=urlencode(
                    {
                        "intent": "save_review",
                        "staff_notes": "Private staff note.",
                        "checklist": "Voice\nHooks",
                    }
                ).encode(),
                headers={**_FORM, "Cookie": _cookie_header(cookies)},
            )
            saved = await client.post(
                "/applications/kitty-pryde",
                body=urlencode(
                    {
                        "intent": "save_review",
                        "staff_notes": "Private staff note.",
                        "checklist": "Voice\nHooks",
                        "_csrf_token": _csrf_token(room.text),
                    }
                ).encode(),
                headers={**_FORM, "Cookie": _cookie_header(cookies)},
            )

        application = services.repo.get_character_application_for_character(
            community.id,
            kitty.id,
        )
        assert room.status == 200
        assert missing_csrf.status == 403
        assert saved.status == 302
        assert application.staff_notes == "Private staff note."
        assert application.checklist == "Voice\nHooks"

    asyncio.run(run())


def test_production_application_room_denies_same_community_outsider(monkeypatch) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch)
        app = create_app(debug=False, services=create_services(path=":memory:"))

        async with TestClient(app) as client:
            _login, cookies = await _production_login(
                client,
                email="simon@example.com",
                next_url="/applications/kitty-pryde",
            )
            room = await client.get(
                "/applications/kitty-pryde",
                headers={"Cookie": _cookie_header(cookies)},
            )

        assert room.status == 403
        assert "Application Review Room" not in room.text
        assert "Director Review" not in room.text
        assert "Applicant Notes" not in room.text

    asyncio.run(run())


def test_production_tenant_prefix_overrides_session_selected_community(monkeypatch) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch)
        app = create_app(debug=False, services=create_services(path=":memory:"))
        services = get_services()
        hp = services.repo.get_community_by_slug("hp-universe")
        hp_membership = services.repo.get_membership_for_user(hp.id, services.seed.user.id)

        async with TestClient(app) as client:
            _login, cookies = await _production_login(client, email="writer@example.com")
            studio_form = await client.get("/studio", headers={"Cookie": _cookie_header(cookies)})
            cookies.update(_cookie_values(studio_form))
            switch = await client.post(
                "/identity",
                body=urlencode(
                    {
                        "intent": "switch_membership",
                        "membership_id": str(hp_membership.id),
                        "next": "/studio",
                        "_csrf_token": _csrf_token(studio_form.text),
                    }
                ).encode(),
                headers={**_FORM, "Cookie": _cookie_header(cookies)},
            )
            cookies.update(_cookie_values(switch))
            hp_studio = await client.get("/studio", headers={"Cookie": _cookie_header(cookies)})
            jurassic_board = await client.get(
                "/c/jurassic-park-universe/boards/paddock-twelve",
                headers={"Cookie": _cookie_header(cookies)},
            )

        assert hp_studio.status == 200
        assert "Director in HP Universe" in hp_studio.text
        assert jurassic_board.status == 200
        assert "Jurassic Park Universe" in jurassic_board.text
        assert "Director in Jurassic Park Universe" in jurassic_board.text
        assert "Paddock Twelve" in jurassic_board.text

    asyncio.run(run())


def test_production_membership_switch_rejects_cross_user_membership(monkeypatch) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch)
        app = create_app(debug=False, services=create_services(path=":memory:"))
        services = get_services()
        community = services.seed.community
        moira = services.repo.get_membership_by_username(community.id, "moira")

        async with TestClient(app) as client:
            _login, cookies = await _production_login(client, email="writer@example.com")
            studio_form = await client.get("/studio", headers={"Cookie": _cookie_header(cookies)})
            cookies.update(_cookie_values(studio_form))
            switch = await client.post(
                "/identity",
                body=urlencode(
                    {
                        "intent": "switch_membership",
                        "membership_id": str(moira.id),
                        "next": "/studio",
                        "_csrf_token": _csrf_token(studio_form.text),
                    }
                ).encode(),
                headers={**_FORM, "Cookie": _cookie_header(cookies)},
            )

        assert switch.status == 403

    asyncio.run(run())


def test_production_identity_failures_render_elbysodic_error_page(monkeypatch) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch)
        app = create_app(debug=False, services=create_services(path=":memory:"))
        services = get_services()
        hp = services.repo.get_community_by_slug("hp-universe")
        hp_membership = services.repo.get_membership_for_user(hp.id, services.seed.user.id)

        async with TestClient(app) as client:
            _login, cookies = await _production_login(client, email="writer@example.com")
            studio_form = await client.get("/studio", headers={"Cookie": _cookie_header(cookies)})
            cookies.update(_cookie_values(studio_form))

            def fail_identity_update(*_args, **_kwargs):
                raise RuntimeError("database write failed")

            monkeypatch.setattr(
                services.repo,
                "update_user_session_identity",
                fail_identity_update,
            )
            switch = await client.post(
                "/identity",
                body=urlencode(
                    {
                        "intent": "switch_membership",
                        "membership_id": str(hp_membership.id),
                        "next": "/c/hp-universe",
                        "_csrf_token": _csrf_token(studio_form.text),
                    }
                ).encode(),
                headers={**_FORM, "Cookie": _cookie_header(cookies)},
            )

        assert switch.status == 500
        assert "Something broke backstage." in switch.text
        assert "Open Studio Network" in switch.text
        assert switch.text != "Internal Server Error"

    asyncio.run(run())


def test_production_identity_rejects_malformed_membership_id(monkeypatch) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch)
        app = create_app(debug=False, services=create_services(path=":memory:"))

        async with TestClient(app) as client:
            _login, cookies = await _production_login(client, email="writer@example.com")
            studio_form = await client.get("/studio", headers={"Cookie": _cookie_header(cookies)})
            cookies.update(_cookie_values(studio_form))
            switch = await client.post(
                "/identity",
                body=urlencode(
                    {
                        "intent": "switch_membership",
                        "membership_id": "not-a-membership",
                        "next": "/network",
                        "_csrf_token": _csrf_token(studio_form.text),
                    }
                ).encode(),
                headers={**_FORM, "Cookie": _cookie_header(cookies)},
            )

        assert switch.status == 400
        assert "That request could not be read." in switch.text
        assert "membership_id must be an integer" in switch.text

    asyncio.run(run())


def test_session_cookies_stay_http_local_in_development(monkeypatch) -> None:
    async def run() -> None:
        monkeypatch.delenv("ELBYSODIC_ENV", raising=False)
        monkeypatch.delenv("ELBYSODIC_SECRET_KEY", raising=False)
        monkeypatch.delenv("ELBYSODIC_ALLOWED_HOSTS", raising=False)
        app = create_app(debug=False, services=create_services(path=":memory:"))

        async with TestClient(app) as client:
            response = await client.post(
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

        assert response.status == 302
        set_cookie = "\n".join(_response_headers(response, "set-cookie"))
        assert "elbysodic_session=" in set_cookie
        assert "Secure" not in set_cookie

    asyncio.run(run())
