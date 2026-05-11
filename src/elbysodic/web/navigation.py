"""Template navigation helpers for route-aware Chirp-UI components."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

from elbysodic.domain.models import Board
from elbysodic.services.read_models import ForumView


def active_route_path(current_path: object) -> str:
    """Return the queryless route path used for shell active-state checks."""

    raw = str(current_path or "/")
    path = urlsplit(raw).path if "://" in raw else raw.split("?", 1)[0].split("#", 1)[0]
    return path or "/"


def shell_route_state(current_path: object, board_section: str = "") -> ShellRouteState:
    return ShellRouteState(
        path=active_route_path(current_path),
        board_section=board_section or "",
    )


def board_section_for_path(viewer: ForumView | None, current_path: object) -> str:
    """Return the configured sidebar section for a direct board route."""

    path = active_route_path(current_path)
    if viewer is None or not path.startswith("/boards/"):
        return ""
    board_slug = path.removeprefix("/boards/").split("/", 1)[0]
    for item in _iter_board_nav_items(viewer):
        if item.board.slug == board_slug:
            return item.board.sidebar_section
    return ""


@dataclass(frozen=True, slots=True)
class ShellRouteState:
    path: str
    board_section: str = ""

    @property
    def active_room(self) -> str:
        if self.network_active:
            return "network"
        if self.is_studio:
            return "studio"
        if self.is_locations:
            return "locations"
        if self.is_wanted:
            return "wanted"
        if self.is_desk:
            return "desk"
        return "home"

    @property
    def active_inner(self) -> str:
        if self.is_locations:
            return "locations"
        if self.is_guidebook:
            return "guidebook"
        if self.community_active:
            return "community"
        if self.is_wanted:
            return "wanted"
        if self.is_desk:
            return "desk"
        if self.is_studio:
            return "studio"
        return "home"

    @property
    def mode(self) -> str:
        """Compatibility alias for existing templates."""

        return self.active_room

    @property
    def home_active(self) -> bool:
        return self.active_room == "home"

    @property
    def world_active(self) -> bool:
        """Compatibility alias for the old `World` primary mode."""

        return self.home_active

    @property
    def locations_room_active(self) -> bool:
        return self.active_room == "locations"

    @property
    def wanted_active(self) -> bool:
        return self.active_room == "wanted"

    @property
    def play_active(self) -> bool:
        """Compatibility alias for the old `Play` primary mode."""

        return self.wanted_active

    @property
    def studio_active(self) -> bool:
        return self.active_room == "studio"

    @property
    def desk_active(self) -> bool:
        return self.active_room == "desk"

    @property
    def network_active(self) -> bool:
        return _path_in(self.path, "/network")

    @property
    def notifications_active(self) -> bool:
        return _path_in(self.path, "/notifications")

    @property
    def dev_personas_active(self) -> bool:
        return _path_in(self.path, "/dev/personas")

    @property
    def login_active(self) -> bool:
        return self.path == "/login"

    @property
    def is_locations(self) -> bool:
        if self.board_section in {"community", "desk", "studio"}:
            return False
        return (
            _path_in(self.path, "/locations")
            or self.path.startswith("/boards/")
            or self.board_section == "locations"
        )

    @property
    def is_wanted(self) -> bool:
        return any(
            _path_in(self.path, prefix)
            for prefix in (
                "/wanted",
                "/claims",
                "/casting",
            )
        )

    @property
    def is_play(self) -> bool:
        """Compatibility alias for the old `Play` route group."""

        return self.is_wanted

    @property
    def is_studio(self) -> bool:
        return _path_in(self.path, "/studio") or self.board_section == "studio"

    @property
    def is_desk(self) -> bool:
        return (
            any(
                _path_in(self.path, prefix)
                for prefix in (
                    "/desk",
                    "/my/threads",
                    "/notifications",
                    "/characters",
                    "/applications",
                    "/interactions",
                    "/plotting",
                    "/discover",
                )
            )
            or self.board_section == "desk"
        )

    @property
    def is_guidebook(self) -> bool:
        return _path_in(self.path, "/world")

    @property
    def locations_active(self) -> bool:
        return self.is_locations

    @property
    def guidebook_active(self) -> bool:
        return self.is_guidebook

    @property
    def community_active(self) -> bool:
        return (
            _path_in(self.path, "/community")
            or _path_in(self.path, "/members")
            or self.board_section == "community"
        )

    @property
    def queue_active(self) -> bool:
        return _path_in(self.path, "/my/threads")

    @property
    def roster_active(self) -> bool:
        return _path_in(self.path, "/characters")

    @property
    def plotting_active(self) -> bool:
        return _path_in(self.path, "/plotting")

    @property
    def applications_active(self) -> bool:
        return _path_in(self.path, "/applications")

    @property
    def interactions_active(self) -> bool:
        return _path_in(self.path, "/interactions")

    @property
    def discovery_active(self) -> bool:
        return _path_in(self.path, "/discover")

    @property
    def wanted_detail_active(self) -> bool:
        return self.path.startswith("/wanted/")

    @property
    def casting_active(self) -> bool:
        return _path_in(self.path, "/casting")

    @property
    def claims_active(self) -> bool:
        return _path_in(self.path, "/claims")


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


def _path_in(path: str, prefix: str) -> bool:
    return path == prefix or path.startswith(prefix + "/")


def _iter_board_nav_items(viewer: ForumView) -> list[Any]:
    items: list[Any] = []
    items.extend(viewer.location_navigation_boards)
    items.extend(viewer.community_navigation_boards)
    items.extend(viewer.desk_navigation_boards)
    items.extend(viewer.studio_navigation_boards)
    return items
