from __future__ import annotations

import asyncio
import re
from pathlib import Path
from urllib.parse import urlencode

from chirp.testing import TestClient

from elbysodic.db.seed import DemoSeed
from elbysodic.services import AppServices, create_services
from elbysodic.web import create_app

_FORM = {"Content-Type": "application/x-www-form-urlencoded"}
_CSRF_RE = re.compile(r'name="_csrf_token" value="([^"]+)"')
_PAGES = Path(__file__).parents[1] / "src/elbysodic/web/pages"
_DOC = (
    Path(__file__).parents[1] / "docs/product/applicant-account-visitor-public-preview-handoff.md"
)


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


async def _production_login(client: TestClient, *, email: str) -> dict[str, str]:
    page = await client.get("/login?next=/network")
    cookies = _cookie_values(page)
    response = await client.post(
        "/login",
        body=urlencode(
            {
                "email": email,
                "password": "password",
                "next": "/network",
                "_csrf_token": _csrf_token(page.text),
            }
        ).encode(),
        headers={**_FORM, "Cookie": _cookie_header(cookies)},
    )
    cookies.update(_cookie_values(response))
    assert response.status == 302
    return cookies


def _dev_identity_cookie(seed: DemoSeed) -> str:
    return f"elbysodic_dev_identity={seed.community.id}:{seed.user.id}:{seed.membership.id}"


def test_public_preview_handoff_templates_and_docs_name_viewer_states() -> None:
    gateway = (_PAGES / "_components/realm_gateway.html").read_text(encoding="utf-8")
    network = (_PAGES / "network/page.html").read_text(encoding="utf-8")
    wanted = (_PAGES / "wanted/{wanted_slug}/page.html").read_text(encoding="utf-8")
    request_access = (_PAGES / "request-access/page.html").read_text(encoding="utf-8")
    access = (_PAGES / "_components/access.html").read_text(encoding="utf-8")
    doc = _DOC.read_text(encoding="utf-8")

    for snippet in [
        "Not a member of",
        "can browse the public preview",
        "Request access",
        "Browse your realms",
    ]:
        assert snippet in gateway
    for snippet in [
        "Browse public previews first",
        "Explore cards stay public-preview safe",
        "Search story fit",
    ]:
        assert snippet in network
    for snippet in [
        "Request access to raise interest",
        "Log in to raise interest",
        "Pitch a new face for this",
    ]:
        assert snippet in wanted
    for snippet in ["Request access with this account", "Writer email", "Wanted hook or way in"]:
        assert snippet in request_access
    assert "Existing Elbysodic account" in access
    for snippet in [
        "Public visitor",
        "Signed-in account without local membership",
        "Pending access requester",
        "Invited writer",
        "Faceless member",
        "Applicant",
        "Inactive/cross-community viewer",
    ]:
        assert snippet in doc


def test_public_and_account_visitors_get_public_safe_wanted_handoffs(monkeypatch) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch)
        app = create_app(debug=False, services=create_services(path=":memory:"))

        async with TestClient(app) as client:
            public_realm = await client.get("/c/afterlight-accord")
            public_wanted = await client.get("/c/afterlight-accord/wanted/archive-thief")
            cookies = await _production_login(client, email="moira@example.com")
            account_realm = await client.get(
                "/c/afterlight-accord",
                headers={"Cookie": _cookie_header(cookies)},
            )
            account_wanted = await client.get(
                "/c/afterlight-accord/wanted/archive-thief",
                headers={"Cookie": _cookie_header(cookies)},
            )
            account_request = await client.get(
                "/c/afterlight-accord/request-access",
                headers={"Cookie": _cookie_header(cookies)},
            )

        assert public_realm.status == 200
        assert "Afterlight Accord" in public_realm.text
        assert "elbysodic-anonymous-actions" in public_realm.text
        assert "Not a member of Afterlight Accord yet" not in public_realm.text
        assert "Account menu: signed in as" not in public_realm.text

        assert public_wanted.status == 200
        assert "Archive thief with a sealed branch" in public_wanted.text
        assert "Log in to raise interest" in public_wanted.text
        assert 'href="/c/afterlight-accord/request-access"' in public_wanted.text
        assert "Plotting room" not in public_wanted.text
        assert "Staff notes" not in public_wanted.text

        assert account_realm.status == 200
        assert "Account menu: signed in as moira@example.com" in account_realm.text
        assert "Not a member of Afterlight Accord yet" in account_realm.text
        assert "moira@example.com can browse the public preview" in account_realm.text
        assert 'href="/c/afterlight-accord/desk"' not in account_realm.text
        assert "playing as Orin Vale" not in account_realm.text

        assert account_wanted.status == 200
        assert "Request access to raise interest" in account_wanted.text
        assert "Log in to raise interest" not in account_wanted.text
        assert 'href="/c/afterlight-accord/request-access"' in account_wanted.text
        assert "Plotting room" not in account_wanted.text
        assert "Staff notes" not in account_wanted.text

        assert account_request.status == 200
        assert "Existing Elbysodic account" in account_request.text
        assert "Request access with this account" in account_request.text
        assert "Writer email" not in account_request.text
        assert "Face concept" in account_request.text

    asyncio.run(run())


def test_faceless_member_gets_first_face_continuation_without_active_face_controls() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        community = services.seed.community
        user = repo.create_user("faceless-preview@example.com", "hash")
        role = repo.get_role_by_slug(community.id, "member")
        membership = repo.create_membership(
            community.id,
            user.id,
            role.id,
            "faceless-preview",
            "Faceless Preview",
        )
        seed = DemoSeed(community, user, membership, None)
        app = create_app(debug=False, services=AppServices(repo, seed), dev_tools=True)

        async with TestClient(app) as client:
            desk = await client.get("/desk", headers={"Cookie": _dev_identity_cookie(seed)})
            application = await client.get(
                "/applications/new",
                headers={"Cookie": _dev_identity_cookie(seed)},
            )

        assert desk.status == 200
        assert "No faces on your roster yet." in desk.text
        assert "First face" in desk.text
        assert "playing as" not in desk.text
        assert "Application Review Room" not in desk.text

        assert application.status == 200
        assert "Begin a new face" in application.text
        assert "This will become your first active face in X-Men Apocalypse" in application.text
        assert "Claims and reserves" in application.text
        assert "Open calls" in application.text
        assert "First scene" in application.text
        assert "playing as" not in application.text
        assert "Staff notes" not in application.text

    asyncio.run(run())
