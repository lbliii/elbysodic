"""Community export manifest read models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from elbysodic.domain.models import (
    Board,
    Character,
    CharacterClaim,
    CharacterPlotHook,
    CharacterReserve,
    ClaimType,
    Community,
    CommunityAccessRequest,
    CommunityInvitation,
    CommunityMembership,
    Material,
    PlottingRoom,
    Post,
    Role,
    Thread,
    WantedAd,
)
from elbysodic.services import policies
from elbysodic.services.read_models import ForumView


@dataclass(frozen=True, slots=True)
class CommunityExportCount:
    label: str
    count: int


@dataclass(frozen=True, slots=True)
class CommunityExportOwnership:
    kind: str
    record_id: int
    membership_id: int | None
    character_id: int | None
    label: str


@dataclass(frozen=True, slots=True)
class CommunityExportSourceLink:
    kind: str
    record_id: int
    href: str
    label: str


@dataclass(frozen=True, slots=True)
class CommunityExportRedaction:
    scope: str
    reason: str


@dataclass(frozen=True, slots=True)
class CommunityExportManifest:
    community_id: int
    community_slug: str
    community_name: str
    counts: tuple[CommunityExportCount, ...]
    ownership: tuple[CommunityExportOwnership, ...]
    source_links: tuple[CommunityExportSourceLink, ...]
    redactions: tuple[CommunityExportRedaction, ...]


class CommunityExportRepository(Protocol):
    def get_community(self, community_id: int) -> Community: ...

    def list_memberships(self, community_id: int) -> list[CommunityMembership]: ...

    def roles_for_memberships(self, membership_ids: list[int]) -> dict[int, Role]: ...

    def list_community_characters(self, community_id: int) -> list[Character]: ...

    def list_boards(self, community_id: int) -> list[Board]: ...

    def list_threads(self, community_id: int, board_id: int | None = None) -> list[Thread]: ...

    def list_posts_for_threads(
        self,
        community_id: int,
        thread_ids: list[int],
    ) -> dict[int, list[Post]]: ...

    def list_materials(self, community_id: int, *, status: str | None = None) -> list[Material]: ...

    def list_claim_types(self, community_id: int) -> list[ClaimType]: ...

    def list_character_claims(
        self,
        community_id: int,
        *,
        status: str | None = "claimed",
        claim_type_id: int | None = None,
    ) -> list[CharacterClaim]: ...

    def list_character_reserves_for_community(
        self,
        community_id: int,
        *,
        status: str | None = "active",
    ) -> list[CharacterReserve]: ...

    def list_wanted_ads(
        self,
        community_id: int,
        *,
        status: str | None = "open",
    ) -> list[WantedAd]: ...

    def list_character_plot_hooks(
        self,
        community_id: int,
        *,
        status: str | None = "open",
    ) -> list[CharacterPlotHook]: ...

    def list_plotting_rooms(
        self,
        community_id: int,
        *,
        status: str | None = None,
    ) -> list[PlottingRoom]: ...

    def list_community_access_requests(
        self,
        community_id: int,
        *,
        status: str | None = None,
    ) -> list[CommunityAccessRequest]: ...

    def list_community_invitations(self, community_id: int) -> list[CommunityInvitation]: ...


def community_export_manifest(
    repo: CommunityExportRepository,
    viewer: ForumView,
) -> CommunityExportManifest:
    if not policies.can_manage_world(viewer.membership, viewer.role):
        raise PermissionError("director access is required to export community archives")
    community = repo.get_community(viewer.community.id)
    memberships = repo.list_memberships(community.id)
    roles = repo.roles_for_memberships([membership.id for membership in memberships])
    characters = repo.list_community_characters(community.id)
    boards = repo.list_boards(community.id)
    threads = repo.list_threads(community.id)
    posts_by_thread = repo.list_posts_for_threads(
        community.id,
        [thread.id for thread in threads],
    )
    materials = repo.list_materials(community.id, status=None)
    claim_types = repo.list_claim_types(community.id)
    claims = repo.list_character_claims(community.id, status=None)
    reserves = repo.list_character_reserves_for_community(community.id, status=None)
    wanted_ads = repo.list_wanted_ads(community.id, status=None)
    plot_hooks = repo.list_character_plot_hooks(community.id, status=None)
    plotting_rooms = repo.list_plotting_rooms(community.id, status=None)
    access_requests = repo.list_community_access_requests(community.id, status=None)
    invitations = repo.list_community_invitations(community.id)
    posts = [post for thread_posts in posts_by_thread.values() for post in thread_posts]
    return CommunityExportManifest(
        community_id=community.id,
        community_slug=community.slug,
        community_name=community.name,
        counts=(
            CommunityExportCount("memberships", len(memberships)),
            CommunityExportCount("roles", len({role.id for role in roles.values()})),
            CommunityExportCount("characters", len(characters)),
            CommunityExportCount("boards", len(boards)),
            CommunityExportCount("threads", len(threads)),
            CommunityExportCount("posts", len(posts)),
            CommunityExportCount("materials", len(materials)),
            CommunityExportCount("claim_types", len(claim_types)),
            CommunityExportCount("claims", len(claims)),
            CommunityExportCount("reserves", len(reserves)),
            CommunityExportCount("wanted_ads", len(wanted_ads)),
            CommunityExportCount("plot_hooks", len(plot_hooks)),
            CommunityExportCount("plotting_rooms", len(plotting_rooms)),
            CommunityExportCount("access_requests", len(access_requests)),
            CommunityExportCount("invitations", len(invitations)),
        ),
        ownership=(
            *(
                CommunityExportOwnership(
                    "character",
                    character.id,
                    character.membership_id,
                    character.id,
                    character.name,
                )
                for character in characters
            ),
            *(
                CommunityExportOwnership(
                    "post",
                    post.id,
                    post.author_membership_id,
                    post.author_character_id,
                    f"post #{post.post_number}",
                )
                for post in posts
            ),
            *(
                CommunityExportOwnership(
                    "wanted_ad",
                    wanted_ad.id,
                    wanted_ad.creator_membership_id,
                    wanted_ad.creator_character_id,
                    wanted_ad.title,
                )
                for wanted_ad in wanted_ads
            ),
            *(
                CommunityExportOwnership(
                    "plot_hook",
                    plot_hook.id,
                    plot_hook.author_membership_id,
                    plot_hook.character_id,
                    plot_hook.title,
                )
                for plot_hook in plot_hooks
            ),
            *(
                CommunityExportOwnership(
                    "plotting_room",
                    room.id,
                    room.owner_membership_id,
                    None,
                    room.title,
                )
                for room in plotting_rooms
            ),
        ),
        source_links=(
            *(
                CommunityExportSourceLink(
                    "board",
                    board.id,
                    f"/c/{community.slug}/boards/{board.slug}",
                    board.name,
                )
                for board in boards
            ),
            *(
                CommunityExportSourceLink(
                    "thread",
                    thread.id,
                    f"/c/{community.slug}/boards/{_board_slug(boards, thread.board_id)}/threads/{thread.slug}",
                    thread.title,
                )
                for thread in threads
            ),
            *(
                CommunityExportSourceLink(
                    "material",
                    material.id,
                    f"/c/{community.slug}/world/{material.slug}",
                    material.title,
                )
                for material in materials
            ),
            *(
                CommunityExportSourceLink(
                    "wanted_ad",
                    wanted_ad.id,
                    f"/c/{community.slug}/wanted/{wanted_ad.slug}",
                    wanted_ad.title,
                )
                for wanted_ad in wanted_ads
            ),
        ),
        redactions=(
            CommunityExportRedaction(
                "global_users",
                "global login accounts and password hashes are outside one community export",
            ),
            CommunityExportRedaction(
                "sessions",
                "session cookies, token hashes, and selected identity state are never archived",
            ),
            CommunityExportRedaction(
                "invitations",
                "raw invite tokens are unavailable after creation because only token hashes are stored",
            ),
            CommunityExportRedaction(
                "access_requests",
                "private request notes and applicant emails require a director-only detail export",
            ),
        ),
    )


def _board_slug(boards: list[Board], board_id: int) -> str:
    for board in boards:
        if board.id == board_id:
            return board.slug
    return "missing-board"
