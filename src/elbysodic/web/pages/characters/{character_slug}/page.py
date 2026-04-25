"""Character profile for the active community roster."""

from __future__ import annotations

from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.web.state import get_services


def get(request: Request, character_slug: str) -> Page:
    services = get_services()
    viewer = services.viewer()
    profile = services.read_character(character_slug)
    return Page(
        "characters/{character_slug}/page.html",
        "page_content",
        page_block_name="page_root",
        current_path=request.url,
        viewer=viewer,
        profile=profile,
    )
