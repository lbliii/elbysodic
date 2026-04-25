"""Character roster for the active community membership."""

from __future__ import annotations

from chirp.http.request import Request
from chirp.http.response import Redirect
from chirp.templating.returns import Page

from elbysodic.web.state import get_services


def get(request: Request) -> Page:
    return _render_roster(request)


async def post(request: Request) -> Page | Redirect:
    form = await request.form()
    name = str(form.get("name") or "")
    summary = str(form.get("summary") or "")
    avatar_url = str(form.get("avatar_url") or "")
    make_default = str(form.get("make_default") or "") == "on"

    try:
        character = get_services().create_character(
            name=name,
            summary=summary,
            avatar_url=avatar_url,
            make_default=make_default,
        )
    except ValueError as exc:
        return _render_roster(
            request,
            error=str(exc),
            name=name,
            summary=summary,
            avatar_url=avatar_url,
            make_default=make_default,
        )

    return Redirect(f"/characters/{character.slug}")


def _render_roster(
    request: Request,
    *,
    error: str | None = None,
    name: str = "",
    summary: str = "",
    avatar_url: str = "",
    make_default: bool = False,
) -> Page:
    viewer = get_services().viewer()
    return Page(
        "characters/page.html",
        "page_content",
        page_block_name="page_root",
        current_path=request.url,
        viewer=viewer,
        error=error,
        name=name,
        summary=summary,
        avatar_url=avatar_url,
        make_default=make_default,
    )
