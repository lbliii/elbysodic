"""Community member directory."""

from __future__ import annotations

from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.web.state import get_services


def get(request: Request) -> Page:
    services = get_services(request)
    return Page.mounted(
        "members/page.html",
        current_path=request.url,
        viewer=services.viewer(),
        directory=services.members_directory(),
    )
