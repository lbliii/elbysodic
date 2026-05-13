"""Network catalog search helpers."""

from __future__ import annotations

from elbysodic.services.read_models import (
    PublicCatalogCard,
    StudioNetworkDirectory,
    StudioNetworkProgramView,
)


def search_studio_network(
    directory: StudioNetworkDirectory,
    query: str,
) -> list[StudioNetworkProgramView]:
    """Return network programs matching a public catalog query."""

    normalized_query = query.strip().lower()
    if not normalized_query:
        return list(directory.programs)
    return [
        program
        for program in directory.programs
        if normalized_query in _program_search_text(program)
    ]


def search_public_catalog(
    cards: list[PublicCatalogCard],
    query: str,
) -> list[PublicCatalogCard]:
    """Return public catalog cards matching a public discovery query."""

    normalized_query = query.strip().lower()
    if not normalized_query:
        return list(cards)
    return [card for card in cards if normalized_query in _public_catalog_search_text(card)]


def _program_search_text(program: StudioNetworkProgramView) -> str:
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
    return " ".join(haystack_parts).lower()


def _public_catalog_search_text(card: PublicCatalogCard) -> str:
    catalog_keywords: list[str] = []
    if card.open_wanted_count:
        catalog_keywords.append("wanted hooks casting open roles")
    if card.application_material_count:
        catalog_keywords.append("application applications first face")
    if card.current_event:
        catalog_keywords.append("event current event")
    if "hp" in card.community.slug or "magic" in card.community.name.lower():
        catalog_keywords.append("magic school fantasy")
    if "jurassic" in card.community.slug:
        catalog_keywords.append("survival sci-fi science island")
    if "x-men" in card.community.slug or "mutant" in card.community.name.lower():
        catalog_keywords.append("superhero crisis mutants")
    if "small-town" in card.community.slug:
        catalog_keywords.append("small town found family slow burn")
    if "nyc" in card.community.slug:
        catalog_keywords.append("urban real life city")
    haystack_parts = [
        card.community.name,
        card.premise.material.title if card.premise else "",
        card.premise.material.summary if card.premise else "",
        card.current_event.material.title if card.current_event else "",
        card.current_event.material.summary if card.current_event else "",
        *catalog_keywords,
    ]
    return " ".join(haystack_parts).lower()
