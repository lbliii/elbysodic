from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from urllib.parse import urlencode

from chirp.app import App
from chirp.testing import TestClient

from elbysodic.db import ForumRepository, connect, create_schema
from elbysodic.db.seed import DemoSeed
from elbysodic.domain import Community, Thread
from elbysodic.services import AppServices, create_services
from elbysodic.web import create_app
from elbysodic.web.state import get_services

_FORM = {"Content-Type": "application/x-www-form-urlencoded"}


def _sidebar_board_count(html: str, board_slug: str) -> int:
    match = re.search(
        rf'<a class="[^"]*elbysodic-sidebar-link[^"]*" href="/boards/{re.escape(board_slug)}"[^>]*>'
        r"(?P<body>.*?)</a>",
        html,
        re.DOTALL,
    )
    assert match is not None
    count = re.search(
        r'<span class="elbysodic-sidebar-count">(?P<count>\d+)</span>',
        match.group("body"),
    )
    return int(count.group("count")) if count is not None else 0


def _app():
    return create_app(debug=False, services=create_services(path=":memory:"))


def _outsider_services(
    services: AppServices, *, prefix: str = "outsider"
) -> tuple[AppServices, int]:
    repo = services.repo
    community = services.seed.community
    role = repo.get_role_by_slug(community.id, "member")
    user = repo.create_user(f"{prefix}@example.com", "hash")
    membership = repo.create_membership(
        community.id,
        user.id,
        role.id,
        prefix,
        prefix.title(),
    )
    character = repo.create_character(
        community.id,
        membership.id,
        f"{prefix}-face",
        f"{prefix.title()} Face",
        make_default=True,
    )
    membership = repo.get_membership(community.id, membership.id)
    return AppServices(repo, DemoSeed(community, user, membership, character)), character.id


def _faceless_services(services: AppServices, *, prefix: str = "faceless") -> AppServices:
    repo = services.repo
    community = services.seed.community
    role = repo.get_role_by_slug(community.id, "member")
    user = repo.create_user(f"{prefix}@example.com", "hash")
    membership = repo.create_membership(
        community.id,
        user.id,
        role.id,
        prefix,
        prefix.title(),
    )
    return AppServices(repo, DemoSeed(community, user, membership, None))


def test_forum_pages_render_seeded_boards_and_thread() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            index = await client.get("/")
            assert index.status == 200
            assert "X-Men Apocalypse" in index.text
            assert "Announcements" in index.text
            assert "Danger Room" in index.text
            assert "Staff Room" not in index.text
            assert "Latest" in index.text
            assert "Recent activity" in index.text
            assert "#post-" in index.text
            assert "/members/starlane" in index.text
            assert "Latest details:" in index.text
            assert "Relevant for Rogue:" in index.text
            assert "elbysodic-board-poster__face-signal-hint" in index.text
            assert "elbysodic-face-switcher" in index.text
            assert "elbysodic-community-table" in index.text
            assert "elbysodic-community-row" in index.text
            assert "✉" in index.text
            assert "✏" in index.text
            assert "◉" in index.text
            assert "⟳" in index.text
            assert "elbysodic-activity-log" in index.text
            assert "elbysodic-activity-log-item" in index.text
            assert re.search(
                r">\s*(?:Today|Yesterday), \d{1,2}:\d{2} [AP]M\s*</time>",
                index.text,
            )
            assert re.search(
                r'<time class="elbysodic-activity-log-item__time"\s+datetime="[^"]+"\s+title="[A-Z][a-z]{2} \d{1,2}, 2026 \d{1,2}:\d{2} [AP]M UTC">',
                index.text,
            )
            assert _sidebar_board_count(index.text, "plotting") == 1

            board = await client.get("/boards/plotting")
            assert board.status == 200
            assert "Open thread roster" in board.text
            assert "Started by" in board.text
            assert "Latest" in board.text
            assert 'id="board-thread-region"' in board.text
            assert 'hx-target="#board-thread-region"' in board.text
            assert 'hx-swap="outerHTML show:none"' in board.text
            assert "First unread" in board.text
            assert "#post-" in board.text
            assert "new replies" in board.text
            assert "min read" in board.text
            assert "written by" in board.text
            assert "Next unread" in board.text
            assert "Magneto" in board.text

            thread = await client.get("/boards/plotting/threads/open-thread-roster")
            assert thread.status == 200
            assert 'id="post-' in thread.text
            assert "Runtime" in thread.text
            assert "Credits" in thread.text
            assert "min read" in thread.text
            assert "Drop your available characters here" in thread.text
            assert "Rogue" in thread.text
            assert "Magneto" in thread.text
            assert "/members/starlane" in thread.text
            assert "caught up" in thread.text
            assert _sidebar_board_count(thread.text, "plotting") == 0

    asyncio.run(run())


def test_seeded_world_surfaces_place_hierarchy() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            index = await client.get("/")
            assert index.status == 200
            assert "/boards/xavier-institute" in index.text
            assert "/boards/med-bay" in index.text
            assert "Locations" in index.text

            academy = await client.get("/boards/xavier-institute")
            assert academy.status == 200
            assert "Sublocations" in academy.text
            assert "Med Bay" in academy.text
            assert "Cerebro" in academy.text
            assert "Danger Room" in academy.text

            med_bay = await client.get("/boards/med-bay")
            assert med_bay.status == 200
            assert "Xavier Institute" in med_bay.text
            assert "Nearby locations" in med_bay.text
            assert "The med-bay lights stay on" in med_bay.text

    asyncio.run(run())


def test_shell_centers_community_brand_and_quiet_platform_mark() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            index = await client.get("/")

            assert index.status == 200
            assert (
                '<span class="elbysodic-community-brand__name">X-Men Apocalypse</span>'
                in index.text
            )
            assert "Built on" in index.text
            assert "<strong>Elbysodic</strong>" in index.text
            assert 'href="/desk"' in index.text
            assert index.text.count("Writer Desk") == 1

    asyncio.run(run())


def test_writer_desk_hub_keeps_meta_tools_reachable() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            desk = await client.get("/desk")

            assert desk.status == 200
            assert "Writer Desk" in desk.text
            assert "/my/threads" in desk.text
            assert "/notifications" in desk.text
            assert "/characters" in desk.text
            assert "/applications" in desk.text
            assert "/casting" in desk.text
            assert "/discover" in desk.text

    asyncio.run(run())


def test_director_studio_surfaces_community_production_work() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            studio = await client.get("/studio")

            assert studio.status == 200
            assert "Director Studio" in studio.text
            assert "Shape X-Men Apocalypse" in studio.text
            assert "World Bible" in studio.text
            assert "Location Studio" in studio.text
            assert "Event Studio" in studio.text
            assert "Applications and hooks" in studio.text
            assert 'href="/world/b-24-winter"' in studio.text
            assert 'href="/applications"' in studio.text
            assert 'href="/wanted"' in studio.text
            assert "Current Event" in studio.text

    asyncio.run(run())


def test_sidebar_modes_follow_major_product_paths() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            world = await client.get("/boards/xavier-institute")
            assert world.status == 200
            assert "World Map" in world.text
            assert "Locations" in world.text
            assert "Sublocations" in world.text
            assert "Wanted board" not in world.text
            assert "data-elbysodic-sidebar-toggle" in world.text
            assert "chirpui-app-shell__sidebar-resize" in world.text
            assert "elbysodic-sidebar-destination" in world.text
            assert 'href="/locations"' in world.text
            assert 'href="/community"' in world.text
            assert 'class="chirpui-sidebar elbysodic-sidebar"' in world.text
            assert "elbysodic-mobile-nav-trigger" in world.text
            assert "elbysodic-mobile-shell-drawer" in world.text

            locations = await client.get("/locations")
            assert locations.status == 200
            assert "Playable world map" in locations.text
            assert "Major locations" in locations.text
            assert "/boards/xavier-institute" in locations.text
            assert "Community table" not in locations.text

            community = await client.get("/community")
            assert community.status == 200
            assert "Writer room and record" in community.text
            assert "Community table" in community.text
            assert "Announcements" in community.text
            assert "Playable world map" not in community.text

            guidebook = await client.get("/world")
            assert guidebook.status == 200
            assert "Guidebook" in guidebook.text
            assert "Start Here" in guidebook.text
            assert "World Map" not in guidebook.text
            assert '<h2 class="chirpui-drawer__title">Guidebook</h2>' in guidebook.text

            desk = await client.get("/desk")
            assert desk.status == 200
            assert "Writer Desk" in desk.text
            assert "My threads" in desk.text
            assert "World Map" not in desk.text
            assert '<h2 class="chirpui-drawer__title">Desk</h2>' in desk.text

            studio = await client.get("/studio")
            assert studio.status == 200
            assert "Director Studio" in studio.text
            assert "Production" in studio.text
            assert "Wanted board" in studio.text
            assert "World Map" not in studio.text
            assert '<h2 class="chirpui-drawer__title">Studio</h2>' in studio.text

            wanted = await client.get("/wanted")
            assert wanted.status == 200
            assert "Casting" in wanted.text
            assert "Wanted board" in wanted.text
            assert "Open Wants" in wanted.text
            assert "World Map" not in wanted.text
            assert '<h2 class="chirpui-drawer__title">Casting</h2>' in wanted.text

    asyncio.run(run())


def test_world_map_sidebar_anchors_current_location_branch() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            parent = await client.get("/boards/new-york-city")
            assert parent.status == 200
            assert re.search(
                r'class="[^"]*elbysodic-sidebar-tree__link--active[^"]*"'
                r'[^>]*href="/boards/new-york-city"',
                parent.text,
            )
            assert "/boards/frozen-midtown" in parent.text

            child = await client.get("/boards/frozen-midtown")
            assert child.status == 200
            assert re.search(
                r'class="[^"]*elbysodic-sidebar-tree__link--branch[^"]*"'
                r'[^>]*href="/boards/new-york-city"',
                child.text,
            )
            assert re.search(
                r'class="[^"]*elbysodic-sidebar-tree__link--active[^"]*"'
                r'[^>]*href="/boards/frozen-midtown"',
                child.text,
            )
            assert 'aria-label="Place path"' in child.text

    asyncio.run(run())


def test_board_pages_render_location_stage_and_place_tiles() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            academy = await client.get("/boards/xavier-institute")

            assert academy.status == 200
            assert "elbysodic-board-stage" in academy.text
            assert "elbysodic-board-media--xavier-institute" in academy.text
            assert "Choose a door inside Xavier Institute" in academy.text
            assert "Xavier Institute threads" in academy.text
            assert "No direct scenes here yet." in academy.text
            assert "Sublocations" in academy.text
            assert "elbysodic-board-poster--tile" in academy.text

            midtown = await client.get("/boards/frozen-midtown")

            assert midtown.status == 200
            assert "elbysodic-board-media--frozen-midtown" in midtown.text
            assert "Nearby" in midtown.text
            assert "New York City" in midtown.text
            assert "/boards/transit-tunnels" in midtown.text

    asyncio.run(run())


