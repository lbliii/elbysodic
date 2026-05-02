"""Post editing form."""

from __future__ import annotations

from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.http.response import Redirect
from chirp.templating.returns import Page

from elbysodic.web.composer import composer_config
from elbysodic.web.state import get_services
from elbysodic.web.tenant import request_scoped_path


def get(request: Request, board_slug: str, thread_slug: str, post_id: str) -> Page:
    return _render_form(request, board_slug, thread_slug, post_id)


async def post(
    request: Request,
    board_slug: str,
    thread_slug: str,
    post_id: str,
) -> Page | Redirect:
    parsed_post_number = _parse_post_number(post_id)
    form = await request.form()
    body = str(form.get("body") or "")

    try:
        post_view = get_services(request).update_post(
            board_slug,
            thread_slug,
            parsed_post_number,
            body,
        )
    except ValueError as exc:
        return _render_form(
            request,
            board_slug,
            thread_slug,
            post_id,
            error=str(exc),
            body=body,
        )
    except LookupError as exc:
        raise HTTPError(status=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc

    return Redirect(f"/boards/{board_slug}/threads/{thread_slug}#post-{post_view.post_number}")


def _render_form(
    request: Request,
    board_slug: str,
    thread_slug: str,
    post_id: str,
    *,
    error: str | None = None,
    body: str | None = None,
) -> Page:
    parsed_post_number = _parse_post_number(post_id)
    services = get_services(request)
    viewer = services.viewer()
    try:
        edit_view = services.read_post_editor(board_slug, thread_slug, parsed_post_number)
    except LookupError as exc:
        raise HTTPError(status=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc

    config_id = "edit-post-composer-config"
    initial_body = edit_view.post.post.body if body is None else body
    return Page(
        "boards/{board_slug}/threads/{thread_slug}/posts/{post_id}/edit/page.html",
        "page_content",
        page_block_name="page_root",
        current_path=request.url,
        viewer=viewer,
        edit_view=edit_view,
        error=error,
        body=initial_body,
        composer_config=composer_config(
            config_id=config_id,
            draft_key=f"edit-post:{viewer.community.id}:{edit_view.post.post.id}",
            roster=[edit_view.post.author],
            selected_character_id=edit_view.post.author.id,
            initial_body=initial_body,
            mention_endpoint=request_scoped_path(request, "/mentionables/search"),
        ),
        composer_config_id=config_id,
    )


def _parse_post_number(raw: object) -> int:
    try:
        return int(str(raw or ""))
    except ValueError as exc:
        raise HTTPError(status=404, detail=f"post not found: {raw}") from exc
