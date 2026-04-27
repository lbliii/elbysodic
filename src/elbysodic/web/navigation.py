"""Template navigation helpers for route-aware Chirp-UI components."""

from __future__ import annotations

from typing import Any

from elbysodic.domain.models import Board
from elbysodic.services.read_models import ForumView


def location_nav_tree_items(
    viewer: ForumView | None,
    current_board_id: int = 0,
    current_parent_board_id: int = 0,
) -> list[dict[str, Any]]:
    """Build server-opened location branches for the sidebar LocationTree."""

    if viewer is None:
        return []

    items: list[dict[str, Any]] = []
    for group in viewer.location_navigation_groups:
        parent = group.parent.board
        parent_active = current_board_id == parent.id
        branch_open = parent_active or current_parent_board_id == parent.id
        item: dict[str, Any] = _board_nav_item(
            parent,
            group.unread_thread_count,
            active=parent_active,
            opened=branch_open,
        )
        if group.children:
            item["children"] = [
                _board_nav_item(
                    child.board,
                    child.unread_thread_count,
                    active=current_board_id == child.board.id,
                )
                for child in group.children
            ]
        items.append(item)
    return items


def _board_nav_item(
    board: Board,
    unread_thread_count: int,
    *,
    active: bool = False,
    opened: bool = False,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "active": active,
        "href": f"/boards/{board.slug}",
        "open": opened,
        "title": board.name,
    }
    if unread_thread_count:
        item["badge"] = unread_thread_count
    return item