def test_topbar_marks_active_product_realm() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            world = await client.get("/boards/xavier-institute")
            assert world.status == 200
            assert re.search(
                r'class="[^"]*elbysodic-topnav__link--active[^"]*"'
                r'\s+href="/"',
                world.text,
            )

            guidebook = await client.get("/world")
            assert guidebook.status == 200
            assert re.search(
                r'class="[^"]*elbysodic-topnav__link--active[^"]*"'
                r'\s+href="/world"',
                guidebook.text,
            )

            desk = await client.get("/desk")
            assert desk.status == 200
            assert re.search(
                r'class="[^"]*elbysodic-topnav__link--active[^"]*"'
                r'\s+href="/desk"',
                desk.text,
            )

            wanted = await client.get("/wanted")
            assert wanted.status == 200
            assert re.search(
                r'class="[^"]*elbysodic-topnav__link--active[^"]*"'
                r'\s+href="/wanted"',
                wanted.text,
            )

            studio = await client.get("/studio")
            assert studio.status == 200
            assert re.search(
                r'class="[^"]*elbysodic-topnav__link--active[^"]*"'
                r'\s+href="/studio"',
                studio.text,
            )

    asyncio.run(run())


def test_parent_board_summaries_roll_up_child_activity_but_thread_lists_stay_direct() -> None:
    connection = connect(check_same_thread=False)
    create_schema(connection)
    repo = ForumRepository(connection)
    community = repo.seed_default_community("Hierarchy Test")
    role = repo.create_role(community.id, "member", "Member")
    user = repo.create_user("writer@example.com", "hash")
    membership = repo.create_membership(community.id, user.id, role.id, "writer", "Writer")
    character = repo.create_character(
        community.id,
        membership.id,
        "active-face",
        "Active Face",
        make_default=True,
    )
    parent = repo.create_board(community.id, "academy", "Academy", board_kind="location")
    child = repo.create_board(
        community.id,
        "med-bay",
        "Med Bay",
        parent_board_id=parent.id,
        board_kind="sublocation",
    )
    parent_thread = repo.create_thread(
        community.id,
        parent.id,
        character.id,
        "hallway-scene",
        "Hallway Scene",
    )
    repo.create_post(community.id, parent_thread.id, character.id, "A direct academy scene.")
    child_thread = repo.create_thread(
        community.id,
        child.id,
        character.id,
        "med-bay-scene",
        "Med Bay Scene",
    )
    repo.create_post(community.id, child_thread.id, character.id, "A child-location scene.")
    services = AppServices(
        repo,
        DemoSeed(
            community=community,
            user=user,
            membership=repo.get_membership(community.id, membership.id),
            default_character=character,
        ),
    )

    summaries = {summary.board.slug: summary for summary in services.list_boards()}
    _, direct_threads = services.board_threads("academy")

    assert summaries["academy"].thread_count == 2
    assert summaries["academy"].post_count == 2
    assert summaries["academy"].has_children is True
    assert summaries["academy"].latest_thread == child_thread
    assert [item.thread.title for item in direct_threads] == ["Hallway Scene"]


def test_discovery_defaults_to_active_face_lens_and_filters_facets() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            discover = await client.get("/discover")
            assert discover.status == 200
            assert "Plot discovery" in discover.text
            assert "For Rogue" in discover.text
            assert "Mutant" in discover.text
            assert "X-Men" in discover.text
            assert "Academy" in discover.text
            assert "Rogue" in discover.text
            assert "Bolivar Trask" not in discover.text

            human_un = await client.get("/discover?facets=human,united-nations")
            assert human_un.status == 200
            assert "Bolivar Trask" in human_un.text
            assert "Moira MacTaggert" in human_un.text
            assert 'href="/characters/rogue">Rogue' not in human_un.text

    asyncio.run(run())


def test_world_materials_render_pillars_events_and_application_guides() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            world = await client.get("/world")
            assert world.status == 200
            assert "World studio" in world.text
            assert "Premise" in world.text
            assert "Application Guide" in world.text
            assert "Current Event: B-24 Winter" in world.text
            assert "Guidebook pulse" in world.text
            assert 'href="/world/premise"' in world.text
            assert 'href="/world/b-24-winter"' in world.text
            assert "United Nations" in world.text

            event = await client.get("/world/b-24-winter")
            assert event.status == 200
            assert "Iceman is infected with B-24" in event.text
            assert "Evil Lab" in event.text
            assert "Wanted hooks" in event.text
            assert "Active scenes" in event.text
            assert "Locations" in event.text
            assert "Related materials" in event.text
            assert "elbysodic-studio-facts" in event.text
            assert "Featured" in event.text
            assert "Carry this event into play" in event.text
            assert 'aria-label="Material sections"' in event.text
            assert 'href="#event-actions"' in event.text
            assert 'id="canon"' in event.text
            assert "Enter scene" in event.text
            assert "Answer hook" in event.text
            assert "Explore location" in event.text
            assert "Open discovery" in event.text
            assert "Event progression" in event.text
            assert "elbysodic-continuity-timeline" in event.text
            assert "elbysodic-continuity-timeline__title-link" in event.text
            assert "Event opened" in event.text
            assert "elbysodic-counter__label chirpui-visually-hidden" in event.text

            location = await client.get("/boards/frozen-midtown")
            assert location.status == 200
            assert "Current event in this location" in location.text
            assert 'href="/world/b-24-winter"' in location.text

            scene = await client.get("/boards/frozen-midtown/threads/frozen-avenue-evacuation")
            assert scene.status == 200
            assert "Current event shaping this scene" in scene.text
            assert 'href="/world/b-24-winter"' in scene.text

            missing = await client.get("/world/not-a-material")
            assert missing.status == 404

    asyncio.run(run())


def test_applications_desk_tracks_character_statuses() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            applications = await client.get("/applications")
            assert applications.status == 200
            assert "Applications" in applications.text
            assert "Application pipeline" in applications.text
            assert "Rogue" in applications.text
            assert "Accepted" in applications.text
            assert "Application Guide" in applications.text
            assert 'href="/world/application-guide"' in applications.text

            roster = await client.get("/characters")
            assert roster.status == 200
            assert "Accepted" in roster.text
            assert "Start a draft application" in roster.text

            response = await client.post(
                "/characters",
                body=urlencode(
                    {
                        "name": "Jubilee",
                        "summary": "Fireworks, mall instincts, and a very loud jacket.",
                        "avatar_url": "",
                    }
                ).encode(),
                headers=_FORM,
            )
            assert response.status == 302

            services = get_services()
            character = services.repo.get_character_by_slug(
                services.seed.community.id,
                "jubilee",
            )
            assert character.application_status == "draft"

            draft_view = await client.get("/applications")
            assert draft_view.status == 200
            assert "Jubilee" in draft_view.text
            assert "Draft" in draft_view.text
            assert "Submit application" in draft_view.text

            submit_response = await client.post(
                "/applications",
                body=urlencode(
                    {
                        "intent": "submit_application",
                        "character_slug": "jubilee",
                    }
                ).encode(),
                headers=_FORM,
            )
            assert submit_response.status == 302
            assert (
                services.repo.get_character_by_slug(
                    services.seed.community.id,
                    "jubilee",
                ).application_status
                == "submitted"
            )

            alex_membership = services.repo.get_membership_by_username(
                services.seed.community.id,
                "alex",
            )
            alex_user = services.repo.get_user(alex_membership.user_id)
            cyclops = services.repo.get_character_by_slug(
                services.seed.community.id,
                "cyclops",
            )
            alex_services = AppServices(
                services.repo,
                DemoSeed(services.seed.community, alex_user, alex_membership, cyclops),
            )
            assert any(
                item.label == "Application submitted" and item.title == "Jubilee"
                for item in alex_services.notifications().items
            )

            alex_app = create_app(debug=False, services=alex_services)
            async with TestClient(alex_app) as alex_client:
                review = await alex_client.get("/applications")
                assert review.status == 200
                assert "Review Queue" in review.text
                assert "Jubilee" in review.text
                assert "Accept" in review.text
                assert "Request revisions" in review.text

                accept_response = await alex_client.post(
                    "/applications",
                    body=urlencode(
                        {
                            "intent": "accept_application",
                            "character_slug": "jubilee",
                        }
                    ).encode(),
                    headers=_FORM,
                )
                assert accept_response.status == 302

                revision_response = await alex_client.post(
                    "/applications",
                    body=urlencode(
                        {
                            "intent": "request_revision",
                            "character_slug": "kitty-pryde",
                        }
                    ).encode(),
                    headers=_FORM,
                )
                assert revision_response.status == 302

            assert (
                services.repo.get_character_by_slug(
                    services.seed.community.id,
                    "jubilee",
                ).application_status
                == "accepted"
            )
            assert any(
                item.label == "Application accepted" and item.title == "Jubilee"
                for item in services.notifications().items
            )

            mira_membership = services.repo.get_membership_by_username(
                services.seed.community.id,
                "mira",
            )
            mira_user = services.repo.get_user(mira_membership.user_id)
            kitty = services.repo.get_character_by_slug(
                services.seed.community.id,
                "kitty-pryde",
            )
            assert kitty.application_status == "revision_requested"
            mira_services = AppServices(
                services.repo,
                DemoSeed(services.seed.community, mira_user, mira_membership, kitty),
            )
            assert any(
                item.label == "Revisions requested" and item.title == "Kitty Pryde"
                for item in mira_services.notifications().items
            )

            mira_app = create_app(debug=False, services=mira_services)
            async with TestClient(mira_app) as mira_client:
                mira_applications = await mira_client.get("/applications")
                assert mira_applications.status == 200
                assert "Resubmit application" in mira_applications.text

                resubmit_response = await mira_client.post(
                    "/applications",
                    body=urlencode(
                        {
                            "intent": "submit_application",
                            "character_slug": "kitty-pryde",
                        }
                    ).encode(),
                    headers=_FORM,
                )
                assert resubmit_response.status == 302
            assert (
                services.repo.get_character_by_slug(
                    services.seed.community.id,
                    "kitty-pryde",
                ).application_status
                == "submitted"
            )

    asyncio.run(run())


