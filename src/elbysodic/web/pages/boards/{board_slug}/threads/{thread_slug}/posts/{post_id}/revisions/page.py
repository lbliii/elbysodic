"""Post revision history."""

from __future__ import annotations

from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.web.state import get_services


def get(request: Request, board_slug: str, thread_slug: str, post_id: str) -> Page:
    parsed_post_number = _parse_post_number(post_id)
    services = get_services(request)
    viewer = services.viewer()
    try:
        history = services.read_post_revisions(board_slug, thread_slug, parsed_post_number)
    except LookupError as exc:
        raise HTTPError(status=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc
    return Page.mounted(
        "boards/{board_slug}/threads/{thread_slug}/posts/{post_id}/revisions/page.html",
        current_path=request.url,
        viewer=viewer,
        history=history,
    )


def _parse_post_number(raw: object) -> int:
    try:
        return int(str(raw or ""))
    except ValueError as exc:
        raise HTTPError(status=404, detail=f"post not found: {raw}") from exc
