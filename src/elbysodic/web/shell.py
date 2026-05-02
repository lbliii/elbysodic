"""Shell navigation compatibility helpers."""

from __future__ import annotations

from typing import Any

from chirp.http.request import Request
from chirp.http.response import Response


class BoostedMainReselectMiddleware:
    """Bridge boosted main navigation until Chirp outlet rendering is released."""

    async def __call__(self, request: Request, next: Any) -> Any:
        response = await next(request)
        if not _needs_page_root_reselect(request, response):
            return response
        return response.with_hx_reselect("#page-root")


def _needs_page_root_reselect(request: Request, response: Any) -> bool:
    if not isinstance(response, Response):
        return False
    if not request.is_boosted or request.htmx_target_id != "main":
        return False
    if response.render_intent != "fragment":
        return False
    if "text/html" not in response.content_type:
        return False
    body = response.text
    return 'id="page-content"' not in body and 'id="page-root"' in body
