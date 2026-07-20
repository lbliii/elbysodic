"""Local logout route."""

from __future__ import annotations

from chirp.http.request import Request
from chirp.http.response import Response

from elbysodic.services.access import DEV_IDENTITY_COOKIE
from elbysodic.services.auth import SESSION_COOKIE, request_session_token
from elbysodic.web.security import clear_global_account, clear_session_cookie
from elbysodic.web.state import get_services, get_web_security_config


def get(request: Request) -> Response:
    return _logout(request)


async def post(request: Request) -> Response:
    _ = await request.form()
    return _logout(request)


def _logout(request: Request) -> Response:
    services = get_services()
    token = request_session_token(request)
    if token is not None:
        services.logout(token)
    clear_global_account()
    security = get_web_security_config()
    return Response(
        "",
        status=302,
        headers=(("Location", "/login"),),
        cookies=(
            clear_session_cookie(SESSION_COOKIE, security=security),
            clear_session_cookie(DEV_IDENTITY_COOKIE, security=security),
        ),
    )
