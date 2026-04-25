"""Board contracts for world/place navigation."""

from __future__ import annotations

from typing import Literal, Protocol, cast

type BoardKind = Literal["location", "sublocation", "community", "desk", "archive", "staff"]

BOARD_KINDS: frozenset[str] = frozenset(
    {"location", "sublocation", "community", "desk", "archive", "staff"}
)
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
