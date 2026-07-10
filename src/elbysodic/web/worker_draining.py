"""Generation-scoped worker draining signal for long-lived SSE streams.

Pounce 0.9 emits a ``pounce.worker.draining`` ASGI scope before reload or
shutdown so apps can close active streams cleanly. Chirp forwards the
configured ``sse_close_event`` to clients when a stream ends; generators
subscribe here so their ``finally`` blocks run (unsubscribe, release) before
the worker exits.
"""

from __future__ import annotations

import asyncio
from typing import Any

from chirp._internal.asgi import Receive, Scope, Send
from chirp.app import App

_DRAIN_EVENT: asyncio.Event | None = None


def _drain_event() -> asyncio.Event:
    global _DRAIN_EVENT
    if _DRAIN_EVENT is None:
        _DRAIN_EVENT = asyncio.Event()
    return _DRAIN_EVENT


def reset_worker_draining() -> None:
    """Clear the draining flag at worker startup (TestClient + Pounce)."""
    global _DRAIN_EVENT
    _DRAIN_EVENT = asyncio.Event()


def signal_worker_draining() -> None:
    """Mark the current worker as draining so SSE generators exit."""
    _drain_event().set()


def is_worker_draining() -> bool:
    return _drain_event().is_set()


async def wait_for_worker_draining() -> None:
    await _drain_event().wait()


async def _worker_lifecycle_receive() -> dict[str, Any]:
    return {"type": "http.disconnect"}


async def _worker_lifecycle_send(_message: object) -> None:
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

    @property
    def _runtime(self):
        return self._app._runtime

    def __getattr__(self, name: str) -> Any:
        return getattr(self._app, name)

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
