"""Thread list for a board."""

from __future__ import annotations

from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.web.state import get_services


def get(request: Request, board_slug: str) -> Page:
    services = get_services()
    viewer = services.viewer()
    board, threads = services.board_threads(board_slug)
    return Page(
        "boards/{board_slug}/page.html",
        "page_content",
        page_block_name="page_root",
        current_path=request.url,
        viewer=viewer,
        board=board,
        threads=threads,
        can_start_thread=services.can_start_thread(board),
    )
