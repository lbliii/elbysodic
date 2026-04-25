"""Thread reader and reply handler."""

from __future__ import annotations

from chirp.http.request import Request
from chirp.http.response import Redirect
from chirp.templating.returns import Page

from elbysodic.domain import Character
from elbysodic.web.composer import composer_config
from elbysodic.web.state import get_services


def get(request: Request, board_slug: str, thread_slug: str) -> Page:
    return _render_thread(request, board_slug, thread_slug)


async def post(request: Request, board_slug: str, thread_slug: str) -> Page | Redirect:
    services = get_services()
    form = await request.form()
    character_id = _parse_character_id(form.get("character_id"))
    body = str(form.get("body") or "")

    try:
        post = services.reply_to_thread(board_slug, thread_slug, character_id, body)
    except (LookupError, PermissionError, ValueError) as exc:
        return _render_thread(
            request,
            board_slug,
            thread_slug,
            error=str(exc),
            body=body,
            selected_character_id=character_id,
        )

    return Redirect(f"{request.path}#post-{post.id}")


def _render_thread(
    request: Request,
    board_slug: str,
    thread_slug: str,
    *,
    error: str | None = None,
    body: str = "",
    selected_character_id: int | None = None,
) -> Page:
    services = get_services()
    viewer = services.viewer()
    thread_view = services.read_thread(board_slug, thread_slug)
    selected_character = _select_character(
        viewer.roster,
        selected_character_id or viewer.current_character.id,
    )
    config_id = "reply-composer-config"
    return Page(
        "boards/{board_slug}/threads/{thread_slug}/page.html",
        "page_content",
        page_block_name="page_root",
        current_path=request.url,
        viewer=viewer,
        selected_character=selected_character,
        thread_view=thread_view,
        error=error,
        body=body,
        composer_config=composer_config(
            config_id=config_id,
            draft_key=f"reply:{viewer.community.id}:{thread_view.thread.id}",
            roster=viewer.roster,
            selected_character_id=selected_character.id,
            initial_body=body,
        ),
        composer_config_id=config_id,
    )


def _parse_character_id(raw: object) -> int:
    try:
        return int(str(raw or ""))
    except ValueError as exc:
        raise ValueError("choose a character before posting") from exc


def _select_character(roster: list[Character], character_id: int) -> Character:
    for character in roster:
        if character.id == character_id:
            return character
    for character in roster:
        return character
    raise LookupError("membership does not have a character roster")
