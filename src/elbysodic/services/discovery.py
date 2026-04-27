"""Facet-powered discovery for characters and open scenes."""

from __future__ import annotations

from typing import Protocol

from elbysodic.domain.models import (
    Board,
    Character,
    CharacterPlotHook,
    CommunityMembership,
    Facet,
    Post,
    Thread,
)
from elbysodic.services import policies
from elbysodic.services.facets import (
    FacetReadRepository,
    clean_facet_slugs,
    current_character_facet_tags,
    facet_filter_groups,
    facet_tags,
    resolve_facets,
)
from elbysodic.services.read_models import (
    DiscoveryCharacterResult,
    DiscoveryPlotHookResult,
    DiscoveryThreadResult,
    ForumView,
    PlotDiscovery,
)
from elbysodic.services.timestamps import timestamp_key


class DiscoveryRepository(FacetReadRepository, Protocol):
    def list_character_ids_for_facets(
        self,
        community_id: int,
        facet_ids: list[int],
    ) -> set[int]: ...

    def list_thread_ids_for_facets(
        self,
        community_id: int,
        facet_ids: list[int],
    ) -> set[int]: ...

    def list_character_plot_hook_ids_for_facets(
        self,
        community_id: int,
        facet_ids: list[int],
    ) -> set[int]: ...

    def list_community_characters(self, community_id: int) -> list[Character]: ...

    def get_membership(
        self,
        community_id: int,
        membership_id: int,
    ) -> CommunityMembership: ...

    def list_threads(self, community_id: int, board_id: int | None = None) -> list[Thread]: ...

    def list_boards(self, community_id: int) -> list[Board]: ...

    def list_posts(self, community_id: int, thread_id: int) -> list[Post]: ...

    def get_character(self, community_id: int, character_id: int) -> Character: ...

    def list_thread_participants(self, community_id: int, thread_id: int) -> list[Character]: ...

    def list_character_plot_hooks(
        self,
        community_id: int,
        *,
        status: str | None = "open",
    ) -> list[CharacterPlotHook]: ...

    def list_character_plot_hook_facets(
        self,
        community_id: int,
        plot_hook_id: int,
    ) -> list[Facet]: ...


def discover_plots(
    repo: DiscoveryRepository,
    viewer: ForumView,
    *,
    facet_slugs: list[str] | None = None,
) -> PlotDiscovery:
    active_face_facets = current_character_facet_tags(repo, viewer)
    requested_slugs = clean_facet_slugs(facet_slugs or [])
    used_active_face_lens = False
    if not requested_slugs and active_face_facets:
        requested_slugs = [
            tag.facet.slug
            for tag in active_face_facets
            if tag.group.slug in {"species", "affiliation", "location"}
        ][:3]
        used_active_face_lens = bool(requested_slugs)
    selected_facets = resolve_facets(repo, viewer.community.id, requested_slugs)
    requested_slugs = [facet.slug for facet in selected_facets]
    selected_ids = [facet.id for facet in selected_facets]
    selected_tags = facet_tags(repo, viewer.community.id, selected_facets)
    character_ids = (
        repo.list_character_ids_for_facets(viewer.community.id, selected_ids)
        if selected_ids
        else {character.id for character in repo.list_community_characters(viewer.community.id)}
    )
    thread_ids = (
        repo.list_thread_ids_for_facets(viewer.community.id, selected_ids)
        if selected_ids
        else {thread.id for thread in repo.list_threads(viewer.community.id)}
    )
    plot_hook_ids = (
        repo.list_character_plot_hook_ids_for_facets(viewer.community.id, selected_ids)
        if selected_ids
        else {hook.id for hook in repo.list_character_plot_hooks(viewer.community.id)}
    )
    return PlotDiscovery(
        selected_facets=selected_tags,
        active_face_facets=active_face_facets,
        filter_groups=facet_filter_groups(
            repo,
            viewer.community.id,
            requested_slugs,
        ),
        plot_hooks=discovery_plot_hooks(
            repo,
            viewer,
            plot_hook_ids,
            selected_ids,
        ),
        characters=discovery_characters(
            repo,
            viewer,
            character_ids,
            selected_ids,
        ),
        open_threads=discovery_open_threads(
            repo,
            viewer,
            thread_ids,
            selected_ids,
        ),
        used_active_face_lens=used_active_face_lens,
    )


