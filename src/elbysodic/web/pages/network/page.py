"""Studio network directory."""

from __future__ import annotations

from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.services.forum import AppServices
from elbysodic.services.read_models import ForumView
from elbysodic.web.state import get_services


def get(request: Request) -> Page:
    services, viewer = _network_services(request)
    query = str(request.query.get("q") or "").strip()
    network_explore = services.network_explore(query)
    mode = "search" if query else "explore"
    return Page.mounted(
        "network/page.html",
        current_path=request.url,
        page_title="Explore · Elbysodic",
        network_mode=mode,
        network_search_query=query,
        browse_facets=network_explore.browse_facets,
        filter_groups=network_explore.filter_groups,
        featured=None,
        home_slices=[],
        network_has_programs=bool(network_explore.results) or bool(query),
        relationship_lanes=network_explore.relationship_lanes,
        return_path=None,
        viewer=viewer,
        account_visitor=None if viewer is not None else services.account_visitor(request),
        explore_programs=network_explore.results,
        show_community_shell=False,
    )


def _network_services(request: Request) -> tuple[AppServices, ForumView | None]:
    try:
        services = get_services(request)
        return services, services.viewer()
    except PermissionError:
        return get_services(), None
