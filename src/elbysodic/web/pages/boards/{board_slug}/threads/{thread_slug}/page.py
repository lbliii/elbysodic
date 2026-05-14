"""Thread reader and reply handler."""

from __future__ import annotations

from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.http.response import Redirect
from chirp.templating.returns import Page

from elbysodic.domain import Character
from elbysodic.services import Mentionable
from elbysodic.services.forum import POSTING_MODES, THREAD_STATUSES
from elbysodic.web.commands import idempotency_key
from elbysodic.web.composer import composer_config, mention_picker_config
from elbysodic.web.state import get_services
from elbysodic.web.tenant import request_scoped_path


def get(request: Request, board_slug: str, thread_slug: str) -> Page:
    return _render_thread(request, board_slug, thread_slug)


async def post(request: Request, board_slug: str, thread_slug: str) -> Page | Redirect:
    services = get_services(request)
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

    if intent == "join_scene":
        try:
            services.join_thread_as_current_character(board_slug, thread_slug)
        except LookupError as exc:
            raise HTTPError(status=404, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPError(status=403, detail=str(exc)) from exc
        except ValueError as exc:
            return _render_thread(request, board_slug, thread_slug, error=str(exc))
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

    if intent == "scene":
        try:
            services.update_thread_scene(
                board_slug,
                thread_slug,
                status=str(form.get("status") or "active"),
                location=str(form.get("location") or ""),
                timeline=str(form.get("timeline") or ""),
                summary=str(form.get("summary") or ""),
                posting_mode=str(form.get("posting_mode") or "freeform"),
                participant_ids=_parse_participant_ids(form),
            )
        except LookupError as exc:
            raise HTTPError(status=404, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPError(status=403, detail=str(exc)) from exc
        except ValueError as exc:
            return _render_thread(request, board_slug, thread_slug, error=str(exc))
        return Redirect(request.path)

    character_id = _parse_character_id(form.get("character_id"))
    body = str(form.get("body") or "")
    key = str(form.get("idempotency_key") or "")
    command_key = f"reply:{board_slug}:{thread_slug}"
    existing_result = services.command_result(command_key, key)
    if existing_result is not None:
        return Redirect(existing_result)
    if not services.reserve_command(command_key, key):
        return Redirect(request.path)

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

    result_path = f"{request.path}#post-{post.post_number}"
    services.complete_command(command_key, key, result_path)
    return Redirect(result_path)


def _render_thread(
    request: Request,
    board_slug: str,
    thread_slug: str,
    *,
    error: str | None = None,
    body: str = "",
    selected_character_id: int | None = None,
) -> Page:
    services = get_services(request)
    thread_view = services.read_thread(board_slug, thread_slug)
    viewer = services.viewer()
    selected_cast = _character_mentionables(
        [
            character
            for character in thread_view.taggable_characters
            if character.id in thread_view.tagged_character_ids
        ]
    )
    mention_endpoint = request_scoped_path(request, "/mentionables/search")
    cast_picker_config = mention_picker_config(
        endpoint=mention_endpoint,
        hidden_name="participant_ids",
        scope="cast",
        selected=selected_cast,
    )
    if viewer.current_character is None:
        return Page.mounted(
            "boards/{board_slug}/threads/{thread_slug}/page.html",
            current_path=request.url,
            viewer=viewer,
            selected_character=None,
            thread_view=thread_view,
            parent_board=services.parent_board(thread_view.board),
            current_event=services.current_event_for_thread(
                thread_view.thread,
                thread_view.board,
            ),
            error=error,
            body=body,
            composer_config={},
            composer_config_id="reply-composer-config",
            idempotency_key=idempotency_key(),
            thread_statuses=THREAD_STATUSES,
            posting_modes=POSTING_MODES,
            cast_picker_config_id="scene-cast-picker-config",
            cast_picker_config=cast_picker_config,
        )
    selected_character = _select_character(
        viewer.roster,
        selected_character_id or viewer.current_character.id,
    )
    config_id = "reply-composer-config"
    return Page.mounted(
        "boards/{board_slug}/threads/{thread_slug}/page.html",
        current_path=request.url,
        viewer=viewer,
        selected_character=selected_character,
        thread_view=thread_view,
        parent_board=services.parent_board(thread_view.board),
        current_event=services.current_event_for_thread(
            thread_view.thread,
            thread_view.board,
        ),
        error=error,
        body=body,
        composer_config=composer_config(
            config_id=config_id,
            draft_key=f"reply:{viewer.community.id}:{thread_view.thread.id}",
            roster=viewer.roster,
            selected_character_id=selected_character.id,
            initial_body=body,
            mention_endpoint=mention_endpoint,
        ),
        composer_config_id=config_id,
        idempotency_key=idempotency_key(),
        thread_statuses=THREAD_STATUSES,
        posting_modes=POSTING_MODES,
        cast_picker_config_id="scene-cast-picker-config",
        cast_picker_config=cast_picker_config,
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


def _parse_participant_ids(form: object) -> list[int]:
    values: list[object]
    get_list = getattr(form, "get_list", None)
    getlist = getattr(form, "getlist", None)
    if callable(get_list):
        values = list(get_list("participant_ids"))
    elif callable(getlist):
        values = list(getlist("participant_ids"))
    else:
        raw = getattr(form, "get", lambda _name: None)("participant_ids")
        values = [] if raw is None else [raw]
    parsed: list[int] = []
    for value in values:
        try:
            character_id = int(str(value))
        except ValueError:
            continue
        if character_id not in parsed:
            parsed.append(character_id)
    return parsed


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


def _character_mentionables(characters: list[Character]) -> list[Mentionable]:
    return [
        Mentionable(
            kind="character",
            id=character.id,
            handle=character.slug,
            label=character.name,
            detail="Character",
            avatar_url=character.avatar_url,
            href=f"/characters/{character.slug}",
        )
        for character in characters
    ]