def test_wanted_ads_render_board_detail_and_character_hub() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            wanted = await client.get("/wanted")
            assert wanted.status == 200
            assert "Wanted" in wanted.text
            assert "Brotherhood rival from Rogue" in wanted.text
            assert "Human UN liaison for B-24 talks" in wanted.text
            assert 'href="/wanted/brotherhood-rival-for-rogue"' in wanted.text
            assert "United Nations" in wanted.text

            detail = await client.get("/wanted/brotherhood-rival-for-rogue")
            assert detail.status == 200
            assert "Rogue needs someone who remembers" in detail.text
            assert 'href="/characters/rogue"' in detail.text
            assert 'href="/world/factions"' in detail.text
            assert "Complicated Romance" in detail.text

            character = await client.get("/characters/rogue")
            assert character.status == 200
            assert "Plotter" in character.text
            assert "Tracker" in character.text
            assert "Brotherhood rival from Rogue" in character.text
            assert 'href="/wanted"' in character.text

            interest_response = await client.post(
                "/wanted/human-un-liaison-for-b24",
                body=b"intent=express_interest",
                headers=_FORM,
            )
            assert interest_response.status == 302

            interested = await client.get("/wanted/human-un-liaison-for-b24")
            assert interested.status == 200
            assert "Rogue is interested in this hook." in interested.text
            assert "Interested faces" in interested.text

            services = get_services()
            repo = services.repo
            community = services.seed.community
            wanted_ad = repo.get_wanted_ad_by_slug(community.id, "human-un-liaison-for-b24")
            rogue = repo.get_character_by_slug(community.id, "rogue")
            interest = repo.get_wanted_ad_interest_for_character(
                community.id,
                wanted_ad.id,
                rogue.id,
            )
            assert interest.character_id == rogue.id

            charlie_membership = repo.get_membership_by_username(community.id, "charlie")
            charlie_user = repo.get_user(charlie_membership.user_id)
            xavier = repo.get_character_by_slug(community.id, "charles-xavier")
            charlie_services = AppServices(
                repo,
                DemoSeed(community, charlie_user, charlie_membership, xavier),
            )
            inbox = charlie_services.notifications()
            assert inbox.unread_count == 1
            assert inbox.items[0].label == "Wanted interest"
            assert inbox.items[0].title == "Human UN liaison for B-24 talks"
            assert inbox.items[0].href == "/wanted/human-un-liaison-for-b24"

            charlie_app = create_app(debug=False, services=charlie_services)
            async with TestClient(charlie_app) as charlie_client:
                creator_view = await charlie_client.get("/wanted/human-un-liaison-for-b24")
                assert creator_view.status == 200
                assert "Reserve for Rogue" in creator_view.text

                reserve_response = await charlie_client.post(
                    "/wanted/human-un-liaison-for-b24",
                    body=f"intent=reserve_interest&interest_id={interest.id}".encode(),
                    headers=_FORM,
                )
                assert reserve_response.status == 302

                reserved_view = await charlie_client.get("/wanted/human-un-liaison-for-b24")
                assert reserved_view.status == 200
                assert "reserved" in reserved_view.text
                assert "Create reserve" in reserved_view.text
                assert "Reserve for Rogue" not in reserved_view.text

                reserve_create = await charlie_client.post(
                    "/wanted/human-un-liaison-for-b24",
                    body=f"intent=create_reserve&interest_id={interest.id}".encode(),
                    headers=_FORM,
                )
                assert reserve_create.status == 302

                reserve_view = await charlie_client.get("/wanted/human-un-liaison-for-b24")
                assert reserve_view.status == 200
                assert "Reserve created" in reserve_view.text
                assert "Reserves" in reserve_view.text
                assert (
                    "Reserved from wanted hook: Human UN liaison for B-24 talks"
                    in reserve_view.text
                )

            assert (
                repo.get_wanted_ad_interest_for_character(
                    community.id,
                    wanted_ad.id,
                    rogue.id,
                ).status
                == "reserved"
            )
            assert repo.get_wanted_ad(community.id, wanted_ad.id).status == "reserved"
            reserve = repo.get_character_reserve_for_wanted_interest(community.id, interest.id)
            assert reserve.character_id == rogue.id

            lane_inbox = AppServices(repo, services.seed).notifications()
            assert any(item.label == "Wanted reserved" for item in lane_inbox.items)
            assert any(item.label == "Reserve created" for item in lane_inbox.items)

            profile_app = create_app(debug=False, services=AppServices(repo, services.seed))
            async with TestClient(profile_app) as profile_client:
                profile = await profile_client.get("/characters/rogue")
                assert profile.status == 200
                assert "Reserves" in profile.text
                assert "Human UN liaison for B-24 talks" in profile.text
                casting = await profile_client.get("/casting")
                assert casting.status == 200
                assert "Casting Desk" in casting.text
                assert "Browsing as Rogue" in casting.text
                assert "Wanted With Interest" in casting.text
                assert "Active Reserves" in casting.text
                assert "Human UN liaison for B-24 talks" in casting.text
                assert "Rogue&#39;s Reserves" in casting.text

            missing = await client.get("/wanted/not-a-hook")
            assert missing.status == 404

    asyncio.run(run())


def test_character_plot_hooks_render_create_and_notify_interest() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            character = await client.get("/characters/rogue")
            assert character.status == 200
            assert "Old ghosts, new lines" in character.text
            assert "New plot hook" in character.text

            response = await client.post(
                "/characters/rogue",
                body=urlencode(
                    {
                        "intent": "create_plot_hook",
                        "plot_hook_title": "Coffee before the crisis",
                        "plot_hook_type": "scene",
                        "plot_hook_summary": "A quieter beat before the event pressure.",
                        "plot_hook_body": "Rogue wants a low-stakes conversation before B-24.",
                        "plot_hook_facets": "x-men",
                    }
                ).encode(),
                headers=_FORM,
            )
            assert response.status == 302

            detail = await client.get("/characters/rogue/hooks/coffee-before-the-crisis")
            assert detail.status == 200
            assert "Coffee before the crisis" in detail.text
            assert "You created this hook." in detail.text

            discover = await client.get("/discover?facets=x-men")
            assert discover.status == 200
            assert "Plot hooks" in discover.text
            assert "Coffee before the crisis" in discover.text

            services = get_services()
            outsider_services, _character_id = _outsider_services(services, prefix="hookfan")
            outsider_app = create_app(debug=False, services=outsider_services)
            async with TestClient(outsider_app) as outsider_client:
                outsider_detail = await outsider_client.get(
                    "/characters/rogue/hooks/coffee-before-the-crisis"
                )
                assert outsider_detail.status == 200
                assert "I'm interested as Hookfan Face" in outsider_detail.text

                interest = await outsider_client.post(
                    "/characters/rogue/hooks/coffee-before-the-crisis",
                    body=b"intent=express_interest",
                    headers=_FORM,
                )
                assert interest.status == 302

            owner_inbox = AppServices(services.repo, services.seed).notifications()
            assert any(item.label == "Plot hook interest" for item in owner_inbox.items)

            repo = services.repo
            community = services.seed.community
            hook = repo.get_character_plot_hook_by_slug(
                community.id,
                repo.get_character_by_slug(community.id, "rogue").id,
                "coffee-before-the-crisis",
            )
            interest = repo.list_character_plot_hook_interests(community.id, hook.id)[0]

            owner_app = create_app(debug=False, services=AppServices(repo, services.seed))
            async with TestClient(owner_app) as owner_client:
                creator_detail = await owner_client.get(
                    "/characters/rogue/hooks/coffee-before-the-crisis"
                )
                assert creator_detail.status == 200
                assert "Start plotting room" in creator_detail.text

                room_response = await owner_client.post(
                    "/characters/rogue/hooks/coffee-before-the-crisis",
                    body=f"intent=start_plotting_room&interest_id={interest.id}".encode(),
                    headers=_FORM,
                )
                assert room_response.status == 302

                room = repo.get_plotting_room_for_plot_hook_interest(community.id, interest.id)
                room_page = await owner_client.get(f"/plotting/{room.id}")
                assert room_page.status == 200
                assert "Coffee before the crisis: Hookfan Face" in room_page.text
                assert "Hookfan Face" in room_page.text

                plotting = await owner_client.get("/plotting")
                assert plotting.status == 200
                assert "Plotting Rooms" in plotting.text
                assert "Open plotting room" in plotting.text

                profile = await owner_client.get("/characters/rogue")
                assert profile.status == 200
                assert "Plotting Now" in profile.text
                assert "Coffee before the crisis: Hookfan Face" in profile.text

            assert (
                repo.get_character_plot_hook_interest(community.id, interest.id).status
                == "plotting"
            )

            outsider_inbox = outsider_services.notifications()
            assert any(item.label == "Plotting room" for item in outsider_inbox.items)

    asyncio.run(run())


def test_wanted_hooks_accept_prospective_character_interest() -> None:
    async def run() -> None:
        _app()
        services = get_services()
        faceless_services = _faceless_services(services, prefix="newface")
        faceless_app = create_app(debug=False, services=faceless_services)
        async with TestClient(faceless_app) as faceless_client:
            wanted = await faceless_client.get("/wanted/human-un-liaison-for-b24")
            assert wanted.status == 200
            assert "I'd create a new character for this" in wanted.text

            response = await faceless_client.post(
                "/wanted/human-un-liaison-for-b24",
                body=urlencode(
                    {
                        "intent": "express_prospective_interest",
                        "prospective_character_name": "Val Cooper",
                        "note": "I would app her as a UN pressure point.",
                    }
                ).encode(),
                headers=_FORM,
            )
            assert response.status == 302

        repo = services.repo
        community = services.seed.community
        wanted_ad = repo.get_wanted_ad_by_slug(community.id, "human-un-liaison-for-b24")
        newface_membership = repo.get_membership_by_username(community.id, "newface")
        prospective = repo.get_prospective_wanted_ad_interest_for_membership(
            community.id,
            wanted_ad.id,
            newface_membership.id,
        )
        assert prospective.character_id is None
        assert prospective.prospective_character_name == "Val Cooper"

        charlie_membership = repo.get_membership_by_username(community.id, "charlie")
        charlie_user = repo.get_user(charlie_membership.user_id)
        xavier = repo.get_character_by_slug(community.id, "charles-xavier")
        charlie_services = AppServices(
            repo,
            DemoSeed(community, charlie_user, charlie_membership, xavier),
        )
        creator_app = create_app(debug=False, services=charlie_services)
        async with TestClient(creator_app) as creator_client:
            creator_view = await creator_client.get("/wanted/human-un-liaison-for-b24")
            assert creator_view.status == 200
            assert "Val Cooper" in creator_view.text
            assert "I would app her as a UN pressure point." in creator_view.text
            assert "Reserve for Val Cooper" in creator_view.text

            reserve = await creator_client.post(
                "/wanted/human-un-liaison-for-b24",
                body=f"intent=reserve_interest&interest_id={prospective.id}".encode(),
                headers=_FORM,
            )
            assert reserve.status == 302

            reserved_view = await creator_client.get("/wanted/human-un-liaison-for-b24")
            assert reserved_view.status == 200
            assert "Create the character before making a reserve record." in reserved_view.text

        inbox = charlie_services.notifications()
        assert any(item.label == "Wanted interest" for item in inbox.items)

    asyncio.run(run())


