"""Invite-only access posture page."""

from __future__ import annotations

from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.web.state import get_services
from elbysodic.web.tenant import request_tenant_slug


def get(request: Request) -> Page:
    services = get_services()
    tenant_slug = request_tenant_slug(request)
    community = None
    if tenant_slug is not None:
        community = services.public_studio_program(tenant_slug).community
    return Page.mounted(
        "request-access/page.html",
        current_path=request.url,
        page_title=f"Request access · {community.name if community else 'Elbysodic'}",
        viewer=None,
        account_visitor=services.account_visitor(request, current_community=community),
        community=community,
        show_community_shell=False,
    )
