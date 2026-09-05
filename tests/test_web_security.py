from __future__ import annotations

import asyncio
import hashlib
import inspect
import io
import re
import tokenize
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlencode

import pytest
from chirp.testing import TestClient
from itsdangerous import BadData, URLSafeTimedSerializer

from elbysodic.db.repositories.discovery import DiscoveryTagInput
from elbysodic.domain.context import (
    DEFAULT_COMMUNITY_ID,
    DEFAULT_COMMUNITY_SLUG,
    CommunityContext,
    resolve_current_community,
)
from elbysodic.services import AppServices, create_services
from elbysodic.services.access import RequestIdentityResolver
from elbysodic.services.auth import session_token_hash
from elbysodic.services.network import (
    network_explore,
    network_home,
    search_public_catalog,
    search_studio_network,
)
from elbysodic.web import create_app
from elbysodic.web.security import CHIRP_GLOBAL_USER_SESSION_KEY
from elbysodic.web.state import get_services

_FORM = {"Content-Type": "application/x-www-form-urlencoded"}
_CSRF_RE = re.compile(r'name="_csrf_token" value="([^"]+)"')
_POST_FORM_TEMPLATE_RE = re.compile(
    r"<form\b(?=[^>]*\bmethod=[\"']post[\"'])[^>]*>.*?</form>",
    re.IGNORECASE | re.DOTALL,
)
_PAGES_DIR = Path(__file__).parents[1] / "src" / "elbysodic" / "web" / "pages"
_SRC_DIR = Path(__file__).parents[1] / "src" / "elbysodic"
_MULTI_TENANCY_DOC = Path(__file__).parents[1] / "docs" / "architecture" / "multi-tenancy.md"


def _python_call_sites(source: str, name: str) -> list[tuple[int, str]]:
    """Return executable `name(` sites, ignoring comments and string literals."""

    previous: tokenize.TokenInfo | None = None
    sites: list[tuple[int, str]] = []
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type in {
            tokenize.COMMENT,
            tokenize.NL,
            tokenize.NEWLINE,
            tokenize.ENCODING,
            tokenize.INDENT,
            tokenize.DEDENT,
            tokenize.ENDMARKER,
        }:
            continue
        if token.type == tokenize.STRING:
            previous = None
            continue
        if (
            previous is not None
            and previous.type == tokenize.NAME
            and previous.string == name
            and token.exact_type == tokenize.LPAR
        ):
            sites.append((previous.start[0], previous.line.strip()))
        previous = token
    return sites


