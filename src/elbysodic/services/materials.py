"""World material, event, and canon read-model helpers."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from elbysodic.domain.models import (
    Board,
    Character,
    CommunityMembership,
    Facet,
    Material,
    Post,
    Thread,
    WantedAd,
)
from elbysodic.domain.vocabulary import material_type_label
from elbysodic.services import policies
from elbysodic.services.facets import FacetReadRepository, facet_tags, facet_tags_with_groups
from elbysodic.services.markup import post_snippet, render_prose_body
from elbysodic.services.posts import PostViewRepository, post_mention_links
from elbysodic.services.read_models import (
    MATERIAL_STATUSES,
    BoardSummary,
    ContinuityBeat,
    DiscoveryThreadResult,
    EventAction,
    FacetTag,
    ForumView,
    MaterialDetail,
    MaterialSummary,
    WantedAdSummary,
)
from elbysodic.services.timestamps import timestamp_key, timestamp_label

type BoardSummaryFactory = Callable[[Board], BoardSummary]
type WantedAdSummaryFactory = Callable[[WantedAd], WantedAdSummary]


class MaterialSummaryRepository(FacetReadRepository, Protocol):
    def list_material_facets(self, community_id: int, material_id: int) -> list[Facet]: ...

    def list_material_facets_for_materials(
        self,
        community_ids: list[int],
        material_ids: list[int],
    ) -> dict[tuple[int, int], list[Facet]]: ...


class MaterialReadRepository(MaterialSummaryRepository, PostViewRepository, Protocol):
    def get_material_by_slug(self, community_id: int, slug: str) -> Material: ...

    def update_material(
        self,
        community_id: int,
        material_id: int,
        *,
        title: str,
        material_type: str,
        summary: str,
        body: str,
        status: str = "published",
        sort_order: int = 0,
        is_featured: bool = False,
    ) -> Material: ...

    def list_materials(self, community_id: int, *, status: str | None = None) -> list[Material]: ...

    def list_boards(self, community_id: int) -> list[Board]: ...

    def list_threads(self, community_id: int, board_id: int | None = None) -> list[Thread]: ...

    def list_posts(self, community_id: int, thread_id: int) -> list[Post]: ...

    def list_posts_for_threads(
        self,
        community_id: int,
        thread_ids: list[int],
    ) -> dict[int, list[Post]]: ...

    def list_thread_participants(self, community_id: int, thread_id: int) -> list[Character]: ...

    def list_thread_participants_for_threads(
        self,
        community_id: int,
        thread_ids: list[int],
    ) -> dict[int, list[Character]]: ...

    def list_board_facets(self, community_id: int, board_id: int) -> list[Facet]: ...

    def list_board_facets_for_boards(
        self,
        community_id: int,
        board_ids: list[int],
    ) -> dict[int, list[Facet]]: ...

    def list_thread_facets_for_threads(
        self,
        community_id: int,
        thread_ids: list[int],
    ) -> dict[int, list[Facet]]: ...

    def list_wanted_ads(
        self, community_id: int, *, status: str | None = "open"
    ) -> list[WantedAd]: ...

    def list_wanted_ad_facets(self, community_id: int, wanted_ad_id: int) -> list[Facet]: ...

    def list_wanted_ad_facets_for_wanted_ads(
        self,
        community_id: int,
        wanted_ad_ids: list[int],
    ) -> dict[int, list[Facet]]: ...

    def get_character(self, community_id: int, character_id: int) -> Character: ...

    def list_characters_by_ids(
        self,
        community_id: int,
        character_ids: list[int],
    ) -> dict[int, Character]: ...

    def get_membership(self, community_id: int, membership_id: int) -> CommunityMembership: ...


def material_summary(
    repo: MaterialSummaryRepository,
    community_id: int,
    material: Material,
) -> MaterialSummary:
    return _material_summary_from_tags(
        material,
        facet_tags(
            repo,
            community_id,
            repo.list_material_facets(community_id, material.id),
        ),
    )


def _material_summary_from_tags(
    material: Material,
    facets: list[FacetTag],
) -> MaterialSummary:
    return MaterialSummary(
        material=material,
        facets=facets,
        rendered_summary=material.summary or post_snippet(material.body, limit=160),
        type_label=material_type_label(material.material_type),
    )


def material_detail(
    repo: MaterialReadRepository,
    viewer: ForumView,
    material: Material,
    *,
    board_summary_factory: BoardSummaryFactory,
    wanted_summary_factory: WantedAdSummaryFactory,
) -> MaterialDetail:
    facets = facet_tags(
        repo,
        viewer.community.id,
        repo.list_material_facets(viewer.community.id, material.id),
    )
    facet_ids = {tag.facet.id for tag in facets}
    related = related_materials(repo, viewer.community.id, material, facet_ids)
    related_wanted_ads = material_related_wanted_ads(
        repo,
        viewer,
        material,
        facet_ids,
        wanted_summary_factory=wanted_summary_factory,
    )[:4]
    related_locations = material_related_locations(
        repo,
        viewer,
        facet_ids,
        board_summary_factory=board_summary_factory,
    )[:4]
    related_scenes = material_related_scenes(repo, viewer, facet_ids)[:4]
    return MaterialDetail(
        material=material,
        facets=facets,
        rendered_body=render_prose_body(
            material.body,
            mentions=post_mention_links(repo, viewer.community.id),
        ),
        type_label=material_type_label(material.material_type),
        related_materials=related[:4],
        related_locations=related_locations,
        related_scenes=related_scenes,
        related_wanted_ads=related_wanted_ads,
        continuity_beats=material_continuity_beats(
            material,
            related_locations,
            related_scenes,
            related_wanted_ads,
        ),
        event_actions=material_event_actions(
            material,
            facets,
            related_locations,
            related_scenes,
            related_wanted_ads,
        ),
        can_manage=policies.can_manage_world(viewer.membership, viewer.role),
    )


def public_material_detail(
    repo: MaterialReadRepository,
    community_id: int,
    material: Material,
    *,
    wanted_summary_factory: WantedAdSummaryFactory,
) -> MaterialDetail:
    facets = facet_tags(
        repo,
        community_id,
        repo.list_material_facets(community_id, material.id),
    )
    facet_ids = {tag.facet.id for tag in facets}
    related = related_materials(repo, community_id, material, facet_ids)
    related_wanted_ads = public_material_related_wanted_ads(
        repo,
        community_id,
        material,
        facet_ids,
        wanted_summary_factory=wanted_summary_factory,
    )[:4]
    return MaterialDetail(
        material=material,
        facets=facets,
        rendered_body=render_prose_body(
            material.body,
            mentions=post_mention_links(repo, community_id),
        ),
        type_label=material_type_label(material.material_type),
        related_materials=related[:4],
        related_locations=[],
        related_scenes=[],
        related_wanted_ads=related_wanted_ads,
        continuity_beats=material_continuity_beats(
            material,
            [],
            [],
            related_wanted_ads,
        ),
        event_actions=material_event_actions(
            material,
            [],
            [],
            [],
            related_wanted_ads,
        ),
        can_manage=False,
    )


def update_material_production_state(
    repo: MaterialReadRepository,
    viewer: ForumView,
    material_slug: str,
    *,
    status: str,
    is_featured: bool | None = None,
) -> Material:
    if not policies.can_manage_world(viewer.membership, viewer.role):
        raise PermissionError(f"membership {viewer.membership.id} cannot manage world materials")
    material = repo.get_material_by_slug(viewer.community.id, material_slug)
    cleaned_status = status.strip()
    if cleaned_status not in MATERIAL_STATUSES:
        raise ValueError("choose a supported material status")
    next_featured = material.is_featured if is_featured is None else is_featured
    if material.material_type == "event" and next_featured:
        for event in repo.list_materials(viewer.community.id, status=None):
            if event.id == material.id or event.material_type != "event" or not event.is_featured:
                continue
            repo.update_material(
                viewer.community.id,
                event.id,
                title=event.title,
                material_type=event.material_type,
                summary=event.summary,
                body=event.body,
                status=event.status,
                sort_order=event.sort_order,
                is_featured=False,
            )
    return repo.update_material(
        viewer.community.id,
        material.id,
        title=material.title,
        material_type=material.material_type,
        summary=material.summary,
        body=material.body,
        status=cleaned_status,
        sort_order=material.sort_order,
        is_featured=next_featured,
    )


def related_materials(
    repo: MaterialReadRepository,
    community_id: int,
    material: Material,
    facet_ids: set[int],
) -> list[MaterialSummary]:
    related = []
    candidates = [
        candidate for candidate in repo.list_materials(community_id) if candidate.id != material.id
    ]
    facets_by_material = repo.list_material_facets_for_materials(
        [community_id],
        [candidate.id for candidate in candidates],
    )
    facet_groups = repo.list_facet_groups(community_id)
    for candidate in candidates:
        candidate_facets = facet_tags_with_groups(
            facet_groups,
            facets_by_material.get((community_id, candidate.id), []),
        )
        if facet_ids and not facet_ids.intersection({tag.facet.id for tag in candidate_facets}):
            continue
        related.append(_material_summary_from_tags(candidate, candidate_facets))
    return related


def material_related_locations(
    repo: MaterialReadRepository,
    viewer: ForumView,
    facet_ids: set[int],
    *,
    board_summary_factory: BoardSummaryFactory,
) -> list[BoardSummary]:
    if not facet_ids:
        return []
    visible_boards = [
        board
        for board in repo.list_boards(viewer.community.id)
        if policies.can_view_board(viewer.membership, board, viewer.role)
    ]
    facets_by_board = repo.list_board_facets_for_boards(
        viewer.community.id,
        [board.id for board in visible_boards],
    )
    summaries: list[BoardSummary] = []
    for board in visible_boards:
        board_facet_ids = {facet.id for facet in facets_by_board.get(board.id, [])}
        if not facet_ids.intersection(board_facet_ids):
            continue
        summaries.append(board_summary_factory(board))
    return sorted(
        summaries,
        key=lambda item: (
            not item.is_relevant_to_current_face,
            item.board.sort_order,
            item.board.name,
            item.board.id,
        ),
    )


def material_related_scenes(
    repo: MaterialReadRepository,
    viewer: ForumView,
    facet_ids: set[int],
) -> list[DiscoveryThreadResult]:
    if not facet_ids:
        return []
    visible_boards = {
        board.id: board
        for board in repo.list_boards(viewer.community.id)
        if policies.can_view_board(viewer.membership, board, viewer.role)
    }
    threads = [
        thread
        for thread in repo.list_threads(viewer.community.id)
        if thread.board_id in visible_boards
    ]
    thread_ids = [thread.id for thread in threads]
    thread_facets_by_thread = repo.list_thread_facets_for_threads(
        viewer.community.id,
        thread_ids,
    )
    board_facets_by_board = repo.list_board_facets_for_boards(
        viewer.community.id,
        list(visible_boards),
    )
    posts_by_thread = repo.list_posts_for_threads(viewer.community.id, thread_ids)
    participants_by_thread = repo.list_thread_participants_for_threads(
        viewer.community.id,
        thread_ids,
    )
    authors = repo.list_characters_by_ids(
        viewer.community.id,
        list({thread.author_character_id for thread in threads}),
    )
    facet_groups = repo.list_facet_groups(viewer.community.id)
    results: list[DiscoveryThreadResult] = []
    for thread in threads:
        board = visible_boards.get(thread.board_id)
        if board is None:
            continue
        thread_facets = facet_tags_with_groups(
            facet_groups,
            thread_facets_by_thread.get(thread.id, []),
        )
        thread_facet_ids = {tag.facet.id for tag in thread_facets}
        board_facet_ids = {facet.id for facet in board_facets_by_board.get(board.id, [])}
        matching_facets = [tag for tag in thread_facets if tag.facet.id in facet_ids]
        if not facet_ids.intersection(thread_facet_ids | board_facet_ids):
            continue
        posts = posts_by_thread.get(thread.id, [])
        results.append(
            DiscoveryThreadResult(
                board=board,
                thread=thread,
                author=authors[thread.author_character_id],
                participants=participants_by_thread.get(thread.id, []),
                facets=thread_facets,
                matching_facets=matching_facets,
                reply_count=max(0, len(posts) - 1),
            )
        )
    return sorted(
        results,
        key=lambda item: (timestamp_key(item.thread.updated_at), item.thread.id),
        reverse=True,
    )


def material_related_wanted_ads(
    repo: MaterialReadRepository,
    viewer: ForumView,
    material: Material,
    facet_ids: set[int],
    *,
    wanted_summary_factory: WantedAdSummaryFactory,
) -> list[WantedAdSummary]:
    results: list[WantedAdSummary] = []
    wanted_ads = repo.list_wanted_ads(viewer.community.id)
    facets_by_wanted_ad = repo.list_wanted_ad_facets_for_wanted_ads(
        viewer.community.id,
        [wanted_ad.id for wanted_ad in wanted_ads],
    )
    for wanted_ad in wanted_ads:
        wanted_facet_ids = {facet.id for facet in facets_by_wanted_ad.get(wanted_ad.id, [])}
        if wanted_ad.related_material_id != material.id and not facet_ids.intersection(
            wanted_facet_ids
        ):
            continue
        results.append(wanted_summary_factory(wanted_ad))
    return sorted(
        results,
        key=lambda item: (
            item.wanted_ad.related_material_id != material.id,
            timestamp_key(item.wanted_ad.updated_at),
            item.wanted_ad.id,
        ),
        reverse=True,
    )


def public_material_related_wanted_ads(
    repo: MaterialReadRepository,
    community_id: int,
    material: Material,
    facet_ids: set[int],
    *,
    wanted_summary_factory: WantedAdSummaryFactory,
) -> list[WantedAdSummary]:
    results: list[WantedAdSummary] = []
    wanted_ads = repo.list_wanted_ads(community_id, status=None)
    facets_by_wanted_ad = repo.list_wanted_ad_facets_for_wanted_ads(
        community_id,
        [wanted_ad.id for wanted_ad in wanted_ads],
    )
    for wanted_ad in wanted_ads:
        if wanted_ad.status == "archived":
            continue
        wanted_facet_ids = {facet.id for facet in facets_by_wanted_ad.get(wanted_ad.id, [])}
        if wanted_ad.related_material_id != material.id and not facet_ids.intersection(
            wanted_facet_ids
        ):
            continue
        results.append(wanted_summary_factory(wanted_ad))
    return sorted(
        results,
        key=lambda item: (
            item.wanted_ad.related_material_id != material.id,
            timestamp_key(item.wanted_ad.updated_at),
            item.wanted_ad.id,
        ),
        reverse=True,
    )


def current_event_for_facet_ids(
    repo: MaterialReadRepository,
    community_id: int,
    facet_ids: set[int],
) -> MaterialSummary | None:
    if not facet_ids:
        return None
    matches: list[Material] = []
    materials = repo.list_materials(community_id)
    facets_by_material = repo.list_material_facets_for_materials(
        [community_id],
        [material.id for material in materials],
    )
    for material in materials:
        if material.material_type != "event" or material.status != "published":
            continue
        material_facet_ids = {
            facet.id for facet in facets_by_material.get((community_id, material.id), [])
        }
        if facet_ids.intersection(material_facet_ids):
            matches.append(material)
    if not matches:
        return None
    current = sorted(
        matches,
        key=lambda item: (
            not item.is_featured,
            item.sort_order,
            timestamp_key(item.updated_at),
            item.id,
        ),
    )[0]
    return _material_summary_from_tags(
        current,
        facet_tags_with_groups(
            repo.list_facet_groups(community_id),
            facets_by_material.get((community_id, current.id), []),
        ),
    )


def material_event_actions(
    material: Material,
    facets: list[FacetTag],
    related_locations: list[BoardSummary],
    related_scenes: list[DiscoveryThreadResult],
    related_wanted_ads: list[WantedAdSummary],
) -> list[EventAction]:
    if material.material_type != "event":
        return []
    actions: list[EventAction] = []
    open_scene = next(
        (scene for scene in related_scenes if scene.thread.status == "open"),
        related_scenes[0] if related_scenes else None,
    )
    if open_scene is not None:
        actions.append(
            EventAction(
                kind="scene",
                label="Scene to write",
                title=open_scene.thread.title,
                description=open_scene.thread.summary
                or f"{open_scene.board.name} is carrying this event into play.",
                href=f"/boards/{open_scene.board.slug}/threads/{open_scene.thread.slug}",
                cta="Enter scene",
            )
        )
    open_wanted = next(
        (item for item in related_wanted_ads if item.wanted_ad.status == "open"),
        related_wanted_ads[0] if related_wanted_ads else None,
    )
    if open_wanted is not None:
        actions.append(
            EventAction(
                kind="wanted",
                label=open_wanted.type_label,
                title=open_wanted.wanted_ad.title,
                description=open_wanted.wanted_ad.summary
                or "A writer-facing hook connected to this event.",
                href=f"/wanted/{open_wanted.wanted_ad.slug}",
                cta="Answer hook",
            )
        )
    if related_locations:
        location = related_locations[0]
        actions.append(
            EventAction(
                kind="location",
                label="Affected location",
                title=location.board.name,
                description=location.board.tagline or location.board.description,
                href=f"/boards/{location.board.slug}",
                cta="Explore location",
            )
        )
    facet_slugs = [tag.facet.slug for tag in facets[:4]]
    if facet_slugs:
        actions.append(
            EventAction(
                kind="discover",
                label="Plot lens",
                title="Find cast by event facets",
                description="Use this event's world lenses to find characters, writers, and open scenes.",
                href=f"/discover?facets={','.join(facet_slugs)}",
                cta="Open discovery",
            )
        )
    return actions[:4]


def material_continuity_beats(
    material: Material,
    related_locations: list[BoardSummary],
    related_scenes: list[DiscoveryThreadResult],
    related_wanted_ads: list[WantedAdSummary],
) -> list[ContinuityBeat]:
    beats = [
        ContinuityBeat(
            title=f"{material_type_label(material.material_type)} opened",
            date_label=timestamp_label(material.created_at),
            content=material.summary
            or "Directors published this world material for writers to carry into play.",
            variant="info",
        )
    ]
    if timestamp_key(material.updated_at) > timestamp_key(material.created_at):
        beats.append(
            ContinuityBeat(
                title="Canon updated",
                date_label=timestamp_label(material.updated_at),
                content="Directors revised this material as the board state changed.",
            )
        )
    if related_locations:
        location = related_locations[0].board
        beats.append(
            ContinuityBeat(
                title="Pressure reaches the map",
                date_label="Now",
                content=(
                    f"{len(related_locations)} relevant location"
                    f"{'' if len(related_locations) == 1 else 's'} are carrying this material, "
                    f"starting with {location.name}."
                ),
                href=f"/boards/{location.slug}",
                variant="success",
            )
        )
    beats.extend(
        ContinuityBeat(
            title=f"Scene: {scene.thread.title}",
            date_label=timestamp_label(scene.thread.updated_at),
            content=(
                f"{scene.board.name} · {scene.reply_count} "
                f"{'reply' if scene.reply_count == 1 else 'replies'} · "
                f"{len(scene.participants)} in the cast"
            ),
            href=f"/boards/{scene.board.slug}/threads/{scene.thread.slug}",
            variant="info",
        )
        for scene in related_scenes[:2]
    )
    beats.extend(
        ContinuityBeat(
            title=f"Open hook: {wanted_ad.wanted_ad.title}",
            date_label=timestamp_label(wanted_ad.wanted_ad.updated_at),
            content=f"{wanted_ad.type_label}: {wanted_ad.wanted_ad.summary}",
            href=f"/wanted/{wanted_ad.wanted_ad.slug}",
            variant="warning",
        )
        for wanted_ad in related_wanted_ads[:2]
    )
    return beats[:6]
