from __future__ import annotations

import asyncio
from urllib.parse import urlencode

import pytest
from chirp.testing import TestClient

from elbysodic.services import create_services
from elbysodic.web import create_app

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
        assert "Secure" in set_cookie
        assert "HttpOnly" in set_cookie
        assert "SameSite=lax" in set_cookie

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
