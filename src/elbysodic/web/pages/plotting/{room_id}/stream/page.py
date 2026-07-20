"""Live plotting room event stream."""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import AsyncIterator
from typing import Any

from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.realtime.events import EventStream, SSEEvent
from chirp.templating.returns import Fragment

from elbysodic.services.read_models import PlottingRoomMessageView
from elbysodic.web.state import close_request_services, get_services
from elbysodic.web.tenant import request_scoped_path
from elbysodic.web.worker_draining import (
    is_worker_draining,
    plotting_stream_closed,
    plotting_stream_opened,
    wait_for_worker_draining,
)

_PLOTTING_POLL_INTERVAL = 0.25


def get(request: Request, room_id: str) -> EventStream:
    services = get_services(request)
    parsed_room_id = _parse_room_id(room_id)
    try:
        services.read_plotting_room(parsed_room_id)
    except LookupError as exc:
        raise HTTPError(status=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc

    async def generate() -> AsyncIterator[Any]:
        # Pounce consumes streaming bodies after ordinary response middleware
        # has returned. Reopen a request-scoped repository for the generator
        # lifetime rather than retaining the already-cleaned handler facade.
        stream_services = get_services(request)
        queue = None
        stream_opened = False
        try:
            room = stream_services.read_plotting_room(parsed_room_id)
            seen_message_ids = {item.message.id for item in room.messages}
            queue = await stream_services.subscribe_plotting_room_live(parsed_room_id)
            plotting_stream_opened()
            stream_opened = True
            while not is_worker_draining():
                get_task = asyncio.create_task(queue.get())
                drain_task = asyncio.create_task(wait_for_worker_draining())
                poll_task = asyncio.create_task(asyncio.sleep(_PLOTTING_POLL_INTERVAL))
                done, pending = await asyncio.wait(
                    {get_task, drain_task, poll_task},
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for task in pending:
                    task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await task
                if get_task in done:
                    event = get_task.result()
                    if event.kind == "ready":
                        yield SSEEvent(event="plotting-room-ready", data="connected")
                    elif (
                        event.kind == "message"
                        and event.message is not None
                        and event.message.message.id not in seen_message_ids
                    ):
                        seen_message_ids.add(event.message.message.id)
                        yield _message_fragment(request, event.message)
                if poll_task in done:
                    for message in _unseen_messages(
                        stream_services.read_plotting_room(parsed_room_id).messages,
                        seen_message_ids,
                    ):
                        yield _message_fragment(request, message)
                if drain_task in done:
                    while not queue.empty():
                        queued = queue.get_nowait()
                        if queued.kind == "ready":
                            yield SSEEvent(event="plotting-room-ready", data="connected")
                        elif (
                            queued.kind == "message"
                            and queued.message is not None
                            and queued.message.message.id not in seen_message_ids
                        ):
                            seen_message_ids.add(queued.message.message.id)
                            yield _message_fragment(request, queued.message)
                    for message in _unseen_messages(
                        stream_services.read_plotting_room(parsed_room_id).messages,
                        seen_message_ids,
                    ):
                        yield _message_fragment(request, message)
                    break
        finally:
            if queue is not None:
                await stream_services.unsubscribe_plotting_room_live(parsed_room_id, queue)
            if stream_opened:
                plotting_stream_closed()
            close_request_services(request)

    return EventStream(generate())


def _unseen_messages(
    messages: list[PlottingRoomMessageView],
    seen_message_ids: set[int],
) -> list[PlottingRoomMessageView]:
    unseen = [item for item in messages if item.message.id not in seen_message_ids]
    seen_message_ids.update(item.message.id for item in unseen)
    return unseen


def _message_fragment(request: Request, message: PlottingRoomMessageView) -> Fragment:
    return Fragment(
        "plotting/{room_id}/page.html",
        "plotting_room_message_item",
        target="plotting-room-message",
        item=_ScopedPlottingRoomMessageView(request, message),
    )


def _parse_room_id(value: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise HTTPError(status=404, detail="plotting room not found") from exc


class _ScopedPlottingRoomMessageView:
    def __init__(self, request: Request, message: PlottingRoomMessageView) -> None:
        self._request = request
        self._message = message

    def __getattr__(self, name: str) -> Any:
        return getattr(self._message, name)

    @property
    def author_href(self) -> str:
        return request_scoped_path(self._request, self._message.author_href)
