"""Scoped public search surface."""

from __future__ import annotations

from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.services.forum import AppServices
from elbysodic.services.read_models import ForumView
from elbysodic.web.state import get_services
from elbysodic.web.tenant import request_tenant_slug


def get(request: Request) -> Page:
    query = str(request.query.get("q") or "").strip()
    tenant_slug = request_tenant_slug(request)
    services, viewer = _search_services(request)
    try:
        search = (
            services.community_search(tenant_slug, query)
            if tenant_slug is not None
            else services.global_search(query)
        )
        community = (
            services.public_studio_program(tenant_slug).community
            if tenant_slug is not None
            else None
        )
    except LookupError as exc:
        raise HTTPError(status=404, detail=str(exc)) from exc
    account_visitor = (
        None
        if viewer is not None
        else services.account_visitor(request, current_community=community)
    )
    return Page.mounted(
        "search/page.html",
        current_path=request.url,
        page_title=f"Search · {search.scope_label}",
        viewer=viewer,
        account_visitor=account_visitor,
        community=community,
        scoped_search=search,
        search_query=query,
        show_community_shell=viewer is not None and tenant_slug is not None,
    )


def _search_services(request: Request) -> tuple[AppServices, ForumView | None]:
    try:
        services = get_services(request)
        return services, services.viewer()
    except LookupError, PermissionError:
        return get_services(), None
