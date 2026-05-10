"""Route recovery helpers for realm-aware navigation misses."""

from __future__ import annotations

from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.services.recovery import (
    RecoveryKind,
    RecoveryLink,
    RecoverySwitchAction,
    RecoveryView,
    recover_next_url,
)
from elbysodic.web.state import get_services

__all__ = [
    "RecoveryKind",
    "RecoveryLink",
    "RecoverySwitchAction",
    "RecoveryView",
    "recover_missing_route",
    "recover_next_url",
]


def recover_missing_route(
    request: Request,
    *,
    kind: RecoveryKind,
    slug: str,
) -> Page:
    services = get_services(request)
    viewer = services.viewer()
    recovery = services.recovery_view(kind=kind, slug=slug)
    return Page(
        "recovery/_page.html",
        "page_content",
        page_block_name="page_root",
        current_path=request.url,
        viewer=viewer,
        recovery=recovery,
    )
