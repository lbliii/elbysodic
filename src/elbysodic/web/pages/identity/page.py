"""Identity settings page and identity-preference intents."""

from __future__ import annotations

from dataclasses import dataclass

from chirp.contracts import FormContract, contract
from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.http.response import Redirect
from chirp.templating.returns import Page

from elbysodic.services import AppServices
from elbysodic.services.access import DEV_IDENTITY_COOKIE, dev_identity_cookie_value
from elbysodic.services.auth import request_session_token
from elbysodic.web.recovery import recover_next_url
from elbysodic.web.security import session_cookie
from elbysodic.web.state import get_services, get_web_security_config


@dataclass(frozen=True, slots=True)
class IdentityForm:
    character_id: str = "0"
    next: str = "/"
    intent: str = "set_default_character"
    membership_id: str = "0"


MAX_PASSKEY_LABEL_LENGTH = 80


def get(request: Request) -> Page:
    services = get_services(request)
    viewer = services.viewer()
    account = services.repo.get_user(viewer.membership.user_id)
    return Page.mounted(
        "identity/page.html",
        current_path=request.url,
        viewer=viewer,
        account_email=account.email,
        passkeys=services.repo.list_user_passkey_credentials(account.id),
    )


@contract(form=FormContract(IdentityForm, "_layout.html", block="topbar_end"))
async def post(request: Request) -> Redirect:
    form = await request.form()
    services = get_services(request)
    next_url = _safe_next(str(form.get("next") or "/"))
    intent = str(form.get("intent") or "set_default_character")
    if intent == "switch_membership":
        membership_id = _form_int(form.get("membership_id"), "membership_id")
        security = get_web_security_config()
        if security.production:
            try:
                identity = services.switch_session_identity(
                    request_session_token(request) or "",
                    membership_id,
                )
            except PermissionError as exc:
                raise HTTPError(status=403, detail=str(exc)) from exc
            next_url = recover_next_url(services.repo, identity, next_url)
            return Redirect(next_url)
        identity = services.switch_dev_identity(membership_id)
        next_url = recover_next_url(services.repo, identity, next_url)
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
    if intent in {"remove_passkey", "rename_passkey"}:
        return _handle_passkey_intent(services, intent, form)
    if intent == "set_default_character":
        character_id = _form_int(form.get("character_id"), "character_id")
        services.set_default_character(character_id)
        return Redirect(next_url)
    return Redirect(next_url)


def _handle_passkey_intent(services: AppServices, intent: str, form: object) -> Redirect:
    viewer = services.viewer()
    getter = getattr(form, "get", None)
    if getter is None:
        raise HTTPError(status=400, detail="malformed form body")
    passkey_id = _form_int(getter("passkey_id"), "passkey_id")
    label_value = str(getter("label") or "").strip()
    try:
        if intent == "remove_passkey":
            services.repo.delete_user_passkey_credential(viewer.membership.user_id, passkey_id)
        else:
            label = label_value[:MAX_PASSKEY_LABEL_LENGTH]
            services.repo.rename_user_passkey_credential(
                viewer.membership.user_id,
                passkey_id,
                label or "Passkey",
            )
    except LookupError as exc:
        raise HTTPError(status=404, detail="passkey not found") from exc
    return Redirect("/identity")


def _safe_next(next_url: str) -> str:
    if not next_url.startswith("/") or next_url.startswith("//"):
        return "/"
    return next_url


def _form_int(value: object, field_name: str) -> int:
    try:
        return int(str(value or "0"))
    except ValueError as exc:
        raise HTTPError(status=400, detail=f"{field_name} must be an integer") from exc
