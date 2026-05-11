"""Focused playable-location landing page."""

from __future__ import annotations

from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.domain.boards import is_location_board
from elbysodic.services import AppServices


def get(request: Request, services: AppServices) -> Page:
    viewer = services.viewer()
    boards = services.list_boards()
    return Page.mounted(
        "locations/page.html",
        current_path=request.url,
        viewer=viewer,
        boards=boards,
        location_boards=[
            summary
            for summary in boards
            if summary.board.parent_board_id is None and is_location_board(summary.board)
        ],
        attention=services.needs_attention(limit=3),
    )
