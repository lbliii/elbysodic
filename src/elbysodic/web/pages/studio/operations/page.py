"""Daily director operations console.

``/studio/operations`` aliases Today. The operations desk renders on ``/studio``.
"""

from __future__ import annotations

from chirp.http.request import Request
from chirp.http.response import Redirect


def get(request: Request) -> Redirect:
    return Redirect("/studio")
