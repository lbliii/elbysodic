"""Character application desk."""

from __future__ import annotations

from dataclasses import dataclass

from chirp.contracts import FormContract, contract
from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.http.response import Redirect
from chirp.templating.returns import Page

from elbysodic.web.state import get_services


@dataclass(frozen=True, slots=True)
class ApplicationActionForm:
    intent: str
    character_slug: str


def get(request: Request) -> Page:
    return _render_applications(request)


@contract(form=FormContract(ApplicationActionForm, "applications/page.html"))
async def post(request: Request) -> Page | Redirect:
    form = await request.form()
    services = get_services(request)
    intent = str(form.get("intent") or "")
    character_slug = str(form.get("character_slug") or "")
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
            services.request_character_application_revision(
                character_slug,
                note=str(form.get("revision_note") or ""),
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
    return Page.mounted(
        "applications/page.html",
        current_path=request.url,
        viewer=services.viewer(),
        desk=services.applications_desk(),
    )