def _package_version(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return ""


def _known_chirpui_context_rail_warning_active() -> bool:
    return _package_version("bengal-chirp").startswith("0.8.") and _package_version(
        "chirp-ui"
    ).startswith("0.10.")


# Advisory-only production warning from chirp's `passkeys` check category: the
# CookieSessionStore carries the single-use WebAuthn challenge between begin
# and finish. Accepted posture — the challenge is popped on finish and this
# single-process deploy has no Redis to move it to.
_KNOWN_PASSKEY_COOKIE_STORE_WARNING = "passkeys=True with a CookieSessionStore"


def _assert_check_passes_or_only_has_known_context_rail_warning(app, capsys) -> None:
    try:
        app.check(warnings_as_errors=True)
    except SystemExit as exc:
        output = capsys.readouterr().out
        if exc.code != 1:
            raise AssertionError(f"unexpected app-check exit code: {exc.code!r}") from exc
        known_warnings = 0
        if _KNOWN_PASSKEY_COOKIE_STORE_WARNING in output:
            known_warnings += 1
        if _known_chirpui_context_rail_warning_active() and 'id="chirpui-context-rail"' in output:
            assert "in chirpui/oob.html" in output
            known_warnings += 1
        if known_warnings == 0:
            raise
        assert "No errors" in output
        assert f"No errors · {known_warnings} warning" in output
    else:
        capsys.readouterr()


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


async def _production_login(
    client: TestClient,
    *,
    email: str,
    password: str | None = None,
    next_url: str = "/studio",
):
    login_phrase = "password" if password is None else password
    page = await client.get(f"/login?next={next_url}")
    cookies = _cookie_values(page)
    login = await client.post(
        "/login",
        body=urlencode(
            {
                "email": email,
                "password": login_phrase,
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


def test_post_form_templates_include_explicit_csrf_field() -> None:
    missing: list[str] = []
    for template in sorted(_PAGES_DIR.rglob("*.html")):
        source = template.read_text()
        for index, match in enumerate(_POST_FORM_TEMPLATE_RE.finditer(source), start=1):
            if "csrf_field()" not in match.group(0):
                relative = template.relative_to(_PAGES_DIR)
                missing.append(f"{relative} form {index}")

    assert missing == []


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


def test_production_config_forces_json_logs_and_honors_chirp_log_level(monkeypatch) -> None:
    _set_production_env(monkeypatch)
    monkeypatch.setenv("CHIRP_LOG_LEVEL", "WARNING")

    app = create_app(debug=False, services=create_services(path=":memory:"))

    assert app.config.log_format == "json"
    assert app.config.log_level == "warning"


def test_invalid_chirp_log_level_falls_back_without_changing_development_format(
    monkeypatch,
) -> None:
    monkeypatch.delenv("ELBYSODIC_ENV", raising=False)
    monkeypatch.setenv("CHIRP_LOG_LEVEL", "verbose")

    app = create_app(debug=True, services=create_services(path=":memory:"))

    assert app.config.log_format == "auto"
    assert app.config.log_level == "info"


def test_chirp_runtime_provisions_htmx_for_hypermedia_templates() -> None:
    async def run() -> None:
        app = create_app(debug=False, services=create_services(path=":memory:"))

        async with TestClient(app) as client:
            response = await client.get("/login")

        assert app.config.htmx is True
        assert 'data-chirp="htmx"' in response.text

    asyncio.run(run())


def test_security_headers_are_registered_for_development_contract_check() -> None:
    async def run() -> None:
        app = create_app(debug=True, services=create_services(path=":memory:"))

        async with TestClient(app) as client:
            response = await client.get("/login")

        headers = dict(response.headers)
        assert headers["x-frame-options"] == "DENY"
        assert headers["x-content-type-options"] == "nosniff"
        assert headers["referrer-policy"] == "strict-origin-when-cross-origin"
        assert "frame-ancestors 'none'" in headers["content-security-policy"]

    asyncio.run(run())


def test_production_default_allowed_hosts_pass_chirp_check(monkeypatch, capsys) -> None:
    monkeypatch.setenv("ELBYSODIC_ENV", "production")
    monkeypatch.setenv("ELBYSODIC_SECRET_KEY", "x" * 32)
    monkeypatch.delenv("ELBYSODIC_ALLOWED_HOSTS", raising=False)
    monkeypatch.setenv("ELBYSODIC_DEMO_MODE", "1")

    app = create_app(debug=False, services=create_services(path=":memory:"))

    assert app.config.allowed_hosts == (".up.railway.app", ".railway.app")
    _assert_check_passes_or_only_has_known_context_rail_warning(app, capsys)


def test_session_cookies_are_secure_in_production(monkeypatch) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch)
        services = create_services(path=":memory:")
        app = create_app(debug=False, services=services)

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
        assert "Already have an account?" in page.text
        assert "linked account request" in page.text
        assert "Invite/demo accounts use password" not in page.text
        assert "email or password is incorrect" in response.text
        assert "elbysodic_session=" not in "\n".join(_response_headers(response, "set-cookie"))

    asyncio.run(run())


def test_unknown_account_and_wrong_password_share_rendered_failure_posture(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch, demo_mode=True)
        app = create_app(debug=False, services=create_services(path=":memory:"))

        async with TestClient(app) as client:
            known_page = await client.get("/login")
            known = await client.post(
                "/login",
                body=urlencode(
                    {
                        "email": "writer@example.com",
                        "password": "wrong-password",
                        "next": "/",
                        "_csrf_token": _csrf_token(known_page.text),
                    }
                ).encode(),
                headers={**_FORM, "Cookie": _cookie_header(_cookie_values(known_page))},
            )
            unknown_page = await client.get("/login")
            unknown = await client.post(
                "/login",
                body=urlencode(
                    {
                        "email": "missing@example.com",
                        "password": "wrong-password",
                        "next": "/",
                        "_csrf_token": _csrf_token(unknown_page.text),
                    }
                ).encode(),
                headers={**_FORM, "Cookie": _cookie_header(_cookie_values(unknown_page))},
            )

        assert known.status == unknown.status == 200
        for response in (known, unknown):
            assert response.text.count("email or password is incorrect") == 1
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
            request_access = await client.get("/request-access")
            studio = await client.get("/studio")
            tenant = await client.get("/c/x-men-apocalypse")
            tenant_world = await client.get("/c/x-men-apocalypse/world")
            tenant_material = await client.get("/c/x-men-apocalypse/world/premise")
            tenant_wanted = await client.get("/c/x-men-apocalypse/wanted")
            tenant_wanted_detail = await client.get(
                "/c/x-men-apocalypse/wanted/brotherhood-rival-for-rogue"
            )
            tenant_search = await client.get("/c/x-men-apocalypse/search?q=rogue")
            tenant_applications = await client.get("/c/x-men-apocalypse/applications")
            tenant_wanted_post = await client.post(
                "/c/x-men-apocalypse/wanted/brotherhood-rival-for-rogue",
                body=urlencode({"intent": "express_interest"}).encode(),
                headers=_FORM,
            )
            post = await client.post(
                "/identity",
                body=urlencode({"intent": "set_default_character", "character_id": "0"}).encode(),
                headers=_FORM,
            )
            personas = await client.get("/dev/personas")

        assert health.status == 200
        assert root.status == 200
        assert "Top 10 realms" in root.text
        assert (
            "Play-by-post realms with faces, scenes, wanted hooks, and continuity." not in root.text
        )
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
        assert "Request access open" in network.text
        assert "Public activity " in network.text
        assert login.status == 200
        assert "_csrf_token" in login.text
        assert 'href="/request-access"' in login.text
        assert "chirpui-sidebar__section-title" not in login.text
        assert "Staff in X-Men Apocalypse" not in login.text
        assert request_access.status == 200
        assert "Access opens through a director invitation." in request_access.text
        assert "Directors gate first entry" in request_access.text
        assert "_csrf_token" not in request_access.text
        assert "chirpui-sidebar__section-title" not in request_access.text
        assert studio.status == 302
        assert dict(studio.headers)["location"] == "/login?next=/studio"
        assert tenant.status == 200
        assert "elbysodic-realm-gateway-hero" in tenant.text
        assert "What has changed" in tenant.text
        assert "Where the story is opening" in tenant.text
        assert "Current Event: B-24 Winter" in tenant.text
        assert "starlane" not in tenant.text
        assert "playing as Rogue" not in tenant.text
        assert "elbysodic-identity-menu" not in tenant.text
        assert tenant_world.status == 200
        assert "World guide" in tenant_world.text
        assert "Application Guide" in tenant_world.text
        assert "Edit guidebook page" not in tenant_world.text
        assert tenant_material.status == 200
        assert "begins after the school has reopened under a fragile truce" in (
            tenant_material.text
        )
        assert "Active scenes" not in tenant_material.text
        assert "Edit guidebook page" not in tenant_material.text
        assert tenant_wanted.status == 200
        assert "Brotherhood rival from Rogue" in tenant_wanted.text
        assert 'href="/c/x-men-apocalypse/characters/rogue"' not in tenant_wanted.text
        assert tenant_wanted_detail.status == 200
        assert "Rogue needs someone who remembers" in tenant_wanted_detail.text
        assert "Log in to raise interest" in tenant_wanted_detail.text
        assert 'href="/c/x-men-apocalypse/request-access"' in tenant_wanted_detail.text
        assert "Interest and reserves" not in tenant_wanted_detail.text
        assert "Interest" not in tenant_wanted_detail.text
        assert tenant_search.status == 200
        assert "Search X-Men Apocalypse" in tenant_search.text
        assert "Rogue" in tenant_search.text
        assert "playing as Rogue" not in tenant_search.text
        assert tenant_applications.status == 302
        assert dict(tenant_applications.headers)["location"] == (
            "/login?next=%2Fc%2Fx-men-apocalypse%2Fapplications"
        )
        assert tenant_wanted_post.status == 403
        assert "Log in to keep writing." in tenant_wanted_post.text
        assert post.status == 403
        assert "Log in to keep writing." in post.text
        assert "/login?next=/identity" in post.text
        assert personas.status == 302

    asyncio.run(run())


def test_anonymous_public_catalog_gets_do_not_issue_or_vary_on_session_cookie(
    monkeypatch,
) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch)
        app = create_app(debug=False, services=create_services(path=":memory:"))

        responses = []
        for path in ("/", "/network", "/c/x-men-apocalypse/world"):
            async with TestClient(app) as client:
                responses.append((path, await client.get(path)))

        for path, response in responses:
            assert response.status == 200
            assert _response_headers(response, "set-cookie") == [], path
            assert "cookie" not in str(dict(response.headers).get("vary", "")).lower()

    asyncio.run(run())


def test_request_user_exposes_global_account_before_membership_resolution(monkeypatch) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch)
        services = create_services(path=":memory:")
        app = create_app(debug=False, services=services)
        seen_users: list[Any] = []

        class RequestUserProbe:
            async def __call__(self, request, call_next):
                if request.path == "/studio":
                    seen_users.append(request.user)
                return await call_next(request)

        app.add_middleware(RequestUserProbe(), priority=5)

        async with TestClient(app) as client:
            _login, cookies = await _production_login(client, email="writer@example.com")
            studio = await client.get(
                "/studio",
                headers={"Cookie": _cookie_header(cookies)},
            )

        assert studio.status == 200
        assert len(seen_users) == 1
        request_user = seen_users[0]
        assert request_user.is_authenticated is True
        assert request_user.id == str(services.seed.user.id)
        assert request_user.account.email == "writer@example.com"
        assert not hasattr(request_user, "membership_id")

    asyncio.run(run())


def test_sha1_chirp_session_is_read_and_reissued_with_sha256(monkeypatch) -> None:
    async def run() -> None:
        secret_key = "x" * 32
        _set_production_env(monkeypatch)
        services = create_services(path=":memory:")
        login, _identity = services.login("writer@example.com", "password")
        app = create_app(debug=False, services=services)
        sha1 = URLSafeTimedSerializer(
            secret_key,
            signer_kwargs={"digest_method": hashlib.sha1},
        )
        legacy_cookie = sha1.dumps(
            {
                "compatibility_marker": "sha1-cookie-loaded",
                CHIRP_GLOBAL_USER_SESSION_KEY: str(login.user.id),
            }
        )

        async with TestClient(app) as client:
            response = await client.get(
                "/network",
                headers={
                    "Cookie": (f"elbysodic_session={login.token}; chirp_session={legacy_cookie}")
                },
            )

        assert response.status == 200
        reissued = _cookie_values(response)["chirp_session"]
        sha256 = URLSafeTimedSerializer(
            secret_key,
            signer_kwargs={"digest_method": hashlib.sha256},
        )
        payload = sha256.loads(reissued)
        assert payload["compatibility_marker"] == "sha1-cookie-loaded"
        assert payload[CHIRP_GLOBAL_USER_SESSION_KEY] == str(login.user.id)
        with pytest.raises(BadData):
            sha1.loads(reissued)

    asyncio.run(run())


def test_production_signed_in_non_member_sees_account_posture_on_public_realm(
    monkeypatch,
) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch)
        services = create_services(path=":memory:")
        app = create_app(debug=False, services=services)

        async with TestClient(app) as client:
            _login, cookies = await _production_login(client, email="moira@example.com")
            response = await client.get(
                "/c/afterlight-accord",
                headers={"Cookie": _cookie_header(cookies)},
            )
            world = await client.get(
                "/c/afterlight-accord/world",
                headers={"Cookie": _cookie_header(cookies)},
            )
            material = await client.get(
                "/c/afterlight-accord/world/accord-seal-fails",
                headers={"Cookie": _cookie_header(cookies)},
            )
            wanted = await client.get(
                "/c/afterlight-accord/wanted",
                headers={"Cookie": _cookie_header(cookies)},
            )
            wanted_detail = await client.get(
                "/c/afterlight-accord/wanted/archive-thief",
                headers={"Cookie": _cookie_header(cookies)},
            )
            search = await client.get(
                "/c/afterlight-accord/search?q=seal",
                headers={"Cookie": _cookie_header(cookies)},
            )
            request_access = await client.get(
                "/c/afterlight-accord/request-access",
                headers={"Cookie": _cookie_header(cookies)},
            )
            request_cookies = {**cookies, **_cookie_values(request_access)}
            request_access_post = await client.post(
                "/request-access",
                body=urlencode(
                    {
                        "community_slug": "afterlight-accord",
                        "display_name": "Moira",
                        "face_concept": "Archivist with a sealed branch",
                        "wanted_hook": "Archive thief",
                        "notes": "Interested in inheritance pressure.",
                        "_csrf_token": _csrf_token(request_access.text),
                    }
                ).encode(),
                headers={**_FORM, "Cookie": _cookie_header(request_cookies)},
            )

        assert response.status == 200
        assert "Afterlight Accord" in response.text
        assert "Account menu: signed in as moira@example.com" in response.text
        assert "Not a member of Afterlight Accord yet" in response.text
        assert "moira@example.com can browse the public preview" in response.text
        assert 'href="/c/afterlight-accord/request-access"' in response.text
        assert "elbysodic-anonymous-actions" not in response.text
        assert "Log in" not in response.text
        assert 'href="/c/afterlight-accord/desk"' not in response.text
        assert "playing as Orin Vale" not in response.text

        for public_route in (world, material, wanted, wanted_detail, search, request_access):
            assert public_route.status == 200
            assert "Account menu: signed in as moira@example.com" in public_route.text
            assert "Not a member of Afterlight Accord yet" in public_route.text
            assert "elbysodic-anonymous-actions" not in public_route.text
            assert "Log in to raise interest" not in public_route.text
            assert 'href="/c/afterlight-accord/desk"' not in public_route.text
            assert "playing as Orin Vale" not in public_route.text

        assert search.status == 200
        assert "Search Afterlight Accord" in search.text
        assert 'aria-label="Search Afterlight Accord"' in search.text
        assert 'title="Afterlight Accord">AA</span>' in search.text
        assert 'action="/c/afterlight-accord/search"' in search.text
        assert 'href="/search?q=seal"' in search.text
        assert "Archive thief with a sealed branch" in wanted_detail.text
        assert "Request access to raise interest" in wanted_detail.text
        assert 'href="/c/afterlight-accord/request-access"' in wanted_detail.text
        assert 'href="/network"' in wanted_detail.text
        assert "Access opens through a director invitation." in request_access.text
        assert "Existing Elbysodic account" in request_access.text
        assert "Request access with this account" in request_access.text
        assert "Writer email" not in request_access.text
        assert "Face concept" in request_access.text
        assert request_access_post.status == 200
        assert "Access request received for your Elbysodic account" in request_access_post.text
        assert "Access request received for moira@example.com" not in request_access_post.text
        access_requests = services.repo.list_community_access_requests(
            services.repo.get_community_by_slug("afterlight-accord").id
        )
        assert access_requests[0].email == "moira@example.com"
        assert access_requests[0].face_concept == "Archivist with a sealed branch"
        assert access_requests[0].wanted_hook == "Archive thief"
        assert (
            access_requests[0].account_user_id
            == services.repo.get_user_by_email("moira@example.com").id
        )

    asyncio.run(run())


