from elbysodic.web.navigation import active_route_path, shell_route_state


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