def discovery_plot_hooks(
    repo: DiscoveryRepository,
    viewer: ForumView,
    plot_hook_ids: set[int],
    selected_facet_ids: list[int],
) -> list[DiscoveryPlotHookResult]:
    selected = set(selected_facet_ids)
    results = []
    for plot_hook in repo.list_character_plot_hooks(viewer.community.id):
        if plot_hook.id not in plot_hook_ids or plot_hook.status != "open":
            continue
        character = repo.get_character(viewer.community.id, plot_hook.character_id)
        if character.application_status != "accepted":
            continue
        author = repo.get_membership(viewer.community.id, plot_hook.author_membership_id)
        if not author.is_active:
            continue
        facets = facet_tags(
            repo,
            viewer.community.id,
            repo.list_character_plot_hook_facets(viewer.community.id, plot_hook.id),
        )
        matching_facets = [tag for tag in facets if tag.facet.id in selected]
        results.append(
            DiscoveryPlotHookResult(
                plot_hook=plot_hook,
                character=character,
                author_membership=author,
                facets=facets,
                matching_facets=matching_facets,
            )
        )
    return sorted(
        results,
        key=lambda item: (
            -len(item.matching_facets),
            timestamp_key(item.plot_hook.updated_at),
            item.plot_hook.id,
        ),
        reverse=True,
    )


def discovery_characters(
    repo: DiscoveryRepository,
    viewer: ForumView,
    character_ids: set[int],
    selected_facet_ids: list[int],
) -> list[DiscoveryCharacterResult]:
    selected = set(selected_facet_ids)
    results = []
    for character in repo.list_community_characters(viewer.community.id):
        if character.id not in character_ids:
            continue
        owner = repo.get_membership(viewer.community.id, character.membership_id)
        if not owner.is_active:
            continue
        facets = facet_tags(
            repo,
            viewer.community.id,
            repo.list_character_facets(viewer.community.id, character.id),
        )
        matching_facets = [tag for tag in facets if tag.facet.id in selected]
        results.append(
            DiscoveryCharacterResult(
                character=character,
                owner_membership=owner,
                facets=facets,
                matching_facets=matching_facets,
            )
        )
    return sorted(
        results,
        key=lambda item: (
            -len(item.matching_facets),
            item.character.name,
            item.character.id,
        ),
    )


def discovery_open_threads(
    repo: DiscoveryRepository,
    viewer: ForumView,
    thread_ids: set[int],
    selected_facet_ids: list[int],
) -> list[DiscoveryThreadResult]:
    selected = set(selected_facet_ids)
    visible_boards = {
        board.id: board
        for board in repo.list_boards(viewer.community.id)
        if policies.can_view_board(viewer.membership, board, viewer.role)
    }
    results = []
    for thread in repo.list_threads(viewer.community.id):
        if thread.id not in thread_ids or thread.status != "open" or thread.is_locked:
            continue
        board = visible_boards.get(thread.board_id)
        if board is None:
            continue
        facets = facet_tags(
            repo,
            viewer.community.id,
            repo.list_thread_facets(viewer.community.id, thread.id),
        )
        matching_facets = [tag for tag in facets if tag.facet.id in selected]
        posts = repo.list_posts(viewer.community.id, thread.id)
        results.append(
            DiscoveryThreadResult(
                board=board,
                thread=thread,
                author=repo.get_character(viewer.community.id, thread.author_character_id),
                participants=repo.list_thread_participants(viewer.community.id, thread.id),
                facets=facets,
                matching_facets=matching_facets,
                reply_count=max(0, len(posts) - 1),
            )
        )
    return sorted(
        results,
        key=lambda item: (
            -len(item.matching_facets),
            timestamp_key(item.thread.updated_at),
            item.thread.id,
        ),
        reverse=True,
    )
