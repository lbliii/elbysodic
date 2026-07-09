"""Passkey credential storage, registration, and sign-in contracts.

WebAuthn ceremonies are exercised through the app's routes with static
py_webauthn vectors (see ``tests/_passkey_vectors.py``); browser QA with a
Playwright virtual authenticator is tracked separately (#248).
"""

from __future__ import annotations

import asyncio
import re
from urllib.parse import urlencode

import pytest
from chirp.security.passkeys import PasskeyCredential
from chirp.testing import TestClient

from elbysodic.services import create_services
from elbysodic.services.auth import SESSION_COOKIE, user_for_session_token
from elbysodic.services.tenant_integrity import tenant_integrity_audit
from elbysodic.web import create_app
from tests._passkey_vectors import (
    AUTH_CREDENTIAL,
    AUTH_CREDENTIAL_ID_BYTES,
    AUTH_NEW_SIGN_COUNT,
    AUTH_PUBLIC_KEY_BYTES,
    AUTH_STORED_SIGN_COUNT,
    REG_CREDENTIAL,
    REG_CREDENTIAL_ID_BYTES,
    TEST_PASSKEY_CONFIG,
    WRONG_ORIGIN_PASSKEY_CONFIG,
    patch_fixed_ceremony,
)

_FORM = {"Content-Type": "application/x-www-form-urlencoded"}
_CSRF_RE = re.compile(r'name="_csrf_token" value="([^"]+)"')


# ---------------------------------------------------------------------------
# Repository contracts (#245)
# ---------------------------------------------------------------------------


def test_stored_passkey_credential_satisfies_chirp_protocol() -> None:
    services = create_services(path=":memory:")
    user = services.repo.create_user("protocol@example.com", "hash")
    credential = services.repo.create_user_passkey_credential(
        user.id,
        credential_id=b"credential-id",
        public_key=b"public-key",
        sign_count=3,
    )

    # Static conformance: the annotated assignment below is checked by ty.
    stored: PasskeyCredential = credential

    assert isinstance(credential, PasskeyCredential)
    assert stored.credential_id == b"credential-id"
    assert stored.public_key == b"public-key"
    assert stored.sign_count == 3
    assert stored.user_id == user.id


def test_passkey_repository_round_trip_supports_ceremony_needs() -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    user = repo.create_user("roundtrip@example.com", "hash")

    first = repo.create_user_passkey_credential(
        user.id,
        credential_id=b"first-credential",
        public_key=b"first-key",
        sign_count=0,
        transports=("internal", "hybrid"),
        label="Laptop",
    )
    second = repo.create_user_passkey_credential(
        user.id,
        credential_id=b"second-credential",
        public_key=b"second-key",
        sign_count=7,
    )

    listed = repo.list_user_passkey_credentials(user.id)
    assert [credential.id for credential in listed] == [first.id, second.id]
    assert listed[0].transports == ("internal", "hybrid")
    assert listed[0].label == "Laptop"
    assert listed[0].last_used_at is None

    loaded = repo.get_user_passkey_credential(b"first-credential")
    assert loaded.id == first.id

    touched = repo.update_user_passkey_credential_sign_count(b"first-credential", 12)
    assert touched.sign_count == 12
    assert touched.last_used_at is not None

    renamed = repo.rename_user_passkey_credential(user.id, first.id, "Desk key")
    assert renamed.label == "Desk key"

    repo.delete_user_passkey_credential(user.id, first.id)
    assert [credential.id for credential in repo.list_user_passkey_credentials(user.id)] == [
        second.id
    ]
    with pytest.raises(LookupError):
        repo.get_user_passkey_credential(b"first-credential")


def test_passkey_repository_scopes_mutations_to_the_owning_account() -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    owner = repo.create_user("owner@example.com", "hash")
    other = repo.create_user("other@example.com", "hash")
    credential = repo.create_user_passkey_credential(
        owner.id,
        credential_id=b"owned-credential",
        public_key=b"key",
        sign_count=0,
    )

    with pytest.raises(PermissionError):
        repo.delete_user_passkey_credential(other.id, credential.id)
    with pytest.raises(PermissionError):
        repo.rename_user_passkey_credential(other.id, credential.id, "hijacked")
    assert repo.get_user_passkey_credential(b"owned-credential").user_id == owner.id


