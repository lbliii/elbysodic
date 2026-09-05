from __future__ import annotations

import ast
import asyncio
import contextlib
import types
from collections.abc import AsyncIterator, Callable
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

import pytest

from elbysodic.db import ForumRepository, connect, create_schema
from elbysodic.services import create_services
from elbysodic.services.notifications import notification_inbox
from elbysodic.services.plotting import read_plotting_room_messages
from tests._sql_probe import trace_sql
from tests.test_forum_slice import _link_seed_plotting_room_to_sentinel, _seeded_services

REPO_ROOT = Path(__file__).resolve().parents[1]
STREAM_PAGE = (
    REPO_ROOT
    / "src"
    / "elbysodic"
    / "web"
    / "pages"
    / "plotting"
    / "{room_id}"
    / "stream"
    / "page.py"
)


def test_post_id_batch_is_tenant_scoped() -> None:
    connection = connect()
    create_schema(connection)
    repo = ForumRepository(connection)

    def create_post(community_slug: str, index: int):
        community = repo.create_community(community_slug, community_slug.title())
        role = repo.create_role(community.id, "member", "Member")
        user = repo.create_user(f"batch-{index}@example.com", "hash")
        membership = repo.create_membership(
            community.id,
            user.id,
            role.id,
            f"writer-{index}",
            f"Writer {index}",
        )
        character = repo.create_character(
            community.id,
            membership.id,
            f"face-{index}",
            f"Face {index}",
        )
        board = repo.create_board(community.id, "scenes", "Scenes")
        thread = repo.create_thread(
            community.id,
            board.id,
            character.id,
            f"scene-{index}",
            f"Scene {index}",
        )
        return community, repo.create_post(
            community.id,
            thread.id,
            character.id,
            f"post {index}",
        )

    try:
        default, default_post = create_post("default", 1)
        _hosted, hosted_post = create_post("hosted", 2)

        posts = repo.list_posts_by_ids(
            default.id,
            [default_post.id, hosted_post.id],
        )

        assert posts == {default_post.id: default_post}
    finally:
        connection.close()


def _add_messages(services, room_id: int, *, start: int, stop: int) -> None:
    character = services.seed.default_character
    assert character is not None
    for index in range(start, stop):
        services.repo.create_plotting_room_message(
            services.seed.community.id,
            room_id,
            services.seed.membership.id,
            f"message {index}",
            author_character_id=character.id,
        )


def test_plotting_room_history_has_constant_query_cost() -> None:
    services = _seeded_services()
    room = _link_seed_plotting_room_to_sentinel(services)
    try:
        _add_messages(services, room.id, start=0, stop=10)
        services.read_plotting_room(room.id)
        with trace_sql(services.repo.connection) as ten_message_trace:
            ten_message_detail = services.read_plotting_room(room.id)

        _add_messages(services, room.id, start=10, stop=100)
        with trace_sql(services.repo.connection) as hundred_message_trace:
            hundred_message_detail = services.read_plotting_room(room.id)

        assert len(ten_message_detail.messages) == 10
        assert len(hundred_message_detail.messages) == 100
        assert hundred_message_trace.count == ten_message_trace.count
        assert hundred_message_trace.count <= 40
    finally:
        services.close()


