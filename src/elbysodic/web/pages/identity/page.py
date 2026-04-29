"""Current-character preference route for the dev viewer."""

from __future__ import annotations

from dataclasses import dataclass

from chirp.contracts import FormContract, contract
from chirp.http.cookies import SetCookie
from chirp.http.request import Request
from chirp.http.response import Redirect

from elbysodic.services.access import DEV_IDENTITY_COOKIE, dev_identity_cookie_value
from elbysodic.web.state import get_services


@dataclass(frozen=True, slots=True)
class IdentityForm:
    character_id: str = "0"
    next: str = "/"
    intent: str = "set_default_character"
    membership_id: str = "0"


@contract(form=FormContract(IdentityForm, "_layout.html"))
async def post(request: Request) -> Redirect:
    form = await request.form()
    services = get_services(request)
    next_url = _safe_next(str(form.get("next") or "/"))
    intent = str(form.get("intent") or "set_default_character")
    if intent == "switch_membership":
        identity = services.switch_dev_identity(int(str(form.get("membership_id") or "0")))
        return Redirect(
            next_url,
            headers=(
                (
                    "Set-Cookie",
                    SetCookie(
                        DEV_IDENTITY_COOKIE,
                        dev_identity_cookie_value(identity),
                        max_age=60 * 60 * 24 * 30,
                    ).to_header_value(),
                ),
            ),
        )
    if intent == "set_default_character":
        character_id = int(str(form.get("character_id") or "0"))
        services.set_default_character(character_id)
        return Redirect(next_url)
    return Redirect(next_url)


def _safe_next(next_url: str) -> str:
    if not next_url.startswith("/") or next_url.startswith("//"):
        return "/"
    return next_url