def test_passkey_repository_rejects_duplicate_credential_ids() -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    user = repo.create_user("duplicate@example.com", "hash")
    repo.create_user_passkey_credential(
        user.id,
        credential_id=b"duplicated",
        public_key=b"key",
        sign_count=0,
    )

    with pytest.raises(ValueError, match="already registered"):
        repo.create_user_passkey_credential(
            user.id,
            credential_id=b"duplicated",
            public_key=b"key",
            sign_count=0,
        )


def test_tenant_integrity_audit_stays_clean_with_passkey_rows() -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    user = repo.create_user("audit@example.com", "hash")
    repo.create_user_passkey_credential(
        user.id,
        credential_id=b"audited-credential",
        public_key=b"key",
        sign_count=0,
        label="Audited key",
    )

    report = tenant_integrity_audit(repo)

    assert report.ok is True


# ---------------------------------------------------------------------------
# Web helpers
# ---------------------------------------------------------------------------


def _cookie_values(*responses) -> dict[str, str]:
    values: dict[str, str] = {}
    for response in responses:
        for key, value in response.headers:
            if str(key).lower() == "set-cookie":
                pair = str(value).split(";", 1)[0]
                name, _, cookie_value = pair.partition("=")
                values[name] = cookie_value
    return values


def _cookie_header(cookies: dict[str, str]) -> str:
    return "; ".join(f"{name}={value}" for name, value in cookies.items())


def _set_cookie_lines(response) -> str:
    return "\n".join(
        str(value) for key, value in response.headers if str(key).lower() == "set-cookie"
    )


def _use_test_passkey_config(monkeypatch, config=TEST_PASSKEY_CONFIG) -> None:
    monkeypatch.setattr(
        "elbysodic.web.passkeys.config_for_request",
        lambda request: config,
    )


def _seed_login_credential(repo, user_id: int, *, sign_count: int = AUTH_STORED_SIGN_COUNT):
    return repo.create_user_passkey_credential(
        user_id,
        credential_id=AUTH_CREDENTIAL_ID_BYTES,
        public_key=AUTH_PUBLIC_KEY_BYTES,
        sign_count=sign_count,
        label="Login key",
    )


# ---------------------------------------------------------------------------
# Registration flow (#246)
# ---------------------------------------------------------------------------


def test_passkey_registration_flow_persists_labeled_credential(monkeypatch) -> None:
    async def run() -> None:
        patch_fixed_ceremony(monkeypatch)
        _use_test_passkey_config(monkeypatch)
        services = create_services(path=":memory:")
        app = create_app(debug=False, services=services)

        async with TestClient(app) as client:
            begin = await client.post("/identity/passkeys/begin")
            assert begin.status == 200
            assert begin.json["challenge"]
            finish = await client.post(
                "/identity/passkeys/finish",
                json={**REG_CREDENTIAL, "label": "Test laptop"},
                headers={"Cookie": _cookie_header(_cookie_values(begin))},
            )

        assert finish.status == 200
        assert finish.json == {"ok": True, "redirect": "/identity"}
        user_id = services.viewer().membership.user_id
        stored = services.repo.list_user_passkey_credentials(user_id)
        assert [credential.credential_id for credential in stored] == [REG_CREDENTIAL_ID_BYTES]
        assert stored[0].label == "Test laptop"
        assert stored[0].transports == ("internal",)

    asyncio.run(run())


def test_passkey_registration_rejects_wrong_origin_and_stores_nothing(monkeypatch) -> None:
    async def run() -> None:
        patch_fixed_ceremony(monkeypatch)
        _use_test_passkey_config(monkeypatch, WRONG_ORIGIN_PASSKEY_CONFIG)
        services = create_services(path=":memory:")
        app = create_app(debug=False, services=services)

        async with TestClient(app) as client:
            begin = await client.post("/identity/passkeys/begin")
            finish = await client.post(
                "/identity/passkeys/finish",
                json=dict(REG_CREDENTIAL),
                headers={"Cookie": _cookie_header(_cookie_values(begin))},
            )

        assert finish.status == 422
        assert finish.json["ok"] is False
        user_id = services.viewer().membership.user_id
        assert services.repo.list_user_passkey_credentials(user_id) == []

    asyncio.run(run())


def test_passkey_registration_finish_requires_a_live_challenge(monkeypatch) -> None:
    async def run() -> None:
        _use_test_passkey_config(monkeypatch)
        services = create_services(path=":memory:")
        app = create_app(debug=False, services=services)

        async with TestClient(app) as client:
            finish = await client.post(
                "/identity/passkeys/finish",
                json=dict(REG_CREDENTIAL),
            )

        assert finish.status == 422
        assert "expired" in finish.json["error"].lower()

    asyncio.run(run())


