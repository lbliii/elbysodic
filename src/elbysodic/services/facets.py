"""Facet read helpers for community world lenses."""

from __future__ import annotations

from elbysodic.db import ForumRepository
from elbysodic.domain.models import Facet
from elbysodic.services.read_models import (
    FacetFilterGroup,
    FacetFilterOption,
    FacetTag,
    ForumView,
)


def current_character_facet_tags(repo: ForumRepository, viewer: ForumView) -> list[FacetTag]:
    if viewer.current_character is None:
        return []
    return facet_tags(
        repo,
        viewer.community.id,
        repo.list_character_facets(viewer.community.id, viewer.current_character.id),
    )


def current_character_facet_ids(repo: ForumRepository, viewer: ForumView) -> set[int]:
    return {tag.facet.id for tag in current_character_facet_tags(repo, viewer)}


def facet_tags(repo: ForumRepository, community_id: int, facets: list[Facet]) -> list[FacetTag]:
    groups = {group.id: group for group in repo.list_facet_groups(community_id)}
    return [
        FacetTag(group=groups[facet.facet_group_id], facet=facet)
        for facet in facets
        if facet.facet_group_id in groups
    ]


def resolve_facets(repo: ForumRepository, community_id: int, slugs: list[str]) -> list[Facet]:
    facets = []
    for slug in clean_facet_slugs(slugs):
        try:
            facets.append(repo.get_facet_by_slug(community_id, slug))
        except LookupError:
            continue
    return facets


def clean_facet_slugs(values: list[str]) -> list[str]:
    slugs: list[str] = []
    for value in values:
        for part in value.split(","):
            slug = part.strip().lower()
            if slug and slug not in slugs:
                slugs.append(slug)
    return slugs


def facet_filter_groups(
    repo: ForumRepository,
    community_id: int,
    selected_slugs: list[str],
) -> list[FacetFilterGroup]:
    selected = set(selected_slugs)
    selected_order = [slug for slug in selected_slugs if slug in selected]
    tags = facet_tags(repo, community_id, repo.list_facets(community_id))
    groups = repo.list_facet_groups(community_id)
    return [
        FacetFilterGroup(
            group=group,
            options=[
                FacetFilterOption(
                    tag=tag,
                    href=facet_filter_href(selected_order, tag.facet.slug),
                    is_selected=tag.facet.slug in selected,
                )
                for tag in tags
                if tag.group.id == group.id
            ],
        )
        for group in groups
        if group.visibility == "public"
    ]


def facet_filter_href(selected_slugs: list[str], slug: str) -> str:
    if slug in selected_slugs:
        next_slugs = [selected_slug for selected_slug in selected_slugs if selected_slug != slug]
    else:
        next_slugs = [*selected_slugs, slug]
    if not next_slugs:
        return "/discover?facets=none"
    return f"/discover?facets={','.join(next_slugs)}"
