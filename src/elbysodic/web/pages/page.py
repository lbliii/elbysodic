"""Home page for the initial Elbysodic shell."""

from __future__ import annotations

from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.web.state import get_services


def get(request: Request) -> Page:
    services = get_services()
    viewer = services.viewer()
    return Page(
        "page.html",
        "page_content",
        page_block_name="page_root",
        current_path=request.url,
        viewer=viewer,
        boards=services.list_boards(),
        activity=services.recent_activity(),
    )
