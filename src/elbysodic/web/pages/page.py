"""Home page for the initial Elbysodic shell."""

from __future__ import annotations

from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.services.forum import AppServices
from elbysodic.services.network import network_empty_state
from elbysodic.services.read_models import ForumView
from elbysodic.web.state import get_services
from elbysodic.web.tenant import request_tenant_slug


def get(request: Request) -> Page:
    tenant_slug = request_tenant_slug(request)
    if tenant_slug is None:
        services, viewer = _network_services(request)
        network_home = services.network_home()
        return Page.mounted(
            "network/page.html",
            current_path=request.url,
            page_title="Elbysodic",
            network_mode="home",
            network_search_query="",
            browse_facets=network_home.browse_facets,
            filter_groups=network_home.filter_groups,
            featured=network_home.featured,
            home_slices=network_home.slices,
            network_has_programs=network_home.featured is not None,
            relationship_lanes=[],
            return_path=network_home.return_path,
            explore_programs=[],
            network_empty_state=network_empty_state(),
            viewer=viewer,
            account_visitor=None if viewer is not None else services.account_visitor(request),
            show_community_shell=False,
        )

    try:
        services = get_services(request)
        viewer = services.viewer()
    except LookupError, PermissionError:
        services = get_services()
        try:
            gateway = services.public_realm_gateway(tenant_slug)
        except LookupError as exc:
            raise HTTPError(status=404, detail=str(exc)) from exc
        return Page.mounted(
            "page.html",
            current_path=request.url,
            page_title=gateway.program.community.name,
            viewer=None,
            account_visitor=services.account_visitor(
                request,
                current_community=gateway.program.community,
            ),
            realm_gateway=gateway,
            public_program=gateway.program,
            community=gateway.program.community,
            world_status_label=gateway.atmosphere.title,
            world_status_copy=gateway.atmosphere.copy,
            guidebook=gateway.guidebook,
            can_manage_home=False,
            show_community_shell=False,
        )
    home = services.realm_home()
    return Page.mounted(
        "page.html",
        current_path=request.url,
        viewer=viewer,
        realm_gateway=home.realm_gateway,
        can_manage_home=home.can_manage_home,
        world_status_label=home.world_status_label,
        world_status_copy=home.world_status_copy,
        boards=home.boards,
        location_boards=home.location_boards,
        community_boards=home.community_boards,
        desk_boards=home.desk_boards,
        attention=home.attention,
        activity=home.activity,
    )


def _network_services(request: Request) -> tuple[AppServices, ForumView | None]:
    try:
        services = get_services(request)
        return services, services.viewer()
    except PermissionError:
        return get_services(), None
