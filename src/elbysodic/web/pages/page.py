"""Home page for the initial Elbysodic shell."""

from __future__ import annotations

from contextlib import suppress

from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.domain.boards import is_community_board, is_desk_board, is_location_board
from elbysodic.services import policies
from elbysodic.services.forum import AppServices
from elbysodic.services.read_models import ForumView, MaterialSummary, WorldHub
from elbysodic.web.state import get_services
from elbysodic.web.tenant import request_tenant_slug


def _home_world_status(hub: WorldHub) -> tuple[str, str]:
    current_event = _first_material(hub.events)
    if current_event is not None:
        return current_event.material.title, current_event.rendered_summary

    featured = _first_material(hub.featured)
    if featured is not None:
        return featured.material.title, featured.rendered_summary

    guide = _first_material(hub.guides)
    if guide is not None:
        return guide.material.title, guide.rendered_summary

    return "World status", "Choose a door into the board's story, locations, and current threads."


def _first_material(materials: list[MaterialSummary]) -> MaterialSummary | None:
    return materials[0] if materials else None


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
    boards = services.list_boards()
    hub = services.world_hub()
    world_status_label, world_status_copy = _home_world_status(hub)
    realm_gateway = None
    with suppress(LookupError):
        realm_gateway = services.realm_gateway()
    return Page.mounted(
        "page.html",
        current_path=request.url,
        viewer=viewer,
        realm_gateway=realm_gateway,
        can_manage_home=_can_manage_home(viewer),
        world_status_label=world_status_label,
        world_status_copy=world_status_copy,
        boards=boards,
        location_boards=[
            summary
            for summary in boards
            if summary.board.parent_board_id is None and is_location_board(summary.board)
        ],
        community_boards=[
            summary
            for summary in boards
            if summary.board.parent_board_id is None and is_community_board(summary.board)
        ],
        desk_boards=[summary for summary in boards if is_desk_board(summary.board)],
        attention=services.needs_attention(),
        activity=services.recent_activity(),
    )


def _network_services(request: Request) -> tuple[AppServices, ForumView | None]:
    try:
        services = get_services(request)
        return services, services.viewer()
    except PermissionError:
        return get_services(), None


def _can_manage_home(viewer: ForumView) -> bool:
    return policies.can_manage_navigation(
        viewer.membership,
        viewer.role,
    ) or policies.can_manage_world(viewer.membership, viewer.role)
