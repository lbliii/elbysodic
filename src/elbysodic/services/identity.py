"""Character and writer identity read-model helpers."""

from __future__ import annotations

from typing import Protocol

from elbysodic.domain.models import (
    Board,
    Character,
    CharacterReserve,
    CommunityMembership,
    Post,
    Role,
    Thread,
    WantedAd,
)
from elbysodic.services import policies
from elbysodic.services.casting import (
    CastingReadRepository,
    character_reserve_view,
    wanted_ad_summary,
)
from elbysodic.services.facets import facet_tags
from elbysodic.services.posts import post_view
from elbysodic.services.read_models import (
    APPLICATION_STATUS_LABELS,
    APPLICATION_STATUS_VARIANTS,
    CharacterAppearance,
    CharacterProfile,
    CharacterRosterCard,
    CharacterRosterDashboard,
    CharacterThreadActivity,
    ForumView,
    MemberDirectory,
    MemberDirectoryCard,
    MemberProfile,
    WriterCollaborator,
)
from elbysodic.services.threads import ThreadReadRepository, thread_obligations
from elbysodic.services.timestamps import timestamp_key


class IdentityRepository(CastingReadRepository, ThreadReadRepository, Protocol):
    def get_character_by_slug(self, community_id: int, slug: str) -> Character: ...

    def get_thread(self, community_id: int, thread_id: int) -> Thread: ...

    def get_membership_by_username(
        self,
        community_id: int,
        username: str,
    ) -> CommunityMembership: ...

    def get_role(self, community_id: int, role_id: int) -> Role: ...

    def list_posts_by_character(self, community_id: int, character_id: int) -> list[Post]: ...

    def list_wanted_ads_for_character(
        self,
        community_id: int,
        character_id: int,
    ) -> list[WantedAd]: ...

    def list_character_reserves(
        self,
        community_id: int,
        character_id: int,
    ) -> list[CharacterReserve]: ...


def selected_character(
    repo: IdentityRepository,
    viewer: ForumView,
    character_slug: str | None,
) -> Character | None:
    if not character_slug:
        return None
    character = repo.get_character_by_slug(viewer.community.id, character_slug)
    if character.membership_id != viewer.membership.id:
        raise PermissionError(
            f"membership {viewer.membership.id} cannot filter by character {character.id}"
        )
    return character


def character_roster_dashboard(
    repo: IdentityRepository,
    viewer: ForumView,
) -> CharacterRosterDashboard:
    return CharacterRosterDashboard(
        cards=[
            CharacterRosterCard(
                character=character,
                is_default=viewer.membership.default_character_id == character.id,
                activity=character_activity(repo, viewer, character),
                application_status_label=application_status_label(character.application_status),
                application_status_variant=application_status_variant(character.application_status),
            )
            for character in viewer.roster
        ]
    )


def member_directory(repo: IdentityRepository, viewer: ForumView) -> MemberDirectory:
    return MemberDirectory(
        cards=[
            member_directory_card(repo, viewer, membership)
            for membership in repo.list_memberships(viewer.community.id)
            if membership.is_active
        ]
    )


def member_profile(repo: IdentityRepository, viewer: ForumView, username: str) -> MemberProfile:
    membership = repo.get_membership_by_username(viewer.community.id, username)
    if not membership.is_active:
        raise LookupError(f"membership not found in community {viewer.community.id}: {username}")
    roster = repo.list_characters(viewer.community.id, membership.id)
    roster_ids = {character.id for character in roster}
    active_threads = thread_obligations(repo, viewer, roster_ids)
    return MemberProfile(
        membership=membership,
        role=repo.get_role(viewer.community.id, membership.role_id),
        roster=roster,
        default_character=default_character(roster, membership.default_character_id),
        known_for=known_for_characters(repo, viewer, roster, limit=3),
        collaborators=writer_collaborators(
            repo,
            viewer,
            membership,
            roster_ids,
            limit=4,
        ),
        visible_post_count=len(visible_character_posts(repo, viewer, roster_ids)),
        visible_thread_count=len(active_threads),
        active_threads=active_threads,
        started_threads=[item for item in active_threads if item.is_started_by_roster],
        recent_posts=recent_character_posts(repo, viewer, roster_ids, limit=8),
        is_current_member=membership.id == viewer.membership.id,
    )


