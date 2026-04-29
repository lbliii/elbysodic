"""Character plot-hook service helpers."""

from __future__ import annotations

import re
from typing import Protocol

from elbysodic.domain.models import (
    Character,
    CharacterPlotHook,
    CharacterPlotHookInterest,
    CommunityMembership,
    Facet,
    Material,
)
from elbysodic.services import policies
from elbysodic.services.facets import (
    FacetReadRepository,
    facet_choice_groups,
    facet_tags,
    resolve_facets,
)
from elbysodic.services.markup import render_prose_body
from elbysodic.services.posts import PostViewRepository, post_mention_links
from elbysodic.services.read_models import (
    CharacterPlotHookDetail,
    CharacterPlotHookInterestView,
    CharacterPlotHookSummary,
    ForumView,
)
from elbysodic.services.timestamps import timestamp_label

PLOT_HOOK_STATUSES = ("open", "plotting", "paused", "closed", "archived")
PLOT_HOOK_TYPES = ("scene", "relationship", "connection", "event", "other")


class PlotHookReadRepository(FacetReadRepository, PostViewRepository, Protocol):
    def get_character(self, community_id: int, character_id: int) -> Character: ...

    def get_character_by_slug(self, community_id: int, slug: str) -> Character: ...

    def get_membership(
        self,
        community_id: int,
        membership_id: int,
    ) -> CommunityMembership: ...

    def get_material(self, community_id: int, material_id: int) -> Material: ...

    def list_character_plot_hooks(
        self,
        community_id: int,
        *,
        status: str | None = "open",
    ) -> list[CharacterPlotHook]: ...

    def list_character_plot_hooks_for_character(
        self,
        community_id: int,
        character_id: int,
        *,
        status: str | None = "open",
    ) -> list[CharacterPlotHook]: ...

    def get_character_plot_hook_by_slug(
        self,
        community_id: int,
        character_id: int,
        slug: str,
    ) -> CharacterPlotHook: ...

    def list_character_plot_hook_facets(
        self,
        community_id: int,
        plot_hook_id: int,
    ) -> list[Facet]: ...

    def list_character_plot_hook_interests(
        self,
        community_id: int,
        plot_hook_id: int,
        *,
        status: str | None = None,
    ) -> list[CharacterPlotHookInterest]: ...


class PlotHookSummaryRepository(FacetReadRepository, Protocol):
    def get_character(self, community_id: int, character_id: int) -> Character: ...

    def get_membership(
        self,
        community_id: int,
        membership_id: int,
    ) -> CommunityMembership: ...

    def get_material(self, community_id: int, material_id: int) -> Material: ...

    def list_character_plot_hook_facets(
        self,
        community_id: int,
        plot_hook_id: int,
    ) -> list[Facet]: ...


class PlotHookRepository(PlotHookReadRepository, Protocol):
    def create_character_plot_hook(
        self,
        community_id: int,
        author_membership_id: int,
        character_id: int,
        slug: str,
        title: str,
        *,
        related_material_id: int | None = None,
        hook_type: str = "scene",
        summary: str = "",
        body: str = "",
        status: str = "open",
    ) -> CharacterPlotHook: ...

    def update_character_plot_hook(
        self,
        community_id: int,
        plot_hook_id: int,
        *,
        title: str,
        hook_type: str,
        summary: str,
        body: str,
        status: str,
        related_material_id: int | None = None,
    ) -> CharacterPlotHook: ...

    def set_character_plot_hook_facets(
        self,
        community_id: int,
        plot_hook_id: int,
        facet_ids: list[int],
    ) -> None: ...

    def create_character_plot_hook_interest(
        self,
        community_id: int,
        plot_hook_id: int,
        membership_id: int,
        character_id: int,
        *,
        note: str = "",
        status: str = "interested",
    ) -> CharacterPlotHookInterest: ...

    def create_notification(
        self,
        community_id: int,
        membership_id: int,
        *,
        kind: str,
        thread_id: int | None = None,
        post_id: int | None = None,
        wanted_ad_id: int | None = None,
        wanted_ad_interest_id: int | None = None,
        character_plot_hook_id: int | None = None,
        character_id: int | None = None,
        actor_membership_id: int,
        actor_character_id: int | None,
    ): ...


