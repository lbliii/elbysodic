"""Development-only seed persona switcher."""

from __future__ import annotations

from dataclasses import dataclass

from chirp.contracts import FormContract, contract
from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.http.response import Redirect
from chirp.templating.returns import Page

from elbysodic.services import AppServices
from elbysodic.services.access import DEV_IDENTITY_COOKIE, dev_identity_cookie_value
from elbysodic.web.security import session_cookie
from elbysodic.web.state import dev_tools_enabled, get_services, get_web_security_config


@dataclass(frozen=True, slots=True)
class DevPersonaForm:
    persona_key: str = ""
    next: str = "/dev/personas"


def get(request: Request) -> Page:
    if not dev_tools_enabled():
        raise HTTPError(status=404, detail="dev personas are disabled")
    services = get_services(request)
    return Page.mounted(
        "dev/personas/page.html",
        current_path=request.url,
        viewer=services.viewer(),
        personas=services.dev_personas(),
    )


@contract(form=FormContract(DevPersonaForm, "dev/personas/page.html"))
async def post(form: DevPersonaForm, services: AppServices) -> Redirect:
    if not dev_tools_enabled():
        raise HTTPError(status=404, detail="dev personas are disabled")
    next_url = _safe_next(form.next)
    try:
        identity = services.switch_dev_persona(form.persona_key)
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPError(status=404, detail=str(exc)) from exc
    return Redirect(
        next_url,
        headers=(
            (
                "Set-Cookie",
                session_cookie(
                    DEV_IDENTITY_COOKIE,
                    dev_identity_cookie_value(identity),
                    max_age=60 * 60 * 24 * 30,
                    security=get_web_security_config(),
                ).to_header_value(),
            ),
        ),
    )


def _safe_next(next_url: str) -> str:
    if not next_url.startswith("/") or next_url.startswith("//"):
        return "/dev/personas"
    return next_url
