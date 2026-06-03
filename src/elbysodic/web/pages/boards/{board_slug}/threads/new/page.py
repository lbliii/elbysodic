"""Start a new thread with an opening character post."""

from __future__ import annotations

from chirp.http.request import Request
from chirp.http.response import Redirect
from chirp.templating.returns import Page

from elbysodic.domain import Character
from elbysodic.services import Mentionable
from elbysodic.services.forum import POSTING_MODES, THREAD_STATUSES
from elbysodic.services.threads import taggable_characters
from elbysodic.web.commands import idempotency_key
from elbysodic.web.composer import composer_config, mention_picker_config
from elbysodic.web.state import get_services
from elbysodic.web.tenant import request_scoped_path


def get(request: Request, board_slug: str) -> Page:
    return _render_form(request, board_slug)


async def post(request: Request, board_slug: str) -> Page | Redirect:
    form = await request.form()
    character_id = _parse_character_id(form.get("character_id"))
    participant_ids = _parse_participant_ids(form)
    title = str(form.get("title") or "")
    status = str(form.get("status") or "active")
    location = str(form.get("location") or "")
    timeline = str(form.get("timeline") or "")
    summary = str(form.get("summary") or "")
    posting_mode = str(form.get("posting_mode") or "freeform")
    body = str(form.get("body") or "")
    key = str(form.get("idempotency_key") or "")
    services = get_services(request)
    command_key = f"start-thread:{board_slug}"
    existing_result = services.command_result(command_key, key)
    if existing_result is not None:
        return Redirect(existing_result)
    if not services.reserve_command(command_key, key):
        return Redirect(f"/boards/{board_slug}/threads/new")

    try:
        created = services.start_thread_with_post(
            board_slug=board_slug,
            character_id=character_id,
            title=title,
            body=body,
            status=status,
            location=location,
            timeline=timeline,
            summary=summary,
            posting_mode=posting_mode,
            participant_ids=participant_ids,
        )
    except (LookupError, PermissionError, ValueError) as exc:
        services.discard_command(command_key, key)
        return _render_form(
            request,
            board_slug,
            error=str(exc),
            character_id=character_id,
            participant_ids=participant_ids,
            title=title,
            status=status,
            location=location,
            timeline=timeline,
            summary=summary,
            posting_mode=posting_mode,
            body=body,
        )
    except Exception:
        services.discard_command(command_key, key)
        raise

    result_path = (
        f"/boards/{board_slug}/threads/{created.thread.slug}#post-{created.post.post_number}"
    )
    services.complete_command(command_key, key, result_path)
    return Redirect(result_path)


def _render_form(
    request: Request,
    board_slug: str,
    *,
    error: str | None = None,
    character_id: int | None = None,
    participant_ids: list[int] | None = None,
    title: str = "",
    status: str = "active",
    location: str = "",
    timeline: str = "",
    summary: str = "",
    posting_mode: str = "freeform",
    body: str = "",
) -> Page:
    services = get_services(request)
    viewer = services.viewer()
    board, _threads = services.board_threads(board_slug)
    mention_endpoint = request_scoped_path(request, "/mentionables/search")
    if viewer.current_character is None:
        return Page.mounted(
            "boards/{board_slug}/threads/new/page.html",
            current_path=request.url,
            viewer=viewer,
            board=board,
            selected_character=None,
            selected_character_id=None,
            error=error,
            title=title,
            status=status,
            location=location,
            timeline=timeline,
            summary=summary,
            posting_mode=posting_mode,
            thread_statuses=THREAD_STATUSES,
            posting_modes=POSTING_MODES,
            taggable_characters=[],
            selected_participant_ids=set(),
            cast_picker_config_id="thread-cast-picker-config",
            cast_picker_config=mention_picker_config(
                endpoint=mention_endpoint,
                hidden_name="participant_ids",
                scope="cast",
                selected=[],
            ),
            body=body,
            composer_config={},
            composer_config_id="thread-composer-config",
            idempotency_key=idempotency_key(),
        )
    selected_character = _select_character(
        viewer.roster,
        character_id or viewer.current_character.id,
    )
    config_id = "thread-composer-config"
    taggable = taggable_characters(
        services.repo.list_community_characters(viewer.community.id), viewer.roster
    )
    taggable_ids = {character.id for character in taggable}
    selected_participant_ids = {
        character_id for character_id in participant_ids or [] if character_id in taggable_ids
    }
    selected_cast = _character_mentionables(
        [character for character in taggable if character.id in selected_participant_ids]
    )
    return Page.mounted(
        "boards/{board_slug}/threads/new/page.html",
        current_path=request.url,
        viewer=viewer,
        board=board,
        selected_character=selected_character,
        selected_character_id=selected_character.id,
        error=error,
        title=title,
        status=status,
        location=location,
        timeline=timeline,
        summary=summary,
        posting_mode=posting_mode,
        thread_statuses=THREAD_STATUSES,
        posting_modes=POSTING_MODES,
        taggable_characters=taggable,
        selected_participant_ids=selected_participant_ids,
        cast_picker_config_id="thread-cast-picker-config",
        cast_picker_config=mention_picker_config(
            endpoint=mention_endpoint,
            hidden_name="participant_ids",
            scope="cast",
            selected=selected_cast,
        ),
        body=body,
        composer_config=composer_config(
            config_id=config_id,
            draft_key=f"thread:{viewer.community.id}:{board.id}",
            roster=viewer.roster,
            selected_character_id=selected_character.id,
            initial_body=body,
            initial_title=title,
            mention_endpoint=mention_endpoint,
        ),
        composer_config_id=config_id,
        idempotency_key=idempotency_key(),
    )


def _parse_character_id(raw: object) -> int:
    try:
        return int(str(raw or ""))
    except ValueError as exc:
        raise ValueError("choose a character before starting a thread") from exc


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
