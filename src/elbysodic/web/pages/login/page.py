"""Local login route for seeded browser QA."""

from __future__ import annotations

from dataclasses import dataclass

from chirp.contracts import FormContract, contract
from chirp.http.request import Request
from chirp.http.response import Response
from chirp.templating.returns import Page

from elbysodic.services.access import DEV_IDENTITY_COOKIE, dev_identity_cookie_value
from elbysodic.services.auth import SESSION_COOKIE, seed_passwords_enabled
from elbysodic.web.security import session_cookie
from elbysodic.web.state import get_services, get_web_security_config


@dataclass(frozen=True, slots=True)
class LoginForm:
    email: str = ""
    password: str = ""
    next: str = "/"


def get(request: Request) -> Page:
    return _render_login(request)


@contract(form=FormContract(LoginForm, "login/page.html"))
async def post(request: Request) -> Page | Response:
    form = await request.form()
    next_url = _safe_next(str(form.get("next") or "/"))
    email = str(form.get("email") or "")
    password = str(form.get("password") or "")
    services = get_services()
    try:
        session, identity = services.login(email, password)
    except PermissionError as exc:
        return _render_login(request, email=email, next_url=next_url, error=str(exc))
    security = get_web_security_config()
    cookies = [
        session_cookie(
            SESSION_COOKIE,
            session.token,
            max_age=60 * 60 * 24 * 30,
            security=security,
        )
    ]
    if not security.production:
        cookies.append(
            session_cookie(
                DEV_IDENTITY_COOKIE,
                dev_identity_cookie_value(identity),
                max_age=60 * 60 * 24 * 30,
                security=security,
            )
        )
    return Response(
        "",
        status=302,
        headers=(("Location", next_url),),
        cookies=tuple(cookies),
    )


def _render_login(
    request: Request,
    *,
    email: str = "",
    next_url: str | None = None,
    error: str | None = None,
) -> Page:
    services = get_services()
    return Page(
        "login/page.html",
        "page_content",
        page_block_name="page_root",
        current_path=request.url,
        viewer=None if get_web_security_config().production else services.viewer(),
        email=email,
        next_url=next_url or _safe_next(str(getattr(request, "query", {}).get("next", "/"))),
        error=error,
        seed_passwords_enabled=seed_passwords_enabled(),
        show_community_shell=False,
    )


def _safe_next(next_url: str) -> str:
    if not next_url.startswith("/") or next_url.startswith("//"):
        return "/"
    return next_url
