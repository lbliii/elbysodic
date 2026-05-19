"""Director operations read model assembly."""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from typing import Protocol

from elbysodic.db.migrations import CURRENT_SCHEMA_VERSION
from elbysodic.domain.models import (
    Character,
    CommunityAccessRequest,
    CommunityInvitation,
    CommunityMembership,
    Role,
)
from elbysodic.services import policies
from elbysodic.services.read_models import (
    ApplicationCharacterView,
    CastingDesk,
    DirectorStudio,
    ForumView,
    PlottingDesk,
)


class InvitationManagementItemLike(Protocol):
    invitation: CommunityInvitation


class AccessRequestManagementItemLike(Protocol):
    request: CommunityAccessRequest


class OperationsRepository(Protocol):
    connection: sqlite3.Connection

    def get_role(self, community_id: int, role_id: int) -> Role: ...

    def list_characters(self, community_id: int, membership_id: int) -> list[Character]: ...

    def list_community_characters(self, community_id: int) -> list[Character]: ...

    def list_memberships(self, community_id: int) -> list[CommunityMembership]: ...


@dataclass(frozen=True, slots=True)
class OperationsCard:
    kicker: str
    title: str
    summary: str
    count: int
    href: str
    cta: str
    variant: str = "status"
    items: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class OperationsLane:
    label: str
    summary: str
    count: int
    href: str
    variant: str


@dataclass(frozen=True, slots=True)
class OperationsShortcut:
    label: str
    count: int
    href: str
    summary: str


@dataclass(frozen=True, slots=True)
class OperationsInspectionConfig:
    environment: str
    secure_cookies: bool


@dataclass(frozen=True, slots=True)
class OperationsInspection:
    app_version: str
    environment: str
    secure_cookies: bool
    database_path: str
    sqlite_user_version: int
    current_schema_version: int
    latest_migration_version: int
    community_count: int
    launch_status: str


@dataclass(frozen=True, slots=True)
class DirectorOperations:
    cards: list[OperationsCard]
    lanes: list[OperationsLane]
    shortcuts: list[OperationsShortcut]
    ready_applications: list[ApplicationCharacterView]
    blocked_applications: list[ApplicationCharacterView]
    can_manage: bool
    inspection: OperationsInspection | None