def test_passkey_registration_rejects_credentials_registered_elsewhere(monkeypatch) -> None:
    async def run() -> None:
        patch_fixed_ceremony(monkeypatch)
        _use_test_passkey_config(monkeypatch)
        services = create_services(path=":memory:")
        other_account = services.repo.create_user("other-account@example.com", "hash")
        services.repo.create_user_passkey_credential(
            other_account.id,
            credential_id=REG_CREDENTIAL_ID_BYTES,
            public_key=b"key",
            sign_count=0,
        )
        app = create_app(debug=False, services=services)

        async with TestClient(app) as client:
            begin = await client.post("/identity/passkeys/begin")
            finish = await client.post(
                "/identity/passkeys/finish",
                json=dict(REG_CREDENTIAL),
                headers={"Cookie": _cookie_header(_cookie_values(begin))},
            )

        assert finish.status == 422
        assert "already registered" in finish.json["error"]
        user_id = services.viewer().membership.user_id
        assert services.repo.list_user_passkey_credentials(user_id) == []

    asyncio.run(run())


def test_identity_settings_page_lists_renames_and_removes_passkeys() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        user_id = services.viewer().membership.user_id
        credential = services.repo.create_user_passkey_credential(
            user_id,
            credential_id=b"settings-credential",
            public_key=b"key",
            sign_count=0,
            label="Original name",
        )
        app = create_app(debug=False, services=services)

        async with TestClient(app) as client:
            page = await client.get("/identity")
            assert page.status == 200
            assert "Original name" in page.text
            assert 'id="passkey-register"' in page.text

            rename = await client.post(
                "/identity",
                body=urlencode(
                    {
                        "intent": "rename_passkey",
                        "passkey_id": str(credential.id),
                        "label": "Renamed key",
                    }
                ).encode(),
                headers=_FORM,
            )
            assert rename.status in {302, 303}
            assert services.repo.get_user_passkey_credential_by_id(credential.id).label == (
                "Renamed key"
            )

            remove = await client.post(
                "/identity",
                body=urlencode(
                    {
                        "intent": "remove_passkey",
                        "passkey_id": str(credential.id),
                    }
                ).encode(),
                headers=_FORM,
            )
            assert remove.status in {302, 303}
            assert services.repo.list_user_passkey_credentials(user_id) == []

    asyncio.run(run())


# ---------------------------------------------------------------------------
# Sign-in flow (#247)
# ---------------------------------------------------------------------------


def test_passkey_login_establishes_the_password_login_session_path(monkeypatch) -> None:
    async def run() -> None:
        patch_fixed_ceremony(monkeypatch)
        _use_test_passkey_config(monkeypatch)
        services = create_services(path=":memory:")
        user_id = services.viewer().membership.user_id
        _seed_login_credential(services.repo, user_id)
        app = create_app(debug=False, services=services)

        async with TestClient(app) as client:
            login_page = await client.get("/login")
            assert 'id="passkey-login"' in login_page.text
            assert "elbysodic-passkeys.js" in login_page.text
            assert 'data-chirp="passkeys"' in login_page.text

            begin = await client.post("/login/passkeys/begin")
            assert begin.status == 200
            assert begin.json["challenge"]
            finish = await client.post(
                "/login/passkeys/finish",
                json={**AUTH_CREDENTIAL, "next": "/my/threads"},
                headers={"Cookie": _cookie_header(_cookie_values(begin))},
            )

        assert finish.status == 200
        assert finish.json == {"ok": True, "redirect": "/my/threads"}
        cookies = _cookie_values(finish)
        assert SESSION_COOKIE in cookies
        assert "elbysodic_dev_identity" in cookies

        signed_in_user = user_for_session_token(services.repo, cookies[SESSION_COOKIE])
        assert signed_in_user is not None
        assert signed_in_user.id == user_id

        updated = services.repo.get_user_passkey_credential(AUTH_CREDENTIAL_ID_BYTES)
        assert updated.sign_count == AUTH_NEW_SIGN_COUNT
        assert updated.last_used_at is not None

    asyncio.run(run())


