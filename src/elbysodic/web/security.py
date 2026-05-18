"""Security configuration helpers for the Elbysodic web app."""

from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import quote

from chirp.http.cookies import SetCookie
from chirp.http.request import Request
from chirp.http.response import Response
from chirp.middleware.protocol import AnyResponse, Next

from elbysodic.services.auth import SESSION_COOKIE, user_for_session_token
from elbysodic.web.errors import error_response

ELBYSODIC_ENV = "ELBYSODIC_ENV"
ELBYSODIC_SECRET_KEY = "ELBYSODIC_SECRET_KEY"  # noqa: S105
ELBYSODIC_ALLOWED_HOSTS = "ELBYSODIC_ALLOWED_HOSTS"
ELBYSODIC_HSTS = "ELBYSODIC_HSTS"
MIN_SECRET_KEY_LENGTH = 32
PRODUCTION_ENVS = frozenset({"production", "prod", "staging"})
DEFAULT_PRODUCTION_ALLOWED_HOSTS = (".up.railway.app", ".railway.app")
PUBLIC_PATHS = frozenset(
    {"/", "/health", "/login", "/logout", "/network", "/request-access", "/search"}
)
PUBLIC_PREFIXES = ("/elbysodic-static/", "/invite/")
PUBLIC_TENANT_GET_PATHS = frozenset({"/", "/request-access", "/search", "/world", "/wanted"})
PUBLIC_TENANT_GET_PREFIXES = ("/world/", "/wanted/")
PRODUCTION_CONTENT_SECURITY_POLICY = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://unpkg.com https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; "
    "connect-src 'self'; "
    "base-uri 'self'; "
    "frame-ancestors 'none'; "
    "object-src 'none'"
)


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


class RequireLoginMiddleware:
    """Require a valid app session for normal production routes."""

    __slots__ = ("_security",)

    def __init__(self, security: WebSecurityConfig) -> None:
        self._security = security

    async def __call__(self, request: Request, call_next: Next) -> AnyResponse:
        if not self._security.production or _is_public_request(request):
            return await call_next(request)

        if _session_is_valid(request):
            return await call_next(request)

        if request.method in {"GET", "HEAD"}:
            next_url = request.path
            raw_query = getattr(request.query, "_raw", b"")
            if isinstance(raw_query, bytes) and raw_query:
                next_url = f"{next_url}?{raw_query.decode('latin-1')}"
            location = f"/login?next={quote(next_url, safe='/')}"
            return Response("", status=302, headers=(("Location", location),))
        return error_response(request, status=403, detail="Login required")


class IdentityFailureMiddleware:
    """Render controlled auth/identity failures raised during page work."""

    __slots__ = ()

    async def __call__(self, request: Request, call_next: Next) -> AnyResponse:
        try:
            return await call_next(request)
        except PermissionError as exc:
            return error_response(request, status=403, detail=str(exc))


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


def _is_public_request(request: Request) -> bool:
    from elbysodic.web.tenant import request_tenant_slug, split_tenant_path

    tenant_local_path = request.path if request_tenant_slug(request) is not None else None
    split = split_tenant_path(request.path)
    if split is not None:
        _community_slug, tenant_local_path = split
    if tenant_local_path is not None:
        return request.method in {"GET", "HEAD"} and (
            tenant_local_path in PUBLIC_TENANT_GET_PATHS
            or any(tenant_local_path.startswith(prefix) for prefix in PUBLIC_TENANT_GET_PREFIXES)
        )
    return request.path in PUBLIC_PATHS or any(
        request.path.startswith(prefix) for prefix in PUBLIC_PREFIXES
    )


def _session_is_valid(request: Request) -> bool:
    from elbysodic.web.state import get_services

    token = request.cookies.get(SESSION_COOKIE)
    if token is None:
        return False
    return user_for_session_token(get_services().repo, str(token)) is not None
