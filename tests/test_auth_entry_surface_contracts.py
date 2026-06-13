from __future__ import annotations

import asyncio
import re
from pathlib import Path
from urllib.parse import urlencode

from chirp.testing import TestClient

from elbysodic.services import create_services
from elbysodic.web import create_app
from elbysodic.web.state import get_services

_FORM = {"Content-Type": "application/x-www-form-urlencoded"}
_CSRF_RE = re.compile(r'name="_csrf_token" value="([^"]+)"')
_PAGES = Path(__file__).parents[1] / "src/elbysodic/web/pages"
_DOC = Path(__file__).parents[1] / "docs/product/auth-entry-session-recovery-ux.md"


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


def _set_production_env(monkeypatch) -> None:
    monkeypatch.setenv("ELBYSODIC_ENV", "production")
    monkeypatch.setenv("ELBYSODIC_SECRET_KEY", "x" * 32)
    monkeypatch.setenv("ELBYSODIC_ALLOWED_HOSTS", "*")
    monkeypatch.setenv("ELBYSODIC_DEMO_MODE", "1")


async def _production_login(
    client: TestClient,
    *,
    email: str,
    next_url: str = "/network",
) -> dict[str, str]:
    page = await client.get(f"/login?next={next_url}")
    cookies = _cookie_values(page)
    response = await client.post(
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
    cookies.update(_cookie_values(response))
    assert response.status == 302
    return cookies


def test_auth_entry_templates_preserve_account_membership_face_language() -> None:
    login = (_PAGES / "login/page.html").read_text(encoding="utf-8")
    access = (_PAGES / "_components/access.html").read_text(encoding="utf-8")
    layout = (_PAGES / "_layout.html").read_text(encoding="utf-8")
    recovery = (_PAGES / "recovery/_page.html").read_text(encoding="utf-8")
    doc = _DOC.read_text(encoding="utf-8")

    for snippet in [
        "Choose the account first",
        "community membership and active face",
        "linked account request",
    ]:
        assert snippet in login
    for snippet in [
        "Existing Elbysodic account",
        "Request access without a separate email handoff",
        "first-face context",
    ]:
        assert snippet in access
    for snippet in [
        "Not a member of",
        "Choose a realm or request access",
        "playing as",
        "clear session",
    ]:
        assert snippet in layout
    for snippet in [
        "recovery.kicker",
        "recovery.summary",
        'name="membership_id"',
        'name="character_id"',
        'name="next"',
    ]:
        assert snippet in recovery
    for snippet in [
        "Signed-out visitor",
        "Signed-in account visitor",
        "Member without face",
        "Active-face writer",
        "Inactive membership",
        "Stale or cross-community selection",
    ]:
        assert snippet in doc


def test_signed_out_auth_entry_stays_public_safe(monkeypatch) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch)
        app = create_app(debug=False, services=create_services(path=":memory:"))

        async with TestClient(app) as client:
            login = await client.get("/login")
            request_access = await client.get("/c/afterlight-accord/request-access")
            studio = await client.get("/studio")

        assert login.status == 200
        assert "Invite/demo accounts use password" in login.text
        assert 'href="/request-access"' in login.text
        assert "Request access" in login.text
        assert "chirpui-sidebar__section-title" not in login.text
        assert "Staff in X-Men Apocalypse" not in login.text
        assert "playing as" not in login.text

        assert request_access.status == 200
        assert "Access opens through a director invitation." in request_access.text
        assert "Writer email" in request_access.text
        assert "Send access request" in request_access.text
        assert "Account menu: signed in as" not in request_access.text
        assert "playing as" not in request_access.text

        assert studio.status == 302
        assert dict(studio.headers)["location"] == "/login?next=/studio"

    asyncio.run(run())


def test_account_visitor_preview_stays_public_safe(monkeypatch) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch)
        app = create_app(debug=False, services=create_services(path=":memory:"))

        async with TestClient(app) as client:
            cookies = await _production_login(client, email="moira@example.com")
            cookie = _cookie_header(cookies)
            realm = await client.get("/c/afterlight-accord", headers={"Cookie": cookie})
            request_access = await client.get(
                "/c/afterlight-accord/request-access",
                headers={"Cookie": cookie},
            )

        assert realm.status == 200
        assert "Not a member of Afterlight Accord yet" in realm.text
        assert "can browse the public preview, then request access" in realm.text
        assert 'href="/c/afterlight-accord/request-access"' in realm.text
        assert 'href="/c/afterlight-accord/desk"' not in realm.text
        assert "playing as" not in realm.text
        assert "Application Review Room" not in realm.text
        assert "Staff in Afterlight Accord" not in realm.text

        assert request_access.status == 200
        assert "Existing Elbysodic account" in request_access.text
        assert "Request access with this account" in request_access.text
        assert "Writer email" not in request_access.text
        assert "Director review" not in request_access.text
        assert "Staff notes" not in request_access.text

    asyncio.run(run())


def test_cross_realm_recovery_renders_sanitized_switch_contract() -> None:
    async def run() -> None:
        app = create_app(debug=False, services=create_services(path=":memory:"), dev_tools=True)
        services = get_services()
        jurassic = services.repo.get_community_by_slug("jurassic-park-universe")
        jurassic_membership = services.repo.get_membership_for_user(
            jurassic.id,
            services.seed.user.id,
        )
        cookie = (
            f"elbysodic_dev_identity={jurassic.id}:{services.seed.user.id}:{jurassic_membership.id}"
        )

        async with TestClient(app) as client:
            recovery = await client.get(
                f"/c/{services.seed.community.slug}/world/paddock-twelve-incident",
                headers={"Cookie": cookie},
            )

        assert recovery.status == 200
        assert "/elbysodic-static/brand/elbysodic-mark.svg" in recovery.text
        assert "That world material lives in Jurassic Park Universe." in recovery.text
        assert (
            'name="next" value="/c/jurassic-park-universe/world/paddock-twelve-incident"'
            in recovery.text
        )
        assert 'name="membership_id"' in recovery.text
        assert 'name="character_id"' in recovery.text
        assert "Staff in X-Men Apocalypse" not in recovery.text
        assert "Application Review Room" not in recovery.text
        assert "elbysodic_session" not in recovery.text

    asyncio.run(run())
