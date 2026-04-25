from __future__ import annotations

import asyncio
from pathlib import Path

from chirp.testing import TestClient

from elbysodic.services import create_services
from elbysodic.web import create_app
from elbysodic.web.state import get_services

_FORM = {"Content-Type": "application/x-www-form-urlencoded"}


def _app():
    return create_app(debug=False, services=create_services(path=":memory:"))


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
            assert "unread" in index.text
            assert "writer starlane" in index.text

            board = await client.get("/boards/plotting")
            assert board.status == 200
            assert "Open thread roster" in board.text
            assert "Started by" in board.text
            assert "Latest" in board.text
            assert "Jump to post" in board.text
            assert "#post-" in board.text
            assert "unread" in board.text
            assert "Magneto" in board.text

            thread = await client.get("/boards/plotting/threads/open-thread-roster")
            assert thread.status == 200
            assert 'id="post-' in thread.text
            assert "Drop your available characters here" in thread.text
            assert "Rogue" in thread.text
            assert "Magneto" in thread.text
            assert "writer starlane" in thread.text

    asyncio.run(run())


def test_reading_thread_clears_unread_marker_for_membership() -> None:
    async def run() -> None:
        app = _app()
        async with TestClient(app) as client:
            board_before = await client.get("/boards/plotting")
            assert "unread" in board_before.text

            thread = await client.get("/boards/plotting/threads/open-thread-roster")
            assert thread.status == 200

            board_after = await client.get("/boards/plotting")
            assert "unread" not in board_after.text

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

    asyncio.run(run())


def test_start_thread_creates_opening_post_as_selected_character() -> None:
    async def run() -> None:
        app = _app()
        services = get_services()
        magneto = next(
            character for character in services.viewer().roster if character.name == "Magneto"
        )

        async with TestClient(app) as client:
            form = await client.get("/boards/danger-room/threads/new")
            assert form.status == 200
            assert "Start thread" in form.text
            assert "elbysodicComposer" in form.text
            assert "thread-composer-config" in form.text
            assert "Posting as" in form.text
            assert "Power-stealing brawler with a careful heart." in form.text

            response = await client.post(
                "/boards/danger-room/threads/new",
                body=(
                    f"character_id={magneto.id}"
                    "&title=Metal+and+Memory"
                    "&body=Magneto+sets+the+simulation+to+unfair."
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

            board = await client.get("/boards/danger-room")
            assert "Metal and Memory" in board.text
            assert "Started by" in board.text
            assert "Latest" in board.text
            assert "writer starlane" in board.text

    asyncio.run(run())


def test_file_backed_services_persist_created_threads(tmp_path: Path) -> None:
    db_path = tmp_path / "elbysodic.sqlite3"
    services = create_services(path=db_path)
    viewer = services.viewer()

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


def test_app_contract_check_passes() -> None:
    _app().check()
