"""Shared pytest fixtures for the Elbysodic test suite."""

from __future__ import annotations

import re

import pytest
from chirp.app import App
from chirp.testing import TestClient

_UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
_CSRF_INPUT_RE = re.compile(r'name="_csrf_token" value="([^"]+)"')
_CHIRP_SESSION_COOKIE = "chirp_session"
_CSRF_HEADER = "X-CSRF-Token"


@pytest.fixture(autouse=True)
def _development_csrf_autofill(monkeypatch: pytest.MonkeyPatch) -> None:
    """Supply a valid session-bound CSRF token for development-env requests.

    secure_stack() enforces sessions + CSRF in every environment (dev/prod
    parity), but most development-mode tests predate CSRF-in-dev and post
    forms without a token. Instead of rewriting every call site, this fixture
    primes one chirp session per app by rendering /login (which emits
    csrf_field()), then pins that session cookie and sends its token via the
    X-CSRF-Token header on unsafe requests — so the real CSRFMiddleware
    validation path still runs against a token it minted.

    Production/staging apps are left untouched: those tests do the real
    form-token dance, including missing-token 403 assertions. A test that
    sets its own X-CSRF-Token header also keeps it (letting dev tests assert
    the rejection path with an invalid token).
    """
    original_request = TestClient.request
    # Keyed by id(app) with a strong app reference so ids cannot be recycled.
    primed: dict[int, tuple[App, str, str]] = {}

    async def _prime(client: TestClient) -> tuple[str, str]:
        key = id(client.app)
        cached = primed.get(key)
        if cached is None:
            page = await original_request(client, "GET", "/login")
            token_match = _CSRF_INPUT_RE.search(page.text)
            assert token_match is not None, (
                "development /login page did not render csrf_field(); "
                "cannot prime a CSRF token for unsafe test requests"
            )
            session_value = ""
            for name, value in page.headers:
                if name.lower() == "set-cookie" and value.startswith(f"{_CHIRP_SESSION_COOKIE}="):
                    session_value = value.split(";", 1)[0].partition("=")[2]
            assert session_value, "development /login response set no chirp session cookie"
            cached = (client.app, session_value, token_match.group(1))
            primed[key] = cached
        return cached[1], cached[2]

    async def request(
        self: TestClient,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        body: bytes | None = None,
    ):
        if method.upper() in _UNSAFE_METHODS and self.app.config.env == "development":
            session_value, token = await _prime(self)
            headers = dict(headers or {})
            cookie_key = next((key for key in headers if key.lower() == "cookie"), "Cookie")
            existing = headers.get(cookie_key, "")
            crumbs = [
                crumb
                for crumb in existing.split("; ")
                if crumb and not crumb.startswith(f"{_CHIRP_SESSION_COOKIE}=")
            ]
            crumbs.append(f"{_CHIRP_SESSION_COOKIE}={session_value}")
            headers[cookie_key] = "; ".join(crumbs)
            if not any(key.lower() == _CSRF_HEADER.lower() for key in headers):
                headers[_CSRF_HEADER] = token
        return await original_request(self, method, path, headers=headers, body=body)

    monkeypatch.setattr(TestClient, "request", request)
