"""Current-character preference route for the dev viewer."""

from __future__ import annotations

from chirp.http.request import Request
from chirp.http.response import Redirect

from elbysodic.web.state import get_services


async def post(request: Request) -> Redirect:
    form = await request.form()
    character_id = int(str(form.get("character_id") or "0"))
    get_services().set_default_character(character_id)
    return Redirect(_safe_next(str(form.get("next") or "/")))


def _safe_next(next_url: str) -> str:
    if not next_url.startswith("/") or next_url.startswith("//"):
        return "/"
    return next_url
