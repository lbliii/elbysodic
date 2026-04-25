"""Thread list for a board."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.services.forum import BoardThreadFilter
from elbysodic.web.state import get_services

_FILTERS: tuple[BoardThreadFilter, ...] = (
    "all",
    "unread",
    "attention",
    "mine",
    "pinned",
    "locked",
)


@dataclass(frozen=True, slots=True)
class ThreadFilterOption:
    value: BoardThreadFilter
    label: str
    href: str
    is_active: bool


def get(request: Request, board_slug: str) -> Page:
    services = get_services()
    viewer = services.viewer()
    active_filter = _parse_filter(request.query.get("filter", "all"))
    board, threads = services.board_threads(board_slug, filter_by=active_filter)
    return Page(
        "boards/{board_slug}/page.html",
        "page_content",
        page_block_name="page_root",
        current_path=request.url,
        viewer=viewer,
        board=board,
        board_facets=services.board_facets(board.slug),
        threads=threads,
        active_filter=active_filter,
        filter_options=_filter_options(board.slug, active_filter),
        next_unread_thread=services.next_unread_thread(board.slug),
        can_start_thread=services.can_start_thread(board),
    )


def _parse_filter(raw: object) -> BoardThreadFilter:
    value = str(raw or "all").lower()
    if value in _FILTERS:
        return cast(BoardThreadFilter, value)
    return "all"


def _filter_options(board_slug: str, active_filter: BoardThreadFilter) -> list[ThreadFilterOption]:
    labels = {
        "all": "All",
        "unread": "New replies",
        "attention": "Needs reply",
        "mine": "Mine",
        "pinned": "Pinned",
        "locked": "Locked",
    }
    return [
        ThreadFilterOption(
            value=value,
            label=labels[value],
            href=f"/boards/{board_slug}"
            if value == "all"
            else f"/boards/{board_slug}?filter={value}",
            is_active=value == active_filter,
        )
        for value in _FILTERS
    ]
