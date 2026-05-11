"""Casting desk for wanted hooks, reserves, and claim state."""

from __future__ import annotations

from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.web.state import get_services


def get(request: Request) -> Page:
    services = get_services(request)
    return Page.mounted(
        "casting/page.html",
        current_path=request.url,
        viewer=services.viewer(),
        desk=services.casting_desk(),
    )