def test_passkey_login_rejects_unknown_and_malformed_credentials(monkeypatch) -> None:
    async def run() -> None:
        patch_fixed_ceremony(monkeypatch)
        _use_test_passkey_config(monkeypatch)
        services = create_services(path=":memory:")
        app = create_app(debug=False, services=services)

        async with TestClient(app) as client:
            begin = await client.post("/login/passkeys/begin")
            cookie = {"Cookie": _cookie_header(_cookie_values(begin))}
            unknown = await client.post(
                "/login/passkeys/finish",
                json=dict(AUTH_CREDENTIAL),
                headers=cookie,
            )
            missing_id = await client.post("/login/passkeys/finish", json={}, headers=cookie)
            bad_encoding = await client.post(
                "/login/passkeys/finish",
                json={"id": "@@not-base64url@@"},
                headers=cookie,
            )

        for response in (unknown, missing_id, bad_encoding):
            assert response.status == 422
            assert response.json["ok"] is False
            assert SESSION_COOKIE not in _cookie_values(response)
        # Unknown and undecodable ids fail identically — no credential oracle.
        assert unknown.json["error"] == bad_encoding.json["error"]

    asyncio.run(run())


def test_passkey_login_rejects_wrong_origin_assertions(monkeypatch) -> None:
    async def run() -> None:
        patch_fixed_ceremony(monkeypatch)
        _use_test_passkey_config(monkeypatch, WRONG_ORIGIN_PASSKEY_CONFIG)
        services = create_services(path=":memory:")
        user_id = services.viewer().membership.user_id
        _seed_login_credential(services.repo, user_id)
        app = create_app(debug=False, services=services)

        async with TestClient(app) as client:
            begin = await client.post("/login/passkeys/begin")
            finish = await client.post(
                "/login/passkeys/finish",
                json=dict(AUTH_CREDENTIAL),
                headers={"Cookie": _cookie_header(_cookie_values(begin))},
            )

        assert finish.status == 422
        assert SESSION_COOKIE not in _cookie_values(finish)
        unchanged = services.repo.get_user_passkey_credential(AUTH_CREDENTIAL_ID_BYTES)
        assert unchanged.sign_count == AUTH_STORED_SIGN_COUNT
        assert unchanged.last_used_at is None

    asyncio.run(run())


def test_passkey_login_fails_closed_on_sign_count_regression(monkeypatch) -> None:
    async def run() -> None:
        patch_fixed_ceremony(monkeypatch)
        _use_test_passkey_config(monkeypatch)
        services = create_services(path=":memory:")
        user_id = services.viewer().membership.user_id
        # Stored counter is already at the assertion's counter value: a cloned
        # (or replayed) authenticator response.
        _seed_login_credential(services.repo, user_id, sign_count=AUTH_NEW_SIGN_COUNT)
        app = create_app(debug=False, services=services)

        async with TestClient(app) as client:
            begin = await client.post("/login/passkeys/begin")
            finish = await client.post(
                "/login/passkeys/finish",
                json=dict(AUTH_CREDENTIAL),
                headers={"Cookie": _cookie_header(_cookie_values(begin))},
            )

        assert finish.status == 422
        assert SESSION_COOKIE not in _cookie_values(finish)
        stored = services.repo.get_user_passkey_credential(AUTH_CREDENTIAL_ID_BYTES)
        assert stored.sign_count == AUTH_NEW_SIGN_COUNT
        assert stored.last_used_at is None

    asyncio.run(run())


def test_passkey_login_challenge_is_single_use(monkeypatch) -> None:
    async def run() -> None:
        patch_fixed_ceremony(monkeypatch)
        _use_test_passkey_config(monkeypatch)
        services = create_services(path=":memory:")
        user_id = services.viewer().membership.user_id
        _seed_login_credential(services.repo, user_id)
        app = create_app(debug=False, services=services)

        async with TestClient(app) as client:
            # Finishing without a begin (no session challenge) fails closed.
            cold = await client.post("/login/passkeys/finish", json=dict(AUTH_CREDENTIAL))
            assert cold.status == 422

            begin = await client.post("/login/passkeys/begin")
            cookie = {"Cookie": _cookie_header(_cookie_values(begin))}
            first = await client.post(
                "/login/passkeys/finish",
                json=dict(AUTH_CREDENTIAL),
                headers=cookie,
            )
            assert first.status == 200

            # Replaying the same assertion (even with the old challenge cookie)
            # is rejected: the persisted sign count already advanced.
            replay = await client.post(
                "/login/passkeys/finish",
                json=dict(AUTH_CREDENTIAL),
                headers=cookie,
            )
            assert replay.status == 422
            assert SESSION_COOKIE not in _cookie_values(replay)

    asyncio.run(run())


