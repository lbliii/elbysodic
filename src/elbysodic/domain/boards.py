"""Board contracts for world/place navigation."""

from __future__ import annotations

from typing import Literal, Protocol, cast

type BoardKind = Literal["location", "sublocation", "community", "desk", "archive", "staff"]

BOARD_KINDS: frozenset[str] = frozenset(
    {"location", "sublocation", "community", "desk", "archive", "staff"}
)
BOARD_KIND_LABELS: dict[BoardKind, str] = {
    "location": "Location",
    "sublocation": "Sublocation",
    "community": "Community board",
    "desk": "Desk board",
    "archive": "Archive",
    "staff": "Staff board",
}
BOARD_KIND_REALMS: dict[BoardKind, str] = {
    "location": "World",
    "sublocation": "World",
    "community": "World",
    "desk": "Writer Desk",
    "archive": "World",
    "staff": "Studio",
}
BOARD_KIND_SIDEBAR_LABELS: dict[BoardKind, str] = {
    "location": "Location tree",
    "sublocation": "Location branch",
    "community": "Community group",
    "desk": "Desk lane",
    "archive": "Community archive",
    "staff": "Studio lane",
}
BOARD_KIND_GUIDANCE: dict[BoardKind, str] = {
    "location": "Major playable place; appears as a parent in the world map.",
    "sublocation": "Nested playable place; needs a major location parent.",
    "community": "OOC or public community board; lives outside the map.",
    "desk": "Writer workflow board; belongs near queue and roster work.",
    "archive": "Read-only or historical community board.",
    "staff": "Director-only production board.",
}
LOCATION_BOARD_KINDS: frozenset[BoardKind] = frozenset({"location", "sublocation"})
COMMUNITY_BOARD_KINDS: frozenset[BoardKind] = frozenset({"community", "archive"})
DESK_BOARD_KINDS: frozenset[BoardKind] = frozenset({"desk", "staff"})


class BoardLike(Protocol):
    @property
    def board_kind(self) -> str: ...


def normalize_board_kind(value: str | None) -> BoardKind:
    """Normalize persisted or external board-kind input to a known contract value."""
    if value in BOARD_KINDS:
        return cast(BoardKind, value)
    return "location"


def is_location_board(board: BoardLike) -> bool:
    return normalize_board_kind(board.board_kind) in LOCATION_BOARD_KINDS


def is_community_board(board: BoardLike) -> bool:
    return normalize_board_kind(board.board_kind) in COMMUNITY_BOARD_KINDS


def is_desk_board(board: BoardLike) -> bool:
    return normalize_board_kind(board.board_kind) in DESK_BOARD_KINDS
