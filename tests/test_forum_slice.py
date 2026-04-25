from __future__ import annotations

import asyncio
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
            assert ">unread<" not in board_after.text

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
            assert "Needs attention" in index.text
            assert "Open thread roster" in index.text
            assert "Attention Face" in index.text
            assert "A different writer nudges the plot forward." in index.text

            board_attention = await client.get("/boards/plotting?filter=attention")
            assert board_attention.status == 200
            assert "Open thread roster" in board_attention.text
            assert "attention" in board_attention.text

            thread_response = await client.get("/boards/plotting/threads/open-thread-roster")
            assert thread_response.status == 200

            cleared = await client.get("/boards/plotting?filter=attention")
            assert cleared.status == 200
            assert "No threads need your attention here." in cleared.text

            index_after_read = await client.get("/")
            assert "No threads need your attention right now." in index_after_read.text

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
            assert "Welcome to the rebuild" in dashboard.text
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
            assert "writer starlane" in revisions.text

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


def test_regular_members_cannot_manage_thread_lifecycle() -> None:
    async def run() -> None:
        app, repo, community, thread = _moderation_app(is_admin=False)

        async with TestClient(app) as client:
            page = await client.get("/boards/ic/threads/moderation-queue")
            assert page.status == 200
            assert "Staff controls" not in page.text

            response = await client.post(
                "/boards/ic/threads/moderation-queue",
                body=b"intent=lock",
                headers=_FORM,
            )
            assert response.status == 403
            assert repo.get_thread(community.id, thread.id).is_locked is False
            assert repo.get_thread(community.id, thread.id).is_pinned is False

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
