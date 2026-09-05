"""Template navigation helpers for route-aware Chirp-UI components."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal
from urllib.parse import urlsplit

from elbysodic.domain.models import Board
from elbysodic.services import policies
from elbysodic.services.read_models import ForumView

type ShellAudience = Literal["public", "applicant", "member", "staff"]


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
class ShellNavItem:
    key: str
    label: str
    href: str
    active: bool
    icon_id: str | None = None
    count: int | None = None
    description: str | None = None
    aria_label: str | None = None
    children: tuple[ShellNavItem, ...] = ()


PrimaryNavItem = ShellNavItem


@dataclass(frozen=True, slots=True)
class ShellNavSection:
    key: str
    label: str | None
    items: tuple[ShellNavItem, ...]
    source: str = "static"


@dataclass(frozen=True, slots=True)
class ShellNavigation:
    active_room: str
    active_inner: str
    primary_items: tuple[ShellNavItem, ...]
    sidebar_sections: tuple[ShellNavSection, ...]


def primary_nav_items(current_path: object, board_section: str = "") -> tuple[PrimaryNavItem, ...]:
    return shell_navigation(None, current_path, board_section).primary_items


def shell_navigation(
    viewer: ForumView | None,
    current_path: object,
    board_section: str = "",
    *,
    board: Any = None,
    parent_board: Any = None,
    guidebook: Any = None,
    material: Any = None,
    wanted: Any = None,
    studio: Any = None,
    include_community_map: bool = False,
) -> ShellNavigation:
    state = shell_route_state(current_path, board_section)
    primary_items = _primary_nav_items_for_viewer(viewer, state)
    sidebar_sections: list[ShellNavSection] = []
    if include_community_map:
        sidebar_sections.append(_community_map_section(state, primary_items))

    if state.is_guidebook:
        sidebar_sections.extend(_guidebook_sections(viewer, state, guidebook, material))
    elif state.is_play:
        sidebar_sections.extend(_wanted_sections(state, board, wanted))
    elif state.is_studio:
        sidebar_sections.extend(_studio_sections(viewer, state, studio, board))
    elif state.is_desk:
        sidebar_sections.extend(_desk_sections(viewer, state, board))
    else:
        sidebar_sections.extend(_world_sections(viewer, state, board, parent_board))

    return ShellNavigation(
        active_room=state.active_room,
        active_inner=state.active_inner,
        primary_items=primary_items,
        sidebar_sections=tuple(section for section in sidebar_sections if section.items),
    )


def _primary_nav_items_for_viewer(
    viewer: ForumView | None,
    state: ShellRouteState,
) -> tuple[ShellNavItem, ...]:
    items: list[ShellNavItem] = [
        ShellNavItem(
            key="home",
            label="World Home",
            href="/",
            active=state.active_room == "home",
            icon_id="home",
        ),
        ShellNavItem(
            key="locations",
            label="Locations",
            href="/locations",
            active=state.active_room == "locations",
            icon_id="locations",
        ),
        ShellNavItem(
            key="wanted",
            label="Wanted",
            href="/wanted",
            active=state.active_room == "wanted",
            icon_id="wanted",
        ),
    ]
    if _can_view_desk(viewer):
        items.append(
            ShellNavItem(
                key="desk",
                label="Desk",
                href="/desk",
                active=state.active_room == "desk",
                icon_id="desk",
            )
        )
    if _can_view_studio(viewer):
        items.append(
            ShellNavItem(
                key="studio",
                label="Studio",
                href="/studio",
                active=state.active_room == "studio",
                icon_id="studio",
            )
        )
    return tuple(items)


def _community_map_section(
    state: ShellRouteState,
    primary_items: tuple[ShellNavItem, ...],
) -> ShellNavSection:
    active_by_key = {item.key: item.active for item in primary_items}
    return ShellNavSection(
        key="community-map",
        label="Community",
        source="primary",
        items=tuple(
            ShellNavItem(
                key=item.key,
                label=item.label,
                href=item.href,
                active=active_by_key.get(item.key, state.active_room == item.key),
                icon_id=item.icon_id,
                count=item.count,
                description=item.description,
                aria_label=item.aria_label,
            )
            for item in primary_items
        ),
    )


def _world_context_section(
    viewer: ForumView | None,
    state: ShellRouteState,
) -> ShellNavSection:
    locations_label = viewer.location_sidebar_section.label if viewer else "Locations"
    community_label = viewer.community_sidebar_section.label if viewer else "Community Table"
    label = "In Locations" if state.locations_active else "On World Home"
    location_count = len(viewer.location_navigation_boards) if viewer else None
    community_count = len(viewer.community_navigation_boards) if viewer else None
    return ShellNavSection(
        key="world-context",
        label=label,
        source="world_context",
        items=(
            ShellNavItem(
                key="locations",
                label=locations_label,
                href="/locations",
                active=state.locations_active,
                icon_id="locations",
                count=location_count,
            ),
            ShellNavItem(
                key="guidebook",
                label="Guidebook",
                href="/world",
                active=state.guidebook_active,
                icon_id="guidebook",
            ),
            ShellNavItem(
                key="community",
                label=community_label,
                href="/community",
                active=state.community_active,
                icon_id="community",
                count=community_count,
            ),
        ),
    )


def _world_sections(
    viewer: ForumView | None,
    state: ShellRouteState,
    board: Any,
    parent_board: Any,
) -> tuple[ShellNavSection, ...]:
    sections: list[ShellNavSection] = [_world_context_section(viewer, state)]
    if viewer and viewer.location_navigation_groups:
        label = (
            viewer.location_sidebar_section.label
            if viewer.location_sidebar_section.show_label
            else "Location Map"
        )
        sections.append(
            ShellNavSection(
                key="location-map",
                label=label,
                source="location_tree",
                items=tuple(
                    _location_tree_items(
                        viewer,
                        _object_id(board),
                        _object_id(parent_board),
                    )
                ),
            )
        )
    community_label = (
        viewer.community_sidebar_section.label
        if viewer and viewer.community_sidebar_section.show_label
        else "Community Table"
    )
    community_items = [
        ShellNavItem(
            key="members",
            label="Members",
            href="/members",
            active=False,
        )
    ]
    if viewer:
        community_items.extend(
            _board_shell_item(item.board, item.unread_thread_count, current_board=board)
            for item in viewer.community_navigation_boards
        )
    sections.append(
        ShellNavSection(
            key="community-table",
            label=community_label,
            source="community_boards",
            items=tuple(community_items),
        )
    )
    return tuple(sections)


def _guidebook_sections(
    viewer: ForumView | None,
    state: ShellRouteState,
    guidebook: Any,
    material: Any,
) -> tuple[ShellNavSection, ...]:
    sections: list[ShellNavSection] = [_world_context_section(viewer, state)]
    if guidebook is not None:
        sections.extend(_guidebook_index_sections(guidebook))
    elif material is not None:
        current_material = getattr(material, "material", None)
        if current_material is not None:
            sections.append(
                ShellNavSection(
                    key="current-material",
                    label="Current Material",
                    source="material",
                    items=(
                        ShellNavItem(
                            key=f"material:{current_material.slug}",
                            label=current_material.title,
                            href=f"/world/{current_material.slug}",
                            active=True,
                        ),
                    ),
                )
            )
        related = tuple(
            ShellNavItem(
                key=f"material:{item.material.slug}",
                label=item.material.title,
                href=f"/world/{item.material.slug}",
                active=False,
            )
            for item in getattr(material, "related_materials", [])
        )
        if related:
            sections.append(
                ShellNavSection(
                    key="related-materials",
                    label="Related",
                    source="material",
                    items=related,
                )
            )
    return tuple(sections)


def _guidebook_index_sections(guidebook: Any) -> tuple[ShellNavSection, ...]:
    sections: list[ShellNavSection] = []
    featured = getattr(guidebook, "featured", [])
    if featured:
        sections.append(
            ShellNavSection(
                key="guidebook-index",
                label="Guidebook Index",
                source="guidebook",
                items=(
                    ShellNavItem(
                        key="start-here",
                        label="Start Here",
                        href="/world#start-here",
                        active=False,
                        icon_id="wanted",
                    ),
                    *tuple(_material_item(item) for item in featured),
                ),
            )
        )
    guides = getattr(guidebook, "guides", [])
    if guides:
        sections.append(
            ShellNavSection(
                key="guides",
                label="Guides",
                source="guidebook",
                items=(
                    ShellNavItem(
                        key="guides-anchor",
                        label="Guides",
                        href="/world#guides",
                        active=False,
                        icon_id="guidebook",
                    ),
                    *tuple(_material_item(item) for item in guides),
                ),
            )
        )
    events = getattr(guidebook, "events", [])
    if events:
        sections.append(
            ShellNavSection(
                key="events",
                label="Events",
                source="guidebook",
                items=(
                    ShellNavItem(
                        key="events-anchor",
                        label="Events",
                        href="/world#events",
                        active=False,
                        icon_id="events",
                    ),
                    *tuple(_material_item(item) for item in events),
                ),
            )
        )
    applications = getattr(guidebook, "application_materials", [])
    if applications:
        sections.append(
            ShellNavSection(
                key="applications",
                label="Applications",
                source="guidebook",
                items=(
                    ShellNavItem(
                        key="applications-anchor",
                        label="Applications",
                        href="/world#applications",
                        active=False,
                        icon_id="applications",
                    ),
                    *tuple(_material_item(item) for item in applications),
                ),
            )
        )
    return tuple(sections)


def _desk_sections(
    viewer: ForumView | None,
    state: ShellRouteState,
    board: Any,
) -> tuple[ShellNavSection, ...]:
    if not _can_view_desk(viewer):
        return ()
    items: list[ShellNavItem] = []
    if state.path != "/desk":
        items.append(
            ShellNavItem(
                key="desk-home",
                label="Desk home",
                href="/desk",
                active=False,
                icon_id="home",
            )
        )
    items.extend(
        [
            ShellNavItem(
                key="queue",
                label="Queue",
                href="/my/threads",
                active=state.queue_active,
                icon_id="queue",
            ),
            ShellNavItem(
                key="inbox",
                label="Inbox",
                href="/notifications",
                active=state.notifications_active,
                icon_id="inbox",
                count=viewer.unread_notification_count if viewer else None,
            ),
        ]
    )
    if viewer:
        items.extend(
            _board_shell_item(item.board, item.unread_thread_count, current_board=board)
            for item in viewer.desk_navigation_boards
        )
    return (
        ShellNavSection(
            key="desk",
            label="On Your Desk",
            source="desk",
            items=tuple(items),
        ),
    )


def _studio_sections(
    viewer: ForumView | None,
    state: ShellRouteState,
    studio: Any,
    board: Any,
) -> tuple[ShellNavSection, ...]:
    if not _can_view_studio(viewer):
        return ()
    studio_items: list[ShellNavItem] = [
        ShellNavItem(
            key="today",
            label="Today",
            href="/studio",
            active=_studio_today_active(state.path),
            icon_id="studio",
        ),
        ShellNavItem(
            key="shape",
            label="Shape",
            href="/studio/structure",
            active=_studio_shape_active(state.path),
            icon_id="boards",
        ),
        ShellNavItem(
            key="open",
            label="Open",
            href="/studio/launch",
            active=_studio_open_active(state.path),
            icon_id="launch",
        ),
    ]
    if viewer:
        studio_items.extend(
            _board_shell_item(item.board, item.unread_thread_count, current_board=board)
            for item in viewer.studio_navigation_boards
        )
    sections = [
        ShellNavSection(
            key="studio",
            label="In Studio",
            source="studio",
            items=tuple(studio_items),
        ),
    ]
    return tuple(sections)


def _wanted_sections(
    state: ShellRouteState,
    board: Any,
    wanted: Any,
) -> tuple[ShellNavSection, ...]:
    items: list[ShellNavItem] = []
    if state.path != "/wanted":
        items.append(
            ShellNavItem(
                key="wanted-board",
                label="Wanted board",
                href="/wanted",
                active=state.wanted_detail_active,
                icon_id="wanted",
            )
        )
    items.extend(
        [
            ShellNavItem(
                key="casting",
                label="Casting desk",
                href="/casting",
                active=state.casting_active,
                icon_id="casting",
            ),
            ShellNavItem(
                key="claims",
                label="Claims",
                href="/claims",
                active=state.claims_active,
                icon_id="claims",
            ),
        ]
    )
    sections: list[ShellNavSection] = [
        ShellNavSection(
            key="wanted",
            label="In Wanted",
            source="wanted",
            items=tuple(items),
        )
    ]
    open_ads = getattr(board, "open_ads", None)
    if open_ads:
        sections.append(
            ShellNavSection(
                key="open-wants",
                label="Open Wants",
                source="wanted",
                items=tuple(
                    ShellNavItem(
                        key=f"wanted:{item.wanted_ad.slug}",
                        label=item.wanted_ad.title,
                        href=f"/wanted/{item.wanted_ad.slug}",
                        active=False,
                    )
                    for item in open_ads
                ),
            )
        )
    elif wanted is not None and getattr(wanted, "related_ads", None):
        sections.append(
            ShellNavSection(
                key="related-wants",
                label="Related Wants",
                source="wanted",
                items=tuple(
                    ShellNavItem(
                        key=f"wanted:{item.wanted_ad.slug}",
                        label=item.wanted_ad.title,
                        href=f"/wanted/{item.wanted_ad.slug}",
                        active=False,
                    )
                    for item in wanted.related_ads
                ),
            )
        )
    return tuple(sections)


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


def _location_tree_items(
    viewer: ForumView,
    current_board_id: int = 0,
    current_parent_board_id: int = 0,
) -> list[ShellNavItem]:
    items: list[ShellNavItem] = []
    for group in viewer.location_navigation_groups:
        parent = group.parent.board
        parent_active = current_board_id == parent.id
        branch_open = parent_active or current_parent_board_id == parent.id
        children: tuple[ShellNavItem, ...] = ()
        if branch_open and group.children:
            children = tuple(
                _board_shell_item(
                    child.board,
                    child.unread_thread_count,
                    active=current_board_id == child.board.id,
                )
                for child in group.children
            )
        items.append(
            _board_shell_item(
                parent,
                group.unread_thread_count,
                active=parent_active,
                opened=branch_open,
                children=children,
            )
        )
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


def _board_shell_item(
    nav_board: Board,
    unread_thread_count: int,
    *,
    active: bool | None = None,
    opened: bool = False,
    children: tuple[ShellNavItem, ...] = (),
    current_board: Any = None,
) -> ShellNavItem:
    is_active = active if active is not None else _object_id(current_board) == nav_board.id
    return ShellNavItem(
        key=f"board:{nav_board.slug}",
        label=nav_board.name,
        href=f"/boards/{nav_board.slug}",
        active=is_active,
        count=unread_thread_count or None,
        description="open" if opened else None,
        children=children,
    )


def _material_item(item: Any) -> ShellNavItem:
    material = item.material
    return ShellNavItem(
        key=f"material:{material.slug}",
        label=material.title,
        href=f"/world/{material.slug}",
        active=False,
    )


def _object_id(value: Any) -> int:
    return int(getattr(value, "id", 0) or 0)


def _can_view_desk(viewer: ForumView | None) -> bool:
    return viewer is not None and viewer.membership.is_active


def _can_view_studio(viewer: ForumView | None) -> bool:
    if viewer is None:
        return False
    return (
        policies.can_manage_world(viewer.membership, viewer.role)
        or policies.can_manage_casting(viewer.membership, viewer.role)
        or policies.can_manage_navigation(viewer.membership, viewer.role)
    )


def _studio_today_active(path: str) -> bool:
    return path == "/studio" or _path_in(path, "/studio/operations")


def _studio_shape_active(path: str) -> bool:
    return any(
        _path_in(path, prefix)
        for prefix in (
            "/studio/structure",
            "/studio/appearance",
            "/studio/content",
            "/studio/intake",
            "/studio/boards",
        )
    )


def _studio_open_active(path: str) -> bool:
    return any(
        _path_in(path, prefix)
        for prefix in ("/studio/launch", "/studio/discovery", "/studio/access-requests")
    )


def _path_in(path: str, prefix: str) -> bool:
    return path == prefix or path.startswith(prefix + "/")


def _iter_board_nav_items(viewer: ForumView) -> list[Any]:
    items: list[Any] = []
    items.extend(viewer.location_navigation_boards)
    items.extend(viewer.community_navigation_boards)
    items.extend(viewer.desk_navigation_boards)
    items.extend(viewer.studio_navigation_boards)
    return items
