"""Community member profile."""

from __future__ import annotations

from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.web.state import get_services


def get(request: Request, username: str) -> Page:
    services = get_services(request)
    try:
        profile = services.read_member(username)
    except LookupError as exc:
        raise HTTPError(status=404, detail=str(exc)) from exc
    return Page(
        "members/{username}/page.html",
        "page_content",
        page_block_name="page_root",
        current_path=request.url,
        viewer=services.viewer(),
        profile=profile,
    )