def test_plotting_rooms_start_from_wanted_interest() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            response = await client.post(
                "/wanted/human-un-liaison-for-b24",
                body=b"intent=express_interest",
                headers=_FORM,
            )
            assert response.status == 302

        services = get_services()
        repo = services.repo
        community = services.seed.community
        wanted_ad = repo.get_wanted_ad_by_slug(community.id, "human-un-liaison-for-b24")
        rogue = repo.get_character_by_slug(community.id, "rogue")
        interest = repo.get_wanted_ad_interest_for_character(community.id, wanted_ad.id, rogue.id)
        charlie_membership = repo.get_membership_by_username(community.id, "charlie")
        charlie_user = repo.get_user(charlie_membership.user_id)
        xavier = repo.get_character_by_slug(community.id, "charles-xavier")
        charlie_services = AppServices(
            repo,
            DemoSeed(community, charlie_user, charlie_membership, xavier),
        )
        charlie_app = create_app(debug=False, services=charlie_services)
        async with TestClient(charlie_app) as charlie_client:
            creator_view = await charlie_client.get("/wanted/human-un-liaison-for-b24")
            assert creator_view.status == 200
            assert "Start plotting room" in creator_view.text

            room_response = await charlie_client.post(
                "/wanted/human-un-liaison-for-b24",
                body=f"intent=start_plotting_room&interest_id={interest.id}".encode(),
                headers=_FORM,
            )
            assert room_response.status == 302

            room = repo.get_plotting_room_for_wanted_interest(community.id, interest.id)
            room_page = await charlie_client.get(f"/plotting/{room.id}")
            assert room_page.status == 200
            assert "Human UN liaison for B-24 talks: Rogue" in room_page.text
            assert "Charles Xavier" in room_page.text
            assert "Rogue" in room_page.text

            plotting = await charlie_client.get("/plotting")
            assert plotting.status == 200
            assert "Interest Inbox" in plotting.text
            assert "Open plotting room" in plotting.text

        lane_inbox = AppServices(repo, services.seed).notifications()
        assert any(item.label == "Plotting room" for item in lane_inbox.items)
        assert repo.get_wanted_ad_interest(community.id, interest.id).status == "plotting"

    asyncio.run(run())


def test_thread_cards_jump_to_first_unread_then_latest() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        membership = services.seed.membership
        role = repo.get_role_by_slug(community.id, "member")
        outsider_user = repo.create_user("jump@example.com", "hash")
        outsider_membership = repo.create_membership(
            community.id,
            outsider_user.id,
            role.id,
            "jumpwriter",
            "Jump Writer",
        )
        outsider = repo.create_character(
            community.id,
            outsider_membership.id,
            "jump-face",
            "Jump Face",
        )
        board = repo.get_board_by_slug(community.id, "plotting")
        thread = repo.get_thread_by_slug(community.id, board.id, "open-thread-roster")
        repo.mark_thread_read(
            community.id,
            thread.id,
            membership.id,
            read_at="2026-01-01T00:00:00+00:00",
        )
        first_unread = repo.create_post(
            community.id,
            thread.id,
            outsider.id,
            "First unread beat.",
        )
        latest_unread = repo.create_post(
            community.id,
            thread.id,
            outsider.id,
            "Latest unread beat.",
        )
        repo.connection.execute(
            """
            UPDATE posts
            SET created_at = '2025-12-31T23:59:00+00:00',
                updated_at = '2025-12-31T23:59:00+00:00'
            WHERE community_id = ? AND thread_id = ? AND id NOT IN (?, ?)
            """,
            (community.id, thread.id, first_unread.id, latest_unread.id),
        )
        repo.connection.execute(
            """
            UPDATE posts
            SET created_at = '2026-01-01T00:00:01+00:00',
                updated_at = '2026-01-01T00:00:01+00:00'
            WHERE community_id = ? AND id = ?
            """,
            (community.id, first_unread.id),
        )
        repo.connection.execute(
            """
            UPDATE posts
            SET created_at = '2026-01-01T00:00:02+00:00',
                updated_at = '2026-01-01T00:00:02+00:00'
            WHERE community_id = ? AND id = ?
            """,
            (community.id, latest_unread.id),
        )
        repo.connection.execute(
            """
            UPDATE threads
            SET updated_at = '2026-01-01T00:00:02+00:00'
            WHERE community_id = ? AND id = ?
            """,
            (community.id, thread.id),
        )
        repo.connection.commit()

        async with TestClient(app) as client:
            board_response = await client.get("/boards/plotting")
            assert board_response.status == 200
            assert "First unread" in board_response.text
            assert (
                f"/boards/plotting/threads/open-thread-roster#post-{first_unread.id}"
                in board_response.text
            )
            assert (
                f"/boards/plotting/threads/open-thread-roster#post-{latest_unread.id}"
                not in board_response.text
            )

            thread_response = await client.get("/boards/plotting/threads/open-thread-roster")
            assert thread_response.status == 200

            board_after_read = await client.get("/boards/plotting")
            assert board_after_read.status == 200
            assert "Jump to latest" in board_after_read.text
            assert (
                f"/boards/plotting/threads/open-thread-roster#post-{latest_unread.id}"
                in board_after_read.text
            )

    asyncio.run(run())


def test_board_page_next_unread_jumps_to_first_unread_post() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        membership = services.seed.membership
        role = repo.get_role_by_slug(community.id, "member")
        outsider_user = repo.create_user("board-next@example.com", "hash")
        outsider_membership = repo.create_membership(
            community.id,
            outsider_user.id,
            role.id,
            "boardnext",
            "Board Next",
        )
        outsider = repo.create_character(
            community.id,
            outsider_membership.id,
            "board-next-face",
            "Board Next Face",
        )
        board = repo.create_board(community.id, "board-next", "Board Next")
        thread = repo.create_thread(
            community.id,
            board.id,
            outsider.id,
            "board-next-thread",
            "Board Next Thread",
        )
        repo.create_post(
            community.id,
            thread.id,
            outsider.id,
            "The board-level thread exists.",
        )
        repo.connection.execute(
            """
            UPDATE posts
            SET created_at = '2026-01-01T00:00:00+00:00',
                updated_at = '2026-01-01T00:00:00+00:00'
            WHERE community_id = ? AND thread_id = ?
            """,
            (community.id, thread.id),
        )
        repo.connection.execute(
            """
            UPDATE threads
            SET updated_at = '2026-01-01T00:00:00+00:00'
            WHERE community_id = ? AND id = ?
            """,
            (community.id, thread.id),
        )
        repo.connection.commit()
        repo.mark_thread_read(
            community.id,
            thread.id,
            membership.id,
            read_at="2026-01-01T00:00:00+00:00",
        )
        post = repo.create_post(
            community.id,
            thread.id,
            outsider.id,
            "The board-level next unread target.",
        )
        repo.connection.execute(
            """
            UPDATE posts
            SET created_at = '2026-01-01T00:00:01+00:00',
                updated_at = '2026-01-01T00:00:01+00:00'
            WHERE community_id = ? AND id = ?
            """,
            (community.id, post.id),
        )
        repo.connection.execute(
            """
            UPDATE threads
            SET updated_at = '2026-01-01T00:00:01+00:00'
            WHERE community_id = ? AND id = ?
            """,
            (community.id, thread.id),
        )
        repo.connection.commit()

        async with TestClient(app) as client:
            page = await client.get("/boards/board-next")
            assert page.status == 200
            assert "Next unread" in page.text
            assert f"/boards/board-next/threads/board-next-thread#post-{post.id}" in page.text

            thread_response = await client.get("/boards/board-next/threads/board-next-thread")
            assert thread_response.status == 200

            caught_up = await client.get("/boards/board-next")
            assert "Next unread" not in caught_up.text

    asyncio.run(run())


def test_reading_thread_clears_unread_marker_for_membership() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            board_before = await client.get("/boards/plotting")
            assert "new replies" in board_before.text

            thread = await client.get("/boards/plotting/threads/open-thread-roster")
            assert thread.status == 200

            board_after = await client.get("/boards/plotting")
            assert ">new replies<" not in board_after.text

    asyncio.run(run())


def test_thread_watch_toggle_controls_thread_notifications() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            thread = await client.get("/boards/plotting/threads/open-thread-roster")
            assert thread.status == 200
            assert "Watch thread" in thread.text

            watched = await client.post(
                "/boards/plotting/threads/open-thread-roster",
                body=b"intent=watch",
                headers=_FORM,
            )
            assert watched.status == 302

            watched_thread = await client.get("/boards/plotting/threads/open-thread-roster")
            assert "watching" in watched_thread.text
            assert "Unwatch thread" in watched_thread.text

            unwatched = await client.post(
                "/boards/plotting/threads/open-thread-roster",
                body=b"intent=unwatch",
                headers=_FORM,
            )
            assert unwatched.status == 302

            unwatched_thread = await client.get("/boards/plotting/threads/open-thread-roster")
            assert "Watch thread" in unwatched_thread.text
            assert "Unwatch thread" not in unwatched_thread.text

    asyncio.run(run())


def test_notifications_track_watched_thread_replies_and_open_read_state() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        services.watch_thread("plotting", "open-thread-roster")
        outsider_services, outsider_character_id = _outsider_services(services, prefix="notify")
        post = outsider_services.reply_to_thread(
            "plotting",
            "open-thread-roster",
            outsider_character_id,
            "A watched reply arrives.",
        )

        async with TestClient(app) as client:
            index = await client.get("/")
            assert index.status == 200
            assert "Notifications" in index.text
            assert "elbysodic-sidebar-count" in index.text

            notifications = await client.get("/notifications")
            assert notifications.status == 200
            assert "Watched thread" in notifications.text
            assert "A watched reply arrives." in notifications.text
            assert "Notify Face" in notifications.text
            assert "new" in notifications.text

            item = services.notifications().items[0]
            opened = await client.post(
                "/notifications",
                body=f"intent=open&notification_id={item.notification.id}".encode(),
                headers=_FORM,
            )
            assert opened.status == 302
            assert dict(opened.headers)["location"] == (
                f"/boards/plotting/threads/open-thread-roster#post-{post.id}"
            )
            assert services.viewer().unread_notification_count == 0

    asyncio.run(run())


