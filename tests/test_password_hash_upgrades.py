from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier, Lock

import pytest
from chirp.security import passwords as chirp_passwords

from elbysodic.domain.models import User, UserSession
from elbysodic.services import auth
from elbysodic.services.auth import (
    _hash_legacy_pbkdf2,
    create_login_session,
    hash_password,
    verify_password,
)
from elbysodic.services.forum import create_services

PASSWORD = "-".join(("writer", "password"))
EMAIL = "writer@example.com"
DEMO_HASH = "-".join(("dev", "password", "hash"))


class RecordingAuthRepository:
    def __init__(
        self,
        password_hash: str,
        *,
        login_barrier: Barrier | None = None,
        concurrent_replacement: str | None = None,
    ) -> None:
        self.user = User(1, EMAIL, password_hash, "2026-07-20T00:00:00+00:00")
        self.login_barrier = login_barrier
        self.concurrent_replacement = concurrent_replacement
        self.update_attempts = 0
        self.update_results: list[bool] = []
        self.sessions: dict[int, UserSession] = {}
        self._lock = Lock()

    def get_user_by_email(self, email: str) -> User:
        if email != EMAIL:
            raise LookupError(email)
        with self._lock:
            user = self.user
        if self.login_barrier is not None:
            self.login_barrier.wait(timeout=10)
        return user

    def get_user(self, user_id: int) -> User:
        if user_id != self.user.id:
            raise LookupError(user_id)
        with self._lock:
            return self.user

    def update_user_password_hash(
        self,
        user_id: int,
        *,
        expected_hash: str,
        new_hash: str,
    ) -> bool:
        with self._lock:
            self.update_attempts += 1
            if self.concurrent_replacement is not None:
                self.user = replace(self.user, password_hash=self.concurrent_replacement)
                self.concurrent_replacement = None
            updated = user_id == self.user.id and self.user.password_hash == expected_hash
            if updated:
                self.user = replace(self.user, password_hash=new_hash)
            self.update_results.append(updated)
            return updated

    def create_user_session(
        self,
        user_id: int,
        token_hash: str,
        *,
        expires_at: str | None = None,
    ) -> UserSession:
        with self._lock:
            session_id = len(self.sessions) + 1
            session = UserSession(
                session_id,
                user_id,
                token_hash,
                None,
                None,
                "2026-07-20T00:00:00+00:00",
                "2026-07-20T00:00:00+00:00",
                expires_at,
                None,
            )
            self.sessions[session_id] = session
            return session

    def update_user_session_identity(
        self,
        session_id: int,
        *,
        community_id: int,
        membership_id: int,
    ) -> UserSession:
        with self._lock:
            session = replace(
                self.sessions[session_id],
                selected_community_id=community_id,
                selected_membership_id=membership_id,
            )
            self.sessions[session_id] = session
            return session

    def get_user_session_by_token_hash(self, token_hash: str) -> UserSession:
        with self._lock:
            return next(
                session for session in self.sessions.values() if session.token_hash == token_hash
            )

    def touch_user_session(self, session_id: int) -> UserSession:
        return self.sessions[session_id]

    def revoke_user_session_by_token_hash(self, token_hash: str) -> None:
        with self._lock:
            session = next(
                session for session in self.sessions.values() if session.token_hash == token_hash
            )
            self.sessions[session.id] = replace(
                session,
                selected_community_id=None,
                selected_membership_id=None,
                revoked_at="2026-07-20T00:00:01+00:00",
            )


def test_new_real_passwords_use_argon2id() -> None:
    password_hash = hash_password(PASSWORD)

    assert password_hash.startswith("$argon2id$")
    assert verify_password(PASSWORD, password_hash) is True
    assert verify_password("wrong-password", password_hash) is False


def test_new_real_passwords_fail_closed_without_argon2id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(auth, "_hash_current_password", lambda _password: "$scrypt$fixture")

    with pytest.raises(RuntimeError, match="argon2id password hashing is unavailable"):
        hash_password(PASSWORD)


def test_successful_legacy_pbkdf2_login_upgrades_exactly_once() -> None:
    legacy_hash = _hash_legacy_pbkdf2(PASSWORD, salt="stable-legacy-fixture")
    repo = RecordingAuthRepository(legacy_hash)

    first = create_login_session(repo, EMAIL, PASSWORD)
    upgraded_hash = repo.user.password_hash
    second = create_login_session(repo, EMAIL, PASSWORD)

    assert legacy_hash.startswith("pbkdf2_sha256$")
    assert upgraded_hash.startswith("$argon2id$")
    assert first.user.password_hash == upgraded_hash
    assert second.user.password_hash == upgraded_hash
    assert repo.update_attempts == 1


