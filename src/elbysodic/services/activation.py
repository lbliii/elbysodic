"""Writer activation read models and first-playable-opening helpers."""

from __future__ import annotations

from typing import Protocol

from elbysodic.domain.context import RequestIdentityContext
from elbysodic.domain.models import (
    Board,
    CharacterClaim,
    CharacterReserve,
    ClaimType,
    Thread,
    WantedAd,
    WantedAdInterest,
)
from elbysodic.domain.vocabulary import wanted_type_label
from elbysodic.services import policies
from elbysodic.services.read_models import (
    ApplicationCharacterView,
    ApplicationsDesk,
    ForumView,
    MyThreadsDashboard,
    PlottingDesk,
    ThreadObligationItem,
    WriterActivation,
    WriterActivationOpening,
)


class WriterActivationRepository(Protocol):
    def list_boards(self, community_id: int) -> list[Board]: ...

    def list_character_claims(
        self,
        community_id: int,
        *,
        status: str | None = "claimed",
        claim_type_id: int | None = None,
    ) -> list[CharacterClaim]: ...

    def list_character_reserves(
        self,
        community_id: int,
        character_id: int,
        *,
        status: str | None = "active",
    ) -> list[CharacterReserve]: ...

    def list_claim_types(self, community_id: int) -> list[ClaimType]: ...

    def list_threads(self, community_id: int) -> list[Thread]: ...

    def list_wanted_ads(
        self,
        community_id: int,
        *,
        status: str | None = "open",
    ) -> list[WantedAd]: ...

    def list_wanted_ad_interests(
        self,
        community_id: int,
        wanted_ad_id: int,
        *,
        status: str | None = None,
    ) -> list[WantedAdInterest]: ...


def writer_activation(
    repo: WriterActivationRepository,
    viewer: ForumView,
    *,
    queue: MyThreadsDashboard,
    applications: ApplicationsDesk,
    plotting: PlottingDesk,
) -> WriterActivation:
    open_applications = _activation_open_applications(applications)
    accepted_faces = [
        character for character in viewer.roster if character.application_status == "accepted"
    ]
    wanted_interests = _activation_wanted_interests(repo, viewer)
    claim_gap_count, claim_conflict_count, reserve_count = _activation_claim_counts(
        repo,
        viewer,
        applications,
    )
    counts = {
        "roster_count": len(viewer.roster),
        "accepted_face_count": len(accepted_faces),
        "open_application_count": len(open_applications),
        "active_scene_count": len(queue.participated),
        "wanted_interest_count": len(wanted_interests),
        "plotting_room_count": len(plotting.rooms),
        "claim_gap_count": claim_gap_count,
        "claim_conflict_count": claim_conflict_count,
        "reserve_count": reserve_count,
    }
    if not accepted_faces:
        if open_applications:
            return _application_activation(open_applications[0], **counts)
        return WriterActivation(
            stage="needs_face",
            headline="Start with a first face",
            summary=(
                "Create or apply with a posting face before reply queues, "
                "plotting rooms, and scene lanes can form."
            ),
            primary_label="Start first face",
            primary_href="/applications/new",
            secondary_label="Read application guide",
            secondary_href=_first_application_material_href(applications),
            **counts,
        )
    if queue.participated:
        next_item = queue.needs_reply[0] if queue.needs_reply else queue.participated[0]
        return WriterActivation(
            stage="active_scene",
            headline="Your first scene path is active",
            summary="Open the next scene attached to your roster.",
            primary_label="Open scene",
            primary_href=_activation_thread_href(next_item),
            secondary_label="Open queue",
            secondary_href="/my/threads",
            **counts,
        )
    if plotting.rooms:
        room = plotting.rooms[0]
        return WriterActivation(
            stage="plotting",
            headline="A plotting room is waiting",
            summary="Finish the handoff and turn the plan into a scene when it is ready.",
            primary_label="Open plotting room",
            primary_href=f"/plotting/{room.room.id}",
            secondary_label="Open plotting",
            secondary_href="/plotting",
            **counts,
        )
    if wanted_interests:
        wanted_ad = wanted_interests[0]
        return WriterActivation(
            stage="wanted_interest",
            headline="Your raised hand is in backstage",
            summary="Watch the wanted hook for owner or staff movement into plotting.",
            primary_label="Open wanted hook",
            primary_href=f"/wanted/{wanted_ad.slug}",
            secondary_label="Open plotting",
            secondary_href="/plotting",
            **counts,
        )
    if claim_gap_count or reserve_count:
        return WriterActivation(
            stage="accepted_no_scene",
            headline="Settle first-face claims",
            summary=(
                "Review required claims and active reserves before choosing the "
                "cleanest opening scene."
            ),
            primary_label="Open claims",
            primary_href="/claims",
            secondary_label="Browse wanted hooks",
            secondary_href="/wanted",
            **counts,
        )
    return WriterActivation(
        stage="accepted_no_scene",
        headline="Find the first playable opening",
        summary="Use wanted hooks, discovery, or starter scene hubs to get your face into play.",
        primary_label="Browse wanted hooks",
        primary_href="/wanted",
        secondary_label="Open discovery",
        secondary_href="/discover",
        **counts,
    )


