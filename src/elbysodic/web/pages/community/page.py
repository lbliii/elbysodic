"""Focused community table landing page."""

from __future__ import annotations

from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.domain.boards import is_community_board
from elbysodic.web.state import get_services


def get(request: Request) -> Page:
    services = get_services()
    viewer = services.viewer()
    boards = services.list_boards()
    return Page(
        "community/page.html",
        "page_content",
        page_block_name="page_root",
        current_path=request.url,
        viewer=viewer,
        boards=boards,
        community_boards=[
            summary
            for summary in boards
            if summary.board.parent_board_id is None and is_community_board(summary.board)
        ],
        activity=services.recent_activity(limit=5),
    )