def test_mentions_notify_character_owner_without_thread_watch() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        outsider_services, outsider_character_id = _outsider_services(services, prefix="mention")
        outsider_services.reply_to_thread(
            "plotting",
            "open-thread-roster",
            outsider_character_id,
            "Hey @Rogue, the plotting board needs you.",
        )

        async with TestClient(app) as client:
            thread = await client.get("/boards/plotting/threads/open-thread-roster")
            assert thread.status == 200
            assert 'href="/characters/rogue"' in thread.text
            assert 'data-mention-kind="character"' in thread.text

            notifications = await client.get("/notifications")
            assert notifications.status == 200
            assert "Mention" in notifications.text
            assert "Hey @Rogue, the plotting board needs you." in notifications.text
            assert "Mention Face" in notifications.text

    asyncio.run(run())


def test_writer_mentions_notify_membership_without_thread_watch() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        outsider_services, outsider_character_id = _outsider_services(
            services,
            prefix="writermention",
        )
        outsider_services.reply_to_thread(
            "plotting",
            "open-thread-roster",
            outsider_character_id,
            "Looping in @starlane for the OOC planning bit.",
        )

        async with TestClient(app) as client:
            thread = await client.get("/boards/plotting/threads/open-thread-roster")
            assert thread.status == 200
            assert 'href="/members/starlane"' in thread.text
            assert 'data-mention-kind="writer"' in thread.text

            notifications = await client.get("/notifications")
            assert notifications.status == 200
            assert "Mention" in notifications.text
            assert "Looping in @starlane for the OOC planning bit." in notifications.text
            assert "Writermention Face" in notifications.text

    asyncio.run(run())


def test_members_directory_and_profile_show_visible_community_cast() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        viewer = services.viewer()
        character = viewer.current_character
        assert character is not None
        private_board = repo.create_board(
            community.id,
            "private-lab",
            "Private Lab",
            is_private=True,
        )
        private_thread = repo.create_thread(
            community.id,
            private_board.id,
            character.id,
            "private-notes",
            "Private notes",
        )
        repo.create_post(
            community.id,
            private_thread.id,
            character.id,
            "Private activity should stay private.",
        )

        async with TestClient(app) as client:
            directory = await client.get("/members")
            assert directory.status == 200
            assert "Members" in directory.text
            assert "Lane" in directory.text
            assert "@starlane" in directory.text
            assert "Known for" in directory.text
            assert "Rogue" in directory.text
            assert "/members/starlane" in directory.text
            assert "Private activity should stay private." not in directory.text

            profile = await client.get("/members/starlane")
            assert profile.status == 200
            assert "Current face: Rogue" in profile.text
            assert "Known For" in profile.text
            assert "Current Roles" in profile.text
            assert "Collaborators" in profile.text
            assert "Visible posts" in profile.text
            assert "Open thread roster" in profile.text
            assert "/characters/rogue" in profile.text
            assert "Private notes" not in profile.text
            assert "Private activity should stay private." not in profile.text

            missing = await client.get("/members/nope")
            assert missing.status == 404

    asyncio.run(run())


def test_external_character_profile_links_to_owning_member_without_edit_controls() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        outsider_services, outsider_character_id = _outsider_services(
            services,
            prefix="castmate",
        )
        assert outsider_services is not None
        assert outsider_character_id > 0

        async with TestClient(app) as client:
            profile = await client.get("/characters/castmate-face")
            assert profile.status == 200
            assert "Castmate Face" in profile.text
            assert "/members/castmate" in profile.text
            assert "Edit character" not in profile.text
            assert "Set current face" not in profile.text
            assert "View writer" in profile.text

    asyncio.run(run())


def test_thread_page_links_previous_next_and_next_unread_threads() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        membership = services.seed.membership
        viewer = services.viewer()
        character = viewer.current_character
        assert character is not None
        board = repo.create_board(community.id, "navigation", "Navigation")
        newer = repo.create_thread(community.id, board.id, character.id, "newer", "Newer thread")
        current = repo.create_thread(
            community.id, board.id, character.id, "middle", "Middle thread"
        )
        older = repo.create_thread(community.id, board.id, character.id, "older", "Older thread")
        repo.create_post(community.id, newer.id, character.id, "Newer post.")
        repo.create_post(community.id, current.id, character.id, "Middle post.")
        older_post = repo.create_post(community.id, older.id, character.id, "Older post.")
        repo.connection.execute(
            """
            UPDATE threads
            SET updated_at = CASE id
                WHEN ? THEN '2026-01-01T00:03:00+00:00'
                WHEN ? THEN '2026-01-01T00:02:00+00:00'
                WHEN ? THEN '2026-01-01T00:01:00+00:00'
                ELSE updated_at
            END
            WHERE community_id = ? AND board_id = ?
            """,
            (newer.id, current.id, older.id, community.id, board.id),
        )
        repo.connection.commit()
        repo.mark_thread_read(community.id, newer.id, membership.id)
        role = repo.get_role_by_slug(community.id, "member")
        attention_user = repo.create_user("nav-attention@example.com", "hash")
        attention_membership = repo.create_membership(
            community.id,
            attention_user.id,
            role.id,
            "navattention",
            "Nav Attention",
        )
        attention_character = repo.create_character(
            community.id,
            attention_membership.id,
            "nav-attention-face",
            "Nav Attention Face",
        )
        repo.create_post(
            community.id,
            newer.id,
            attention_character.id,
            "A nearby scene needs a reply.",
        )

        async with TestClient(app) as client:
            page = await client.get("/boards/navigation/threads/middle")
            assert page.status == 200
            assert "Thread navigation" in page.text
            assert "Previous" in page.text
            assert "Previous unreplied" in page.text
            assert "Newer thread" in page.text
            assert "/boards/navigation/threads/newer" in page.text
            assert "Next" in page.text
            assert "Older thread" in page.text
            assert "Next unread" in page.text
            assert f"/boards/navigation/threads/older#post-{older_post.id}" in page.text

    asyncio.run(run())


def test_thread_page_bottom_next_unread_uses_visible_community_queue() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        membership = services.seed.membership
        viewer = services.viewer()
        character = viewer.current_character
        assert character is not None
        for existing_thread in repo.list_threads(community.id):
            repo.mark_thread_read(community.id, existing_thread.id, membership.id)
        current_board = repo.create_board(community.id, "current-nav", "Current Nav")
        unread_board = repo.create_board(community.id, "unread-nav", "Unread Nav")
        current = repo.create_thread(
            community.id,
            current_board.id,
            character.id,
            "current-scene",
            "Current scene",
        )
        unread = repo.create_thread(
            community.id,
            unread_board.id,
            character.id,
            "elsewhere-scene",
            "Elsewhere scene",
        )
        repo.create_post(community.id, current.id, character.id, "Current post.")
        unread_post = repo.create_post(
            community.id,
            unread.id,
            character.id,
            "Unread elsewhere.",
        )

        async with TestClient(app) as client:
            page = await client.get("/boards/current-nav/threads/current-scene")
            assert page.status == 200
            assert "Next unread" in page.text
            assert f"/boards/unread-nav/threads/elsewhere-scene#post-{unread_post.id}" in page.text

    asyncio.run(run())


def test_board_thread_filters_use_roster_participation() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        role = repo.get_role_by_slug(community.id, "member")
        outsider_user = repo.create_user("outsider@example.com", "hash")
        outsider_membership = repo.create_membership(
            community.id,
            outsider_user.id,
            role.id,
            "outsider",
            "Outsider",
        )
        outsider = repo.create_character(
            community.id,
            outsider_membership.id,
            "outsider-face",
            "Outsider Face",
        )
        board = repo.get_board_by_slug(community.id, "plotting")
        outside_thread = repo.create_thread(
            community.id,
            board.id,
            outsider.id,
            "outsider-plot",
            "Outsider plot",
        )
        repo.create_post(
            community.id,
            outside_thread.id,
            outsider.id,
            "A visible thread from another writer.",
        )

        async with TestClient(app) as client:
            all_threads = await client.get("/boards/plotting")
            assert all_threads.status == 200
            assert "Outsider plot" in all_threads.text
            assert "?filter=mine" in all_threads.text
            assert "?filter=unread" in all_threads.text
            assert "?filter=attention" in all_threads.text

            mine = await client.get("/boards/plotting?filter=mine")
            assert mine.status == 200
            assert "Open thread roster" in mine.text
            assert "Outsider plot" not in mine.text
            assert "mine" in mine.text

            pinned = await client.get("/boards/plotting?filter=pinned")
            assert pinned.status == 200
            assert "No pinned threads here yet." in pinned.text

            locked = await client.get("/boards/announcements?filter=locked")
            assert locked.status == 200
            assert "Welcome to the rebuild" in locked.text
            assert "locked" in locked.text

    asyncio.run(run())


def test_attention_surfaces_threads_where_someone_else_posted_last() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        role = repo.get_role_by_slug(community.id, "member")
        outsider_user = repo.create_user("attention@example.com", "hash")
        outsider_membership = repo.create_membership(
            community.id,
            outsider_user.id,
            role.id,
            "attention",
            "Attention",
        )
        outsider = repo.create_character(
            community.id,
            outsider_membership.id,
            "attention-face",
            "Attention Face",
        )
        board = repo.get_board_by_slug(community.id, "plotting")
        thread = repo.get_thread_by_slug(community.id, board.id, "open-thread-roster")
        repo.create_post(
            community.id,
            thread.id,
            outsider.id,
            "A different writer nudges the plot forward.",
        )

        async with TestClient(app) as client:
            index = await client.get("/")
            assert index.status == 200
            assert "Needs reply" in index.text
            assert "Open thread roster" in index.text
            assert "Attention Face" in index.text
            assert "A different writer nudges the plot forward." in index.text

            board_attention = await client.get("/boards/plotting?filter=attention")
            assert board_attention.status == 200
            assert "Open thread roster" in board_attention.text
            assert "needs reply" in board_attention.text

            thread_response = await client.get("/boards/plotting/threads/open-thread-roster")
            assert thread_response.status == 200

            cleared = await client.get("/boards/plotting?filter=attention")
            assert cleared.status == 200
            assert "No threads need a reply here." in cleared.text

            index_after_read = await client.get("/")
            assert "No threads need a reply right now." in index_after_read.text

    asyncio.run(run())