def test_production_signed_in_duplicate_access_request_links_existing_record(
    monkeypatch,
) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch)
        services = create_services(path=":memory:")
        community = services.repo.get_community_by_slug("afterlight-accord")
        existing = services.repo.create_community_access_request(
            community.id,
            email="moira@example.com",
            display_name="Anonymous Moira",
            face_concept="Archivist with a sealed branch",
            wanted_hook="Archive thief",
            notes="Submitted before logging in.",
        )
        app = create_app(debug=False, services=services)

        async with TestClient(app) as client:
            _login, cookies = await _production_login(client, email="moira@example.com")
            request_access = await client.get(
                "/c/afterlight-accord/request-access",
                headers={"Cookie": _cookie_header(cookies)},
            )
            request_cookies = {**cookies, **_cookie_values(request_access)}
            before_memberships = services.repo.list_memberships(community.id)
            before_characters = services.repo.list_community_characters(community.id)
            before_invitations = services.repo.list_community_invitations(community.id)
            before_claims = services.repo.list_character_claims(community.id, status=None)
            before_reserves = services.repo.list_character_reserves_for_community(
                community.id,
                status=None,
            )
            before_session_count = services.repo.connection.execute(
                "SELECT COUNT(*) FROM user_sessions"
            ).fetchone()[0]
            response = await client.post(
                "/request-access",
                body=urlencode(
                    {
                        "community_slug": "afterlight-accord",
                        "display_name": "Moira",
                        "face_concept": "Archivist with a sealed branch",
                        "wanted_hook": "Archive thief",
                        "notes": "Link this request to my account.",
                        "_csrf_token": _csrf_token(request_access.text),
                    }
                ).encode(),
                headers={**_FORM, "Cookie": _cookie_header(request_cookies)},
            )
            response_cookies = {**request_cookies, **_cookie_values(response)}
            withdrawn = await client.post(
                "/request-access",
                body=urlencode(
                    {
                        "intent": "withdraw_access_request",
                        "access_request_id": str(existing.id),
                        "community_slug": community.slug,
                        "_csrf_token": _csrf_token(response.text),
                    }
                ).encode(),
                headers={**_FORM, "Cookie": _cookie_header(response_cookies)},
            )

        requests = [
            item
            for item in services.repo.list_community_access_requests(community.id)
            if item.email == "moira@example.com"
        ]
        moira = services.repo.get_user_by_email("moira@example.com")

        assert response.status == 200
        assert "Access request received for your Elbysodic account" in response.text
        assert "Withdraw access request" in response.text
        assert withdrawn.status == 200
        assert "Your access request was withdrawn" in withdrawn.text
        assert "Anonymous Moira" not in withdrawn.text
        assert "Submitted before logging in" not in withdrawn.text
        assert len(requests) == 1
        assert requests[0].id == existing.id
        assert requests[0].account_user_id == moira.id
        assert requests[0].display_name == "Anonymous Moira"
        assert requests[0].status == "withdrawn"
        assert services.repo.list_memberships(community.id) == before_memberships
        assert services.repo.list_community_characters(community.id) == before_characters
        assert services.repo.list_community_invitations(community.id) == before_invitations
        assert services.repo.list_character_claims(community.id, status=None) == before_claims
        assert (
            services.repo.list_character_reserves_for_community(community.id, status=None)
            == before_reserves
        )
        assert (
            services.repo.connection.execute("SELECT COUNT(*) FROM user_sessions").fetchone()[0]
            == before_session_count
        )
        with pytest.raises(LookupError):
            services.repo.get_membership_for_user(community.id, moira.id)

    asyncio.run(run())


