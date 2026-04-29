"""Studio board editor."""

from __future__ import annotations

from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.http.response import Redirect
from chirp.templating.returns import Page

from elbysodic.domain.boards import BOARD_KIND_LABELS, BOARD_SIDEBAR_SECTION_LABELS
from elbysodic.domain.models import Board
from elbysodic.web.state import get_services


def get(request: Request, board_slug: str) -> Page:
    return _render_board_editor(request, board_slug)


async def post(request: Request, board_slug: str) -> Page | Redirect:
    services = get_services(request)
    form = await request.form()
    try:
        raw_parent_id = str(form.get("parent_board_id") or "")
        board = services.update_studio_board(
            board_slug,
            name=str(form.get("name") or ""),
            board_kind=str(form.get("board_kind") or ""),
            parent_board_id=int(raw_parent_id) if raw_parent_id else None,
            tagline=str(form.get("tagline") or ""),
            description=str(form.get("description") or ""),
            image_url=str(form.get("image_url") or ""),
            image_alt=str(form.get("image_alt") or ""),
            sort_order=_required_int(form.get("sort_order"), "choose a board sort order"),
            navigation_order=_required_int(
                form.get("navigation_order"),
                "choose a navigation order",
            ),
            show_in_navigation=form.get("show_in_navigation") == "on",
            sidebar_section=str(form.get("sidebar_section") or ""),
            is_private=form.get("is_private") == "on",
        )
    except LookupError as exc:
        raise HTTPError(status=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc
    except ValueError as exc:
        return _render_board_editor(
            request,
            board_slug,
            error=str(exc),
            form_values={
                "name": str(form.get("name") or ""),
                "board_kind": str(form.get("board_kind") or ""),
                "parent_board_id": int(str(form.get("parent_board_id") or "0")) or None,
                "tagline": str(form.get("tagline") or ""),
                "description": str(form.get("description") or ""),
                "image_url": str(form.get("image_url") or ""),
                "image_alt": str(form.get("image_alt") or ""),
                "sort_order": str(form.get("sort_order") or ""),
                "navigation_order": str(form.get("navigation_order") or ""),
                "show_in_navigation": form.get("show_in_navigation") == "on",
                "sidebar_section": str(form.get("sidebar_section") or ""),
                "is_private": form.get("is_private") == "on",
            },
        )
    return Redirect(f"/studio/boards/{board.slug}")


def _render_board_editor(
    request: Request,
    board_slug: str,
    *,
    error: str | None = None,
    form_values: dict[str, object] | None = None,
) -> Page:
    services = get_services(request)
    try:
        editor = services.studio_board_editor(board_slug)
    except LookupError as exc:
        raise HTTPError(status=404, detail=str(exc)) from exc
    values = form_values or _values_from_board(editor.board)
    return Page(
        "studio/boards/{board_slug}/page.html",
        "page_content",
        page_block_name="page_root",
        current_path=request.url,
        viewer=services.viewer(),
        studio=services.director_studio(),
        editor=editor,
        board=editor.board,
        board_kind_labels=BOARD_KIND_LABELS,
        sidebar_section_labels=BOARD_SIDEBAR_SECTION_LABELS,
        error=error,
        values=values,
    )


def _values_from_board(board: Board) -> dict[str, object]:
    return {
        "name": board.name,
        "board_kind": board.board_kind,
        "parent_board_id": board.parent_board_id,
        "tagline": board.tagline,
        "description": board.description,
        "image_url": board.image_url or "",
        "image_alt": board.image_alt,
        "sort_order": str(board.sort_order),
        "navigation_order": str(board.navigation_order),
        "show_in_navigation": board.show_in_navigation,
        "sidebar_section": board.sidebar_section,
        "is_private": board.is_private,
    }


def _required_int(raw: object, message: str) -> int:
    value = str(raw or "")
    if not value:
        raise ValueError(message)
    return int(value)