def test_my_threads_tracks_obligations_after_threads_are_read() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        role = repo.get_role_by_slug(community.id, "member")
        outsider_user = repo.create_user("obligation@example.com", "hash")
        outsider_membership = repo.create_membership(
            community.id,
            outsider_user.id,
            role.id,
            "obligation",
            "Obligation",
        )
        outsider = repo.create_character(
            community.id,
            outsider_membership.id,
            "obligation-face",
            "Obligation Face",
        )
        board = repo.get_board_by_slug(community.id, "plotting")
        thread = repo.get_thread_by_slug(community.id, board.id, "open-thread-roster")
        repo.create_post(
            community.id,
            thread.id,
            outsider.id,
            "A different writer puts the ball back in your court.",
        )

        async with TestClient(app) as client:
            read_thread = await client.get("/boards/plotting/threads/open-thread-roster")
            assert read_thread.status == 200

            dashboard = await client.get("/my/threads")
            assert dashboard.status == 200
            assert "My threads" in dashboard.text
            assert "Needs reply" in dashboard.text
            assert "Waiting on others" in dashboard.text
            assert "Started by me" in dashboard.text
            assert "All participated" in dashboard.text
            assert "Open thread roster" in dashboard.text
            assert "Obligation Face" in dashboard.text
            assert "elbysodic-thread-card__poster" in dashboard.text
            assert "elbysodic-scene-cast--stacked" in dashboard.text
            assert "elbysodic-thread-card__metrics" in dashboard.text
            assert "elbysodic-queue-history" in dashboard.text
            assert "needs reply" in dashboard.text
            assert "Sentinel drill after midnight" in dashboard.text
            assert "waiting" in dashboard.text
            assert "Welcome to the rebuild" not in dashboard.text
            assert "/boards/plotting/threads/open-thread-roster#post-" in dashboard.text

    asyncio.run(run())


def test_locked_seed_thread_suppresses_reply_composer() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        storm = next(
            character for character in services.viewer().roster if character.name == "Storm"
        )

        async with TestClient(app) as client:
            thread = await client.get("/boards/announcements/threads/welcome-to-the-rebuild")
            assert thread.status == 200
            assert "locked" in thread.text
            assert "Thread locked" in thread.text
            assert "Post reply" not in thread.text

            response = await client.post(
                "/boards/announcements/threads/welcome-to-the-rebuild",
                body=f"character_id={storm.id}&body=Staff+update.".encode(),
                headers=_FORM,
            )
            assert response.status == 200
            assert "cannot reply" in response.text

    asyncio.run(run())


def test_identity_route_changes_default_character_face() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        storm = next(
            character for character in services.viewer().roster if character.name == "Storm"
        )

        async with TestClient(app) as client:
            response = await client.post(
                "/identity",
                body=f"character_id={storm.id}&next=/".encode(),
                headers=_FORM,
            )
            assert response.status == 302

            index = await client.get("/")
            assert "Current face: Storm" in index.text

    asyncio.run(run())


def test_theme_stylesheet_is_loaded_and_theme_aware() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            index = await client.get("/")
            assert index.status == 200
            assert "/elbysodic-static/elbysodic-theme.css" in index.text

            stylesheet = await client.get("/elbysodic-static/elbysodic-theme.css")
            assert stylesheet.status == 200
            assert '[data-theme="light"]' in stylesheet.text
            assert '[data-theme="system"]' in stylesheet.text

    asyncio.run(run())


def test_character_roster_and_profiles_are_community_scoped() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            roster = await client.get("/characters")
            assert roster.status == 200
            assert "Your roster" in roster.text
            assert "Rogue" in roster.text
            assert "Storm" in roster.text
            assert "Magneto" in roster.text

            profile = await client.get("/characters/rogue")
            assert profile.status == 200
            assert "Power-stealing brawler with a careful heart." in profile.text
            assert "Sentinel drill after midnight" in profile.text
            assert "#post-" in profile.text

    asyncio.run(run())


def test_character_activity_center_tracks_identity_specific_threads() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            roster = await client.get("/characters")
            assert roster.status == 200
            assert "Needs Rogue" in roster.text
            assert "Waiting on Magneto" in roster.text
            assert "/my/threads?character=rogue" in roster.text

            profile = await client.get("/characters/rogue")
            assert profile.status == 200
            assert "Tracker" in profile.text
            assert "Open filtered queue" in profile.text
            assert "Open thread roster" in profile.text
            assert "Sentinel drill after midnight" in profile.text
            assert "needs reply" in profile.text
            assert "waiting" in profile.text

            filtered = await client.get("/my/threads?character=rogue")
            assert filtered.status == 200
            assert "Character threads" in filtered.text
            assert "Rogue · 1" in filtered.text
            assert "Open thread roster" in filtered.text
            assert "Sentinel drill after midnight" in filtered.text
            assert "Welcome to the rebuild" not in filtered.text

    asyncio.run(run())


def test_character_roster_can_create_new_default_character() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            response = await client.post(
                "/characters",
                body=(b"name=Jean+Grey&summary=Telepath+with+a+plot-problem.&make_default=on"),
                headers=_FORM,
            )
            assert response.status == 302

            profile = await client.get("/characters/jean-grey")
            assert profile.status == 200
            assert "Jean Grey" in profile.text
            assert "Telepath with a plot-problem." in profile.text

            index = await client.get("/")
            assert "Current face: Jean Grey" in index.text

    asyncio.run(run())


def test_character_profile_can_set_current_face() -> None:
    async def run() -> None:
        app = _app()

        async with TestClient(app) as client:
            response = await client.post(
                "/characters/storm",
                body=b"intent=set_default",
                headers=_FORM,
            )
            assert response.status == 302
            assert dict(response.headers)["location"] == "/characters/storm"

            profile = await client.get("/characters/storm")
            assert "current" in profile.text

            index = await client.get("/")
            assert "Current face: Storm" in index.text

    asyncio.run(run())


def test_character_profile_can_edit_owned_character() -> None:
    async def run() -> None:
        app = _app()

        async with TestClient(app) as client:
            response = await client.post(
                "/characters/rogue",
                body=(
                    b"intent=save"
                    b"&name=Rogue+Prime"
                    b"&avatar_url=https%3A%2F%2Fexample.test%2Frogue.png"
                    b"&post_profile_variant=poster"
                    b"&post_accent_style=line"
                    b"&post_border_style=double"
                    b"&post_title_style=mono"
                    b"&post_density=compact"
                    b"&summary=Still+carrying+the+whole+plot."
                ),
                headers=_FORM,
            )
            assert response.status == 302
            assert dict(response.headers)["location"] == "/characters/rogue-prime"

            profile = await client.get("/characters/rogue-prime")
            assert profile.status == 200
            assert "Rogue Prime" in profile.text
            assert "Still carrying the whole plot." in profile.text
            assert "https://example.test/rogue.png" in profile.text

            thread = await client.get("/boards/danger-room/threads/sentinel-drill")
            assert "Rogue Prime" in thread.text
            assert "elbysodic-post-profile--poster" in thread.text
            assert "elbysodic-post-accent--line" in thread.text
            assert "elbysodic-post-border--double" in thread.text
            assert "elbysodic-post-title--mono" in thread.text
            assert "elbysodic-post-density--compact" in thread.text
            assert "Rogue drops from the observation gantry" in thread.text

    asyncio.run(run())


def test_post_shell_inherits_identity_accent_from_facet_group() -> None:
    async def run() -> None:
        app = _app()

        async with TestClient(app) as client:
            thread = await client.get("/boards/danger-room/threads/moonlight-skirmish")

            assert thread.status == 200
            assert 'style="--elbysodic-character-accent: #60a5fa"' in thread.text
            assert 'style="--elbysodic-character-accent: #79a889"' in thread.text

    asyncio.run(run())


def test_studio_can_set_identity_accent_source() -> None:
    async def run() -> None:
        services = create_services(path=":memory:")
        repo = services.repo
        community = repo.get_community(services.seed.community.id)
        user = repo.get_user_by_email("moira@example.com")
        membership = repo.get_membership_by_username(community.id, "moira")
        character = repo.get_character_by_slug(community.id, "moira-mactaggert")
        admin_services = AppServices(
            repo,
            DemoSeed(community, user, membership, character),
        )
        app = create_app(debug=False, services=admin_services)
        species = repo.get_facet_group_by_slug(community.id, "species")

        async with TestClient(app) as client:
            response = await client.post(
                "/studio",
                body=f"identity_accent_facet_group_id={species.id}".encode(),
                headers=_FORM,
            )

            assert response.status == 302
            assert dict(response.headers)["location"] == "/studio"
            assert repo.get_community(community.id).identity_accent_facet_group_id == species.id

    asyncio.run(run())


def test_reply_uses_selected_character() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        storm = next(
            character for character in services.viewer().roster if character.name == "Storm"
        )

        async with TestClient(app) as client:
            response = await client.post(
                "/boards/plotting/threads/open-thread-roster",
                body=f"character_id={storm.id}&body=Lightning+answers.".encode(),
                headers=_FORM,
            )
            assert response.status == 302
            assert dict(response.headers)["location"].startswith(
                "/boards/plotting/threads/open-thread-roster#post-"
            )

            thread = await client.get("/boards/plotting/threads/open-thread-roster")
            assert "Lightning answers." in thread.text
            assert "Storm" in thread.text
            assert 'role="toolbar"' in thread.text
            assert 'aria-label="Bold"' in thread.text

    asyncio.run(run())


def test_thread_posts_render_safe_markup() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        storm = next(
            character for character in services.viewer().roster if character.name == "Storm"
        )
        body = (
            "**Lightning** answers.\n\n"
            "> Hold the line.\n\n"
            "[Briefing](https://example.test/briefing) "
            '<script>alert("x")</script>'
        )

        async with TestClient(app) as client:
            response = await client.post(
                "/boards/plotting/threads/open-thread-roster",
                body=urlencode({"character_id": storm.id, "body": body}).encode(),
                headers=_FORM,
            )
            assert response.status == 302

            thread = await client.get("/boards/plotting/threads/open-thread-roster")
            assert "<strong>Lightning</strong> answers." in thread.text
            assert "<blockquote><p>Hold the line.</p></blockquote>" in thread.text
            assert 'href="https://example.test/briefing"' in thread.text
            assert '<script>alert("x")</script>' not in thread.text
            assert "&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;" in thread.text

    asyncio.run(run())