def director_operations(
    repo: OperationsRepository,
    viewer: ForumView,
    studio: DirectorStudio,
    casting: CastingDesk,
    plotting: PlottingDesk,
    *,
    writer_invitations: Sequence[InvitationManagementItemLike],
    writer_access_requests: Sequence[AccessRequestManagementItemLike],
    unread_notification_count: int,
    inspection_config: OperationsInspectionConfig | None,
) -> DirectorOperations:
    ready_applications = [
        item for item in studio.applications.review_queue if not item.has_claim_conflicts
    ]
    blocked_applications = [
        item for item in studio.applications.review_queue if item.has_claim_conflicts
    ]
    conflicted_applications = _unique_applications(
        [
            *studio.applications.my_applications,
            *studio.applications.review_queue,
        ]
    )
    conflicted_applications = [item for item in conflicted_applications if item.has_claim_conflicts]
    cards: list[OperationsCard] = []
    activation_card = _writer_activation_card(
        repo,
        viewer,
        studio,
        casting,
        plotting,
        writer_invitations=writer_invitations,
        writer_access_requests=writer_access_requests,
    )
    if activation_card is not None:
        cards.append(activation_card)
    if studio.applications.review_queue:
        cards.append(
            OperationsCard(
                kicker="Applications",
                title="Review queue",
                summary="Submitted faces waiting for director movement.",
                count=len(studio.applications.review_queue),
                href="/applications",
                cta="Open applications",
                variant="attention",
                items=tuple(
                    f"{item.character.name} - {'claim conflict' if item.has_claim_conflicts else 'ready'}"
                    for item in studio.applications.review_queue[:4]
                ),
            )
        )
    if conflicted_applications:
        cards.append(
            OperationsCard(
                kicker="Claims",
                title="Claim conflicts",
                summary="Mapped application claims that need resolution before acceptance.",
                count=len(conflicted_applications),
                href="/applications",
                cta="Review conflicts",
                variant="warning",
                items=tuple(
                    f"{item.character.name} - {item.claim_conflict_summary}"
                    for item in conflicted_applications[:4]
                ),
            )
        )
    if casting.active_reserves:
        cards.append(
            OperationsCard(
                kicker="Casting",
                title="Active reserves",
                summary="Held concepts and visual slots directors may need to honor.",
                count=len(casting.active_reserves),
                href="/casting",
                cta="Open casting desk",
                items=tuple(reserve.reserve.title for reserve in casting.active_reserves[:4]),
            )
        )
    if casting.wanted_with_interest:
        cards.append(
            OperationsCard(
                kicker="Wanted",
                title="Hooks with movement",
                summary="Wanted hooks that have interest or reserves attached.",
                count=len(casting.wanted_with_interest),
                href="/casting",
                cta="Review casting movement",
                items=tuple(
                    item.wanted_ad.wanted_ad.title for item in casting.wanted_with_interest[:4]
                ),
            )
        )
    if plotting.wanted_ready_interests:
        cards.append(
            OperationsCard(
                kicker="Backstage",
                title="Ready for scene",
                summary="Wanted handoffs whose plotting rooms are ready to become IC scenes.",
                count=len(plotting.wanted_ready_interests),
                href="/plotting#interest-inbox",
                cta="Open plotting",
                variant="attention",
                items=tuple(
                    item.wanted_ad.wanted_ad.title for item in plotting.wanted_ready_interests[:4]
                ),
            )
        )
    if unread_notification_count:
        cards.append(
            OperationsCard(
                kicker="Inbox",
                title="Staff notifications",
                summary="Unread signals in the current realm.",
                count=unread_notification_count,
                href="/notifications",
                cta="Open inbox",
                variant="attention",
            )
        )
    if studio.navigation_warnings:
        cards.append(
            OperationsCard(
                kicker="Navigation",
                title="Production health",
                summary="Sidebar, board taxonomy, and route-shape notes.",
                count=len(studio.navigation_warnings),
                href="/studio#navigation",
                cta="Open navigation studio",
                variant="warning",
                items=tuple(warning.title for warning in studio.navigation_warnings[:4]),
            )
        )
    if studio.draft_materials:
        cards.append(
            OperationsCard(
                kicker="World",
                title="Draft materials",
                summary="Guidebook, event, and canon materials still in draft.",
                count=len(studio.draft_materials),
                href="/studio#continuity-events",
                cta="Review materials",
                items=tuple(item.material.title for item in studio.draft_materials[:4]),
            )
        )
    if not studio.launch_readiness.is_ready:
        cards.append(
            OperationsCard(
                kicker="Launch",
                title="Community builder checklist",
                summary="Director-owned surfaces a real program needs before writers arrive.",
                count=studio.launch_readiness.missing_required_count,
                href="/studio/launch",
                cta="Open launch room",
                variant="attention",
                items=tuple(
                    f"{item.label} - {item.status_label}"
                    for item in studio.launch_readiness.items
                    if item.is_required and not item.is_complete
                )[:4],
            )
        )
    inspection = (
        operations_inspection(repo, viewer, inspection_config)
        if studio.can_manage and inspection_config is not None
        else None
    )
    return DirectorOperations(
        cards=cards,
        lanes=_operations_lanes(cards),
        shortcuts=_operations_shortcuts(studio, casting, plotting, writer_access_requests),
        ready_applications=ready_applications,
        blocked_applications=blocked_applications,
        can_manage=studio.can_manage,
        inspection=inspection,
    )


def _operations_shortcuts(
    studio: DirectorStudio,
    casting: CastingDesk,
    plotting: PlottingDesk,
    writer_access_requests: Sequence[AccessRequestManagementItemLike],
) -> list[OperationsShortcut]:
    casting_count = len(casting.active_reserves) + len(casting.wanted_with_interest)
    launch_count = (
        0 if studio.launch_readiness.is_ready else studio.launch_readiness.missing_required_count
    )
    return [
        OperationsShortcut(
            "Applications",
            len(studio.applications.review_queue),
            "/applications",
            "Submitted faces and claim-blocked reviews.",
        ),
        OperationsShortcut(
            "Casting",
            casting_count,
            "/casting",
            "Reserves, claims, and wanted movement.",
        ),
        OperationsShortcut(
            "Plotting",
            len(plotting.wanted_ready_interests),
            "/plotting#interest-inbox",
            "Wanted interest ready for scene handoff.",
        ),
        OperationsShortcut(
            "Launch",
            launch_count + len(writer_access_requests),
            "/studio/launch#access-requests" if writer_access_requests else "/studio/launch",
            "Opening checklist gaps and access requests.",
        ),
    ]


def _operations_lanes(cards: list[OperationsCard]) -> list[OperationsLane]:
    if not cards:
        return []
    attention_count = sum(card.count for card in cards if card.variant == "attention")
    warning_count = sum(card.count for card in cards if card.variant == "warning")
    watch_count = sum(
        card.count for card in cards if card.variant not in {"attention", "warning"}
    )
    return [
        OperationsLane(
            label="Needs decision",
            summary="Queues that should move before writers stall.",
            count=attention_count,
            href="#director-operation-signals",
            variant="attention",
        ),
        OperationsLane(
            label="Blocked",
            summary="Claim, navigation, or production conflicts to resolve.",
            count=warning_count,
            href="#director-operation-signals",
            variant="warning",
        ),
        OperationsLane(
            label="Watching",
            summary="Active reserves, drafts, and signals worth keeping warm.",
            count=watch_count,
            href="#director-operation-signals",
            variant="status",
        ),
    ]