def test_incremental_plotting_read_finds_cross_worker_rows_at_constant_cost() -> None:
    services = _seeded_services()
    room = _link_seed_plotting_room_to_sentinel(services)
    try:
        character = services.seed.default_character
        assert character is not None
        _add_messages(services, room.id, start=0, stop=10)
        first_cursor = services.read_plotting_room(room.id).messages[-1].message.id
        direct_message = services.repo.create_plotting_room_message(
            services.seed.community.id,
            room.id,
            services.seed.membership.id,
            "written outside the local stream queue",
            author_character_id=character.id,
        )
        with trace_sql(services.repo.connection) as short_history_trace:
            first_batch = services.read_plotting_room_messages(
                room.id,
                after_id=first_cursor,
            )

        _add_messages(services, room.id, start=11, stop=100)
        long_cursor = services.read_plotting_room(room.id).messages[-1].message.id
        final_message = services.repo.create_plotting_room_message(
            services.seed.community.id,
            room.id,
            services.seed.membership.id,
            "another worker row after a long history",
            author_character_id=character.id,
        )
        with trace_sql(services.repo.connection) as long_history_trace:
            second_batch = services.read_plotting_room_messages(
                room.id,
                after_id=long_cursor,
            )

        assert [item.message.id for item in first_batch.messages] == [direct_message.id]
        assert first_batch.last_message_id == direct_message.id
        assert [item.message.id for item in second_batch.messages] == [final_message.id]
        assert second_batch.last_message_id == final_message.id
        assert long_history_trace.count == short_history_trace.count
        assert long_history_trace.count <= 25
    finally:
        services.close()


def test_incremental_plotting_read_rechecks_current_access() -> None:
    services = _seeded_services()
    room = _link_seed_plotting_room_to_sentinel(services)
    try:
        stale_viewer = services.viewer()
        services.repo.connection.execute(
            "UPDATE community_memberships SET is_active = 0 WHERE id = ?",
            (services.seed.membership.id,),
        )
        services.repo.connection.commit()

        with pytest.raises(PermissionError, match="cannot view room"):
            read_plotting_room_messages(
                services.repo,
                stale_viewer,
                room.id,
                after_id=None,
            )
    finally:
        services.close()


def test_notification_inbox_batches_snippet_context() -> None:
    services = create_services(":memory:")
    viewer = services.viewer()
    character = viewer.current_character
    assert character is not None
    created = services.start_thread_with_post(
        board_slug="danger-room",
        character_id=character.id,
        title="Bounded inbox",
        body="original",
    )
    try:
        unrelated_post_ids = {
            services.repo.create_post(
                viewer.community.id,
                created.thread.id,
                character.id,
                f"unrelated scene history {index}",
            ).id
            for index in range(200)
        }
        notification_post_ids: list[int] = []
        for index in range(50):
            post = services.repo.create_post(
                viewer.community.id,
                created.thread.id,
                character.id,
                f"inbox snippet {index}",
            )
            notification_post_ids.append(post.id)
            services.repo.create_notification(
                viewer.community.id,
                viewer.membership.id,
                kind="thread_reply",
                thread_id=created.thread.id,
                post_id=post.id,
                actor_membership_id=viewer.membership.id,
                actor_character_id=character.id,
            )

        with (
            patch.object(
                services.repo,
                "list_posts_by_ids",
                wraps=services.repo.list_posts_by_ids,
            ) as post_loader,
            trace_sql(services.repo.connection) as trace,
        ):
            inbox = notification_inbox(services.repo, viewer, limit=50)

        full_roster_queries = [
            statement
            for statement in trace.statements
            if "FROM characters" in statement and "ORDER BY name, id" in statement
        ]
        membership_queries = [
            statement for statement in trace.statements if "FROM community_memberships" in statement
        ]
        assert len(inbox.items) == 50
        assert inbox.items[0].snippet == "inbox snippet 49"
        assert len(full_roster_queries) <= 1
        assert len(membership_queries) <= 3
        post_loader.assert_called_once_with(
            viewer.community.id,
            sorted(notification_post_ids),
        )
        loaded_post_ids = set(post_loader.call_args.args[1])
        assert loaded_post_ids.isdisjoint(unrelated_post_ids)
        assert not any(
            "thread_id IN (SELECT value FROM json_each" in sql for sql in trace.statements
        )
    finally:
        services.close()


