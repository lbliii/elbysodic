"""Studio network directory."""

from __future__ import annotations

from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.web.state import get_services


def get(request: Request) -> Page:
    services = get_services(request)
    return Page(
        "network/page.html",
        "page_content",
        page_block_name="page_root",
        current_path=request.url,
        viewer=services.viewer(),
        network=services.studio_network(),
        show_community_shell=False,
    )
