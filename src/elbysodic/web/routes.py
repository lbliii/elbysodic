"""Rendered route helpers for shell navigation state."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit


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


@dataclass(frozen=True, slots=True)
class ShellRouteState:
    path: str
    board_section: str = ""

    @property
    def mode(self) -> str:
        if self.path == "/":
            return "home"
        if self.is_play:
            return "play"
        if self.is_studio:
            return "studio"
        if self.is_desk:
            return "desk"
        return "world"

    @property
    def active_room(self) -> str:
        return self.mode

    @property
    def world_active(self) -> bool:
        return self.mode == "world"

    @property
    def play_active(self) -> bool:
        return self.mode == "play"

    @property
    def studio_active(self) -> bool:
        return self.mode == "studio"

    @property
    def desk_active(self) -> bool:
        return self.mode == "desk"

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
    def is_play(self) -> bool:
        return any(
            _path_in(self.path, prefix)
            for prefix in (
                "/wanted",
                "/claims",
                "/casting",
                "/plotting",
                "/discover",
            )
        )

    @property
    def is_studio(self) -> bool:
        return _path_in(self.path, "/studio") or self.board_section == "studio"

    @property
    def is_desk(self) -> bool:
        return any(
            _path_in(self.path, prefix)
            for prefix in (
                "/desk",
                "/my/threads",
                "/notifications",
                "/characters",
                "/applications",
                "/interactions",
            )
        ) or self.board_section == "desk"

    @property
    def is_guidebook(self) -> bool:
        return _path_in(self.path, "/world")

    @property
    def locations_active(self) -> bool:
        return _path_in(self.path, "/locations") or self.board_section == "locations"

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


def _path_in(path: str, prefix: str) -> bool:
    return path == prefix or path.startswith(prefix + "/")
