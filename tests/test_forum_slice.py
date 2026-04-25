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
        rf'<a class="[^"]*elbysodic-sidebar-link[^"]*" href="/boards/{re.escape(board_slug)}">'
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
            assert _sidebar_board_count(index.text, "plotting") == 1

            board = await client.get("/boards/plotting")
            assert board.status == 200
            assert "Open thread roster" in board.text
            assert "Started by" in board.text
            assert "Latest" in board.text
            assert "First unread" in board.text
            assert "#post-" in board.text
            assert "new replies" in board.text
            assert "Next unread" in board.text
            assert "Magneto" in board.text

            thread = await client.get("/boards/plotting/threads/open-thread-roster")
            assert thread.status == 200
            assert 'id="post-' in thread.text
            assert "Drop your available characters here" in thread.text
            assert "Rogue" in thread.text
            assert "Magneto" in thread.text
            assert "/members/starlane" in thread.text
            assert "caught up" in thread.text
            assert _sidebar_board_count(thread.text, "plotting") == 0

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
            assert "Rogue" in directory.text
            assert "/members/starlane" in directory.text
            assert "Private activity should stay private." not in directory.text

            profile = await client.get("/members/starlane")
            assert profile.status == 200
            assert "Current face: Rogue" in profile.text
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

        async with TestClient(app) as client:
            page = await client.get("/boards/navigation/threads/middle")
            assert page.status == 200
            assert "Thread navigation" in page.text
            assert "Previous" in page.text
            assert "Newer thread" in page.text
            assert "/boards/navigation/threads/newer" in page.text
            assert "Next" in page.text
            assert "Older thread" in page.text
            assert "Next unread" in page.text
            assert f"/boards/navigation/threads/older#post-{older_post.id}" in page.text

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
            assert "Active threads" in profile.text
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
            assert "Rogue drops from the observation gantry" in thread.text

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
