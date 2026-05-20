"""Director-only access request detail."""

from __future__ import annotations

from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.web.state import get_services


def get(request: Request, request_id: str) -> Page:
    try:
        parsed_request_id = int(request_id)
    except ValueError as exc:
        raise HTTPError(status=404, detail="access request not found") from exc
    services = get_services(request)
    try:
        item = services.access_request_detail(parsed_request_id)
    except LookupError as exc:
        raise HTTPError(status=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc
    return Page.mounted(
        "studio/access-requests/{request_id}/page.html",
        current_path=request.url,
        viewer=services.viewer(),
        item=item,
    )
