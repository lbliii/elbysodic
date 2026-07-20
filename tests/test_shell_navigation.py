from types import SimpleNamespace
from typing import Any, cast

from elbysodic.services import policies
from elbysodic.web.navigation import (
    active_route_path,
    primary_nav_items,
    shell_navigation,
    shell_route_state,
)


def test_active_route_path_strips_query_fragment_and_absolute_url() -> None:
    assert active_route_path("/desk?face=rowan#queue") == "/desk"
    assert active_route_path("https://example.test/c/hp-universe/wanted?x=1") == (
        "/c/hp-universe/wanted"
    )
    assert active_route_path("") == "/"


def test_shell_route_state_maps_major_rooms() -> None:
    cases = [
        ("/", "", "home", "home"),
        ("/locations", "", "locations", "locations"),
        ("/boards/frozen-midtown", "", "locations", "locations"),
        ("/boards/frozen-midtown", "locations", "locations", "locations"),
        ("/world/b-24-winter", "", "home", "guidebook"),
        ("/members/llane", "", "home", "community"),
        ("/boards/announcements", "community", "home", "community"),
        ("/wanted", "", "wanted", "wanted"),
        ("/casting", "", "wanted", "wanted"),
        ("/claims", "", "wanted", "wanted"),
        ("/desk", "", "desk", "desk"),
        ("/my/threads", "", "desk", "desk"),
        ("/applications", "", "desk", "desk"),
        ("/plotting", "", "desk", "desk"),
        ("/discover", "", "desk", "desk"),
        ("/studio", "", "studio", "studio"),
        ("/boards/staff-room", "studio", "studio", "studio"),
        ("/network", "", "network", "home"),
    ]
    for path, board_section, expected_room, expected_inner in cases:
        state = shell_route_state(path, board_section)
        assert state.active_room == expected_room
        assert state.active_inner == expected_inner


def test_shell_route_state_keeps_legacy_aliases_for_templates() -> None:
    assert shell_route_state("/wanted").play_active is True
    assert shell_route_state("/wanted").is_play is True
    assert shell_route_state("/").world_active is True
    assert shell_route_state("/locations").locations_room_active is True


def test_primary_nav_items_share_shell_route_active_state() -> None:
    items = primary_nav_items("/claims?status=reserved")

    assert [item.key for item in items] == [
        "home",
        "locations",
        "wanted",
    ]
    assert [item.label for item in items] == [
        "World Home",
        "Locations",
        "Wanted",
    ]
    assert [item.key for item in items if item.active] == ["wanted"]


def test_shell_navigation_gates_primary_rooms_by_viewer_audience() -> None:
    public = shell_navigation(None, "/desk")
    member = shell_navigation(cast(Any, _viewer(is_admin=False)), "/desk")
    staff = shell_navigation(cast(Any, _viewer(is_admin=True)), "/studio")

    assert [item.key for item in public.primary_items] == ["home", "locations", "wanted"]
    assert [item.key for item in member.primary_items] == [
        "home",
        "locations",
        "wanted",
        "desk",
    ]
    assert [item.key for item in staff.primary_items] == [
        "home",
        "locations",
        "wanted",
        "desk",
        "studio",
    ]
    assert [item.key for item in member.primary_items if item.active] == ["desk"]
    assert [item.key for item in staff.primary_items if item.active] == ["studio"]


def test_shell_navigation_builds_inner_sections_from_shared_model() -> None:
    member = shell_navigation(cast(Any, _viewer(is_admin=False)), "/desk")
    staff = shell_navigation(cast(Any, _viewer(is_admin=True)), "/studio")

    assert [(section.key, section.label) for section in member.sidebar_sections] == [
        ("desk", "On Your Desk")
    ]
    assert [item.key for item in member.sidebar_sections[0].items[:4]] == [
        "queue",
        "inbox",
        "roster",
        "plotting",
    ]
    assert [(section.key, section.label) for section in staff.sidebar_sections] == [
        ("studio", "In Studio"),
    ]
    assert [item.key for item in staff.sidebar_sections[0].items] == [
        "operations",
        "launch",
        "discovery",
        "structure",
        "intake",
        "appearance",
        "content",
    ]
    assert all(item.href.startswith("/studio") for item in staff.sidebar_sections[0].items)


def _viewer(*, is_admin: bool) -> SimpleNamespace:
    role = SimpleNamespace(
        id=1,
        community_id=1,
        is_admin=is_admin,
        capabilities=policies.ADMIN_CAPABILITIES if is_admin else frozenset(),
    )
    membership = SimpleNamespace(
        id=1,
        community_id=1,
        role_id=1,
        is_active=True,
    )
    section = SimpleNamespace(label="Locations", show_label=True)
    return SimpleNamespace(
        membership=membership,
        role=role,
        current_character=SimpleNamespace(id=1) if not is_admin else None,
        location_navigation_boards=[],
        location_navigation_groups=[],
        location_sidebar_section=section,
        community_navigation_boards=[],
        community_sidebar_section=SimpleNamespace(label="Community", show_label=True),
        desk_navigation_boards=[],
        desk_sidebar_section=SimpleNamespace(label="Desk", show_label=True),
        studio_navigation_boards=[],
        studio_sidebar_section=SimpleNamespace(label="Studio", show_label=True),
        unread_notification_count=0,
    )