def test_production_signed_out_public_realm_keeps_anonymous_posture(monkeypatch) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch)
        app = create_app(debug=False, services=create_services(path=":memory:"))

        async with TestClient(app) as client:
            response = await client.get("/c/afterlight-accord")
            search = await client.get("/c/afterlight-accord/search?q=seal")
            request_access = await client.get("/c/afterlight-accord/request-access")

        assert response.status == 200
        assert "Afterlight Accord" in response.text
        assert "elbysodic-anonymous-actions" in response.text
        assert "Log in" in response.text
        assert "Not a member of Afterlight Accord yet" not in response.text
        assert "Account menu: signed in as" not in response.text
        assert 'href="/c/afterlight-accord/desk"' not in response.text
        assert "playing as Orin Vale" not in response.text

        assert search.status == 200
        assert "Search Afterlight Accord" in search.text
        assert 'title="Afterlight Accord">AA</span>' in search.text
        assert "Account menu: signed in as" not in search.text

        assert request_access.status == 200
        assert "Access opens through a director invitation." in request_access.text
        assert "Writer email" in request_access.text
        assert "Send access request" in request_access.text
        assert 'value="moira@example.com"' not in request_access.text
        assert "Not a member of Afterlight Accord yet" not in request_access.text

    asyncio.run(run())


def test_production_signed_out_public_scene_stops_after_four_posts(monkeypatch) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch)
        services = create_services(path=":memory:")
        community = services.repo.get_community_by_slug("x-men-apocalypse")
        board = services.repo.get_board_by_slug(community.id, "danger-room")
        thread = services.repo.get_thread_by_slug(
            community.id,
            board.id,
            "sentinel-drill",
        )
        rogue = services.repo.get_character_by_slug(community.id, "rogue")
        xavier = services.repo.get_character_by_slug(community.id, "charles-xavier")
        services.repo.create_post(
            community.id,
            thread.id,
            xavier.id,
            "PUBLIC PREVIEW SECOND POST",
        )
        services.repo.create_post(
            community.id,
            thread.id,
            rogue.id,
            "PUBLIC PREVIEW THIRD POST",
        )
        services.repo.create_post(
            community.id,
            thread.id,
            xavier.id,
            "PUBLIC PREVIEW FOURTH POST",
        )
        services.repo.create_post(
            community.id,
            thread.id,
            rogue.id,
            "MEMBER ONLY FIFTH POST",
        )
        app = create_app(debug=False, services=services)
        path = "/c/x-men-apocalypse/boards/danger-room/threads/sentinel-drill"

        async with TestClient(app) as client:
            public = await client.get(path)
            login, cookies = await _production_login(
                client,
                email="writer@example.com",
                next_url=path,
            )
            cookies.update(_cookie_values(login))
            member = await client.get(path, headers={"Cookie": _cookie_header(cookies)})

        assert public.status == 200
        assert "Public scene preview" in public.text
        assert "PUBLIC PREVIEW SECOND POST" in public.text
        assert "PUBLIC PREVIEW FOURTH POST" in public.text
        assert "MEMBER ONLY FIFTH POST" not in public.text
        assert "The scene continues inside the realm" in public.text
        assert 'href="/c/x-men-apocalypse/request-access"' in public.text
        assert '<meta name="robots" content="noindex, nofollow">' in public.text
        assert "writer starlane" not in public.text
        assert "reply-composer" not in public.text
        assert "Staff controls" not in public.text
        assert "active face" not in public.text.lower()
        assert not _response_headers(public, "set-cookie")

        assert member.status == 200
        assert "MEMBER ONLY FIFTH POST" in member.text
        assert "Public scene preview" not in member.text

    asyncio.run(run())