def character_profile(
    repo: IdentityRepository,
    viewer: ForumView,
    character_slug: str,
) -> CharacterProfile:
    character = repo.get_character_by_slug(viewer.community.id, character_slug)
    owner_membership = repo.get_membership(viewer.community.id, character.membership_id)
    can_manage = character.membership_id == viewer.membership.id
    activity = character_activity(repo, viewer, character)
    return CharacterProfile(
        character=character,
        owner_membership=owner_membership,
        facets=facet_tags(
            repo,
            viewer.community.id,
            repo.list_character_facets(viewer.community.id, character.id),
        ),
        wanted_ads=[
            wanted_ad_summary(repo, viewer.community.id, wanted_ad)
            for wanted_ad in repo.list_wanted_ads_for_character(
                viewer.community.id,
                character.id,
            )
        ],
        reserves=[
            character_reserve_view(repo, viewer.community.id, reserve)
            for reserve in repo.list_character_reserves(viewer.community.id, character.id)
        ],
        application_status_label=application_status_label(character.application_status),
        application_status_variant=application_status_variant(character.application_status),
        is_default=can_manage and viewer.membership.default_character_id == character.id,
        can_manage=can_manage,
        post_count=len(visible_character_posts(repo, viewer, {character.id})),
        thread_count=len(activity.started_by_character),
        activity=activity,
        recent_posts=recent_character_posts(repo, viewer, {character.id}, limit=5),
    )


def character_activity(
    repo: IdentityRepository,
    viewer: ForumView,
    character: Character,
) -> CharacterThreadActivity:
    items = thread_obligations(repo, viewer, {character.id})
    return CharacterThreadActivity(
        character=character,
        needs_reply=[item for item in items if item.needs_reply],
        waiting_on_others=[item for item in items if item.waiting_on_others],
        started_by_character=[item for item in items if item.is_started_by_roster],
        participated=items,
    )


def roster_activity(
    repo: IdentityRepository,
    viewer: ForumView,
) -> list[CharacterThreadActivity]:
    return [character_activity(repo, viewer, character) for character in viewer.roster]


def member_directory_card(
    repo: IdentityRepository,
    viewer: ForumView,
    membership: CommunityMembership,
) -> MemberDirectoryCard:
    roster = repo.list_characters(viewer.community.id, membership.id)
    roster_ids = {character.id for character in roster}
    active_threads = thread_obligations(repo, viewer, roster_ids)
    latest_posts = recent_character_posts(repo, viewer, roster_ids, limit=1)
    return MemberDirectoryCard(
        membership=membership,
        role=repo.get_role(viewer.community.id, membership.role_id),
        roster=roster,
        default_character=default_character(roster, membership.default_character_id),
        known_for=known_for_characters(repo, viewer, roster, limit=2),
        visible_post_count=len(visible_character_posts(repo, viewer, roster_ids)),
        active_thread_count=len(active_threads),
        latest_post=latest_posts[0] if latest_posts else None,
        is_current_member=membership.id == viewer.membership.id,
    )


def default_character(
    roster: list[Character],
    default_character_id: int | None,
) -> Character | None:
    if default_character_id is None:
        return roster[0] if roster else None
    return next(
        (character for character in roster if character.id == default_character_id),
        roster[0] if roster else None,
    )


def application_status_label(status: str) -> str:
    return APPLICATION_STATUS_LABELS.get(status, status.replace("_", " ").title())


def application_status_variant(status: str) -> str:
    return APPLICATION_STATUS_VARIANTS.get(status, "muted")


