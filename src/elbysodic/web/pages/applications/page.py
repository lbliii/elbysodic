"""Character application desk."""

from __future__ import annotations

from dataclasses import dataclass

from chirp.contracts import FormContract, contract
from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.services.read_models import ApplicationCharacterView
from elbysodic.web.state import get_services


@dataclass(frozen=True, slots=True)
class ApplicationActionForm:
    _action: str
    character_slug: str


def get(request: Request) -> Page:
    return _render_applications(request)


@contract(form=FormContract(ApplicationActionForm, "applications/page.html"))
async def post(request: Request) -> Page:
    """Register POST; Chirp dispatches submitted ``_action`` values."""
    return _render_applications(request)


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