def test_writer_can_edit_own_post_with_safe_markup() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        storm = next(
            character for character in services.viewer().roster if character.name == "Storm"
        )

        async with TestClient(app) as client:
            created = await client.post(
                "/boards/plotting/threads/open-thread-roster",
                body=urlencode({"character_id": storm.id, "body": "Original typo."}).encode(),
                headers=_FORM,
            )
            assert created.status == 302
            post_id = dict(created.headers)["location"].split("#post-")[1]

            edit_form = await client.get(
                f"/boards/plotting/threads/open-thread-roster/posts/{post_id}/edit"
            )
            assert edit_form.status == 200
            assert "Edit post" in edit_form.text
            assert "Original typo." in edit_form.text
            assert "edit-post-composer-config" in edit_form.text
            assert 'role="toolbar"' in edit_form.text
            assert 'aria-label="Bold"' in edit_form.text

            edited = await client.post(
                f"/boards/plotting/threads/open-thread-roster/posts/{post_id}/edit",
                body=urlencode(
                    {
                        "body": (
                            '**Updated** line.\n\n> Edited safely.\n\n<script>alert("x")</script>'
                        )
                    }
                ).encode(),
                headers=_FORM,
            )
            assert edited.status == 302
            assert dict(edited.headers)["location"] == (
                f"/boards/plotting/threads/open-thread-roster#post-{post_id}"
            )

            thread = await client.get("/boards/plotting/threads/open-thread-roster")
            assert "Original typo." not in thread.text
            assert "<strong>Updated</strong> line." in thread.text
            assert "<blockquote><p>Edited safely.</p></blockquote>" in thread.text
            assert '<script>alert("x")</script>' not in thread.text
            assert "&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;" in thread.text
            assert "edited" in thread.text
            assert f"/posts/{post_id}/revisions" in thread.text
            assert f"/posts/{post_id}/edit" in thread.text

            revisions = await client.get(
                f"/boards/plotting/threads/open-thread-roster/posts/{post_id}/revisions"
            )
            assert revisions.status == 200
            assert "Post history" in revisions.text
            assert "Revision 1" in revisions.text
            assert "Original typo." in revisions.text
            assert "**Updated** line." in revisions.text
            assert "/members/starlane" in revisions.text

    asyncio.run(run())


def test_noop_post_edit_does_not_create_revision() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        storm = next(
            character for character in services.viewer().roster if character.name == "Storm"
        )

        async with TestClient(app) as client:
            created = await client.post(
                "/boards/plotting/threads/open-thread-roster",
                body=urlencode({"character_id": storm.id, "body": "Already polished."}).encode(),
                headers=_FORM,
            )
            assert created.status == 302
            post_id = int(dict(created.headers)["location"].split("#post-")[1])
            original = repo.get_post(services.seed.community.id, post_id)

            edited = await client.post(
                f"/boards/plotting/threads/open-thread-roster/posts/{post_id}/edit",
                body=urlencode({"body": "Already polished."}).encode(),
                headers=_FORM,
            )
            assert edited.status == 302

            unchanged = repo.get_post(services.seed.community.id, post_id)
            assert unchanged.updated_at == original.updated_at
            assert repo.list_post_revisions(services.seed.community.id, post_id) == []

    asyncio.run(run())


def test_writer_cannot_edit_someone_elses_post() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        role = repo.get_role_by_slug(community.id, "member")
        outsider_user = repo.create_user("not-yours@example.com", "hash")
        outsider_membership = repo.create_membership(
            community.id,
            outsider_user.id,
            role.id,
            "notyours",
            "Not Yours",
        )
        outsider = repo.create_character(
            community.id,
            outsider_membership.id,
            "not-yours-face",
            "Not Yours Face",
        )
        board = repo.get_board_by_slug(community.id, "plotting")
        thread = repo.get_thread_by_slug(community.id, board.id, "open-thread-roster")
        outsider_post = repo.create_post(
            community.id,
            thread.id,
            outsider.id,
            "This belongs to another writer.",
        )

        async with TestClient(app) as client:
            edit_form = await client.get(
                f"/boards/plotting/threads/open-thread-roster/posts/{outsider_post.id}/edit"
            )
            assert edit_form.status == 403

            edited = await client.post(
                f"/boards/plotting/threads/open-thread-roster/posts/{outsider_post.id}/edit",
                body=urlencode({"body": "Trying to overwrite."}).encode(),
                headers=_FORM,
            )
            assert edited.status == 403
            assert repo.get_post(community.id, outsider_post.id).body == (
                "This belongs to another writer."
            )
            assert repo.list_post_revisions(community.id, outsider_post.id) == []

    asyncio.run(run())


def test_locked_threads_still_allow_editing_own_existing_post() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        board = repo.get_board_by_slug(community.id, "announcements")
        thread = repo.get_thread_by_slug(community.id, board.id, "welcome-to-the-rebuild")
        post = repo.list_posts(community.id, thread.id)[0]

        async with TestClient(app) as client:
            response = await client.post(
                f"/boards/announcements/threads/welcome-to-the-rebuild/posts/{post.id}/edit",
                body=urlencode({"body": "Updated staff note."}).encode(),
                headers=_FORM,
            )
            assert response.status == 302

            restored = await client.get("/boards/announcements/threads/welcome-to-the-rebuild")
            assert "Updated staff note." in restored.text
            assert "Thread locked" in restored.text

    asyncio.run(run())


def test_staff_can_pin_and_lock_threads() -> None:
    async def run() -> None:
        app, repo, community, thread = _moderation_app(is_admin=True)

        async with TestClient(app) as client:
            page = await client.get("/boards/ic/threads/moderation-queue")
            assert page.status == 200
            assert "Staff controls" in page.text
            assert "Pin thread" in page.text
            assert "Lock thread" in page.text
            assert "Move thread" in page.text

            pinned = await client.post(
                "/boards/ic/threads/moderation-queue",
                body=b"intent=pin",
                headers=_FORM,
            )
            assert pinned.status == 302
            assert repo.get_thread(community.id, thread.id).is_pinned is True

            locked = await client.post(
                "/boards/ic/threads/moderation-queue",
                body=b"intent=lock",
                headers=_FORM,
            )
            assert locked.status == 302
            assert repo.get_thread(community.id, thread.id).is_locked is True

            updated = await client.get("/boards/ic/threads/moderation-queue")
            assert "pinned" in updated.text
            assert "locked" in updated.text
            assert "Unpin thread" in updated.text
            assert "Unlock thread" in updated.text

            unpinned = await client.post(
                "/boards/ic/threads/moderation-queue",
                body=b"intent=unpin",
                headers=_FORM,
            )
            assert unpinned.status == 302
            assert repo.get_thread(community.id, thread.id).is_pinned is False

            unlocked = await client.post(
                "/boards/ic/threads/moderation-queue",
                body=b"intent=unlock",
                headers=_FORM,
            )
            assert unlocked.status == 302
            assert repo.get_thread(community.id, thread.id).is_locked is False

    asyncio.run(run())


def test_staff_can_move_thread_without_rewriting_thread_history() -> None:
    async def run() -> None:
        app, repo, community, thread = _moderation_app(is_admin=True)
        target_board = repo.get_board_by_slug(community.id, "archive")
        original = repo.get_thread(community.id, thread.id)
        post = repo.list_posts(community.id, thread.id)[0]
        repo.create_post_revision(
            community.id,
            post.id,
            post.author_membership_id,
            "Old wording.",
            post.body,
        )
        repo.mark_thread_read(
            community.id,
            thread.id,
            post.author_membership_id,
            read_at="2026-01-01T00:00:00+00:00",
        )

        async with TestClient(app) as client:
            response = await client.post(
                "/boards/ic/threads/moderation-queue",
                body=f"intent=move&target_board_id={target_board.id}".encode(),
                headers=_FORM,
            )
            assert response.status == 302
            assert dict(response.headers)["location"] == "/boards/archive/threads/moderation-queue"

            moved = repo.get_thread(community.id, thread.id)
            assert moved.board_id == target_board.id
            assert moved.slug == original.slug
            assert moved.title == original.title
            assert moved.updated_at == original.updated_at
            assert [restored.body for restored in repo.list_posts(community.id, moved.id)] == [
                "A thread ready for staff tools."
            ]
            assert len(repo.list_post_revisions(community.id, post.id)) == 1
            assert repo.get_thread_read_at(community.id, moved.id, post.author_membership_id) == (
                "2026-01-01T00:00:00+00:00"
            )

            new_page = await client.get("/boards/archive/threads/moderation-queue")
            assert new_page.status == 200
            assert "Archive" in new_page.text
            assert "A thread ready for staff tools." in new_page.text

    asyncio.run(run())


def test_regular_members_cannot_manage_thread_lifecycle() -> None:
    async def run() -> None:
        app, repo, community, thread = _moderation_app(is_admin=False)
        target_board = repo.get_board_by_slug(community.id, "archive")

        async with TestClient(app) as client:
            page = await client.get("/boards/ic/threads/moderation-queue")
            assert page.status == 200
            assert "Staff controls" not in page.text

            lock_response = await client.post(
                "/boards/ic/threads/moderation-queue",
                body=b"intent=lock",
                headers=_FORM,
            )
            assert lock_response.status == 403

            move_response = await client.post(
                "/boards/ic/threads/moderation-queue",
                body=f"intent=move&target_board_id={target_board.id}".encode(),
                headers=_FORM,
            )
            assert move_response.status == 403
            assert repo.get_thread(community.id, thread.id).is_locked is False
            assert repo.get_thread(community.id, thread.id).is_pinned is False
            assert repo.get_thread(community.id, thread.id).board_id != target_board.id

    asyncio.run(run())


def test_start_thread_creates_opening_post_as_selected_character() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        roster = services.viewer().roster
        magneto = next(character for character in roster if character.name == "Magneto")
        xavier = services.repo.get_character_by_slug(
            services.seed.community.id,
            "charles-xavier",
        )

        async with TestClient(app) as client:
            form = await client.get("/boards/danger-room/threads/new")
            assert form.status == 200
            assert "Start thread" in form.text
            assert "elbysodicComposer" in form.text
            assert "thread-composer-config" in form.text
            assert "Posting as" in form.text
            assert "Scene summary" in form.text
            assert "Tag cast" in form.text
            assert "elbysodicMentionPicker" in form.text
            assert "/mentionables/search" in form.text
            assert (
                re.search(
                    rf'<input type="checkbox"\s+name="participant_ids"\s+value="{magneto.id}"',
                    form.text,
                )
                is None
            )
            assert "Open to join" in form.text
            assert "Posting order" in form.text
            assert 'role="toolbar"' in form.text
            assert 'aria-label="Bold"' in form.text
            assert 'aria-label="Italic"' in form.text
            assert 'aria-label="Quote"' in form.text
            assert 'aria-label="Link"' in form.text
            assert "Power-stealing brawler with a careful heart." in form.text

            response = await client.post(
                "/boards/danger-room/threads/new",
                body=urlencode(
                    {
                        "character_id": magneto.id,
                        "participant_ids": [xavier.id],
                        "title": "Metal and Memory",
                        "status": "open",
                        "location": "Sublevel 3",
                        "timeline": "Before breakfast",
                        "summary": "Magneto tags Xavier into an unreasonable simulation.",
                        "posting_mode": "posting_order",
                        "body": "Magneto sets the simulation to unfair.",
                    },
                    doseq=True,
                ).encode(),
                headers=_FORM,
            )
            assert response.status == 302
            assert dict(response.headers)["location"].startswith(
                "/boards/danger-room/threads/metal-and-memory#post-"
            )

            thread = await client.get("/boards/danger-room/threads/metal-and-memory")
            assert thread.status == 200
            assert "Metal and Memory" in thread.text
            assert "Magneto sets the simulation to unfair." in thread.text
            assert "Magneto" in thread.text
            assert "Scene details" in thread.text
            assert "open to join" in thread.text
            assert "Sublevel 3" in thread.text
            assert "Before breakfast" in thread.text
            assert "Magneto tags Xavier into an unreasonable simulation." in thread.text
            assert "/characters/charles-xavier" in thread.text

            board = await client.get("/boards/danger-room")
            assert "Metal and Memory" in board.text
            assert "Started by" in board.text
            assert "open to join" in board.text
            assert "Sublevel 3" in board.text
            assert "Latest" in board.text
            assert "/members/starlane" in board.text

    asyncio.run(run())


