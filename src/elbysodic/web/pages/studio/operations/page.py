"""Daily director operations console."""

from __future__ import annotations

from dataclasses import dataclass

from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.services.read_models import (
    ApplicationCharacterView,
    CastingDesk,
    DirectorStudio,
    PlottingDesk,
)
from elbysodic.web.state import get_services


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
    )
    return Page(
        "studio/operations/page.html",
        "page_content",
        page_block_name="page_root",
        current_path=request.url,
        viewer=services.viewer(),
        operations=operations,
    )


def _director_operations(
    studio: DirectorStudio,
    casting: CastingDesk,
    plotting: PlottingDesk,
    unread_notification_count: int,
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
    cards = [
        OperationsCard(
            kicker="Applications",
            title="Review queue",
            summary="Submitted faces waiting for director movement.",
            count=len(studio.applications.review_queue),
            href="/applications",
            cta="Open applications",
            variant="attention" if studio.applications.review_queue else "status",
            items=tuple(
                f"{item.character.name} - {'claim conflict' if item.has_claim_conflicts else 'ready'}"
                for item in studio.applications.review_queue[:4]
            ),
        ),
        OperationsCard(
            kicker="Claims",
            title="Claim conflicts",
            summary="Mapped application claims that need resolution before acceptance.",
            count=len(conflicted_applications),
            href="/applications",
            cta="Review conflicts",
            variant="warning" if conflicted_applications else "success",
            items=tuple(
                f"{item.character.name} - {item.claim_conflict_summary}"
                for item in conflicted_applications[:4]
            ),
        ),
        OperationsCard(
            kicker="Casting",
            title="Active reserves",
            summary="Held concepts and visual slots directors may need to honor.",
            count=len(casting.active_reserves),
            href="/casting",
            cta="Open casting desk",
            items=tuple(reserve.reserve.title for reserve in casting.active_reserves[:4]),
        ),
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
        ),
        OperationsCard(
            kicker="Backstage",
            title="Ready for scene",
            summary="Wanted handoffs whose plotting rooms are ready to become IC scenes.",
            count=len(plotting.wanted_ready_interests),
            href="/plotting#interest-inbox",
            cta="Open plotting",
            variant="attention" if plotting.wanted_ready_interests else "status",
            items=tuple(
                item.wanted_ad.wanted_ad.title for item in plotting.wanted_ready_interests[:4]
            ),
        ),
        OperationsCard(
            kicker="Inbox",
            title="Staff notifications",
            summary="Unread signals in the current realm.",
            count=unread_notification_count,
            href="/notifications",
            cta="Open inbox",
            variant="attention" if unread_notification_count else "success",
        ),
        OperationsCard(
            kicker="Navigation",
            title="Production health",
            summary="Sidebar, board taxonomy, and route-shape notes.",
            count=len(studio.navigation_warnings),
            href="/studio#navigation",
            cta="Open navigation studio",
            variant="warning" if studio.navigation_warnings else "success",
            items=tuple(warning.title for warning in studio.navigation_warnings[:4]),
        ),
        OperationsCard(
            kicker="World",
            title="Draft materials",
            summary="Guidebook, event, and canon materials still in draft.",
            count=len(studio.draft_materials),
            href="/studio#continuity-events",
            cta="Review materials",
            items=tuple(item.material.title for item in studio.draft_materials[:4]),
        ),
        OperationsCard(
            kicker="Blueprints",
            title="Dry-run intake",
            summary="Validate director starter packets before any hydration work is allowed.",
            count=0,
            href="/studio/intake#program-blueprint-preview",
            cta="Open intake",
            variant="status",
            items=(
                "Apply stays gated behind a service-layer hydration plan.",
                "Preview checks counts, slugs, references, and safe theme tokens.",
            ),
        ),
        OperationsCard(
            kicker="Production",
            title="Release smoke",
            summary="Core flows to prove before the Railway URL is shared broadly.",
            count=7,
            href="/network",
            cta="Open network home",
            variant="attention",
            items=(
                "Log in, enter a realm, and switch memberships.",
                "Read a scene, review wanted movement, and check notifications.",
                "Complete one CSRF-protected write, then log out.",
            ),
        ),
        OperationsCard(
            kicker="Launch",
            title="Community builder checklist",
            summary="Director-owned surfaces a real program needs before writers arrive.",
            count=studio.launch_readiness.missing_required_count,
            href="/studio/launch",
            cta="Open launch room",
            variant="success" if studio.launch_readiness.is_ready else "attention",
            items=tuple(
                f"{item.label} - {item.status_label}" for item in studio.launch_readiness.items[:4]
            ),
        ),
    ]
    return DirectorOperations(
        cards=cards,
        ready_applications=ready_applications,
        blocked_applications=blocked_applications,
        can_manage=studio.can_manage,
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
