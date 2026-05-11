"""Character application desk."""

from __future__ import annotations

from dataclasses import dataclass

from chirp.contracts import FormContract, contract
from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.http.response import Redirect
from chirp.templating.returns import Page

from elbysodic.services import AppServices
from elbysodic.services.read_models import ApplicationCharacterView
from elbysodic.web.state import get_services


@dataclass(frozen=True, slots=True)
class ApplicationActionForm:
    intent: str
    character_slug: str


def get(request: Request) -> Page:
    return _render_applications(request)


@contract(form=FormContract(ApplicationActionForm, "applications/page.html"))
async def post(
    request: Request, form: ApplicationActionForm, services: AppServices
) -> Page | Redirect:
    intent = form.intent
    character_slug = form.character_slug
    if intent not in {
        "submit_application",
        "accept_application",
        "request_revision",
    }:
        raise HTTPError(status=400, detail=f"unknown application action: {intent}")
    try:
        if intent == "submit_application":
            services.submit_character_application(character_slug)
        elif intent == "accept_application":
            services.accept_character_application(character_slug)
        else:
            raw_form = await request.form()
            services.request_character_application_revision(
                character_slug,
                note=str(raw_form.get("revision_note") or ""),
            )
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPError(status=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPError(status=400, detail=str(exc)) from exc
    return Redirect("/applications")


def _render_applications(request: Request) -> Page:
    services = get_services(request)
    desk = services.applications_desk()
    return Page.mounted(
        "applications/page.html",
        current_path=request.url,
        viewer=services.viewer(),
        desk=desk,
        active_my_applications=_active_application_items(desk.my_applications),
    )


def _active_application_items(
    items: list[ApplicationCharacterView],
) -> list[ApplicationCharacterView]:
    return [
        item
        for item in items
        if item.character.application_status in {"draft", "submitted", "revision_requested"}
    ]