def plot_hook_summary(
    repo: PlotHookSummaryRepository,
    community_id: int,
    plot_hook: CharacterPlotHook,
) -> CharacterPlotHookSummary:
    return CharacterPlotHookSummary(
        plot_hook=plot_hook,
        character=repo.get_character(community_id, plot_hook.character_id),
        author_membership=repo.get_membership(community_id, plot_hook.author_membership_id),
        related_material=(
            repo.get_material(community_id, plot_hook.related_material_id)
            if plot_hook.related_material_id is not None
            else None
        ),
        facets=facet_tags(
            repo,
            community_id,
            repo.list_character_plot_hook_facets(community_id, plot_hook.id),
        ),
        hook_type_label=plot_hook_type_label(plot_hook.hook_type),
    )


def read_plot_hook(
    repo: PlotHookReadRepository,
    viewer: ForumView,
    character_slug: str,
    hook_slug: str,
) -> CharacterPlotHookDetail:
    character = repo.get_character_by_slug(viewer.community.id, character_slug)
    plot_hook = repo.get_character_plot_hook_by_slug(
        viewer.community.id,
        character.id,
        hook_slug,
    )
    if plot_hook.status == "archived" and not can_manage_plot_hook(viewer, plot_hook):
        raise LookupError(f"plot hook not found in community {viewer.community.id}: {hook_slug}")
    interests = [
        plot_hook_interest_view(repo, viewer.community.id, interest)
        for interest in repo.list_character_plot_hook_interests(
            viewer.community.id,
            plot_hook.id,
        )
    ]
    plot_hook_facets = repo.list_character_plot_hook_facets(viewer.community.id, plot_hook.id)
    viewer_interest = None
    if viewer.current_character is not None:
        viewer_interest = next(
            (
                interest
                for interest in interests
                if interest.interest.character_id == viewer.current_character.id
            ),
            None,
        )
    return CharacterPlotHookDetail(
        plot_hook=plot_hook,
        character=character,
        author_membership=repo.get_membership(viewer.community.id, plot_hook.author_membership_id),
        related_material=(
            repo.get_material(viewer.community.id, plot_hook.related_material_id)
            if plot_hook.related_material_id is not None
            else None
        ),
        facets=facet_tags(repo, viewer.community.id, plot_hook_facets),
        facet_choices=facet_choice_groups(
            repo,
            viewer.community.id,
            {facet.id for facet in plot_hook_facets},
        ),
        interests=interests,
        viewer_interest=viewer_interest,
        can_express_interest=(
            plot_hook.status == "open"
            and viewer.current_character is not None
            and viewer_interest is None
            and plot_hook.author_membership_id != viewer.membership.id
        ),
        can_manage=can_manage_plot_hook(viewer, plot_hook),
        rendered_body=render_prose_body(
            plot_hook.body,
            mentions=post_mention_links(repo, viewer.community.id),
        ),
        hook_type_label=plot_hook_type_label(plot_hook.hook_type),
    )


def create_plot_hook(
    repo: PlotHookRepository,
    viewer: ForumView,
    character_slug: str,
    *,
    title: str,
    hook_type: str,
    summary: str,
    body: str,
    facet_slugs: list[str],
) -> CharacterPlotHook:
    character = repo.get_character_by_slug(viewer.community.id, character_slug)
    if not policies.can_post_as(viewer.membership, character):
        raise PermissionError(
            f"membership {viewer.membership.id} cannot create hooks for character {character.id}"
        )
    cleaned_title = title.strip()
    if not cleaned_title:
        raise ValueError("plot hook title is required")
    cleaned_hook_type = hook_type.strip()
    if cleaned_hook_type not in PLOT_HOOK_TYPES:
        raise ValueError("choose a supported plot hook type")
    plot_hook = repo.create_character_plot_hook(
        viewer.community.id,
        viewer.membership.id,
        character.id,
        unique_plot_hook_slug(repo, viewer.community.id, character.id, cleaned_title),
        cleaned_title,
        hook_type=cleaned_hook_type,
        summary=summary.strip(),
        body=body.strip(),
    )
    facets = resolve_facets(repo, viewer.community.id, facet_slugs)
    repo.set_character_plot_hook_facets(
        viewer.community.id,
        plot_hook.id,
        [facet.id for facet in facets],
    )
    return plot_hook