def test_passkey_login_sanitizes_the_next_destination(monkeypatch) -> None:
    async def run() -> None:
        patch_fixed_ceremony(monkeypatch)
        _use_test_passkey_config(monkeypatch)
        services = create_services(path=":memory:")
        user_id = services.viewer().membership.user_id
        _seed_login_credential(services.repo, user_id)
        app = create_app(debug=False, services=services)

        async with TestClient(app) as client:
            begin = await client.post("/login/passkeys/begin")
            finish = await client.post(
                "/login/passkeys/finish",
                json={**AUTH_CREDENTIAL, "next": "https://evil.example/steal"},
                headers={"Cookie": _cookie_header(_cookie_values(begin))},
            )

        assert finish.status == 200
        assert finish.json["redirect"] == "/"

    asyncio.run(run())


# ---------------------------------------------------------------------------
# Production posture (#247)
# ---------------------------------------------------------------------------


def _set_production_env(monkeypatch) -> None:
    monkeypatch.setenv("ELBYSODIC_ENV", "production")
    monkeypatch.setenv("ELBYSODIC_SECRET_KEY", "x" * 32)
    monkeypatch.setenv("ELBYSODIC_ALLOWED_HOSTS", "*")
    monkeypatch.setenv("ELBYSODIC_DEMO_MODE", "1")


def test_production_passkey_login_is_public_and_shares_cookie_posture(monkeypatch) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch)
        patch_fixed_ceremony(monkeypatch)
        _use_test_passkey_config(monkeypatch)
        services = create_services(path=":memory:")
        user_id = services.viewer().membership.user_id
        _seed_login_credential(services.repo, user_id)
        app = create_app(debug=False, services=services)

        async with TestClient(app) as client:
            login_page = await client.get("/login")
            csrf = _CSRF_RE.search(login_page.text)
            assert csrf is not None
            cookies = _cookie_values(login_page)
            begin = await client.post(
                "/login/passkeys/begin",
                headers={
                    "Cookie": _cookie_header(cookies),
                    "X-CSRF-Token": csrf.group(1),
                },
            )
            assert begin.status == 200
            cookies.update(_cookie_values(begin))
            finish = await client.post(
                "/login/passkeys/finish",
                json={**AUTH_CREDENTIAL, "next": "/my/threads"},
                headers={
                    "Cookie": _cookie_header(cookies),
                    "X-CSRF-Token": csrf.group(1),
                },
            )

        assert finish.status == 200
        set_cookie = _set_cookie_lines(finish)
        assert "elbysodic_session=" in set_cookie
        assert "elbysodic_dev_identity=" not in set_cookie
        assert "Secure" in set_cookie
        assert "HttpOnly" in set_cookie
        assert "SameSite=lax" in set_cookie

    asyncio.run(run())


def test_production_auth_rate_limit_covers_passkey_endpoints(monkeypatch) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch)
        app = create_app(debug=False, services=create_services(path=":memory:"))

        async with TestClient(app) as client:
            responses = [
                await client.post("/login/passkeys/begin", body=b"") for _attempt in range(11)
            ]

        # CSRF rejects the unauthenticated posts (403) until the auth limiter
        # trips (429) — the same budget password login shares.
        assert [response.status for response in responses[:10]] == [403] * 10
        assert responses[10].status == 429

    asyncio.run(run())


def test_production_password_fallback_is_unchanged_by_passkey_wiring(monkeypatch) -> None:
    async def run() -> None:
        _set_production_env(monkeypatch)
        app = create_app(debug=False, services=create_services(path=":memory:"))

        async with TestClient(app) as client:
            page = await client.get("/login")
            csrf = _CSRF_RE.search(page.text)
            assert csrf is not None
            response = await client.post(
                "/login",
                body=urlencode(
                    {
                        "email": "moira@example.com",
                        "password": "password",
                        "next": "/studio",
                        "_csrf_token": csrf.group(1),
                    }
                ).encode(),
                headers={**_FORM, "Cookie": _cookie_header(_cookie_values(page))},
            )

        assert response.status == 302
        assert "elbysodic_session=" in _set_cookie_lines(response)

    asyncio.run(run())