def operations_inspection(
    repo: OperationsRepository,
    viewer: ForumView,
    config: OperationsInspectionConfig,
) -> OperationsInspection:
    connection = repo.connection
    database_row = connection.execute("PRAGMA database_list").fetchone()
    migration_row = connection.execute(
        "SELECT MAX(version) AS version FROM schema_migrations"
    ).fetchone()
    user_version = connection.execute("PRAGMA user_version").fetchone()[0]
    community_count = connection.execute("SELECT COUNT(*) AS count FROM communities").fetchone()
    try:
        app_version = version("elbysodic")
    except PackageNotFoundError:
        app_version = "local"
    return OperationsInspection(
        app_version=app_version,
        environment=config.environment,
        secure_cookies=config.secure_cookies,
        database_path=str(database_row["file"] or ":memory:"),
        sqlite_user_version=int(user_version),
        current_schema_version=CURRENT_SCHEMA_VERSION,
        latest_migration_version=int(migration_row["version"] or 0),
        community_count=int(community_count["count"] if community_count is not None else 0),
        launch_status=viewer.community.launch_status,
    )


def _writer_activation_card(
    repo: OperationsRepository,
    viewer: ForumView,
    studio: DirectorStudio,
    casting: CastingDesk,
    plotting: PlottingDesk,
    *,
    writer_invitations: Sequence[InvitationManagementItemLike],
    writer_access_requests: Sequence[AccessRequestManagementItemLike],
) -> OperationsCard | None:
    if not studio.can_manage:
        return None
    pending_invites = [item for item in writer_invitations if item.invitation.status == "pending"]
    active_applications = [
        character
        for character in repo.list_community_characters(viewer.community.id)
        if character.application_status in {"draft", "submitted", "revision_requested"}
    ]
    no_face_members = []
    for membership in repo.list_memberships(viewer.community.id):
        if not membership.is_active:
            continue
        role = repo.get_role(viewer.community.id, membership.role_id)
        if policies.can_manage_applications(membership, role):
            continue
        accepted_faces = [
            character
            for character in repo.list_characters(viewer.community.id, membership.id)
            if character.application_status == "accepted"
        ]
        if not accepted_faces:
            no_face_members.append(membership)
    activation_items: list[str] = []
    if writer_access_requests:
        activation_items.append(f"{len(writer_access_requests)} access request(s)")
        activation_items.extend(
            _access_request_item_label(item.request)
            for item in writer_access_requests[:2]
        )
    if pending_invites:
        activation_items.append(f"{len(pending_invites)} pending invite(s)")
    if no_face_members:
        activation_items.append(f"{len(no_face_members)} accepted member(s) without faces")
    if active_applications:
        activation_items.append(f"{len(active_applications)} draft/review face(s)")
    if casting.wanted_with_interest:
        activation_items.append(
            f"{len(casting.wanted_with_interest)} wanted hook(s) with raised hands"
        )
    if plotting.wanted_ready_interests:
        activation_items.append(f"{len(plotting.wanted_ready_interests)} ready scene handoff(s)")
    if not activation_items:
        return None
    return OperationsCard(
        kicker="Activation",
        title="Writer activation",
        summary="Invites, first faces, applications, raised hands, and first-scene handoffs.",
        count=sum(
            (
                len(pending_invites),
                len(writer_access_requests),
                len(no_face_members),
                len(active_applications),
                len(casting.wanted_with_interest),
                len(plotting.wanted_ready_interests),
            )
        ),
        href="/studio/launch#access-requests" if writer_access_requests else "/studio/launch",
        cta="Open launch room",
        variant="attention",
        items=tuple(activation_items[:4]),
    )


def _access_request_item_label(access_request: CommunityAccessRequest) -> str:
    writer = access_request.display_name or access_request.email
    if access_request.face_concept:
        return f"{writer} - {access_request.face_concept}"
    if access_request.wanted_hook:
        return f"{writer} - {access_request.wanted_hook}"
    return writer


def _unique_applications(
    applications: list[ApplicationCharacterView],
) -> list[ApplicationCharacterView]:
    seen: set[int] = set()
    unique = []
    for item in applications:
        if item.character.id in seen:
            continue
        seen.add(item.character.id)
        unique.append(item)
    return unique