def test_cancelled_plotting_stream_awaits_every_child_task() -> None:
    source = STREAM_PAGE.read_text()
    function = next(
        node
        for node in ast.parse(source).body
        if isinstance(node, ast.FunctionDef) and node.name == "get"
    )

    class Services:
        def read_plotting_room(self, _room_id: int):
            return types.SimpleNamespace(messages=[])

        async def subscribe_plotting_room_live(self, _room_id: int) -> asyncio.Queue:
            return asyncio.Queue()

        async def unsubscribe_plotting_room_live(self, *_args: object) -> None:
            return None

    async def exercise() -> None:
        drain_event = asyncio.Event()
        services = Services()
        namespace: dict[str, Any] = {
            "asyncio": asyncio,
            "get_services": lambda *_args: services,
            "_parse_room_id": int,
            "plotting_stream_opened": lambda: None,
            "plotting_stream_closed": lambda: None,
            "is_worker_draining": lambda: False,
            "wait_for_worker_draining": drain_event.wait,
            "_PLOTTING_POLL_INTERVAL": 0.25,
            "close_request_services": lambda _request: None,
            "EventStream": lambda generator: generator,
        }
        exec(  # noqa: S102 -- isolate the checked route generator with controlled fakes
            "from __future__ import annotations\n" + ast.unparse(function),
            namespace,
        )
        get_stream = cast(
            Callable[[object, str], AsyncIterator[Any]],
            namespace["get"],
        )
        stream = get_stream(object(), "1")

        async def consume_one() -> Any:
            return await anext(stream)

        consumer = asyncio.create_task(consume_one())
        await asyncio.sleep(0.01)
        consumer.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await consumer
        await asyncio.sleep(0)

        pending = [
            task
            for task in asyncio.all_tasks()
            if task is not asyncio.current_task() and not task.done()
        ]
        assert pending == []

    asyncio.run(exercise())


def test_local_queue_message_rechecks_access_before_rendering() -> None:
    source = STREAM_PAGE.read_text()
    function = next(
        node
        for node in ast.parse(source).body
        if isinstance(node, ast.FunctionDef) and node.name == "get"
    )

    class Services:
        def __init__(self) -> None:
            self.authorized = True
            self.queue: asyncio.Queue[object] = asyncio.Queue()

        def read_plotting_room(self, _room_id: int):
            return types.SimpleNamespace(messages=[])

        def read_plotting_room_messages(self, _room_id: int, *, after_id: int | None):
            if not self.authorized:
                raise PermissionError("participant access revoked")
            return types.SimpleNamespace(messages=[], last_message_id=after_id)

        async def subscribe_plotting_room_live(self, _room_id: int) -> asyncio.Queue:
            await self.queue.put(types.SimpleNamespace(kind="ready", message=None))
            return self.queue

        async def unsubscribe_plotting_room_live(self, *_args: object) -> None:
            return None

    async def exercise() -> None:
        drain_event = asyncio.Event()
        services = Services()
        namespace: dict[str, Any] = {
            "asyncio": asyncio,
            "get_services": lambda *_args: services,
            "_parse_room_id": int,
            "plotting_stream_opened": lambda: None,
            "plotting_stream_closed": lambda: None,
            "is_worker_draining": lambda: False,
            "wait_for_worker_draining": drain_event.wait,
            "_PLOTTING_POLL_INTERVAL": 30.0,
            "close_request_services": lambda _request: None,
            "EventStream": lambda generator: generator,
            "SSEEvent": lambda **values: types.SimpleNamespace(**values),
            "_message_fragment": lambda *_args: "private message",
            "_unseen_messages": lambda messages, _seen: messages,
        }
        exec(  # noqa: S102 -- isolate the checked route generator with controlled fakes
            "from __future__ import annotations\n" + ast.unparse(function),
            namespace,
        )
        get_stream = cast(
            Callable[[object, str], AsyncIterator[Any]],
            namespace["get"],
        )
        stream = get_stream(object(), "1")
        ready = await anext(stream)
        assert ready.event == "plotting-room-ready"

        services.authorized = False
        await services.queue.put(
            types.SimpleNamespace(
                kind="message",
                message=types.SimpleNamespace(message=types.SimpleNamespace(id=1)),
            )
        )
        with pytest.raises(StopAsyncIteration):
            await anext(stream)

    asyncio.run(exercise())
