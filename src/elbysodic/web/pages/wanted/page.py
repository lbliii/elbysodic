"""Wanted hooks board."""

from __future__ import annotations

from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.web.state import get_services
from elbysodic.web.tenant import request_tenant_slug


def get(request: Request) -> Page:
    tenant_slug = request_tenant_slug(request)
    try:
        services = get_services(request)
        viewer = services.viewer()
        board = services.wanted_ads()
        community = viewer.community
    except LookupError, PermissionError:
        if tenant_slug is None:
            raise
        services = get_services()
        viewer = None
        try:
            board = services.public_wanted_ads(tenant_slug)
            community = services.public_studio_program(tenant_slug).community
        except LookupError as exc:
            raise HTTPError(status=404, detail=str(exc)) from exc
    return Page.mounted(
        "wanted/page.html",
        current_path=request.url,
        viewer=viewer,
        community=community,
        board=board,
        show_community_shell=viewer is not None,
    )
