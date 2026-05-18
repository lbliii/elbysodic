"""Invite acceptance for writer onboarding."""

from __future__ import annotations

from dataclasses import dataclass

from chirp.contracts import FormContract, contract
from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.http.response import Response
from chirp.templating.returns import Page

from elbysodic.services.auth import SESSION_COOKIE
from elbysodic.web.security import session_cookie
from elbysodic.web.state import get_services, get_web_security_config


@dataclass(frozen=True, slots=True)
class InviteAcceptanceForm:
    username: str = ""
    display_name: str = ""
    password: str = ""
    first_face_name: str = ""


def get(request: Request, invite_token: str) -> Page:
    return _render_invite(request, invite_token)


@contract(form=FormContract(InviteAcceptanceForm, "invite/{invite_token}/page.html"))
async def post(
    request: Request,
    invite_token: str,
    form: InviteAcceptanceForm,
) -> Page | Response:
    services = get_services()
    try:
        accepted = services.accept_invitation(
            invite_token,
            password=form.password,
            username=form.username,
            display_name=form.display_name,
            first_face_name=form.first_face_name,
        )
    except LookupError as exc:
        raise HTTPError(status=404, detail=str(exc)) from exc
    except PermissionError as exc:
        return _render_invite(request, invite_token, error=str(exc), form=form)
    except ValueError as exc:
        return _render_invite(request, invite_token, error=str(exc), form=form)
    security = get_web_security_config()
    return Response(
        "",
        status=302,
        headers=(("Location", accepted.next_path),),
        cookies=(
            session_cookie(
                SESSION_COOKIE,
                accepted.session.token,
                max_age=60 * 60 * 24 * 30,
                security=security,
            ),
        ),
    )


def _render_invite(
    request: Request,
    invite_token: str,
    *,
    error: str | None = None,
    form: InviteAcceptanceForm | None = None,
) -> Page:
    services = get_services()
    try:
        invitation, community = services.read_invitation(invite_token)
    except LookupError as exc:
        raise HTTPError(status=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc
    return Page.mounted(
        "invite/{invite_token}/page.html",
        current_path=request.url,
        page_title=f"Accept invitation · {community.name}",
        viewer=None,
        invitation=invitation,
        community=community,
        form=form or InviteAcceptanceForm(),
        error=error,
        show_community_shell=False,
    )
