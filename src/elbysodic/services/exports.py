"""Community export manifest read models."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal, Protocol

from elbysodic.domain.continuity import (
    ContinuityAffectedObject,
    ContinuityCanonEntry,
    ContinuityProposal,
    ContinuityProposalState,
    ContinuityReviewEvent,
    ContinuitySourceCitation,
)
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

type CommunityExportPrivacyTier = Literal["public", "member", "staff", "director_archive"]


@dataclass(frozen=True, slots=True)
class CommunityExportDomain:
    community_id: int
    name: str
    reason: str


@dataclass(frozen=True, slots=True)
class CommunityExportProfile:
    community_id: int
    community_slug: str
    tier: CommunityExportPrivacyTier
    label: str
    audience: str
    included_domains: tuple[CommunityExportDomain, ...]
    excluded_domains: tuple[CommunityExportDomain, ...]
    sensitive_domains: tuple[CommunityExportDomain, ...]


@dataclass(frozen=True, slots=True)
class CommunityExportCount:
    community_id: int
    label: str
    count: int


@dataclass(frozen=True, slots=True)
class CommunityExportOwnership:
    community_id: int
    kind: str
    record_id: int
    membership_id: int | None
    character_id: int | None
    label: str


@dataclass(frozen=True, slots=True)
class CommunityExportSourceLink:
    community_id: int
    kind: str
    record_id: int
    href: str
    label: str


@dataclass(frozen=True, slots=True)
class CommunityExportRedaction:
    community_id: int
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
    privacy_profiles: tuple[CommunityExportProfile, ...]


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

    def list_continuity_proposals(
        self,
        community_id: int,
        *,
        states: Iterable[ContinuityProposalState] | None = None,
        author_membership_id: int | None = None,
    ) -> list[ContinuityProposal]: ...

    def list_continuity_source_citations(
        self,
        community_id: int,
        proposal_id: int,
    ) -> list[ContinuitySourceCitation]: ...

    def list_continuity_affected_objects(
        self,
        community_id: int,
        proposal_id: int,
    ) -> list[ContinuityAffectedObject]: ...

    def list_continuity_review_events(
        self,
        community_id: int,
        proposal_id: int,
    ) -> list[ContinuityReviewEvent]: ...

    def list_continuity_canon_entries(self, community_id: int) -> list[ContinuityCanonEntry]: ...


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
    continuity_proposals = repo.list_continuity_proposals(community.id)
    continuity_citations = [
        citation
        for proposal in continuity_proposals
        for citation in repo.list_continuity_source_citations(community.id, proposal.id)
    ]
    continuity_affected = [
        affected
        for proposal in continuity_proposals
        for affected in repo.list_continuity_affected_objects(community.id, proposal.id)
    ]
    continuity_reviews = [
        event
        for proposal in continuity_proposals
        for event in repo.list_continuity_review_events(community.id, proposal.id)
    ]
    canon_entries = repo.list_continuity_canon_entries(community.id)
    posts = [post for thread_posts in posts_by_thread.values() for post in thread_posts]
    return CommunityExportManifest(
        community_id=community.id,
        community_slug=community.slug,
        community_name=community.name,
        counts=(
            CommunityExportCount(community.id, "memberships", len(memberships)),
            CommunityExportCount(community.id, "roles", len({role.id for role in roles.values()})),
            CommunityExportCount(community.id, "characters", len(characters)),
            CommunityExportCount(community.id, "boards", len(boards)),
            CommunityExportCount(community.id, "threads", len(threads)),
            CommunityExportCount(community.id, "posts", len(posts)),
            CommunityExportCount(community.id, "materials", len(materials)),
            CommunityExportCount(community.id, "claim_types", len(claim_types)),
            CommunityExportCount(community.id, "claims", len(claims)),
            CommunityExportCount(community.id, "reserves", len(reserves)),
            CommunityExportCount(community.id, "wanted_ads", len(wanted_ads)),
            CommunityExportCount(community.id, "plot_hooks", len(plot_hooks)),
            CommunityExportCount(community.id, "plotting_rooms", len(plotting_rooms)),
            CommunityExportCount(community.id, "access_requests", len(access_requests)),
            CommunityExportCount(community.id, "invitations", len(invitations)),
            CommunityExportCount(
                community.id,
                "continuity_proposals",
                len(continuity_proposals),
            ),
            CommunityExportCount(
                community.id,
                "continuity_citations",
                len(continuity_citations),
            ),
            CommunityExportCount(
                community.id,
                "continuity_affected_objects",
                len(continuity_affected),
            ),
            CommunityExportCount(
                community.id,
                "continuity_review_events",
                len(continuity_reviews),
            ),
            CommunityExportCount(community.id, "canon_entries", len(canon_entries)),
        ),
        ownership=(
            *(
                CommunityExportOwnership(
                    community.id,
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
                    community.id,
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
                    community.id,
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
                    community.id,
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
                    community.id,
                    "plotting_room",
                    room.id,
                    room.owner_membership_id,
                    None,
                    room.title,
                )
                for room in plotting_rooms
            ),
            *(
                CommunityExportOwnership(
                    community.id,
                    "continuity_proposal",
                    proposal.id,
                    proposal.author_membership_id,
                    proposal.author_character_id,
                    proposal.title,
                )
                for proposal in continuity_proposals
            ),
            *(
                CommunityExportOwnership(
                    community.id,
                    "canon_entry",
                    entry.id,
                    entry.approved_by_membership_id,
                    None,
                    entry.title,
                )
                for entry in canon_entries
            ),
        ),
        source_links=(
            *(
                CommunityExportSourceLink(
                    community.id,
                    "board",
                    board.id,
                    f"/c/{community.slug}/boards/{board.slug}",
                    board.name,
                )
                for board in boards
            ),
            *(
                CommunityExportSourceLink(
                    community.id,
                    "thread",
                    thread.id,
                    f"/c/{community.slug}/boards/{_board_slug(boards, thread.board_id)}/threads/{thread.slug}",
                    thread.title,
                )
                for thread in threads
            ),
            *(
                CommunityExportSourceLink(
                    community.id,
                    "material",
                    material.id,
                    f"/c/{community.slug}/world/{material.slug}",
                    material.title,
                )
                for material in materials
            ),
            *(
                CommunityExportSourceLink(
                    community.id,
                    "wanted_ad",
                    wanted_ad.id,
                    f"/c/{community.slug}/wanted/{wanted_ad.slug}",
                    wanted_ad.title,
                )
                for wanted_ad in wanted_ads
            ),
            *(
                CommunityExportSourceLink(
                    community.id,
                    f"continuity_{citation.source_type}_citation",
                    citation.id,
                    _continuity_citation_href(
                        community.slug,
                        boards,
                        threads,
                        posts,
                        citation,
                    ),
                    f"{citation.source_type} provenance",
                )
                for citation in continuity_citations
            ),
        ),
        redactions=(
            CommunityExportRedaction(
                community.id,
                "global_users",
                "global login accounts and password hashes are outside one community export",
            ),
            CommunityExportRedaction(
                community.id,
                "sessions",
                "session cookies, token hashes, and selected identity state are never archived",
            ),
            CommunityExportRedaction(
                community.id,
                "passkey_credentials",
                "passkey credential ids, public keys, and sign counts are account "
                "auth material and are never archived",
            ),
            CommunityExportRedaction(
                community.id,
                "invitations",
                "raw invite tokens are unavailable after creation because only token hashes are stored",
            ),
            CommunityExportRedaction(
                community.id,
                "access_requests",
                "private request notes and applicant emails require a director-only detail export",
            ),
            CommunityExportRedaction(
                community.id,
                "continuity_review_material",
                "public/member export tiers omit reviewer notes, private post excerpts, and hidden source labels",
            ),
        ),
        privacy_profiles=_community_export_profiles(community),
    )


def _board_slug(boards: list[Board], board_id: int) -> str:
    for board in boards:
        if board.id == board_id:
            return board.slug
    return "missing-board"


def _continuity_citation_href(
    community_slug: str,
    boards: list[Board],
    threads: list[Thread],
    posts: list[Post],
    citation: ContinuitySourceCitation,
) -> str:
    thread = next(
        (item for item in threads if item.id == citation.source_thread_id),
        None,
    )
    if thread is None:
        return ""
    href = (
        f"/c/{community_slug}/boards/{_board_slug(boards, thread.board_id)}/threads/{thread.slug}"
    )
    if citation.source_type == "post":
        post = next((item for item in posts if item.id == citation.source_id), None)
        if post is not None:
            href = f"{href}#post-{post.post_number}"
    return href


def _community_export_profiles(community: Community) -> tuple[CommunityExportProfile, ...]:
    return (
        CommunityExportProfile(
            community.id,
            community.slug,
            "public",
            "Public realm export",
            "signed-out visitors and off-site public archive readers",
            included_domains=_domains(
                community.id,
                (
                    ("realm_profile", "public community name, slug, premise, and entry posture"),
                    ("published_roster", "approved public faces and roster labels"),
                    ("open_wanted_hooks", "public wanted hooks that are not archived"),
                    (
                        "claimed_claims",
                        "claimed public casting values without private review notes",
                    ),
                    (
                        "published_material_metadata",
                        "published guidebook titles, slugs, and summaries",
                    ),
                    (
                        "approved_public_canon",
                        "approved public canon metadata with public-safe provenance",
                    ),
                ),
            ),
            excluded_domains=_domains(
                community.id,
                (
                    ("member_identities", "membership names and active-face state are not public"),
                    (
                        "private_notes",
                        "writer, applicant, and staff notes are not public archive data",
                    ),
                    ("staff_queues", "operations and review queues require staff capability"),
                    (
                        "inactive_identities",
                        "inactive memberships and faces stay outside public export",
                    ),
                    ("draft_materials", "draft guidebook and event materials stay inside Studio"),
                    ("notification_rows", "membership inbox rows are private operational state"),
                    (
                        "unreviewed_continuity",
                        "proposal drafts, reviewer notes, and hidden sources are never public",
                    ),
                    ("cross_community_records", "export rows must belong to this community only"),
                ),
            ),
            sensitive_domains=(),
        ),
        CommunityExportProfile(
            community.id,
            community.slug,
            "member",
            "Member-visible realm export",
            "active members inside this community",
            included_domains=_domains(
                community.id,
                (
                    ("realm_profile", "community identity and member navigation context"),
                    ("published_roster", "approved public faces and roster labels"),
                    (
                        "member_visible_threads",
                        "threads visible to the member's current membership",
                    ),
                    ("member_visible_posts", "posts visible to the member's current membership"),
                    ("open_wanted_hooks", "member-visible wanted hooks and public hook context"),
                    (
                        "claimed_claims",
                        "member-visible casting values without private review notes",
                    ),
                    (
                        "published_material_metadata",
                        "published guidebook titles, slugs, and summaries",
                    ),
                    (
                        "approved_public_canon",
                        "approved public canon metadata with public-safe provenance",
                    ),
                ),
            ),
            excluded_domains=_domains(
                community.id,
                (
                    (
                        "other_writer_private_records",
                        "member exports cannot include another writer's drafts or notes",
                    ),
                    (
                        "private_notes",
                        "writer, applicant, and staff notes stay out of member exports",
                    ),
                    ("staff_queues", "operations and review queues require staff capability"),
                    (
                        "inactive_identities",
                        "inactive memberships and faces are not member export data",
                    ),
                    ("draft_materials", "draft guidebook and event materials stay inside Studio"),
                    ("notification_rows", "membership inbox rows need a separate privacy contract"),
                    (
                        "unreviewed_continuity",
                        "proposal drafts, reviewer notes, and hidden sources stay outside member exports",
                    ),
                    ("cross_community_records", "export rows must belong to this community only"),
                ),
            ),
            sensitive_domains=(),
        ),
        CommunityExportProfile(
            community.id,
            community.slug,
            "staff",
            "Staff operations export",
            "staff with current-community capability for the included workflow",
            included_domains=_domains(
                community.id,
                (
                    ("realm_profile", "community identity for the current realm only"),
                    ("memberships", "community-local membership records for staff workflow review"),
                    ("roles", "community-local role assignments used by staff workflows"),
                    ("characters", "current-community faces and application posture"),
                    ("boards_threads_posts", "community boards, threads, posts, and authorship"),
                    ("materials", "published and draft director materials visible to staff"),
                    ("claims_reserves_wanted", "claim, reserve, and wanted-hook workflow state"),
                    ("plot_hooks_plotting_rooms", "plotting and handoff spaces visible to staff"),
                    ("staff_queues", "operations queues visible to current-community staff"),
                    (
                        "continuity_proposals_canon",
                        "current-community proposals, citations, review state, and canon",
                    ),
                ),
            ),
            excluded_domains=_domains(
                community.id,
                (
                    (
                        "global_users",
                        "global login accounts and password hashes are outside one community export",
                    ),
                    (
                        "sessions",
                        "session cookies, token hashes, and selected identity state are never archived",
                    ),
                    ("raw_invitation_tokens", "only token hashes are stored after creation"),
                    ("notification_rows", "membership inbox rows require director archive review"),
                    ("cross_community_records", "export rows must belong to this community only"),
                ),
            ),
            sensitive_domains=_domains(
                community.id,
                (
                    (
                        "memberships",
                        "membership state can reveal writer identity inside this community",
                    ),
                    ("roles", "role assignments expose current staff posture"),
                    ("draft_materials", "draft guidebook and event materials are staff-only"),
                    ("staff_queues", "operations queues can reveal private workflow state"),
                    (
                        "continuity_review_material",
                        "review notes and private source provenance are staff-only",
                    ),
                ),
            ),
        ),
        CommunityExportProfile(
            community.id,
            community.slug,
            "director_archive",
            "Director archive export",
            "directors preserving one complete community archive",
            included_domains=_domains(
                community.id,
                (
                    ("realm_profile", "community identity for the current realm only"),
                    ("memberships", "community-local writer identities and active state"),
                    ("roles", "community-local staff role assignments"),
                    ("characters", "public faces owned by memberships in this community"),
                    (
                        "boards_threads_posts",
                        "community boards, scenes, threads, posts, and authorship",
                    ),
                    ("materials", "published and draft director materials"),
                    ("claims_reserves_wanted", "claim, reserve, and wanted-hook workflow state"),
                    ("plot_hooks_plotting_rooms", "plotter hooks and private handoff room state"),
                    (
                        "access_request_metadata",
                        "request lifecycle records without applicant emails or private notes",
                    ),
                    ("invitations", "invitation state without raw invite tokens"),
                    (
                        "notification_rows",
                        "community-scoped membership inbox rows after target visibility review",
                    ),
                    ("staff_queues", "operations, review, and continuation queues"),
                    (
                        "continuity_proposals_canon",
                        "manual proposals, citations, affected links, review events, and canon",
                    ),
                ),
            ),
            excluded_domains=_domains(
                community.id,
                (
                    (
                        "global_users",
                        "global login accounts and password hashes are outside one community export",
                    ),
                    (
                        "sessions",
                        "session cookies, token hashes, and selected identity state are never archived",
                    ),
                    (
                        "password_hashes",
                        "password hashes are global auth material, not realm archive material",
                    ),
                    ("raw_invitation_tokens", "only token hashes are stored after creation"),
                    (
                        "applicant_private_notes",
                        "notes and applicant emails need a detail-export privacy review",
                    ),
                    ("cross_community_records", "export rows must belong to this community only"),
                ),
            ),
            sensitive_domains=_domains(
                community.id,
                (
                    (
                        "memberships",
                        "membership state can reveal writer identity inside this community",
                    ),
                    ("roles", "role assignments expose current staff posture"),
                    (
                        "inactive_identities",
                        "inactive memberships and faces remain sensitive archive material",
                    ),
                    ("draft_materials", "draft guidebook and event materials are not public"),
                    ("private_plotting_rooms", "handoff rooms can expose private plotting context"),
                    ("access_request_metadata", "request lifecycle can expose applicant history"),
                    ("invitations", "invitation state is staff workflow history"),
                    (
                        "notification_rows",
                        "inbox rows can reveal private targets and counterparties",
                    ),
                    ("staff_queues", "operations queues can reveal private workflow state"),
                    (
                        "continuity_review_material",
                        "review notes and private provenance require director archive handling",
                    ),
                ),
            ),
        ),
    )


def _domains(
    community_id: int,
    domains: tuple[tuple[str, str], ...],
) -> tuple[CommunityExportDomain, ...]:
    return tuple(CommunityExportDomain(community_id, name, reason) for name, reason in domains)