def first_playable_openings(
    repo: WriterActivationRepository,
    viewer: ForumView,
    *,
    applications: ApplicationsDesk,
    plotting: PlottingDesk,
    limit: int = 6,
) -> list[WriterActivationOpening]:
    openings: list[WriterActivationOpening] = []
    openings.extend(_activation_claim_openings(repo, viewer, applications))
    openings.extend(_activation_plotting_openings(plotting))
    openings.extend(_activation_application_openings(applications))
    openings.extend(_activation_wanted_openings(repo, viewer))
    openings.extend(_activation_starter_thread_openings(repo, viewer))
    return openings[:limit]


def tenant_activation_path(identity: RequestIdentityContext, href: str) -> str:
    path = href if href.startswith("/") else f"/{href}"
    return f"/c/{identity.community_slug}{path}"


def _activation_open_applications(
    applications: ApplicationsDesk,
) -> list[ApplicationCharacterView]:
    priority = {"revision_requested": 0, "draft": 1, "submitted": 2}
    return sorted(
        (
            item
            for item in applications.my_applications
            if item.character.application_status in priority
        ),
        key=lambda item: (
            priority[item.character.application_status],
            item.character.name,
            item.character.id,
        ),
    )


def _application_activation(
    application: ApplicationCharacterView,
    **counts: int,
) -> WriterActivation:
    href = f"/applications/{application.character.slug}"
    status = application.character.application_status
    if status == "submitted":
        return WriterActivation(
            stage="application_submitted",
            headline=f"{application.character.name} is in review",
            summary="Watch the application room for director notes or approval.",
            primary_label="Open application",
            primary_href=href,
            secondary_label="Open applications",
            secondary_href="/applications",
            **counts,
        )
    if status == "revision_requested":
        return WriterActivation(
            stage="application_revision",
            headline=f"{application.character.name} needs revision",
            summary="Update the requested face work before this application can move forward.",
            primary_label="Revise application",
            primary_href=href,
            secondary_label="Open applications",
            secondary_href="/applications",
            **counts,
        )
    return WriterActivation(
        stage="application_draft",
        headline=f"Finish {application.character.name}",
        summary="Complete the draft and submit this face for director review.",
        primary_label="Continue application",
        primary_href=href,
        secondary_label="Open applications",
        secondary_href="/applications",
        **counts,
    )


def _first_application_material_href(applications: ApplicationsDesk) -> str:
    if applications.application_materials:
        return f"/world/{applications.application_materials[0].material.slug}"
    return "/applications"


def _activation_wanted_interests(
    repo: WriterActivationRepository,
    viewer: ForumView,
) -> list[WantedAd]:
    wanted_ads: list[WantedAd] = []
    for wanted_ad in repo.list_wanted_ads(viewer.community.id, status=None):
        if wanted_ad.status == "archived":
            continue
        interests = repo.list_wanted_ad_interests(viewer.community.id, wanted_ad.id)
        if any(interest.membership_id == viewer.membership.id for interest in interests):
            wanted_ads.append(wanted_ad)
    return wanted_ads


def _activation_claim_counts(
    repo: WriterActivationRepository,
    viewer: ForumView,
    applications: ApplicationsDesk,
) -> tuple[int, int, int]:
    accepted_faces = [
        character for character in viewer.roster if character.application_status == "accepted"
    ]
    required_claim_types = [
        claim_type
        for claim_type in repo.list_claim_types(viewer.community.id)
        if claim_type.is_required
    ]
    claimed_by_character: dict[int, set[int]] = {}
    for claim in repo.list_character_claims(viewer.community.id, status="claimed"):
        if claim.character_id is None:
            continue
        claimed_by_character.setdefault(claim.character_id, set()).add(claim.claim_type_id)
    claim_gap_count = sum(
        1
        for character in accepted_faces
        for claim_type in required_claim_types
        if claim_type.id not in claimed_by_character.get(character.id, set())
    )
    reserve_count = sum(
        len(repo.list_character_reserves(viewer.community.id, character.id))
        for character in accepted_faces
    )
    claim_conflict_count = sum(
        item.claim_conflict_count
        for item in applications.my_applications
        if item.character.application_status in {"draft", "submitted", "revision_requested"}
    )
    return claim_gap_count, claim_conflict_count, reserve_count


