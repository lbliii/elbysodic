"""Character application review room."""

from __future__ import annotations

from dataclasses import dataclass

from chirp.contracts import FormContract, contract
from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.http.response import Redirect
from chirp.templating.returns import Page

from elbysodic.web.recovery import recover_missing_route
from elbysodic.web.state import get_services


@dataclass(frozen=True, slots=True)
class ApplicationRoomForm:
    intent: str
    summary: str = ""
    body: str = ""
    revision_notes: str = ""
    staff_notes: str = ""
    checklist: str = ""


def get(request: Request, character_slug: str) -> Page:
    return _render_application_room(request, character_slug)


@contract(form=FormContract(ApplicationRoomForm, "applications/{character_slug}/page.html"))
async def post(request: Request, character_slug: str) -> Page | Redirect:
    form = await request.form()
    services = get_services(request)
    intent = str(form.get("intent") or "")
    try:
        if intent == "save_application":
            services.update_application_draft(
                character_slug,
                summary=str(form.get("summary") or ""),
                body=str(form.get("body") or ""),
            )
        elif intent == "submit_application":
            services.submit_character_application(character_slug)
        elif intent == "save_review":
            services.update_application_review(
                character_slug,
                revision_notes=str(form.get("revision_notes") or ""),
                staff_notes=str(form.get("staff_notes") or ""),
                checklist=str(form.get("checklist") or ""),
            )
        elif intent == "accept_application":
            services.accept_character_application(character_slug)
        elif intent == "request_revision":
            services.request_character_application_revision(
                character_slug,
                note=str(form.get("revision_notes") or ""),
            )
        else:
            raise HTTPError(status=400, detail=f"unknown application room action: {intent}")
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPError(status=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPError(status=400, detail=str(exc)) from exc
    return Redirect(f"/applications/{character_slug}")


def _render_application_room(request: Request, character_slug: str) -> Page:
    services = get_services(request)
    try:
        room = services.read_application_review_room(character_slug)
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc
    except LookupError:
        return recover_missing_route(request, kind="application", slug=character_slug)
    return Page(
        "applications/{character_slug}/page.html",
        "page_content",
        page_block_name="page_root",
        current_path=request.url,
        viewer=services.viewer(),
        room=room,
    )
