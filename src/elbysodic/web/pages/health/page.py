"""App-owned /health alias for load balancers and timing middleware.

Chirp framework probes live at ``/livez`` (liveness) and ``/ready``
(readiness, SQLite-backed). Railway uses ``/ready`` so deploy healthchecks
see 503 while the process is draining.
"""

from __future__ import annotations

from chirp.http.request import Request
from chirp.http.response import Response


def get(request: Request) -> Response:
    return Response("ok\n", headers=(("Content-Type", "text/plain; charset=utf-8"),))
