"""Home page for the initial Elbysodic shell."""

from __future__ import annotations

from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.domain.boards import is_community_board, is_desk_board, is_location_board
from elbysodic.services.read_models import MaterialSummary, WorldHub
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
    services = get_services(request)
    if request_tenant_slug(request) is None:
        return Page(
            "network/page.html",
            "page_content",
            page_block_name="page_root",
            current_path=request.url,
            viewer=services.viewer(),
            network=services.studio_network(),
            show_community_shell=False,
        )

    viewer = services.viewer()
    boards = services.list_boards()
    hub = services.world_hub()
    world_status_label, world_status_copy = _home_world_status(hub)
    return Page(
        "page.html",
        "page_content",
        page_block_name="page_root",
        current_path=request.url,
        viewer=viewer,
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