def test_production_public_scene_route_fails_closed_for_member_only_and_private_scenes(
    monkeypatch,
) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch)
        services = create_services(path=":memory:")
        community = services.repo.get_community_by_slug("x-men-apocalypse")
        board = services.repo.get_board_by_slug(community.id, "danger-room")
        rogue = services.repo.get_character_by_slug(community.id, "rogue")
        member_only = services.repo.create_thread(
            community.id,
            board.id,
            rogue.id,
            "member-only-preview-check",
            "MEMBER ONLY SCENE TITLE",
            visibility="members",
        )
        services.repo.create_post(
            community.id,
            member_only.id,
            rogue.id,
            "MEMBER ONLY SCENE BODY",
        )
        private_board = services.repo.get_board_by_slug(community.id, "staff-room")
        private = services.repo.create_thread(
            community.id,
            private_board.id,
            rogue.id,
            "private-preview-check",
            "PRIVATE SCENE TITLE",
            visibility="public_preview",
        )
        services.repo.create_post(
            community.id,
            private.id,
            rogue.id,
            "PRIVATE SCENE BODY",
        )
        draft_face = services.repo.create_character(
            community.id,
            rogue.membership_id,
            "draft-preview-face",
            "DRAFT PREVIEW FACE",
            application_status="draft",
        )
        draft_scene = services.repo.create_thread(
            community.id,
            board.id,
            draft_face.id,
            "draft-face-preview-check",
            "DRAFT FACE SCENE TITLE",
            visibility="public_preview",
        )
        services.repo.create_post(
            community.id,
            draft_scene.id,
            draft_face.id,
            "DRAFT FACE SCENE BODY",
        )
        closed_scene = services.repo.create_thread(
            community.id,
            board.id,
            rogue.id,
            "closed-preview-check",
            "CLOSED SCENE TITLE",
            status="closed",
            visibility="public_preview",
        )
        services.repo.create_post(
            community.id,
            closed_scene.id,
            rogue.id,
            "CLOSED SCENE BODY",
        )
        app = create_app(debug=False, services=services)

        async with TestClient(app) as client:
            member_response = await client.get(
                "/c/x-men-apocalypse/boards/danger-room/threads/member-only-preview-check"
            )
            private_response = await client.get(
                "/c/x-men-apocalypse/boards/staff-room/threads/private-preview-check"
            )
            draft_response = await client.get(
                "/c/x-men-apocalypse/boards/danger-room/threads/draft-face-preview-check"
            )
            closed_response = await client.get(
                "/c/x-men-apocalypse/boards/danger-room/threads/closed-preview-check"
            )

        assert member_response.status == 404
        assert "MEMBER ONLY SCENE BODY" not in member_response.text
        assert private_response.status == 404
        assert "PRIVATE SCENE BODY" not in private_response.text
        assert draft_response.status == 404
        assert "DRAFT FACE SCENE BODY" not in draft_response.text
        assert closed_response.status == 404
        assert "CLOSED SCENE BODY" not in closed_response.text

    asyncio.run(run())


def test_production_account_cannot_withdraw_another_access_request(monkeypatch) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch)
        services = create_services(path=":memory:")
        community = services.repo.get_community_by_slug("afterlight-accord")
        owner = services.repo.get_user_by_email("moira@example.com")
        access_request = services.repo.create_community_access_request(
            community.id,
            email=owner.email,
            display_name="Private Moira Request",
            face_concept="Private sealed archivist",
            wanted_hook="Private archive opening",
            notes="PRIVATE WITHDRAWAL NOTE",
            account_user_id=owner.id,
        )
        app = create_app(debug=False, services=services)

        async with TestClient(app) as client:
            _login, cookies = await _production_login(client, email="writer@example.com")
            page = await client.get(
                "/c/afterlight-accord/request-access",
                headers={"Cookie": _cookie_header(cookies)},
            )
            request_cookies = {**cookies, **_cookie_values(page)}
            response = await client.post(
                "/request-access",
                body=urlencode(
                    {
                        "intent": "withdraw_access_request",
                        "access_request_id": str(access_request.id),
                        "community_slug": community.slug,
                        "_csrf_token": _csrf_token(page.text),
                    }
                ).encode(),
                headers={**_FORM, "Cookie": _cookie_header(request_cookies)},
            )

        unchanged = services.repo.get_community_access_request(
            community.id,
            access_request.id,
        )

        assert response.status == 200
        assert "That access request is not available." in response.text
        assert "Private Moira Request" not in response.text
        assert "Private sealed archivist" not in response.text
        assert "PRIVATE WITHDRAWAL NOTE" not in response.text
        assert unchanged.status == "pending"
        assert [
            event.event_type
            for event in services.repo.list_community_access_request_events(
                community.id,
                access_request.id,
            )
        ] == ["submitted"]

    asyncio.run(run())


def test_access_request_notes_do_not_leak_to_public_or_member_surfaces(monkeypatch) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch)
        services = create_services(path=":memory:")
        community = services.repo.get_community_by_slug("x-men-apocalypse")
        services.repo.create_community_access_request(
            community.id,
            email="private-prospect@example.com",
            display_name="Private Prospect",
            face_concept="Secret transfer",
            wanted_hook="Private hook",
            notes="PRIVATE ACCESS NOTE: knows the staff-only twist.",
        )
        app = create_app(debug=False, services=services)

        async with TestClient(app) as client:
            public_realm = await client.get("/c/x-men-apocalypse")
            network = await client.get("/network?q=private")
            request_access = await client.get("/c/x-men-apocalypse/request-access")
            _login, cookies = await _production_login(
                client,
                email="writer@example.com",
                next_url="/c/x-men-apocalypse/studio/launch",
            )
            member_studio = await client.get(
                "/c/x-men-apocalypse/studio/launch",
                headers={"Cookie": _cookie_header(cookies)},
            )
            member_operations = await client.get(
                "/c/x-men-apocalypse/studio/operations",
                headers={"Cookie": _cookie_header(cookies)},
            )

            member_today = await client.get(
                "/c/x-men-apocalypse/studio",
                headers={"Cookie": _cookie_header(cookies)},
            )

        for response in (
            public_realm,
            network,
            request_access,
            member_studio,
            member_operations,
            member_today,
        ):
            assert "PRIVATE ACCESS NOTE" not in response.text
            assert "private-prospect@example.com" not in response.text
            assert "Secret transfer" not in response.text

        assert public_realm.status == 200
        assert network.status == 200
        assert request_access.status == 200
        assert member_studio.status == 403
        assert member_operations.status == 302
        assert _response_headers(member_operations, "location")
        assert any(
            value.endswith("/studio") or "/studio" in value
            for value in _response_headers(member_operations, "location")
        )
        assert member_today.status == 200

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
            assert "No public-ready realms" in response.text
            assert "No public-ready realms are open yet." in response.text
            assert "The request completed, but this database has no realm" in response.text
            assert 'href="/request-access"' in response.text
            assert 'href="/login?next=/"' in response.text
            assert "No programs are available yet." not in response.text
            assert "elbysodic-identity-menu" not in response.text

    asyncio.run(run())


def test_production_backstage_realm_stays_out_of_public_network(monkeypatch) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch)
        services = create_services(path=":memory:", seed_demo=False)
        director_phrase = "director-password"
        services.create_first_realm(
            realm_name="Starter Realm",
            realm_slug="starter-realm",
            director_email="director@example.com",
            director_password=director_phrase,
            director_username="starlane",
            director_display_name="Starter Director",
        )
        app = create_app(debug=False, services=services)

        async with TestClient(app) as client:
            root = await client.get("/")
            network = await client.get("/network")
            direct_preview = await client.get("/c/starter-realm")
            direct_world = await client.get("/c/starter-realm/world")
            login, cookies = await _production_login(
                client,
                email="director@example.com",
                password=director_phrase,
                next_url="/network",
            )
            director_network = await client.get(
                "/network",
                headers={"Cookie": _cookie_header(cookies)},
            )

        assert root.status == 200
        assert network.status == 200
        for response in (root, network):
            assert "No public-ready realms" in response.text
            assert "No public-ready realms are open yet." in response.text
            assert "Starter Realm" not in response.text
            assert "starter-realm" not in response.text
        assert direct_preview.status == 404
        assert direct_world.status == 404
        assert "Starter Director" not in direct_preview.text
        assert "Starter Director" not in direct_world.text
        assert login.status == 302
        assert director_network.status == 200
        assert "No public-ready realms are open yet." in director_network.text
        assert "Starter Director" in director_network.text
        assert "Director in Starter Realm" in director_network.text
        assert services.repo.get_user_by_email("director@example.com").password_hash.startswith(
            "$argon2id$"
        )
        assert (
            'class="elbysodic-network-card__realm-link" href="/c/starter-realm"'
            not in director_network.text
        )

    asyncio.run(run())


