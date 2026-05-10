"""Studio network directory."""

from __future__ import annotations

from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.services.forum import AppServices
from elbysodic.services.network import search_studio_network
from elbysodic.services.read_models import ForumView
from elbysodic.web.state import get_services


def get(request: Request) -> Page:
    services, viewer = _network_services(request)
    network = services.studio_network() if viewer is not None else services.public_studio_network()
    query = str(request.query.get("q") or "").strip()
    return Page(
        "network/page.html",
        "page_content",
        page_block_name="page_root",
        current_path=request.url,
        page_title="Explore · Elbysodic",
        network_mode="explore",
        network_search_query=query,
        viewer=viewer,
        network=network,
        explore_programs=search_studio_network(network, query),
        show_community_shell=False,
    )


def _network_services(request: Request) -> tuple[AppServices, ForumView | None]:
    try:
        services = get_services(request)
        return services, services.viewer()
    except PermissionError:
        return get_services(), None
