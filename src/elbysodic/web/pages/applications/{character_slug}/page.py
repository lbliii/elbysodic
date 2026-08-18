"""Character application review room.

Mutations live in ``_actions.py`` (Chirp page actions, dispatched on the
hidden ``_action`` form field). ``post()`` below is only the no-``_action``
fallback that keeps the POST method registered on this path.
"""

from __future__ import annotations

from dataclasses import dataclass

from chirp.contracts import FormContract, contract
from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.web.recovery import recover_missing_route
from elbysodic.web.state import get_services

APPLICATION_ROOM_TEMPLATE = "applications/{character_slug}/page.html"


@dataclass(frozen=True, slots=True)
class ApplicationRoomForm:
    _action: str
    summary: str = ""
    body: str = ""
    revision_notes: str = ""
    staff_notes: str = ""
    checklist: str = ""


def get(request: Request, character_slug: str) -> Page:
    return _render_application_room(request, character_slug)


@contract(form=FormContract(ApplicationRoomForm, APPLICATION_ROOM_TEMPLATE))
async def post(request: Request, character_slug: str) -> Page:
    """Fallback — mutations dispatch via ``pages/applications/{character_slug}/_actions.py``."""
    return _render_application_room(request, character_slug)


def _render_application_room(request: Request, character_slug: str) -> Page:
    services = get_services(request)
    try:
        room = services.read_application_review_room(character_slug)
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc
    except LookupError:
        return recover_missing_route(request, kind="application", slug=character_slug)
    return Page.mounted(
        APPLICATION_ROOM_TEMPLATE,
        current_path=request.url,
        viewer=services.viewer(),
        room=room,
        accepted_next_move=(
            services.writer_activation()
            if room.character_view.is_owned_by_viewer
            and room.character_view.character.application_status == "accepted"
            else None
        ),
    )
