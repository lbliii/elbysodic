"""Community-scoped mentionable search endpoint."""

from __future__ import annotations

from chirp.http.request import Request
from chirp.http.response import JSONResponse

from elbysodic.web.state import get_services


def get(request: Request) -> JSONResponse:
    query = str(request.query.get("q", ""))
    scope = str(request.query.get("scope", "all"))
    items = get_services().search_mentionables(query, scope=scope, limit=8)
    return JSONResponse.from_value({"items": [item.to_dict() for item in items]})
