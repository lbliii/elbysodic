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
    services = get_services(request)
    viewer = services.viewer()
    active_filter = _parse_filter(request.query.get("filter", "all"))
    board_page = services.board_page(board_slug, filter_by=active_filter)
    return Page.mounted(
        "boards/{board_slug}/page.html",
        current_path=request.url,
        current_board_section=board_page.board.sidebar_section,
        viewer=viewer,
        board=board_page.board,
        board_summary=board_page.summary,
        parent_board=board_page.parent_board,
        is_location_board=board_page.is_location_board,
        is_community_board=board_page.is_community_board,
        board_facets=board_page.board_facets,
        subboards=board_page.subboards,
        sibling_boards=board_page.sibling_boards,
        current_event=board_page.current_event,
        threads=board_page.threads,
        direct_thread_count=board_page.direct_thread_count,
        active_filter=active_filter,
        filter_options=_filter_options(board_page.board.slug, active_filter),
        next_unread_thread=board_page.next_unread_thread,
        can_start_thread=board_page.can_start_thread,
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
