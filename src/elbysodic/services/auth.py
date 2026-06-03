"""Small local authentication helpers for seed and browser QA flows."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
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
ENVIRONMENT_ENV = "ELBYSODIC_ENV"
DEMO_MODE_ENV = "ELBYSODIC_DEMO_MODE"
PRODUCTION_ENVS = frozenset({"production", "prod", "staging"})
MIN_PRODUCTION_SECRET_KEY_LENGTH = 32


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


@dataclass(frozen=True, slots=True)
class AuthTrustPosture:
    environment: str
    production: bool
    demo_mode_enabled: bool
    seed_passwords_enabled: bool
    secret_key_configured: bool
    secret_key_meets_minimum: bool
    session_cookie_name: str
    session_ttl_days: int
    development_identity_allowed: bool
    session_required_for_app_routes: bool

    @property
    def warnings(self) -> tuple[str, ...]:
        warnings: list[str] = []
        if self.production and not self.secret_key_meets_minimum:
            warnings.append("production secret key is missing or too short")
        if self.production and self.demo_mode_enabled:
            warnings.append("production demo mode accepts seeded demo passwords")
        if not self.production and self.development_identity_allowed:
            warnings.append("development identity shortcuts are enabled")
        return tuple(warnings)


def auth_trust_posture() -> AuthTrustPosture:
    env = (os.environ.get(ENVIRONMENT_ENV) or "development").strip().lower()
    production = env in PRODUCTION_ENVS
    demo_mode = _truthy_env(os.environ.get(DEMO_MODE_ENV))
    secret_key = (os.environ.get("ELBYSODIC_SECRET_KEY") or "").strip()
    return AuthTrustPosture(
        environment=env,
        production=production,
        demo_mode_enabled=demo_mode,
        seed_passwords_enabled=seed_passwords_enabled(),
        secret_key_configured=bool(secret_key),
        secret_key_meets_minimum=len(secret_key) >= MIN_PRODUCTION_SECRET_KEY_LENGTH,
        session_cookie_name=SESSION_COOKIE,
        session_ttl_days=SESSION_TTL.days,
        development_identity_allowed=not production,
        session_required_for_app_routes=production,
    )


def format_auth_trust_posture(posture: AuthTrustPosture) -> str:
    lines = [
        "auth trust posture",
        f"environment: {posture.environment}",
        f"production: {_yes_no(posture.production)}",
        f"demo_mode_enabled: {_yes_no(posture.demo_mode_enabled)}",
        f"seed_passwords_enabled: {_yes_no(posture.seed_passwords_enabled)}",
        f"secret_key_configured: {_yes_no(posture.secret_key_configured)}",
        f"secret_key_meets_minimum: {_yes_no(posture.secret_key_meets_minimum)}",
        f"session_cookie: {posture.session_cookie_name}",
        f"session_ttl_days: {posture.session_ttl_days}",
        f"development_identity_allowed: {_yes_no(posture.development_identity_allowed)}",
        f"session_required_for_app_routes: {_yes_no(posture.session_required_for_app_routes)}",
    ]
    if posture.warnings:
        lines.append("warnings:")
        lines.extend(f"- {warning}" for warning in posture.warnings)
    return "\n".join(lines) + "\n"


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
        if not seed_passwords_enabled():
            return False
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


def seed_passwords_enabled() -> bool:
    env = (os.environ.get(ENVIRONMENT_ENV) or "development").strip().lower()
    if env not in PRODUCTION_ENVS:
        return True
    return _truthy_env(os.environ.get(DEMO_MODE_ENV))


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


def _truthy_env(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"
