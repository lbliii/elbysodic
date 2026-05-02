"""Railway health check endpoint."""

from __future__ import annotations

from chirp.http.request import Request
from chirp.http.response import Response


def get(request: Request) -> Response:
    return Response("ok\n", headers=(("Content-Type", "text/plain; charset=utf-8"),))
