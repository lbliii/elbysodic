"""Small local authentication helpers for seed and browser QA flows."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

from elbysodic.domain.models import User, UserSession

SESSION_COOKIE = "elbysodic_session"
SESSION_TTL = timedelta(days=30)
HASH_SCHEME = "pbkdf2_sha256"
HASH_ITERATIONS = 210_000
SEED_LOGIN_PHRASE = "password"


class AuthRepository(Protocol):
    def get_user_by_email(self, email: str) -> User: ...

    def get_user(self, user_id: int) -> User: ...

    def create_user_session(
        self,
        user_id: int,
        token_hash: str,
        *,
        expires_at: str | None = None,
    ) -> UserSession: ...

    def update_user_session_identity(
        self,
        session_id: int,
        *,
        community_id: int,
        membership_id: int,
    ) -> UserSession: ...

    def get_user_session_by_token_hash(self, token_hash: str) -> UserSession: ...

    def touch_user_session(self, session_id: int) -> UserSession: ...

    def revoke_user_session_by_token_hash(self, token_hash: str) -> None: ...


class SessionLookupRepository(Protocol):
    def get_user(self, user_id: int) -> User: ...

    def get_user_session_by_token_hash(self, token_hash: str) -> UserSession: ...

    def touch_user_session(self, session_id: int) -> UserSession: ...


@dataclass(frozen=True, slots=True)
class LoginSession:
    session_id: int
    user: User
    token: str
    expires_at: str


def hash_password(password: str, *, salt: str | None = None) -> str:
    normalized_salt = salt or secrets.token_urlsafe(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        normalized_salt.encode("utf-8"),
        HASH_ITERATIONS,
    )
    digest = base64.urlsafe_b64encode(derived).decode("ascii").rstrip("=")
    return f"{HASH_SCHEME}${HASH_ITERATIONS}${normalized_salt}${digest}"


def verify_password(password: str, stored_hash: str) -> bool:
    if stored_hash == "dev-password-hash":
        return hmac.compare_digest(password, SEED_LOGIN_PHRASE)
    parts = stored_hash.split("$")
    if len(parts) != 4 or parts[0] != HASH_SCHEME:
        return False
    _scheme, raw_iterations, salt, expected = parts
    try:
        iterations = int(raw_iterations)
    except ValueError:
        return False
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    )
    actual = base64.urlsafe_b64encode(derived).decode("ascii").rstrip("=")
    return hmac.compare_digest(actual, expected)


def create_login_session(repo: AuthRepository, email: str, password: str) -> LoginSession:
    normalized_email = email.strip().lower()
    if not normalized_email or not password:
        raise PermissionError("email and password are required")
    try:
        user = repo.get_user_by_email(normalized_email)
    except LookupError as exc:
        raise PermissionError("email or password is incorrect") from exc
    if not verify_password(password, user.password_hash):
        raise PermissionError("email or password is incorrect")
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(UTC) + SESSION_TTL).isoformat(timespec="seconds")
    stored_session = repo.create_user_session(
        user.id,
        session_token_hash(token),
        expires_at=expires_at,
    )
    return LoginSession(
        session_id=stored_session.id,
        user=user,
        token=token,
        expires_at=expires_at,
    )


def session_token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def user_for_session_token(repo: SessionLookupRepository, token: str) -> User | None:
    session = session_for_session_token(repo, token)
    if session is None:
        return None
    return repo.get_user(session.user_id)


def session_for_session_token(
    repo: SessionLookupRepository,
    token: str,
) -> UserSession | None:
    if not token:
        return None
    try:
        session = repo.get_user_session_by_token_hash(session_token_hash(token))
    except LookupError:
        return None
    if session.revoked_at is not None:
        return None
    if session.expires_at is not None:
        try:
            expires_at = datetime.fromisoformat(session.expires_at)
        except ValueError:
            return None
        if expires_at <= datetime.now(UTC):
            return None
    return repo.touch_user_session(session.id)
