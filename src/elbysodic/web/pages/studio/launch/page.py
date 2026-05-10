"""Director launch checklist for opening a realm."""

from __future__ import annotations

from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.web.state import get_services


def get(request: Request) -> Page:
    services = get_services(request)
    studio = services.director_studio()
    if not studio.can_manage:
        raise HTTPError(status=403, detail="director access is required")
    return Page(
        "studio/launch/page.html",
        "page_content",
        page_block_name="page_root",
        current_path=request.url,
        viewer=services.viewer(),
        studio=studio,
        launch=studio.launch_readiness,
    )
