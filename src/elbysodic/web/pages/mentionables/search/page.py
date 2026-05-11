"""Community-scoped mentionable search endpoint."""

from __future__ import annotations

from chirp.http.request import Request
from chirp.http.response import JSONResponse

from elbysodic.web.state import get_services
from elbysodic.web.tenant import request_scoped_path


def get(request: Request) -> JSONResponse:
    query = str(request.query.get("q", ""))
    scope = str(request.query.get("scope", "all"))
    items = get_services(request).search_mentionables(query, scope=scope, limit=8)
    return JSONResponse.from_value(
        {"items": [_scoped_mentionable(request, item.to_dict()) for item in items]}
    )


def _scoped_mentionable(request: Request, item: dict[str, object]) -> dict[str, object]:
    href = item.get("href")
    if isinstance(href, str):
        return {**item, "href": request_scoped_path(request, href)}
    return item