def _activation_claim_openings(
    repo: WriterActivationRepository,
    viewer: ForumView,
    applications: ApplicationsDesk,
) -> list[WriterActivationOpening]:
    claim_gap_count, claim_conflict_count, reserve_count = _activation_claim_counts(
        repo,
        viewer,
        applications,
    )
    openings: list[WriterActivationOpening] = []
    if claim_gap_count:
        openings.append(
            WriterActivationOpening(
                kind="claims",
                label="Required face claims",
                href="/claims",
                summary=f"{claim_gap_count} required claim slot(s) still need this roster.",
                detail="Claims",
            )
        )
    if reserve_count:
        openings.append(
            WriterActivationOpening(
                kind="reserves",
                label="Active reserves",
                href="/claims?status=reserved",
                summary=f"{reserve_count} reserve(s) should be checked before the first scene.",
                detail="Reserves",
            )
        )
    if claim_conflict_count:
        openings.append(
            WriterActivationOpening(
                kind="claims",
                label="Application claim conflicts",
                href="/applications",
                summary=f"{claim_conflict_count} claim conflict(s) need revision or staff review.",
                detail="Claims",
            )
        )
    return openings


def _activation_plotting_openings(plotting: PlottingDesk) -> list[WriterActivationOpening]:
    return [
        WriterActivationOpening(
            kind="plotting",
            label=room.room.title,
            href=f"/plotting/{room.room.id}",
            summary=room.room.summary or "A plotting room is already waiting on this writer.",
            detail=room.source_label,
        )
        for room in plotting.rooms
    ]


def _activation_application_openings(
    applications: ApplicationsDesk,
) -> list[WriterActivationOpening]:
    openings = [
        WriterActivationOpening(
            kind="application",
            label=application.character.name,
            href=f"/applications/{application.character.slug}",
            summary="Continue the face application already in progress.",
            detail=application.status_label,
        )
        for application in _activation_open_applications(applications)
    ]
    openings.extend(
        WriterActivationOpening(
            kind="guide",
            label=material.material.title,
            href=f"/world/{material.material.slug}",
            summary=material.material.summary or "Application guidance for this realm.",
            detail=material.type_label,
        )
        for material in applications.application_materials[:2]
    )
    return openings


def _activation_wanted_openings(
    repo: WriterActivationRepository,
    viewer: ForumView,
) -> list[WriterActivationOpening]:
    active_interest_ids = {wanted_ad.id for wanted_ad in _activation_wanted_interests(repo, viewer)}
    openings: list[WriterActivationOpening] = []
    for wanted_ad in repo.list_wanted_ads(viewer.community.id):
        if wanted_ad.creator_membership_id == viewer.membership.id:
            continue
        if wanted_ad.id in active_interest_ids:
            continue
        openings.append(
            WriterActivationOpening(
                kind="wanted",
                label=wanted_ad.title,
                href=f"/wanted/{wanted_ad.slug}",
                summary=wanted_ad.summary or "Open wanted hook ready for interest.",
                detail=wanted_type_label(wanted_ad.wanted_type),
            )
        )
    return openings


def _activation_starter_thread_openings(
    repo: WriterActivationRepository,
    viewer: ForumView,
) -> list[WriterActivationOpening]:
    visible_boards = {
        board.id: board
        for board in repo.list_boards(viewer.community.id)
        if policies.can_view_board(viewer.membership, board, viewer.role)
    }
    openings: list[WriterActivationOpening] = []
    for thread in repo.list_threads(viewer.community.id):
        if thread.status != "open":
            continue
        board = visible_boards.get(thread.board_id)
        if board is None:
            continue
        openings.append(
            WriterActivationOpening(
                kind="thread",
                label=thread.title,
                href=f"/boards/{board.slug}/threads/{thread.slug}",
                summary=thread.summary or "Open scene ready for another face.",
                detail=board.name,
            )
        )
    return openings


def _activation_thread_href(item: ThreadObligationItem) -> str:
    anchor = f"#{item.jump_post.anchor}" if item.jump_post else ""
    return f"/boards/{item.board.slug}/threads/{item.thread.slug}{anchor}"
