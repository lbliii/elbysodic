"""Writer obligation dashboard."""

from __future__ import annotations

from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.web.state import get_services


def get(request: Request) -> Page:
    services = get_services()
    return Page(
        "my/threads/page.html",
        "page_content",
        page_block_name="page_root",
        current_path=request.url,
        viewer=services.viewer(),
        dashboard=services.my_threads(character_slug=_selected_character_slug(request)),
    )


def _selected_character_slug(request: Request) -> str | None:
    value = str(request.query.get("character") or "").strip()
    return value or None
