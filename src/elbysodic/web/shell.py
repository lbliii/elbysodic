"""Request-scoped shell preferences for rendered app chrome."""

from __future__ import annotations

from chirp.context import get_request
from chirp.http.request import Request

SIDEBAR_HIDDEN_COOKIE = "elbysodic_sidebar_hidden_v2"
SIDEBAR_HIDDEN_CLASS = "elbysodic-app-shell--sidebar-hidden"


def sidebar_is_hidden(request: Request | None = None) -> bool:
    """Return the persisted sidebar visibility preference for the request."""

    if request is None:
        try:
            request = get_request()
        except LookupError:
            return False
    return request.cookies.get(SIDEBAR_HIDDEN_COOKIE) == "true"
