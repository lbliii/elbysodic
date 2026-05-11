"""World materials hub."""

from __future__ import annotations

from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.services import AppServices


def get(request: Request, services: AppServices) -> Page:
    hub = services.world_hub()
    return Page.mounted(
        "world/page.html",
        current_path=request.url,
        viewer=services.viewer(),
        hub=hub,
        guidebook=hub,
    )