def test_public_network_catalog_hides_membership_and_staff_signals(monkeypatch) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch)
        app = create_app(debug=False, services=create_services(path=":memory:"))

        async with TestClient(app) as client:
            network = await client.get("/network?q=wanted")

        assert network.status == 200
        assert "Request access open" in network.text
        assert "Public activity " in network.text
        assert "Application guide ready" in network.text
        assert "Claims configured" in network.text
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


def test_public_network_cards_link_to_request_access(monkeypatch) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch)
        app = create_app(debug=False, services=create_services(path=":memory:"))

        async with TestClient(app) as client:
            network = await client.get("/network?q=x-men")

        assert network.status == 200
        assert 'href="/c/x-men-apocalypse/request-access"' in network.text
        assert 'aria-label="Request access"' in network.text
        assert "Application Review Room" not in network.text
        assert "unread" not in network.text

    asyncio.run(run())


def test_signed_in_network_marks_current_realm_without_leaking_staff(monkeypatch) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch)
        app = create_app(debug=False, services=create_services(path=":memory:"))

        async with TestClient(app) as client:
            _login, cookies = await _production_login(client, email="writer@example.com")
            root = await client.get("/", headers={"Cookie": _cookie_header(cookies)})
            network = await client.get(
                "/network?q=x-men",
                headers={"Cookie": _cookie_header(cookies)},
            )

        assert root.status == 200
        assert "Signed in as Lane in X-Men Apocalypse" in root.text
        assert (
            "Your account is active; choose a realm card to enter, preview, or request access."
            in (root.text)
        )
        assert "Log in" not in root.text
        assert "Log out" in root.text
        assert network.status == 200
        assert "Signed in as Lane in X-Men Apocalypse" in network.text
        assert "Explore cards stay public-preview safe" in network.text
        assert "Log in" not in network.text
        assert "Log out" in network.text
        assert "current membership" in network.text
        assert 'href="/c/x-men-apocalypse/request-access"' not in network.text
        assert "Staff in X-Men Apocalypse" not in network.text
        assert "Application Review Room" not in network.text

    asyncio.run(run())


def test_public_network_search_contract_stays_service_owned() -> None:
    services = create_services(path=":memory:")

    directory = services.public_studio_network()
    magic_results = search_studio_network(directory, "glass staircase")
    wanted_results = search_studio_network(directory, "wanted")

    assert [program.community.slug for program in magic_results] == ["hp-universe"]
    assert {program.community.slug for program in wanted_results}
    assert all(program.membership is None for program in wanted_results)
    assert all(program.current_character is None for program in wanted_results)
    assert all(program.unread_notification_count == 0 for program in wanted_results)
    assert all(program.plotting_room_count == 0 for program in wanted_results)
    assert all(program.invite_posture_label == "Public preview" for program in wanted_results)
    assert all(program.application_material_count >= 0 for program in wanted_results)
    assert all(program.claim_type_count >= 0 for program in wanted_results)


def test_public_network_uses_only_published_catalog_materials(monkeypatch) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch)
        services = create_services(path=":memory:")
        hp = services.repo.get_community_by_slug("hp-universe")
        services.repo.create_material(
            hp.id,
            "draft-public-catalog-leak",
            "Draft Public Catalog Leak",
            material_type="premise",
            summary="draft-only catalog phrase",
            body="This draft should never appear in public discovery.",
            status="draft",
            sort_order=-100,
            is_featured=True,
        )
        services.repo.create_material(
            hp.id,
            "draft-event-leak",
            "Draft Event Leak",
            material_type="event",
            summary="draft-only event phrase",
            body="This draft event should never appear in public discovery.",
            status="draft",
            sort_order=-100,
            is_featured=True,
        )
        app = create_app(debug=False, services=services)

        directory = services.public_studio_network()
        hp_program = next(
            program for program in directory.programs if program.community.id == hp.id
        )
        explore = services.network_explore("draft-only")

        async with TestClient(app) as client:
            network = await client.get("/network?q=draft-only")

        assert hp_program.premise is None or hp_program.premise.material.status == "published"
        assert (
            hp_program.current_event is None
            or hp_program.current_event.material.status == "published"
        )
        assert explore.results == []
        assert network.status == 200
        assert "Draft Public Catalog Leak" not in network.text
        assert "draft-only catalog phrase" not in network.text
        assert "Draft Event Leak" not in network.text
        assert "draft-only event phrase" not in network.text

    asyncio.run(run())


def test_network_read_models_split_public_cards_from_viewer_state() -> None:
    services = create_services(path=":memory:")

    home = services.network_home()
    explore = services.network_explore("wanted")

    assert home.featured is not None
    assert home.featured.community.slug == "afterlight-accord"
    assert home.return_path is not None
    assert home.return_path.desk_href.startswith("/c/")
    assert home.slices[0].title == "Top 10 realms"
    assert len(home.slices[0].programs) == 10
    assert {home_slice.title for home_slice in home.slices[1:]} >= {
        "Small-town social webs",
        "Weird-town mysteries",
    }
    assert explore.results
    assert {facet.label for facet in explore.browse_facets} >= {
        "open wanted hooks",
        "small-town social web",
        "weird-town mystery",
    }
    assert {group.title for group in explore.filter_groups} >= {
        "Premise engine",
        "Play engine",
        "Lore aperture",
        "Start here",
        "Pace and touchpoints",
        "Roster posture",
    }
    premise_group = next(
        group for group in explore.filter_groups if group.title == "Premise engine"
    )
    assert {option.label for option in premise_group.options} >= {
        "Small Town Social Web",
        "Weird Town Mystery",
        "Urban Supernatural Pressure Cooker",
        "Court And Faction Fantasy",
        "Strange Frontier",
    }
    assert all(option.result_count > 0 for option in premise_group.options)
    assert {lane.title for lane in explore.relationship_lanes} >= {
        "Start with a premise",
        "Start with a wanted hook",
        "Start with a current chapter",
    }
    lanes_by_title = {lane.title: lane for lane in explore.relationship_lanes}
    assert lanes_by_title["Start with a premise"].result_count == len(
        services.network_explore().results
    )
    assert lanes_by_title["Start with a wanted hook"].result_count == len(explore.results)

    for card in [home.featured, *explore.results]:
        assert card is not None
        assert not hasattr(card, "membership")
        assert not hasattr(card, "role")
        assert not hasattr(card, "current_character")
        assert not hasattr(card, "unread_notification_count")
        assert not hasattr(card, "plotting_room_count")
        assert card.invite_posture_label == "Public preview"
        assert card.request_access_href == f"/c/{card.community.slug}/request-access"


