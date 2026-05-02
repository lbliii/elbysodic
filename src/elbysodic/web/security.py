"""Security configuration helpers for the Elbysodic web app."""

from __future__ import annotations

import os
from dataclasses import dataclass

from chirp.http.cookies import SetCookie

ELBYSODIC_ENV = "ELBYSODIC_ENV"
ELBYSODIC_SECRET_KEY = "ELBYSODIC_SECRET_KEY"  # noqa: S105
ELBYSODIC_ALLOWED_HOSTS = "ELBYSODIC_ALLOWED_HOSTS"
ELBYSODIC_HSTS = "ELBYSODIC_HSTS"
MIN_SECRET_KEY_LENGTH = 32
PRODUCTION_ENVS = frozenset({"production", "prod", "staging"})
DEFAULT_PRODUCTION_ALLOWED_HOSTS = (".up.railway.app", ".railway.app")


@dataclass(frozen=True, slots=True)
class WebSecurityConfig:
    env: str
    secret_key: str
    allowed_hosts: tuple[str, ...]
    strict_transport_security: str | None
    secure_cookies: bool

    @property
    def production(self) -> bool:
        return self.env in PRODUCTION_ENVS


def resolve_web_security_config(*, debug: bool) -> WebSecurityConfig:
    env = (os.environ.get(ELBYSODIC_ENV) or "development").strip().lower()
    production = env in PRODUCTION_ENVS
    secret_key = (os.environ.get(ELBYSODIC_SECRET_KEY) or "").strip()

    if production and not debug and len(secret_key) < MIN_SECRET_KEY_LENGTH:
        raise RuntimeError(
            f"{ELBYSODIC_SECRET_KEY} must be at least {MIN_SECRET_KEY_LENGTH} characters "
            "when ELBYSODIC_ENV is production or staging."
        )

    allowed_hosts = _parse_allowed_hosts(os.environ.get(ELBYSODIC_ALLOWED_HOSTS))
    if not allowed_hosts:
        allowed_hosts = DEFAULT_PRODUCTION_ALLOWED_HOSTS if production else ("*",)

    return WebSecurityConfig(
        env=env,
        secret_key=secret_key,
        allowed_hosts=allowed_hosts,
        strict_transport_security=_strict_transport_security(),
        secure_cookies=production and not debug,
    )


def session_cookie(
    name: str,
    value: str,
    *,
    max_age: int | None = None,
    security: WebSecurityConfig,
) -> SetCookie:
    return SetCookie(
        name,
        value,
        max_age=max_age,
        path="/",
        secure=security.secure_cookies,
        httponly=True,
        samesite="lax",
    )


def clear_session_cookie(name: str, *, security: WebSecurityConfig) -> SetCookie:
    return session_cookie(name, "", max_age=0, security=security)


def _parse_allowed_hosts(raw: str | None) -> tuple[str, ...]:
    if raw is None:
        return ()
    hosts = tuple(host.strip().lower() for host in raw.replace("\n", ",").split(","))
    return tuple(host for host in hosts if host)


def _strict_transport_security() -> str | None:
    raw = os.environ.get(ELBYSODIC_HSTS)
    if raw is None:
        return None
    normalized = raw.strip()
    if not normalized or normalized.lower() in {"0", "false", "no", "off"}:
        return None
    if normalized.lower() in {"1", "true", "yes", "on"}:
        return "max-age=31536000; includeSubDomains"
    return normalized
