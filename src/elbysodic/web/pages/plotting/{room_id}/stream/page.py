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
from elbysodic.web.state import get_services
from elbysodic.web.tenant import request_scoped_path
from elbysodic.web.worker_draining import is_worker_draining, wait_for_worker_draining


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
        queue = await services.subscribe_plotting_room_live(parsed_room_id)
        try:
            while not is_worker_draining():
                get_task = asyncio.create_task(queue.get())
                drain_task = asyncio.create_task(wait_for_worker_draining())
                done, pending = await asyncio.wait(
                    {get_task, drain_task},
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
                    elif event.kind == "message" and event.message is not None:
                        yield Fragment(
                            "plotting/{room_id}/page.html",
                            "plotting_room_message_item",
                            target="plotting-room-message",
                            item=_ScopedPlottingRoomMessageView(request, event.message),
                        )
                if drain_task in done:
                    while not queue.empty():
                        queued = queue.get_nowait()
                        if queued.kind == "ready":
                            yield SSEEvent(event="plotting-room-ready", data="connected")
                        elif queued.kind == "message" and queued.message is not None:
                            yield Fragment(
                                "plotting/{room_id}/page.html",
                                "plotting_room_message_item",
                                target="plotting-room-message",
                                item=_ScopedPlottingRoomMessageView(request, queued.message),
                            )
                    break
        finally:
            await services.unsubscribe_plotting_room_live(parsed_room_id, queue)

    return EventStream(generate())


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
