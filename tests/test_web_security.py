from __future__ import annotations

import asyncio
from urllib.parse import urlencode

import pytest
from chirp.testing import TestClient

from elbysodic.services import create_services
from elbysodic.web import create_app
from elbysodic.web.state import get_services

_FORM = {"Content-Type": "application/x-www-form-urlencoded"}


def _response_headers(response, name: str) -> list[str]:
    headers = response.headers
    if isinstance(headers, dict):
        value = headers.get(name)
        return [] if value is None else [str(value)]
    return [str(value) for key, value in headers if str(key).lower() == name.lower()]


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
        monkeypatch.setenv("ELBYSODIC_ENV", "production")
        monkeypatch.setenv("ELBYSODIC_SECRET_KEY", "x" * 32)
        monkeypatch.setenv("ELBYSODIC_ALLOWED_HOSTS", "*")
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
        assert "elbysodic_dev_identity=" not in set_cookie
        assert "Secure" in set_cookie
        assert "HttpOnly" in set_cookie
        assert "SameSite=lax" in set_cookie

    asyncio.run(run())


def test_production_routes_require_session(monkeypatch) -> None:
    async def run() -> None:
        monkeypatch.setenv("ELBYSODIC_ENV", "production")
        monkeypatch.setenv("ELBYSODIC_SECRET_KEY", "x" * 32)
        monkeypatch.setenv("ELBYSODIC_ALLOWED_HOSTS", "*")
        app = create_app(debug=False, services=create_services(path=":memory:"), dev_tools=True)

        async with TestClient(app) as client:
            health = await client.get("/health")
            login = await client.get("/login")
            studio = await client.get("/studio")
            post = await client.post(
                "/identity",
                body=urlencode({"intent": "set_default_character", "character_id": "0"}).encode(),
                headers=_FORM,
            )
            personas = await client.get("/dev/personas")

        assert health.status == 200
        assert login.status == 200
        assert "Staff in X-Men Apocalypse" not in login.text
        assert studio.status == 302
        assert dict(studio.headers)["location"] == "/login?next=/studio"
        assert post.status == 403
        assert personas.status == 302

    asyncio.run(run())


def test_production_ignores_forged_dev_identity(monkeypatch) -> None:
    async def run() -> None:
        monkeypatch.setenv("ELBYSODIC_ENV", "production")
        monkeypatch.setenv("ELBYSODIC_SECRET_KEY", "x" * 32)
        monkeypatch.setenv("ELBYSODIC_ALLOWED_HOSTS", "*")
        app = create_app(debug=False, services=create_services(path=":memory:"), dev_tools=True)
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
                headers={
                    "Cookie": f"{session_cookie}; {forged_identity}",
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
        monkeypatch.setenv("ELBYSODIC_ENV", "production")
        monkeypatch.setenv("ELBYSODIC_SECRET_KEY", "x" * 32)
        monkeypatch.setenv("ELBYSODIC_ALLOWED_HOSTS", "*")
        app = create_app(debug=False, services=create_services(path=":memory:"))
        services = get_services()
        hp = services.repo.get_community_by_slug("hp-universe")
        hp_membership = services.repo.get_membership_for_user(hp.id, services.seed.user.id)

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
            switch = await client.post(
                "/identity",
                body=urlencode(
                    {
                        "intent": "switch_membership",
                        "membership_id": str(hp_membership.id),
                        "next": "/studio",
                    }
                ).encode(),
                headers={**_FORM, "Cookie": session_cookie},
            )
            studio = await client.get("/studio", headers={"Cookie": session_cookie})

        assert switch.status == 302
        assert _response_headers(switch, "set-cookie") == []
        assert studio.status == 200
        assert "Director in HP Universe" in studio.text
        assert "Member in X-Men Apocalypse" not in studio.text

    asyncio.run(run())


def test_production_membership_switch_rejects_cross_user_membership(monkeypatch) -> None:
    async def run() -> None:
        monkeypatch.setenv("ELBYSODIC_ENV", "production")
        monkeypatch.setenv("ELBYSODIC_SECRET_KEY", "x" * 32)
        monkeypatch.setenv("ELBYSODIC_ALLOWED_HOSTS", "*")
        app = create_app(debug=False, services=create_services(path=":memory:"))
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
            switch = await client.post(
                "/identity",
                body=urlencode(
                    {
                        "intent": "switch_membership",
                        "membership_id": str(moira.id),
                        "next": "/studio",
                    }
                ).encode(),
                headers={**_FORM, "Cookie": session_cookie},
            )

        assert switch.status == 403

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
