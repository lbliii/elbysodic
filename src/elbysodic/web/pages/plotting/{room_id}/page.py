"""Plotting room detail page."""

from __future__ import annotations

from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.web.state import get_services


def get(request: Request, room_id: str) -> Page:
    services = get_services()
    try:
        room = services.read_plotting_room(_parse_room_id(room_id))
    except LookupError as exc:
        raise HTTPError(status=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc
    return Page(
        "plotting/{room_id}/page.html",
        "page_content",
        page_block_name="page_root",
        current_path=request.url,
        viewer=services.viewer(),
        room=room,
    )


def _parse_room_id(value: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise HTTPError(status=404, detail="plotting room not found") from exc
