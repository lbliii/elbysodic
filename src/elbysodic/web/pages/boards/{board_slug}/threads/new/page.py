"""Start a new thread with an opening character post."""

from __future__ import annotations

from chirp.http.request import Request
from chirp.http.response import Redirect
from chirp.templating.returns import Page

from elbysodic.domain import Character
from elbysodic.web.composer import composer_config
from elbysodic.web.state import get_services


def get(request: Request, board_slug: str) -> Page:
    return _render_form(request, board_slug)


async def post(request: Request, board_slug: str) -> Page | Redirect:
    form = await request.form()
    character_id = _parse_character_id(form.get("character_id"))
    title = str(form.get("title") or "")
    body = str(form.get("body") or "")

    try:
        created = get_services().start_thread_with_post(
            board_slug=board_slug,
            character_id=character_id,
            title=title,
            body=body,
        )
    except (LookupError, PermissionError, ValueError) as exc:
        return _render_form(
            request,
            board_slug,
            error=str(exc),
            character_id=character_id,
            title=title,
            body=body,
        )

    return Redirect(f"/boards/{board_slug}/threads/{created.thread.slug}#post-{created.post.id}")


def _render_form(
    request: Request,
    board_slug: str,
    *,
    error: str | None = None,
    character_id: int | None = None,
    title: str = "",
    body: str = "",
) -> Page:
    services = get_services()
    viewer = services.viewer()
    board, _threads = services.board_threads(board_slug)
    if viewer.current_character is None:
        return Page(
            "boards/{board_slug}/threads/new/page.html",
            "page_content",
            page_block_name="page_root",
            current_path=request.url,
            viewer=viewer,
            board=board,
            selected_character=None,
            selected_character_id=None,
            error=error,
            title=title,
            body=body,
            composer_config={},
            composer_config_id="thread-composer-config",
        )
    selected_character = _select_character(
        viewer.roster,
        character_id or viewer.current_character.id,
    )
    config_id = "thread-composer-config"
    return Page(
        "boards/{board_slug}/threads/new/page.html",
        "page_content",
        page_block_name="page_root",
        current_path=request.url,
        viewer=viewer,
        board=board,
        selected_character=selected_character,
        selected_character_id=selected_character.id,
        error=error,
        title=title,
        body=body,
        composer_config=composer_config(
            config_id=config_id,
            draft_key=f"thread:{viewer.community.id}:{board.id}",
            roster=viewer.roster,
            selected_character_id=selected_character.id,
            initial_body=body,
            initial_title=title,
        ),
        composer_config_id=config_id,
    )


def _parse_character_id(raw: object) -> int:
    try:
        return int(str(raw or ""))
    except ValueError as exc:
        raise ValueError("choose a character before starting a thread") from exc


def _select_character(roster: list[Character], character_id: int) -> Character:
    for character in roster:
        if character.id == character_id:
            return character
    for character in roster:
        return character
    raise LookupError("membership does not have a character roster")