def visible_character_posts(
    repo: IdentityRepository,
    viewer: ForumView,
    character_ids: set[int],
) -> list[CharacterAppearance]:
    if not character_ids:
        return []
    visible_boards = {
        board.id: board
        for board in repo.list_boards(viewer.community.id)
        if policies.can_view_board(viewer.membership, board, viewer.role)
    }
    items: list[CharacterAppearance] = []
    for character_id in character_ids:
        for post in repo.list_posts_by_character(viewer.community.id, character_id):
            thread = repo.get_thread(viewer.community.id, post.thread_id)
            board = visible_boards.get(thread.board_id)
            if board is None:
                continue
            items.append(
                CharacterAppearance(
                    post=post_view(repo, viewer.community.id, post),
                    thread=thread,
                    board=board,
                )
            )
    return sorted(
        items,
        key=lambda item: (timestamp_key(item.post.post.created_at), item.post.post.id),
        reverse=True,
    )


def recent_character_posts(
    repo: IdentityRepository,
    viewer: ForumView,
    character_ids: set[int],
    *,
    limit: int,
) -> list[CharacterAppearance]:
    return visible_character_posts(repo, viewer, character_ids)[:limit]


def known_for_characters(
    repo: IdentityRepository,
    viewer: ForumView,
    roster: list[Character],
    *,
    limit: int,
) -> list[Character]:
    if not roster:
        return []
    appearances = visible_character_posts(
        repo,
        viewer,
        {character.id for character in roster},
    )
    counts: dict[int, int] = {}
    latest: dict[int, tuple[str, int]] = {}
    for appearance in appearances:
        character_id = appearance.post.author.id
        counts[character_id] = counts.get(character_id, 0) + 1
        latest[character_id] = max(
            latest.get(character_id, ("", 0)),
            (
                appearance.post.post.created_at,
                appearance.post.post.id,
            ),
        )
    ranked = sorted(
        roster,
        key=lambda character: (
            counts.get(character.id, 0),
            latest.get(character.id, ("", 0)),
            character.name.lower(),
        ),
        reverse=True,
    )
    return ranked[:limit]


def writer_collaborators(
    repo: IdentityRepository,
    viewer: ForumView,
    membership: CommunityMembership,
    roster_ids: set[int],
    *,
    limit: int,
) -> list[WriterCollaborator]:
    if not roster_ids:
        return []
    visible_boards = {
        board.id: board
        for board in repo.list_boards(viewer.community.id)
        if policies.can_view_board(viewer.membership, board, viewer.role)
    }
    counts: dict[int, int] = {}
    latest: dict[int, tuple[str, int, Thread, Board]] = {}
    for thread in repo.list_threads(viewer.community.id):
        board = visible_boards.get(thread.board_id)
        if board is None:
            continue
        posts = repo.list_posts(viewer.community.id, thread.id)
        if not any(
            post.author_membership_id == membership.id or post.author_character_id in roster_ids
            for post in posts
        ):
            continue
        other_membership_ids = {
            post.author_membership_id
            for post in posts
            if post.author_membership_id != membership.id
        }
        for other_id in other_membership_ids:
            counts[other_id] = counts.get(other_id, 0) + 1
            candidate = (thread.updated_at, thread.id, thread, board)
            if candidate[:2] > latest.get(other_id, ("", 0, thread, board))[:2]:
                latest[other_id] = candidate
    collaborators: list[WriterCollaborator] = []
    for membership_id, shared_thread_count in counts.items():
        try:
            collaborator = repo.get_membership(viewer.community.id, membership_id)
        except LookupError:
            continue
        if not collaborator.is_active:
            continue
        _stamp, _thread_id, latest_thread, latest_board = latest[membership_id]
        collaborators.append(
            WriterCollaborator(
                membership=collaborator,
                shared_thread_count=shared_thread_count,
                latest_thread=latest_thread,
                latest_board=latest_board,
            )
        )
    return sorted(
        collaborators,
        key=lambda item: (
            item.shared_thread_count,
            timestamp_key(item.latest_thread.updated_at),
            item.membership.display_name.lower(),
        ),
        reverse=True,
    )[:limit]