def test_public_catalog_helpers_reject_member_network_read_models() -> None:
    services = create_services(path=":memory:")
    member_program = services.studio_network().programs[0]
    wrong_cards = cast(Any, [member_program])

    with pytest.raises(TypeError, match="network_home requires PublicCatalogCard"):
        network_home(wrong_cards, None)
    with pytest.raises(TypeError, match="network_explore requires PublicCatalogCard"):
        network_explore(wrong_cards, "wanted")
    with pytest.raises(TypeError, match="search_public_catalog requires PublicCatalogCard"):
        search_public_catalog(wrong_cards, "wanted")


def test_public_network_explore_keeps_filters_below_results() -> None:
    async def run() -> None:
        app = create_app(debug=False, services=create_services(path=":memory:"))
        async with TestClient(app) as client:
            response = await client.get("/network")

        assert response.status == 200
        assert 'class="elbysodic-network-filter-drawer"' in response.text
        assert "elbysodic-network-explore-map" not in response.text
        assert "elbysodic-network-two-up" not in response.text
        assert "Browse by fit" in response.text
        assert response.text.index("explore-results-heading") < response.text.index(
            "elbysodic-network-filter-drawer"
        )

    asyncio.run(run())


def test_network_home_does_not_render_full_filter_matrix() -> None:
    async def run() -> None:
        app = create_app(debug=False, services=create_services(path=":memory:"))
        async with TestClient(app) as client:
            response = await client.get("/")

        assert response.status == 200
        assert "Search by premise, pace, hooks, and chapters in motion." not in response.text
        assert 'class="elbysodic-network-home-genres"' not in response.text
        assert "Top 10 realms" in response.text
        assert "Premise engines" not in response.text
        assert "Your desk is one click away." not in response.text
        assert 'class="elbysodic-network-filter-panel"' not in response.text

    asyncio.run(run())


def test_public_network_search_uses_explicit_discovery_metadata() -> None:
    services = create_services(path=":memory:")
    community = services.repo.get_community_by_slug("rl-small-town")
    services.repo.upsert_discovery_profile(
        community.id,
        premise_archetype="coastal-status-town",
        play_engine="character-driven",
        lore_aperture="low-lore-real-life",
        access_model="public-preview",
        application_model="profile-app",
        activity_pace="relaxed",
        catalog_pitch="A coastal social web around rituals, status, and returning faces.",
    )
    services.repo.replace_discovery_tags(
        community.id,
        (
            DiscoveryTagInput(
                "premise",
                "porch-ritual",
                "Porch ritual town",
                search_text="porch rituals ladder",
            ),
        ),
    )

    results = services.network_explore("porch-ritual").results

    assert [card.community.slug for card in results] == ["rl-small-town"]
    assert results[0].discovery_profile is not None
    assert results[0].discovery_profile.premise_archetype == "coastal-status-town"
    assert [tag.tag_key for tag in results[0].discovery_tags] == ["porch-ritual"]


def test_public_network_search_finds_middle_premise_seed_archetypes() -> None:
    services = create_services(path=":memory:")

    court_results = services.network_explore("succession-crisis").results
    accord_results = services.network_explore("role-archetype").results
    brightline_results = services.network_explore("spotlight city").results

    assert [card.community.slug for card in court_results] == ["crownfall"]
    assert [card.community.slug for card in accord_results] == ["afterlight-accord"]
    assert [card.community.slug for card in brightline_results] == ["brightline"]


def test_public_network_search_finds_final_premise_seed_archetypes() -> None:
    services = create_services(path=":memory:")

    trial_results = services.network_explore("consent-safe-trials").results
    occult_results = services.network_explore("murder-inquiry").results
    frontier_results = services.network_explore("station law").results

    assert [card.community.slug for card in trial_results] == ["emberhouse"]
    assert [card.community.slug for card in occult_results] == ["gaslight-ward"]
    assert [card.community.slug for card in frontier_results] == ["wayfarer-station"]


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


def test_production_login_rate_limit_ignores_spoofed_forwarded_for(monkeypatch) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch)
        app = create_app(debug=False, services=create_services(path=":memory:"))

        async with TestClient(app) as client:
            responses = [
                await client.post(
                    "/login",
                    body=b"",
                    headers={**_FORM, "X-Forwarded-For": f"198.51.100.{attempt}"},
                )
                for attempt in range(11)
            ]

        assert [response.status for response in responses[:10]] == [403] * 10
        assert responses[10].status == 429

    asyncio.run(run())


def test_login_rate_limit_renders_htmx_429_fragment(monkeypatch) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch)
        app = create_app(debug=False, services=create_services(path=":memory:"))

        async with TestClient(app) as client:
            for _attempt in range(10):
                await client.post("/login", body=b"", headers=_FORM)
            htmx_blocked = await client.post(
                "/login",
                body=b"",
                headers={**_FORM, "HX-Request": "true"},
            )
            plain_blocked = await client.post("/login", body=b"", headers=_FORM)

        assert htmx_blocked.status == 429
        assert dict(htmx_blocked.headers)["retry-after"] == "300"
        assert "Too many login attempts" in htmx_blocked.text
        assert 'role="alert"' in htmx_blocked.text
        assert "elbysodic-form-error" in htmx_blocked.text
        assert plain_blocked.status == 429
        assert plain_blocked.text == "Too Many Requests"

    asyncio.run(run())


def test_development_login_rate_limit_ignores_spoofed_forwarded_for(monkeypatch) -> None:
    async def run() -> None:
        monkeypatch.delenv("ELBYSODIC_ENV", raising=False)
        monkeypatch.delenv("ELBYSODIC_SECRET_KEY", raising=False)
        app = create_app(debug=False, services=create_services(path=":memory:"))

        async with TestClient(app) as client:
            responses = [
                await client.post(
                    "/login",
                    body=b"",
                    headers={**_FORM, "X-Forwarded-For": f"203.0.113.{attempt}"},
                )
                for attempt in range(11)
            ]

        # A rotating spoofed X-Forwarded-For must not rotate the limiter key:
        # keying uses the fail-closed Request.trusted_client_ip, so the 11th
        # attempt from the same client is blocked even in development.
        assert all(response.status != 429 for response in responses[:10])
        assert responses[10].status == 429

    asyncio.run(run())


def test_development_and_production_resolve_the_same_middleware_chain(monkeypatch) -> None:
    def resolved_chain(app) -> list[str]:
        state = app._mutable_state
        ordered = sorted(
            zip(
                state.middleware_priorities,
                range(len(state.middleware_list)),
                state.middleware_list,
                strict=True,
            )
        )
        return [type(middleware).__name__ for _priority, _index, middleware in ordered]

    monkeypatch.delenv("ELBYSODIC_ENV", raising=False)
    monkeypatch.delenv("ELBYSODIC_SECRET_KEY", raising=False)
    development = create_app(debug=True, services=create_services(path=":memory:"))
    _set_production_env(monkeypatch)
    production = create_app(debug=False, services=create_services(path=":memory:"))

    development_chain = resolved_chain(development)
    assert development_chain == resolved_chain(production)
    assert development_chain.index("SessionMiddleware") < development_chain.index(
        "AppSessionIdentityMiddleware"
    )
    assert development_chain.index("AppSessionIdentityMiddleware") < development_chain.index(
        "AuthMiddleware"
    )
    assert development_chain.index("AuthMiddleware") < development_chain.index("CSRFMiddleware")
    assert development_chain.index("CSRFMiddleware") < development_chain.index(
        "SecurityHeadersMiddleware"
    )
    assert "AuthRateLimitMiddleware" in development_chain


