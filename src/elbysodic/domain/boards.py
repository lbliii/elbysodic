"""Board contracts for world/place navigation."""

from __future__ import annotations

from typing import Literal, Protocol, cast

type BoardKind = Literal["location", "sublocation", "community", "desk", "archive", "staff"]
type BoardSidebarSection = Literal["locations", "community", "desk", "studio"]
type BoardImageTreatment = Literal["poster", "background", "compact", "text"]
type BoardImageFocalPoint = Literal["center", "top", "bottom", "left", "right"]
type BoardImageOverlay = Literal["light", "medium", "heavy"]
type SidebarRealm = Literal["world", "desk", "studio"]

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
BOARD_SIDEBAR_SECTIONS: frozenset[str] = frozenset({"locations", "community", "desk", "studio"})
BOARD_IMAGE_TREATMENTS: frozenset[str] = frozenset({"poster", "background", "compact", "text"})
BOARD_IMAGE_TREATMENT_LABELS: dict[BoardImageTreatment, str] = {
    "poster": "Poster/card",
    "background": "Full background",
    "compact": "Compact thumbnail",
    "text": "Text first",
}
BOARD_IMAGE_FOCAL_POINTS: frozenset[str] = frozenset({"center", "top", "bottom", "left", "right"})
BOARD_IMAGE_FOCAL_POINT_LABELS: dict[BoardImageFocalPoint, str] = {
    "center": "Center",
    "top": "Top",
    "bottom": "Bottom",
    "left": "Left",
    "right": "Right",
}
BOARD_IMAGE_OVERLAYS: frozenset[str] = frozenset({"light", "medium", "heavy"})
BOARD_IMAGE_OVERLAY_LABELS: dict[BoardImageOverlay, str] = {
    "light": "Light",
    "medium": "Medium",
    "heavy": "Heavy",
}
BOARD_SIDEBAR_SECTION_LABELS: dict[BoardSidebarSection, str] = {
    "locations": "Locations",
    "community": "Community",
    "desk": "Writer Desk",
    "studio": "Director Studio",
}
BOARD_SIDEBAR_SECTION_GUIDANCE: dict[BoardSidebarSection, str] = {
    "locations": "Playable places in the world map.",
    "community": "Public OOC, records, announcements, and archives.",
    "desk": "Writer workflow lanes near queues and roster work.",
    "studio": "Director production lanes for staff and board operations.",
}
BOARD_KIND_DEFAULT_SECTIONS: dict[BoardKind, BoardSidebarSection] = {
    "location": "locations",
    "sublocation": "locations",
    "community": "community",
    "archive": "community",
    "desk": "desk",
    "staff": "studio",
}
BOARD_SIDEBAR_SECTION_REALMS: dict[BoardSidebarSection, SidebarRealm] = {
    "locations": "world",
    "community": "world",
    "desk": "desk",
    "studio": "studio",
}
BOARD_SIDEBAR_SECTION_DEFAULT_ORDER: dict[BoardSidebarSection, int] = {
    "locations": 10,
    "community": 20,
    "desk": 10,
    "studio": 20,
}
DEFAULT_SIDEBAR_SECTION_CONFIGS: tuple[
    tuple[SidebarRealm, BoardSidebarSection, str, str, int, bool],
    ...,
] = tuple(
    (
        BOARD_SIDEBAR_SECTION_REALMS[key],
        key,
        BOARD_SIDEBAR_SECTION_LABELS[key],
        BOARD_SIDEBAR_SECTION_GUIDANCE[key],
        BOARD_SIDEBAR_SECTION_DEFAULT_ORDER[key],
        False,
    )
    for key in ("locations", "community", "desk", "studio")
)
LOCATION_BOARD_KINDS: frozenset[BoardKind] = frozenset({"location", "sublocation"})
COMMUNITY_BOARD_KINDS: frozenset[BoardKind] = frozenset({"community", "archive"})
DESK_BOARD_KINDS: frozenset[BoardKind] = frozenset({"desk", "staff"})


class BoardLike(Protocol):
    @property
    def board_kind(self) -> str: ...

    @property
    def sidebar_section(self) -> str: ...


def normalize_board_kind(value: str | None) -> BoardKind:
    """Normalize persisted or external board-kind input to a known contract value."""
    if value in BOARD_KINDS:
        return cast(BoardKind, value)
    return "location"


def default_sidebar_section_for_kind(board_kind: str | None) -> BoardSidebarSection:
    return BOARD_KIND_DEFAULT_SECTIONS[normalize_board_kind(board_kind)]


def normalize_board_sidebar_section(
    value: str | None,
    board_kind: str | None = None,
) -> BoardSidebarSection:
    if value in BOARD_SIDEBAR_SECTIONS:
        return cast(BoardSidebarSection, value)
    return default_sidebar_section_for_kind(board_kind)


def normalize_board_image_treatment(value: str | None) -> BoardImageTreatment:
    if value in BOARD_IMAGE_TREATMENTS:
        return cast(BoardImageTreatment, value)
    return "poster"


def normalize_board_image_focal_point(value: str | None) -> BoardImageFocalPoint:
    if value in BOARD_IMAGE_FOCAL_POINTS:
        return cast(BoardImageFocalPoint, value)
    return "center"


def normalize_board_image_overlay(value: str | None) -> BoardImageOverlay:
    if value in BOARD_IMAGE_OVERLAYS:
        return cast(BoardImageOverlay, value)
    return "medium"


def is_location_board(board: BoardLike) -> bool:
    return normalize_board_kind(board.board_kind) in LOCATION_BOARD_KINDS


def is_community_board(board: BoardLike) -> bool:
    return normalize_board_kind(board.board_kind) in COMMUNITY_BOARD_KINDS


def is_desk_board(board: BoardLike) -> bool:
    return normalize_board_kind(board.board_kind) in DESK_BOARD_KINDS


def is_location_sidebar_board(board: BoardLike) -> bool:
    return normalize_board_sidebar_section(board.sidebar_section, board.board_kind) == "locations"


def is_community_sidebar_board(board: BoardLike) -> bool:
    return normalize_board_sidebar_section(board.sidebar_section, board.board_kind) == "community"


def is_desk_sidebar_board(board: BoardLike) -> bool:
    return normalize_board_sidebar_section(board.sidebar_section, board.board_kind) == "desk"


def is_studio_sidebar_board(board: BoardLike) -> bool:
    return normalize_board_sidebar_section(board.sidebar_section, board.board_kind) == "studio"
