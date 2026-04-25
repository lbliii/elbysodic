"""Thread reader and reply handler."""

from __future__ import annotations

from chirp.errors import HTTPError
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
    intent = str(form.get("intent") or "reply")
    if intent == "move":
        try:
            target_board, moved_thread = services.move_thread(
                board_slug,
                thread_slug,
                _parse_board_id(form.get("target_board_id")),
            )
        except LookupError as exc:
            raise HTTPError(status=404, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPError(status=403, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPError(status=400, detail=str(exc)) from exc
        return Redirect(f"/boards/{target_board.slug}/threads/{moved_thread.slug}")

    if intent in {"watch", "unwatch"}:
        try:
            if intent == "watch":
                services.watch_thread(board_slug, thread_slug)
            else:
                services.unwatch_thread(board_slug, thread_slug)
        except LookupError as exc:
            raise HTTPError(status=404, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPError(status=403, detail=str(exc)) from exc
        return Redirect(request.path)

    if intent in {"lock", "unlock", "pin", "unpin"}:
        try:
            services.update_thread_state(
                board_slug,
                thread_slug,
                is_locked=_locked_state(intent),
                is_pinned=_pinned_state(intent),
            )
        except LookupError as exc:
            raise HTTPError(status=404, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPError(status=403, detail=str(exc)) from exc
        return Redirect(request.path)

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
    thread_view = services.read_thread(board_slug, thread_slug)
    viewer = services.viewer()
    if viewer.current_character is None:
        return Page(
            "boards/{board_slug}/threads/{thread_slug}/page.html",
            "page_content",
            page_block_name="page_root",
            current_path=request.url,
            viewer=viewer,
            selected_character=None,
            thread_view=thread_view,
            error=error,
            body=body,
            composer_config={},
            composer_config_id="reply-composer-config",
        )
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


def _parse_board_id(raw: object) -> int:
    try:
        return int(str(raw or ""))
    except ValueError as exc:
        raise ValueError("choose a board before moving the thread") from exc


def _locked_state(intent: str) -> bool | None:
    match intent:
        case "lock":
            return True
        case "unlock":
            return False
        case _:
            return None


def _pinned_state(intent: str) -> bool | None:
    match intent:
        case "pin":
            return True
        case "unpin":
            return False
        case _:
            return None


def _select_character(roster: list[Character], character_id: int) -> Character:
    for character in roster:
        if character.id == character_id:
            return character
    for character in roster:
        return character
    raise LookupError("membership does not have a character roster")