def test_successful_scrypt_login_upgrades_to_argon2id() -> None:
    legacy_hash = chirp_passwords._hash_scrypt(PASSWORD)
    repo = RecordingAuthRepository(legacy_hash)

    session = create_login_session(repo, EMAIL, PASSWORD)

    assert legacy_hash.startswith("$scrypt$")
    assert repo.user.password_hash.startswith("$argon2id$")
    assert session.user.password_hash == repo.user.password_hash
    assert repo.update_attempts == 1


def test_failed_legacy_login_never_writes_or_creates_a_session() -> None:
    legacy_hash = _hash_legacy_pbkdf2(PASSWORD, salt="failed-login-fixture")
    repo = RecordingAuthRepository(legacy_hash)

    with pytest.raises(PermissionError, match="email or password is incorrect"):
        create_login_session(repo, EMAIL, "wrong-password")

    assert repo.user.password_hash == legacy_hash
    assert repo.update_attempts == 0
    assert repo.sessions == {}


def test_current_argon2id_login_does_not_rewrite_the_hash() -> None:
    current_hash = hash_password(PASSWORD)
    repo = RecordingAuthRepository(current_hash)

    session = create_login_session(repo, EMAIL, PASSWORD)

    assert session.user.password_hash == current_hash
    assert repo.user.password_hash == current_hash
    assert repo.update_attempts == 0


def test_demo_seed_hash_remains_environment_gated_and_is_never_upgraded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ELBYSODIC_ENV", "staging")
    monkeypatch.delenv("ELBYSODIC_DEMO_MODE", raising=False)
    disabled_repo = RecordingAuthRepository(DEMO_HASH)

    with pytest.raises(PermissionError, match="email or password is incorrect"):
        create_login_session(disabled_repo, EMAIL, "password")

    monkeypatch.setenv("ELBYSODIC_DEMO_MODE", "1")
    enabled_repo = RecordingAuthRepository(DEMO_HASH)
    session = create_login_session(enabled_repo, EMAIL, "password")

    assert session.user.password_hash == DEMO_HASH
    assert enabled_repo.user.password_hash == DEMO_HASH
    assert enabled_repo.update_attempts == 0


def test_concurrent_successful_legacy_logins_compare_and_swap_safely() -> None:
    legacy_hash = _hash_legacy_pbkdf2(PASSWORD, salt="concurrent-login-fixture")
    repo = RecordingAuthRepository(legacy_hash, login_barrier=Barrier(2))

    with ThreadPoolExecutor(max_workers=2) as executor:
        sessions = list(
            executor.map(
                lambda _index: create_login_session(repo, EMAIL, PASSWORD),
                range(2),
            )
        )

    assert repo.user.password_hash.startswith("$argon2id$")
    assert repo.update_attempts == 2
    assert sorted(repo.update_results) == [False, True]
    assert len(sessions) == 2
    assert all(session.user.password_hash == repo.user.password_hash for session in sessions)


def test_concurrent_unrelated_password_change_fails_closed() -> None:
    legacy_hash = _hash_legacy_pbkdf2(PASSWORD, salt="concurrent-reset-fixture")
    reset_hash = hash_password("new-" + PASSWORD)
    repo = RecordingAuthRepository(legacy_hash, concurrent_replacement=reset_hash)

    with pytest.raises(PermissionError, match="email or password is incorrect"):
        create_login_session(repo, EMAIL, PASSWORD)

    assert repo.user.password_hash == reset_hash
    assert repo.update_results == [False]
    assert repo.sessions == {}


def test_repository_password_hash_update_is_compare_and_swap() -> None:
    services = create_services(path=":memory:", seed_demo=False)
    repo = services.repo
    old_hash = "old-" + "hash"
    first_replacement = "first-" + "replacement"
    stale_replacement = "stale-" + "replacement"
    user = repo.create_user(EMAIL, old_hash)

    assert repo.update_user_password_hash(
        user.id,
        expected_hash=old_hash,
        new_hash=first_replacement,
    )
    assert not repo.update_user_password_hash(
        user.id,
        expected_hash=old_hash,
        new_hash=stale_replacement,
    )
    assert repo.get_user(user.id).password_hash == first_replacement
