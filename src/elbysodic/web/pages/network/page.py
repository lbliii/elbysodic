"""Studio network directory."""

from __future__ import annotations

from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.services.forum import AppServices
from elbysodic.services.read_models import ForumView, StudioNetworkProgramView
from elbysodic.web.state import get_services


def _matches_query(program: StudioNetworkProgramView, query: str) -> bool:
    if not query:
        return True
    catalog_keywords: list[str] = []
    if program.open_wanted_count:
        catalog_keywords.append("wanted hooks casting open roles")
    if program.application_count:
        catalog_keywords.append("application applications")
    if program.plotting_room_count:
        catalog_keywords.append("plotting rooms")
    if program.current_event:
        catalog_keywords.append("event current event")
    if "hp" in program.community.slug or "magic" in program.community.name.lower():
        catalog_keywords.append("magic school fantasy")
    if "jurassic" in program.community.slug:
        catalog_keywords.append("survival sci-fi science island")
    if "x-men" in program.community.slug or "mutant" in program.community.name.lower():
        catalog_keywords.append("superhero crisis mutants")
    if "small-town" in program.community.slug:
        catalog_keywords.append("small town found family")
    if "nyc" in program.community.slug:
        catalog_keywords.append("urban real life city")
    haystack_parts = [
        program.community.name,
        program.membership.display_name if program.membership else "",
        program.membership.username if program.membership else "",
        program.role.name if program.role else "",
        program.current_character.name if program.current_character else "",
        program.premise.material.title if program.premise else "",
        program.premise.material.summary if program.premise else "",
        program.current_event.material.title if program.current_event else "",
        program.current_event.material.summary if program.current_event else "",
        *catalog_keywords,
    ]
    haystack = " ".join(haystack_parts).lower()
    return query.lower() in haystack


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
        explore_programs=[
            program for program in network.programs if _matches_query(program, query)
        ],
        show_community_shell=False,
    )


def _network_services(request: Request) -> tuple[AppServices, ForumView | None]:
    try:
        services = get_services(request)
        return services, services.viewer()
    except PermissionError:
        return get_services(), None
