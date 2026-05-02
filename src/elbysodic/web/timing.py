"""Request timing instrumentation."""

from __future__ import annotations

from dataclasses import replace
from time import perf_counter
from typing import Any

from chirp.http.request import Request
from chirp.http.response import Redirect, Response


class RequestTimingMiddleware:
    """Expose app handling duration through standard Server-Timing headers."""

    async def __call__(self, request: Request, next: Any) -> Any:
        started = perf_counter()
        response = await next(request)
        duration_ms = (perf_counter() - started) * 1000
        return _with_timing_headers(response, duration_ms)


def _with_timing_headers(response: Any, duration_ms: float) -> Any:
    headers = (
        ("Server-Timing", f'app;dur={duration_ms:.1f};desc="Elbysodic app"'),
        ("X-Elbysodic-Route-Time-Ms", f"{duration_ms:.1f}"),
    )
    if isinstance(response, Response):
        return response.with_headers(dict(headers))
    if isinstance(response, Redirect):
        return replace(response, headers=(*response.headers, *headers))
    return response