def update_plot_hook(
    repo: PlotHookRepository,
    viewer: ForumView,
    character_slug: str,
    hook_slug: str,
    *,
    title: str,
    hook_type: str,
    summary: str,
    body: str,
    status: str,
    facet_slugs: list[str],
) -> CharacterPlotHook:
    detail = read_plot_hook(repo, viewer, character_slug, hook_slug)
    if not detail.can_manage:
        raise PermissionError(
            f"membership {viewer.membership.id} cannot manage plot hook {detail.plot_hook.id}"
        )
    cleaned_title = title.strip()
    if not cleaned_title:
        raise ValueError("plot hook title is required")
    cleaned_hook_type = hook_type.strip()
    cleaned_status = status.strip()
    if cleaned_hook_type not in PLOT_HOOK_TYPES:
        raise ValueError("choose a supported plot hook type")
    if cleaned_status not in PLOT_HOOK_STATUSES:
        raise ValueError("choose a supported plot hook status")
    plot_hook = repo.update_character_plot_hook(
        viewer.community.id,
        detail.plot_hook.id,
        title=cleaned_title,
        hook_type=cleaned_hook_type,
        summary=summary.strip(),
        body=body.strip(),
        status=cleaned_status,
        related_material_id=detail.plot_hook.related_material_id,
    )
    facets = resolve_facets(repo, viewer.community.id, facet_slugs)
    repo.set_character_plot_hook_facets(
        viewer.community.id,
        plot_hook.id,
        [facet.id for facet in facets],
    )
    return plot_hook


def express_plot_hook_interest(
    repo: PlotHookRepository,
    viewer: ForumView,
    character_slug: str,
    hook_slug: str,
) -> CharacterPlotHookInterest:
    if viewer.current_character is None:
        raise ValueError("create a character before expressing interest")
    detail = read_plot_hook(repo, viewer, character_slug, hook_slug)
    if detail.plot_hook.status != "open":
        raise ValueError(f"plot hook {detail.plot_hook.id} is not open")
    if detail.plot_hook.author_membership_id == viewer.membership.id:
        raise ValueError("you cannot express interest in your own plot hook")
    interest = repo.create_character_plot_hook_interest(
        viewer.community.id,
        detail.plot_hook.id,
        viewer.membership.id,
        viewer.current_character.id,
    )
    repo.create_notification(
        viewer.community.id,
        detail.plot_hook.author_membership_id,
        kind="plot_hook_interest",
        character_plot_hook_id=detail.plot_hook.id,
        actor_membership_id=viewer.membership.id,
        actor_character_id=viewer.current_character.id,
    )
    return interest


def plot_hook_interest_view(
    repo: PlotHookReadRepository,
    community_id: int,
    interest: CharacterPlotHookInterest,
) -> CharacterPlotHookInterestView:
    return CharacterPlotHookInterestView(
        interest=interest,
        membership=repo.get_membership(community_id, interest.membership_id),
        character=repo.get_character(community_id, interest.character_id),
        created_at_label=timestamp_label(interest.created_at),
    )


def plot_hook_type_label(hook_type: str) -> str:
    return {
        "scene": "Scene",
        "relationship": "Relationship",
        "connection": "Connection",
        "event": "Event",
        "other": "Other",
    }.get(hook_type, hook_type.replace("_", " ").title())


def can_manage_plot_hook(viewer: ForumView, plot_hook: CharacterPlotHook) -> bool:
    return plot_hook.author_membership_id == viewer.membership.id or policies.can_manage_casting(
        viewer.membership,
        viewer.role,
    )


def unique_plot_hook_slug(
    repo: PlotHookReadRepository,
    community_id: int,
    character_id: int,
    title: str,
) -> str:
    base = slugify(title)
    slug = base
    suffix = 2
    while True:
        try:
            repo.get_character_plot_hook_by_slug(community_id, character_id, slug)
        except LookupError:
            return slug
        slug = f"{base}-{suffix}"
        suffix += 1


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "plot-hook"
