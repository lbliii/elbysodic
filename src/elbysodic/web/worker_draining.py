"""Generation-scoped worker draining signal for long-lived SSE streams.

Pounce 0.9 emits a ``pounce.worker.draining`` ASGI scope before reload or
shutdown so apps can close active streams cleanly. Chirp forwards the
configured ``sse_close_event`` to clients when a stream ends; generators
subscribe here so their ``finally`` blocks run (unsubscribe, release) before
the worker exits.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import threading
from collections.abc import Awaitable, Callable, MutableMapping
from typing import Any

from chirp.app import App

from elbysodic.web.pounce_railway import run_chirp_asgi_adapter

type Scope = MutableMapping[str, Any]
type Receive = Callable[[], Awaitable[MutableMapping[str, Any]]]
type Send = Callable[[MutableMapping[str, Any]], Awaitable[None]]

_DRAIN_EVENT: asyncio.Event | None = None
_PLOTTING_STREAMS_ACTIVE = 0
_PLOTTING_STREAMS_LOCK = threading.Lock()
_LOGGER = logging.getLogger("pounce.elbysodic")


def _drain_event() -> asyncio.Event:
    global _DRAIN_EVENT
    if _DRAIN_EVENT is None:
        _DRAIN_EVENT = asyncio.Event()
    return _DRAIN_EVENT


def reset_worker_draining() -> None:
    """Clear the draining flag at worker startup (TestClient + Pounce)."""
    global _DRAIN_EVENT
    global _PLOTTING_STREAMS_ACTIVE
    _DRAIN_EVENT = asyncio.Event()
    with _PLOTTING_STREAMS_LOCK:
        _PLOTTING_STREAMS_ACTIVE = 0
    gil_probe = getattr(sys, "_is_gil_enabled", None)
    gil_enabled = bool(gil_probe()) if callable(gil_probe) else True
    build_id = os.environ.get("POUNCE_BUILD_ID", "unset")
    _LOGGER.info(
        "event=worker_started plotting_streams_active=0 build_id=%s gil_enabled=%s",
        build_id,
        str(gil_enabled).lower(),
    )


def signal_worker_draining() -> None:
    """Mark the current worker as draining so SSE generators exit."""
    _LOGGER.info(
        "event=worker_draining plotting_streams_active=%d",
        active_plotting_streams(),
    )
    _drain_event().set()


def is_worker_draining() -> bool:
    return _drain_event().is_set()


async def wait_for_worker_draining() -> None:
    await _drain_event().wait()


def active_plotting_streams() -> int:
    """Return this worker's aggregate plotting-stream gauge."""
    with _PLOTTING_STREAMS_LOCK:
        return _PLOTTING_STREAMS_ACTIVE


def plotting_stream_opened() -> int:
    """Increment and report the aggregate plotting-stream gauge."""
    global _PLOTTING_STREAMS_ACTIVE
    with _PLOTTING_STREAMS_LOCK:
        _PLOTTING_STREAMS_ACTIVE += 1
        active = _PLOTTING_STREAMS_ACTIVE
    _LOGGER.info("event=plotting_stream_opened plotting_streams_active=%d", active)
    return active


def plotting_stream_closed() -> int:
    """Decrement and report the aggregate plotting-stream gauge."""
    global _PLOTTING_STREAMS_ACTIVE
    with _PLOTTING_STREAMS_LOCK:
        _PLOTTING_STREAMS_ACTIVE = max(0, _PLOTTING_STREAMS_ACTIVE - 1)
        active = _PLOTTING_STREAMS_ACTIVE
    _LOGGER.info("event=plotting_stream_closed plotting_streams_active=%d", active)
    return active


async def _worker_lifecycle_receive() -> MutableMapping[str, Any]:
    return {"type": "http.disconnect"}


async def _worker_lifecycle_send(_message: MutableMapping[str, Any]) -> None:
    return None


class DrainingAwareApp:
    """ASGI proxy that handles ``pounce.worker.draining`` before the Chirp app."""

    __slots__ = ("_app",)

    def __init__(self, app: App) -> None:
        self._app = app

    @property
    def chirp_app(self) -> App:
        """Inner Chirp app for contract checks (not the ASGI drain proxy)."""
        return self._app

    def __getattr__(self, name: str) -> Any:
        return getattr(self._app, name)

    def run(
        self,
        host: str | None = None,
        port: int | None = None,
        *,
        lifecycle_collector: Any | None = None,
    ) -> None:
        """Launch Pounce with this proxy as the runtime ASGI application."""
        run_chirp_asgi_adapter(
            self._app,
            self,
            host=host,
            port=port,
            lifecycle_collector=lifecycle_collector,
        )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get("type") == "pounce.worker.draining":
            signal_worker_draining()
            return
        await self._app(scope, receive, send)


def wrap_worker_draining(app: App) -> DrainingAwareApp:
    """Return an ASGI proxy that signals SSE generators on worker drain."""
    return DrainingAwareApp(app)


def unwrap_chirp_app(app: App | DrainingAwareApp) -> App:
    """Return the inner Chirp app when contract tooling needs its concrete type."""
    if isinstance(app, DrainingAwareApp):
        return app.chirp_app
    return app


async def emit_worker_draining(
    app: App | DrainingAwareApp,
    *,
    worker_id: int = 0,
    generation: int = 1,
    reason: str = "reload",
    timeout: float = 5.0,
) -> None:
    """Simulate Pounce's draining hook (used by regression tests)."""
    await app(
        {
            "type": "pounce.worker.draining",
            "worker_id": worker_id,
            "generation": generation,
            "reason": reason,
            "timeout": timeout,
        },
        _worker_lifecycle_receive,
        _worker_lifecycle_send,
    )