def test_development_enforces_csrf_with_real_tokens(monkeypatch) -> None:
    async def run() -> None:
        monkeypatch.delenv("ELBYSODIC_ENV", raising=False)
        monkeypatch.delenv("ELBYSODIC_SECRET_KEY", raising=False)
        app = create_app(debug=False, services=create_services(path=":memory:"))

        async with TestClient(app) as client:
            login_page = await client.get("/login")
            invalid = await client.post(
                "/login",
                body=urlencode(
                    {"email": "moira@example.com", "password": "password", "next": "/studio"}
                ).encode(),
                headers={**_FORM, "X-CSRF-Token": "not-the-session-token"},
            )
            valid = await client.post(
                "/login",
                body=urlencode(
                    {"email": "moira@example.com", "password": "password", "next": "/studio"}
                ).encode(),
                headers=_FORM,
            )

        # The dev stubs are gone: csrf_field() renders a real session-bound
        # token in development, and CSRFMiddleware enforces it on POST.
        assert login_page.status == 200
        assert _CSRF_RE.search(login_page.text) is not None
        assert invalid.status == 403
        assert valid.status == 302

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
            public_root = await client.get("/")
            public_search = await client.get("/search?q=rogue")
            public_realm = await client.get("/c/x-men-apocalypse")
            seed_media = await client.get("/elbysodic-static/seed-media/xmen-hero.svg")
            signed_out_studio = await client.get("/studio")
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
            revoked_session = services.repo.get_user_session_by_token_hash(
                session_token_hash(original_session)
            )

        assert health.status == 200
        assert public_root.status == 200
        assert "Top 10 realms" in public_root.text
        assert "playing as Rogue" not in public_root.text
        assert public_search.status == 200
        assert "Search All realms" in public_search.text
        assert 'results for "rogue"' in public_search.text
        assert "playing as Rogue" not in public_search.text
        assert public_realm.status == 200
        assert "X-Men Apocalypse" in public_realm.text
        assert "elbysodic-identity-menu" not in public_realm.text
        assert seed_media.status == 200
        assert signed_out_studio.status == 302
        assert dict(signed_out_studio.headers)["location"] == "/login?next=/studio"
        assert login.status == 302
        assert dict(login.headers)["location"] == "/c/x-men-apocalypse"
        assert xmen_home.status == 200
        assert "X-Men Apocalypse" in xmen_home.text
        assert network.status == 200
        assert "HP Universe" in network.text
        assert "playing as Rogue" in network.text
        assert thread.status == 200
        assert "Sentinel drill after midnight" in thread.text
        assert "Reply" in thread.text
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
        assert revoked_session.revoked_at is not None
        assert revoked_session.selected_community_id is None
        assert revoked_session.selected_membership_id is None

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


def test_production_session_selected_inactive_membership_fails_closed(
    monkeypatch,
) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch)
        app = create_app(debug=False, services=create_services(path=":memory:"))
        services = get_services()
        community = services.seed.community
        writer = services.repo.get_user_by_email("writer@example.com")
        membership = services.repo.get_membership_for_user(community.id, writer.id)

        async with TestClient(app) as client:
            _login, cookies = await _production_login(client, email="writer@example.com")
            active_studio = await client.get(
                "/studio",
                headers={"Cookie": _cookie_header(cookies)},
            )
            services.repo.connection.execute(
                """
                UPDATE community_memberships
                SET is_active = 0
                WHERE community_id = ? AND id = ?
                """,
                (community.id, membership.id),
            )
            services.repo.connection.commit()
            inactive_studio = await client.get(
                "/studio",
                headers={"Cookie": _cookie_header(cookies)},
            )

        assert active_studio.status == 200
        assert "Member in X-Men Apocalypse" in active_studio.text
        assert inactive_studio.status == 403
        assert "Member in X-Men Apocalypse" not in inactive_studio.text
        assert "Staff in X-Men Apocalypse" not in inactive_studio.text
        assert "playing as Rogue" not in inactive_studio.text

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
                        "_action": "save_review",
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
                        "_action": "save_review",
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


def _request_identity_call_offenders(name: str) -> list[str]:
    offenders: list[str] = []
    for directory in (_SRC_DIR / "web", _SRC_DIR / "services"):
        for path in sorted(directory.rglob("*.py")):
            source = path.read_text(encoding="utf-8")
            relative = path.relative_to(_SRC_DIR)
            for lineno, line in _python_call_sites(source, name):
                offenders.append(f"{relative}:{lineno}:{line}")
    return offenders


def test_request_identity_resolution_never_calls_resolve_current_community() -> None:
    assert _request_identity_call_offenders("resolve_current_community") == []
    assert _request_identity_call_offenders("CommunityContext") == []

    resolver_source = inspect.getsource(RequestIdentityResolver)
    assert "resolve_current_community(" not in resolver_source
    assert "CommunityContext(" not in resolver_source

    for_request_source = inspect.getsource(AppServices.for_request)
    assert "RequestIdentityResolver" in for_request_source
    assert "resolve_current_community(" not in for_request_source
    assert "CommunityContext(" not in for_request_source

    get_services_source = inspect.getsource(get_services)
    assert ".for_request(request)" in get_services_source
    assert "resolve_current_community(" not in get_services_source


def test_for_request_identity_does_not_mint_from_community_context_defaults() -> None:
    assert DEFAULT_COMMUNITY_ID == 1
    assert DEFAULT_COMMUNITY_SLUG == "x-men-apocalypse"
    community_doc = " ".join((CommunityContext.__doc__ or "").split())
    assert "not a request minting path" in community_doc
    assert "for_request" in community_doc
    assert "RequestIdentityResolver" in community_doc

    helper_doc = " ".join((resolve_current_community.__doc__ or "").split())
    assert "legacy" in helper_doc
    assert "not a request minting path" in helper_doc
    assert "for_request" in helper_doc
    assert "RequestIdentityResolver" in helper_doc

    identity_docs = _MULTI_TENANCY_DOC.read_text(encoding="utf-8")
    boundary = identity_docs.split("## Request Identity Boundary", 1)[1]
    assert "AppServices.for_request()" in boundary
    assert "RequestIdentityResolver" in boundary
    assert "`CommunityContext()` defaults" in boundary
    assert "not a request minting path" in boundary
    assert "`resolve_current_community()`" in boundary
    assert "legacy helper" in boundary
    assert "DEFAULT_COMMUNITY_SLUG" in boundary
    assert "DEFAULT_COMMUNITY_ID" in boundary
    assert "Unknown-host fallthrough" in boundary