def test_mentionable_search_supports_character_and_writer_scopes() -> None:
    async def run() -> None:
        app = _app()

        async with TestClient(app) as client:
            cast = await client.get("/mentionables/search?q=char&scope=cast")
            assert cast.status == 200
            cast_payload = json.loads(cast.body)
            assert cast_payload["items"][0]["kind"] == "character"
            assert cast_payload["items"][0]["handle"] == "charles-xavier"

            own_roster = await client.get("/mentionables/search?q=rogue&scope=cast")
            assert own_roster.status == 200
            assert json.loads(own_roster.body)["items"] == []

            ooc = await client.get("/mentionables/search?q=star&scope=ooc")
            assert ooc.status == 200
            ooc_payload = json.loads(ooc.body)
            assert ooc_payload["items"][0]["kind"] == "writer"
            assert ooc_payload["items"][0]["handle"] == "starlane"

    asyncio.run(run())


def test_open_thread_can_be_joined_as_active_face() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        plotting = repo.get_board_by_slug(community.id, "plotting")
        xavier = repo.get_character_by_slug(community.id, "charles-xavier")
        thread = repo.create_thread(
            community.id,
            plotting.id,
            xavier.id,
            "telepathy-office-hours",
            "Telepathy office hours",
            status="open",
            summary="Charles opens the study for whoever needs to talk.",
        )
        repo.create_post(
            community.id,
            thread.id,
            xavier.id,
            "Charles leaves the study door open and waits.",
        )

        async with TestClient(app) as client:
            page = await client.get("/boards/plotting/threads/telepathy-office-hours")
            assert page.status == 200
            assert "Join as Rogue" in page.text
            assert "watching" not in page.text

            joined = await client.post(
                "/boards/plotting/threads/telepathy-office-hours",
                body=b"intent=join_scene",
                headers=_FORM,
            )
            assert joined.status == 302

            assert {
                character.slug
                for character in repo.list_thread_participants(community.id, thread.id)
            } == {"charles-xavier", "rogue"}
            assert repo.is_thread_watched(community.id, thread.id, services.seed.membership.id)

            joined_page = await client.get("/boards/plotting/threads/telepathy-office-hours")
            assert joined_page.status == 200
            assert "Join as Rogue" not in joined_page.text
            assert 'aria-label="Rogue"' in joined_page.text
            assert "watching" in joined_page.text

    asyncio.run(run())


def test_non_open_threads_do_not_show_join_action() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        danger_room = repo.get_board_by_slug(community.id, "danger-room")
        xavier = repo.get_character_by_slug(community.id, "charles-xavier")
        thread = repo.create_thread(
            community.id,
            danger_room.id,
            xavier.id,
            "closed-practice",
            "Closed practice",
            status="active",
        )
        repo.create_post(
            community.id,
            thread.id,
            xavier.id,
            "This practice has already started.",
        )

        async with TestClient(app) as client:
            page = await client.get("/boards/danger-room/threads/closed-practice")
            assert page.status == 200
            assert "Join as Rogue" not in page.text

    asyncio.run(run())


def test_thread_view_hides_unspecified_scene_metadata() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        role = repo.get_role_by_slug(community.id, "member")
        author_user = repo.create_user("quiet-scene-author@example.com", "hash")
        author_membership = repo.create_membership(
            community.id,
            author_user.id,
            role.id,
            "quietauthor",
            "Quiet Author",
        )
        author = repo.create_character(
            community.id,
            author_membership.id,
            "quiet-author-face",
            "Quiet Author Face",
        )
        board = repo.get_board_by_slug(community.id, "danger-room")
        thread = repo.create_thread(
            community.id,
            board.id,
            author.id,
            "quiet-default-scene",
            "Quiet default scene",
        )
        repo.create_post(
            community.id,
            thread.id,
            author.id,
            "Rogue waits for someone else to make the first bad decision.",
        )

        async with TestClient(app) as client:
            page = await client.get("/boards/danger-room/threads/quiet-default-scene")
            assert page.status == 200
            assert "Scene details" in page.text
            assert "Scene management" not in page.text
            assert "Unspecified" not in page.text
            assert "Freeform" not in page.text
            assert "open to join" not in page.text

    asyncio.run(run())


def test_thread_starter_can_manage_scene_cast() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        repo = services.repo
        community = services.seed.community
        board = repo.get_board_by_slug(community.id, "danger-room")
        thread = repo.get_thread_by_slug(community.id, board.id, "sentinel-drill")
        kitty = repo.get_character_by_slug(community.id, "kitty-pryde")
        xavier = repo.get_character_by_slug(community.id, "charles-xavier")

        async with TestClient(app) as client:
            page = await client.get("/boards/danger-room/threads/sentinel-drill")
            assert page.status == 200
            assert "Scene management" in page.text
            assert "Tag cast" in page.text
            assert "Charles Xavier" in page.text

            response = await client.post(
                "/boards/danger-room/threads/sentinel-drill",
                body=urlencode(
                    {
                        "intent": "scene",
                        "status": "paused",
                        "posting_mode": "freeform",
                        "location": "West lawn",
                        "timeline": "After inspection",
                        "summary": "Rogue calls a timeout before the simulation gets personal.",
                        "participant_ids": str(kitty.id),
                    }
                ).encode(),
                headers=_FORM,
            )
            assert response.status in {302, 303}

            updated = repo.get_thread(community.id, thread.id)
            assert updated.status == "paused"
            assert updated.location == "West lawn"
            assert updated.timeline == "After inspection"
            assert updated.summary == "Rogue calls a timeout before the simulation gets personal."
            assert updated.posting_mode == "freeform"
            assert {
                character.slug
                for character in repo.list_thread_participants(community.id, thread.id)
            } == {"rogue", "kitty-pryde"}
            assert xavier.id not in repo.list_thread_participant_ids(community.id, thread.id)

            rendered = await client.get("/boards/danger-room/threads/sentinel-drill")
            assert rendered.status == 200
            assert "paused" in rendered.text
            assert "West lawn" in rendered.text
            assert "After inspection" in rendered.text
            assert "Rogue calls a timeout before the simulation gets personal." in rendered.text

    asyncio.run(run())


def test_file_backed_services_persist_created_threads(tmp_path: Path) -> None:
    db_path = tmp_path / "elbysodic.sqlite3"
    services = create_services(path=db_path)
    viewer = services.viewer()
    assert viewer.current_character is not None

    thread = services.start_thread(
        board_slug="danger-room",
        character_id=viewer.current_character.id,
        title="Persistent Moonlight",
        body="This scene survives the next service boot.",
    )

    restarted = create_services(path=db_path)
    restored = restarted.read_thread("danger-room", thread.slug)
    assert restored.thread.title == "Persistent Moonlight"
    assert [post.post.body for post in restored.posts] == [
        "This scene survives the next service boot."
    ]
    assert len(restarted.viewer().roster) == 3


def test_composer_pages_point_empty_roster_to_character_setup() -> None:
    async def run() -> None:
        connection = connect(check_same_thread=False)
        create_schema(connection)
        repo = ForumRepository(connection)
        community = repo.seed_default_community("Empty Roster")
        role = repo.create_role(community.id, "member", "Member")
        user = repo.create_user("empty@example.com", "hash")
        membership = repo.create_membership(
            community.id,
            user.id,
            role.id,
            "empty",
            "Empty",
        )
        author_user = repo.create_user("author@example.com", "hash")
        author_membership = repo.create_membership(
            community.id,
            author_user.id,
            role.id,
            "author",
            "Author",
        )
        author = repo.create_character(
            community.id,
            author_membership.id,
            "author-face",
            "Author Face",
        )
        board = repo.create_board(community.id, "ic", "In Character")
        thread = repo.create_thread(
            community.id,
            board.id,
            author.id,
            "open-scene",
            "Open Scene",
        )
        repo.create_post(community.id, thread.id, author.id, "A scene exists.")
        services = AppServices(
            repo,
            DemoSeed(
                community=community,
                user=user,
                membership=membership,
                default_character=None,
            ),
        )

        app = create_app(debug=False, services=services)
        async with TestClient(app) as client:
            index = await client.get("/")
            assert index.status == 200
            assert "Create your first character" in index.text

            new_thread = await client.get(f"/boards/{board.slug}/threads/new")
            assert new_thread.status == 200
            assert "Create a character first" in new_thread.text
            assert "Open roster" in new_thread.text
            assert "elbysodicComposer" not in new_thread.text

            reply = await client.get(f"/boards/{board.slug}/threads/{thread.slug}")
            assert reply.status == 200
            assert "Create a character first" in reply.text
            assert "A scene exists." in reply.text

    asyncio.run(run())


def test_app_contract_check_passes() -> None:
    _app().check()


def _moderation_app(
    *,
    is_admin: bool,
) -> tuple[App, ForumRepository, Community, Thread]:
    connection = connect(check_same_thread=False)
    create_schema(connection)
    repo = ForumRepository(connection)
    community = repo.seed_default_community("Moderation Test")
    role = repo.create_role(
        community.id,
        "staff" if is_admin else "member",
        "Staff" if is_admin else "Member",
        is_admin=is_admin,
    )
    user = repo.create_user("moderator@example.com", "hash")
    membership = repo.create_membership(
        community.id,
        user.id,
        role.id,
        "modlane" if is_admin else "memberlane",
        "Mod Lane" if is_admin else "Member Lane",
    )
    character = repo.create_character(
        community.id,
        membership.id,
        "moderator-face" if is_admin else "member-face",
        "Moderator Face" if is_admin else "Member Face",
        make_default=True,
    )
    board = repo.create_board(community.id, "ic", "In Character")
    repo.create_board(community.id, "archive", "Archive", sort_order=20)
    thread = repo.create_thread(
        community.id,
        board.id,
        character.id,
        "moderation-queue",
        "Moderation Queue",
    )
    repo.create_post(community.id, thread.id, character.id, "A thread ready for staff tools.")
    services = AppServices(
        repo,
        DemoSeed(
            community=community,
            user=user,
            membership=repo.get_membership(community.id, membership.id),
            default_character=character,
        ),
    )
    return create_app(debug=False, services=services), repo, community, thread
