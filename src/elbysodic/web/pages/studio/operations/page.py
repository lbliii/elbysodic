"""Daily director operations console."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version

from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.db.migrations import CURRENT_SCHEMA_VERSION
from elbysodic.services import AppServices
from elbysodic.services.read_models import (
    ApplicationCharacterView,
    CastingDesk,
    DirectorStudio,
    PlottingDesk,
)
from elbysodic.web.state import get_services, get_web_security_config


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
class DirectorOperations:
    cards: list[OperationsCard]
    ready_applications: list[ApplicationCharacterView]
    blocked_applications: list[ApplicationCharacterView]
    can_manage: bool
    inspection: OperationsInspection | None


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


def get(request: Request) -> Page:
    services = get_services(request)
    studio = services.director_studio()
    casting = services.casting_desk()
    plotting = services.plotting_desk()
    operations = _director_operations(
        studio,
        casting,
        plotting,
        services.viewer().unread_notification_count,
        inspection=_operations_inspection(services) if studio.can_manage else None,
    )
    return Page.mounted(
        "studio/operations/page.html",
        current_path=request.url,
        viewer=services.viewer(),
        operations=operations,
    )


def _director_operations(
    studio: DirectorStudio,
    casting: CastingDesk,
    plotting: PlottingDesk,
    unread_notification_count: int,
    *,
    inspection: OperationsInspection | None,
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
    return DirectorOperations(
        cards=cards,
        ready_applications=ready_applications,
        blocked_applications=blocked_applications,
        can_manage=studio.can_manage,
        inspection=inspection,
    )


def _operations_inspection(services: AppServices) -> OperationsInspection:
    connection = services.repo.connection
    security = get_web_security_config()
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
        environment=security.env,
        secure_cookies=security.secure_cookies,
        database_path=str(database_row["file"] or ":memory:"),
        sqlite_user_version=int(user_version),
        current_schema_version=CURRENT_SCHEMA_VERSION,
        latest_migration_version=int(migration_row["version"] or 0),
        community_count=int(community_count["count"] if community_count is not None else 0),
        launch_status=services.viewer().community.launch_status,
    )


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
