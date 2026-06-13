"""Director operations read model assembly."""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
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
    NavigationHealthWarning,
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


class RestoreCheckRepository(OperationsRepository, Protocol):
    def list_boards(self, community_id: int) -> Sequence[object]: ...

    def list_materials(
        self,
        community_id: int,
        *,
        status: str | None = "published",
    ) -> Sequence[object]: ...

    def list_threads(
        self,
        community_id: int,
        board_id: int | None = None,
    ) -> Sequence[RestoreCheckRowWithId]: ...

    def list_posts_for_threads(
        self,
        community_id: int,
        thread_ids: list[int],
    ) -> Mapping[int, Sequence[object]]: ...


class RestoreCheckRowWithId(Protocol):
    id: int


RESTORE_CHECK_CORE_TABLES: tuple[tuple[str, str], ...] = (
    ("users", "users"),
    ("communities", "communities"),
    ("memberships", "community_memberships"),
    ("roles", "roles"),
    ("characters", "characters"),
    ("boards", "boards"),
    ("materials", "materials"),
    ("threads", "threads"),
    ("posts", "posts"),
    ("sessions", "user_sessions"),
    ("command submissions", "command_submissions"),
    ("invitations", "community_invitations"),
    ("access requests", "community_access_requests"),
    ("plotting rooms", "plotting_rooms"),
    ("notifications", "notifications"),
)


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
class OperationsParityRow:
    label: str
    count: int
    list_href: str
    first_action_href: str
    action_scope: str
    notification_scope: str
    diagnostic_scope: str


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
    journal_mode: str
    integrity_check: str
    sqlite_user_version: int
    current_schema_version: int
    latest_migration_version: int
    community_count: int
    launch_status: str


@dataclass(frozen=True, slots=True)
class RestoreCheckCount:
    label: str
    table_name: str
    count: int


@dataclass(frozen=True, slots=True)
class RestoreCheckReadback:
    label: str
    status: str
    detail: str


@dataclass(frozen=True, slots=True)
class RestoreCheckResult:
    database_path: str
    opened_read_only: bool
    integrity_check: str
    foreign_key_violations: int
    journal_mode: str
    sqlite_user_version: int
    current_schema_version: int
    latest_migration_version: int
    community_count: int
    core_counts: tuple[RestoreCheckCount, ...]
    readback_checks: tuple[RestoreCheckReadback, ...]
    failures: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return (
            self.integrity_check == "ok"
            and self.foreign_key_violations == 0
            and self.sqlite_user_version == self.current_schema_version
            and self.latest_migration_version == self.current_schema_version
            and self.community_count > 0
            and not self.failures
            and all(check.status == "ok" for check in self.readback_checks)
        )


@dataclass(frozen=True, slots=True)
class RestorePlanStep:
    order: int
    severity: str
    domain: str
    title: str
    detail: str
    risk: str
    human_confirmation_required: bool
    source: str


@dataclass(frozen=True, slots=True)
class RestorePlan:
    database_path: str
    status: str
    steps: tuple[RestorePlanStep, ...]

    @property
    def blockers(self) -> tuple[RestorePlanStep, ...]:
        return tuple(step for step in self.steps if step.severity == "blocker")

    @property
    def human_confirmation_steps(self) -> tuple[RestorePlanStep, ...]:
        return tuple(step for step in self.steps if step.human_confirmation_required)


@dataclass(frozen=True, slots=True)
class DirectorOperations:
    cards: list[OperationsCard]
    lanes: list[OperationsLane]
    shortcuts: list[OperationsShortcut]
    ready_applications: list[ApplicationCharacterView]
    blocked_applications: list[ApplicationCharacterView]
    parity_rows: list[OperationsParityRow]
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
                href=_application_review_href(studio.applications.review_queue[0]),
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
                href=_application_review_href(conflicted_applications[0]),
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
                summary="Sidebar, board map, and route-shape notes.",
                count=len(studio.navigation_warnings),
                href=_navigation_warning_href(studio.navigation_warnings[0]),
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
                href=_first_required_launch_gap_href(studio) or "/studio/launch",
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
        parity_rows=_operations_parity_rows(
            studio,
            casting,
            plotting,
            writer_access_requests,
            unread_notification_count=unread_notification_count,
            inspection=inspection,
        ),
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
    lanes: list[OperationsLane] = []
    lane_specs = (
        (
            "attention",
            "Needs decision",
            "Queues that should move before writers stall.",
        ),
        (
            "warning",
            "Blocked",
            "Claim, navigation, or production conflicts to resolve.",
        ),
        (
            "status",
            "Watching",
            "Active reserves, drafts, and signals worth keeping warm.",
        ),
    )
    for variant, label, summary in lane_specs:
        matching_cards = [
            card
            for card in cards
            if card.variant == variant
            or (variant == "status" and card.variant not in {"attention", "warning"})
        ]
        count = sum(card.count for card in matching_cards)
        if count == 0:
            continue
        lanes.append(
            OperationsLane(
                label=label,
                summary=summary,
                count=count,
                href=matching_cards[0].href,
                variant=variant,
            )
        )
    return lanes


def _operations_parity_rows(
    studio: DirectorStudio,
    casting: CastingDesk,
    plotting: PlottingDesk,
    writer_access_requests: Sequence[AccessRequestManagementItemLike],
    *,
    unread_notification_count: int,
    inspection: OperationsInspection | None,
) -> list[OperationsParityRow]:
    launch_count = (
        0 if studio.launch_readiness.is_ready else studio.launch_readiness.missing_required_count
    )
    launch_href = "/studio/launch#access-requests" if writer_access_requests else "/studio/launch"
    return [
        OperationsParityRow(
            label="Applications",
            count=len(studio.applications.review_queue),
            list_href="/applications",
            first_action_href=(
                _application_review_href(studio.applications.review_queue[0])
                if studio.applications.review_queue
                else "/applications"
            ),
            action_scope="application review capability",
            notification_scope="membership inbox only",
            diagnostic_scope="queue names hidden from non-staff",
        ),
        OperationsParityRow(
            label="Casting",
            count=len(casting.active_reserves) + len(casting.wanted_with_interest),
            list_href="/casting",
            first_action_href="/casting",
            action_scope="casting capability",
            notification_scope="wanted and plotting targets rechecked",
            diagnostic_scope="private notes stay out of Operations cards",
        ),
        OperationsParityRow(
            label="Plotting",
            count=len(plotting.wanted_ready_interests),
            list_href="/plotting#interest-inbox",
            first_action_href="/plotting#interest-inbox",
            action_scope="participant or casting capability",
            notification_scope="room targets rechecked before unread counts",
            diagnostic_scope="room messages stay out of Operations cards",
        ),
        OperationsParityRow(
            label="Launch",
            count=launch_count + len(writer_access_requests),
            list_href=launch_href,
            first_action_href=(
                _writer_activation_href(writer_access_requests)
                if writer_access_requests
                else _first_required_launch_gap_href(studio) or "/studio/launch"
            ),
            action_scope="director launch capability",
            notification_scope="access requests are Studio-only, not inbox-global",
            diagnostic_scope="request notes stay in access-request detail",
        ),
        OperationsParityRow(
            label="Notifications",
            count=unread_notification_count,
            list_href="/notifications",
            first_action_href="/notifications",
            action_scope="membership-scoped inbox",
            notification_scope="own visible unread targets only",
            diagnostic_scope="hidden targets do not affect visible page windows",
        ),
        OperationsParityRow(
            label="Runtime diagnostics",
            count=1 if inspection is not None else 0,
            list_href="/studio/operations#hosted-inspection-heading",
            first_action_href="/studio/operations#hosted-inspection-heading",
            action_scope="director operations capability",
            notification_scope="not notification-backed",
            diagnostic_scope=(
                "visible to managers only" if inspection is not None else "hidden from this viewer"
            ),
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
    journal_mode = connection.execute("PRAGMA journal_mode").fetchone()[0]
    integrity_check = connection.execute("PRAGMA integrity_check").fetchone()[0]
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
        journal_mode=str(journal_mode),
        integrity_check=str(integrity_check),
        sqlite_user_version=int(user_version),
        current_schema_version=CURRENT_SCHEMA_VERSION,
        latest_migration_version=int(migration_row["version"] or 0),
        community_count=int(community_count["count"] if community_count is not None else 0),
        launch_status=viewer.community.launch_status,
    )


def restore_check_database(path: Path) -> RestoreCheckResult:
    """Open a candidate SQLite backup read-only and verify service readback."""

    if str(path) == ":memory:":
        raise ValueError("restore check requires a filesystem database path")
    if not path.exists():
        raise FileNotFoundError(path)
    resolved = path.resolve()
    connection = sqlite3.connect(f"{resolved.as_uri()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA query_only = ON")
        return _restore_check_connection(connection, resolved)
    finally:
        connection.close()


def format_restore_check_report(result: RestoreCheckResult) -> str:
    status = "ok" if result.ok else "failed"
    lines = [
        f"restore-check {status}",
        f"database: {result.database_path}",
        f"read-only: {'yes' if result.opened_read_only else 'no'}",
        f"integrity_check: {result.integrity_check}",
        f"foreign_key_violations: {result.foreign_key_violations}",
        f"journal_mode: {result.journal_mode}",
        (
            "schema: "
            f"user_version={result.sqlite_user_version} "
            f"current={result.current_schema_version} "
            f"latest_migration={result.latest_migration_version}"
        ),
        f"communities: {result.community_count}",
        "counts:",
    ]
    lines.extend(f"- {count.label}: {count.count}" for count in result.core_counts)
    lines.append("readback:")
    lines.extend(
        f"- {check.label}: {check.status} ({check.detail})" for check in result.readback_checks
    )
    if result.failures:
        lines.append("failures:")
        lines.extend(f"- {failure}" for failure in result.failures)
    return "\n".join(lines) + "\n"


def restore_plan_from_check(result: RestoreCheckResult) -> RestorePlan:
    """Build a deterministic, read-only operator plan from restore-check output."""

    steps: list[RestorePlanStep] = []
    _append_restore_plan_preflight_steps(steps, result)
    _append_restore_plan_readback_steps(steps, result)
    _append_restore_plan_workflow_steps(steps, result)
    _append_restore_plan_failure_steps(steps, result)
    _append_restore_plan_confirmation_steps(steps, result)
    blockers = [step for step in steps if step.severity == "blocker"]
    status = "ready" if result.ok and not blockers else "blocked" if blockers else "review"
    return RestorePlan(
        database_path=result.database_path,
        status=status,
        steps=tuple(sorted(steps, key=lambda step: (step.order, step.domain, step.title))),
    )


def format_restore_plan_report(plan: RestorePlan) -> str:
    lines = [
        f"restore-plan {plan.status}",
        f"database: {plan.database_path}",
        f"steps: {len(plan.steps)}",
        f"blockers: {len(plan.blockers)}",
        f"human_confirmation: {len(plan.human_confirmation_steps)}",
    ]
    for step in plan.steps:
        confirmation = "human-confirmation" if step.human_confirmation_required else "read-only"
        lines.append(
            f"- [{step.severity}] {step.order} {step.domain}: {step.title} ({confirmation})"
        )
        lines.append(f"  detail: {step.detail}")
        lines.append(f"  risk: {step.risk}")
        lines.append(f"  source: {step.source}")
    return "\n".join(lines) + "\n"


def _restore_check_connection(
    connection: sqlite3.Connection,
    path: Path,
) -> RestoreCheckResult:
    failures: list[str] = []
    table_names = _restore_check_table_names(connection)
    integrity_check = _restore_check_integrity(connection, failures)
    foreign_key_violations = _restore_check_foreign_keys(connection, failures)
    journal_mode = _restore_check_text_pragma(connection, "journal_mode", failures)
    sqlite_user_version = _restore_check_int_pragma(connection, "user_version", failures)
    latest_migration_version = _restore_check_latest_migration(connection, failures)
    core_counts = _restore_check_counts(connection, table_names, failures)
    community_count = next(
        (count.count for count in core_counts if count.table_name == "communities"),
        0,
    )
    if integrity_check != "ok":
        failures.append(f"integrity_check failed: {integrity_check}")
    if foreign_key_violations != 0:
        failures.append(f"foreign_key_check reported {foreign_key_violations} violation(s)")
    if sqlite_user_version != CURRENT_SCHEMA_VERSION:
        failures.append(
            f"schema user_version mismatch: {sqlite_user_version} != {CURRENT_SCHEMA_VERSION}"
        )
    if latest_migration_version != CURRENT_SCHEMA_VERSION:
        failures.append(
            f"migration ledger mismatch: {latest_migration_version} != {CURRENT_SCHEMA_VERSION}"
        )
    if community_count == 0:
        failures.append("no communities found")
    readback_checks = _restore_check_readback(connection, table_names)
    failures.extend(
        f"service readback failed: {check.label}"
        for check in readback_checks
        if check.status != "ok"
    )
    return RestoreCheckResult(
        database_path=str(path),
        opened_read_only=True,
        integrity_check=integrity_check,
        foreign_key_violations=foreign_key_violations,
        journal_mode=journal_mode,
        sqlite_user_version=sqlite_user_version,
        current_schema_version=CURRENT_SCHEMA_VERSION,
        latest_migration_version=latest_migration_version,
        community_count=community_count,
        core_counts=tuple(core_counts),
        readback_checks=tuple(readback_checks),
        failures=tuple(failures),
    )


def _append_restore_plan_preflight_steps(
    steps: list[RestorePlanStep],
    result: RestoreCheckResult,
) -> None:
    _append_step(
        steps,
        10,
        "ok" if result.opened_read_only else "blocker",
        "operations",
        "Open candidate database read-only",
        "Restore planning must inspect the backup without changing it.",
        "A writable inspection can mutate or lock a candidate backup during an incident.",
        not result.opened_read_only,
        "restore_check.opened_read_only",
    )
    _append_step(
        steps,
        20,
        "ok" if result.integrity_check == "ok" else "blocker",
        "storage",
        "Verify SQLite integrity",
        f"PRAGMA integrity_check returned {result.integrity_check}.",
        "A failed integrity check can make later row-level conclusions unreliable.",
        result.integrity_check != "ok",
        "restore_check.integrity_check",
    )
    _append_step(
        steps,
        30,
        "ok" if result.foreign_key_violations == 0 else "blocker",
        "storage",
        "Verify foreign-key integrity",
        f"PRAGMA foreign_key_check reported {result.foreign_key_violations} violation(s).",
        "Foreign-key violations can attach objects to missing or wrong tenant roots.",
        result.foreign_key_violations != 0,
        "restore_check.foreign_key_violations",
    )
    schema_ok = (
        result.sqlite_user_version == result.current_schema_version
        and result.latest_migration_version == result.current_schema_version
    )
    _append_step(
        steps,
        40,
        "ok" if schema_ok else "blocker",
        "schema",
        "Verify schema and migration ledger",
        (
            f"user_version={result.sqlite_user_version}; "
            f"latest_migration={result.latest_migration_version}; "
            f"current={result.current_schema_version}."
        ),
        "Schema drift can make restore checks read the wrong columns or miss repaired rows.",
        not schema_ok,
        "restore_check.schema_versions",
    )
    _append_step(
        steps,
        50,
        "ok" if result.community_count > 0 else "blocker",
        "community",
        "Verify tenant roots",
        f"Candidate contains {result.community_count} community row(s).",
        "A restore without tenant roots cannot safely recover memberships, faces, or story rows.",
        result.community_count == 0,
        "restore_check.community_count",
    )


def _append_restore_plan_readback_steps(
    steps: list[RestorePlanStep],
    result: RestoreCheckResult,
) -> None:
    for offset, check in enumerate(result.readback_checks, start=1):
        _append_step(
            steps,
            60 + offset,
            "ok" if check.status == "ok" else "blocker",
            _restore_plan_domain_for_text(check.label),
            f"Read back {check.label}",
            check.detail,
            "Service readback failure means operators should not trust raw table counts alone.",
            check.status != "ok",
            f"restore_check.readback.{check.label}",
        )


def _append_restore_plan_workflow_steps(
    steps: list[RestorePlanStep],
    result: RestoreCheckResult,
) -> None:
    counts = {count.table_name: count.count for count in result.core_counts}
    workflow_domains = (
        ("auth posture", "user_sessions", "Review session rows before reuse"),
        ("commands", "command_submissions", "Review command submission reservations"),
        ("invitations", "community_invitations", "Review invitation token posture"),
        ("access requests", "community_access_requests", "Review access-request staff context"),
        ("plotting", "plotting_rooms", "Review plotting room continuity"),
        ("notification", "notifications", "Review notification targets"),
    )
    for offset, (domain, table_name, title) in enumerate(workflow_domains, start=1):
        count = counts.get(table_name)
        severity = "info" if count is not None else "warning"
        detail = (
            f"{table_name} has {count} row(s) in the candidate."
            if count is not None
            else f"{table_name} was not counted by restore-check."
        )
        _append_step(
            steps,
            80 + offset,
            severity,
            domain,
            title,
            detail,
            "Workflow rows can carry private notes, tokens, redirects, or stale command state.",
            False,
            f"restore_check.counts.{table_name}",
        )


def _append_restore_plan_failure_steps(
    steps: list[RestorePlanStep],
    result: RestoreCheckResult,
) -> None:
    for offset, failure in enumerate(result.failures, start=1):
        _append_step(
            steps,
            120 + offset,
            "blocker",
            _restore_plan_domain_for_text(failure),
            "Resolve restore-check failure",
            failure,
            "Restore-check failures must be understood before any import, repair, or cutover.",
            True,
            "restore_check.failures",
        )


def _append_restore_plan_confirmation_steps(
    steps: list[RestorePlanStep],
    result: RestoreCheckResult,
) -> None:
    dependency_steps = (
        (
            "claims/reserves",
            "Plan claim and reserve ownership review",
            "Check claim and reserve ownership before any repair that touches first-face or casting state.",
        ),
        (
            "wanted",
            "Plan wanted hook and interest review",
            "Check wanted availability, private interest notes, and plotting handoffs before repair.",
        ),
        (
            "continuity",
            "Plan continuity source review",
            "Continuity source links are not a public restore surface yet; inspect source visibility before repair.",
        ),
        (
            "export",
            "Plan export privacy review",
            "Compare export expectations before restoring data that may omit sessions, token hashes, or private notes.",
        ),
        (
            "auth posture",
            "Plan auth and session cutover review",
            "Decide whether sessions, demo-mode posture, and invite-only access should survive the restore.",
        ),
    )
    severity = "warning" if result.ok else "blocker"
    for offset, (domain, title, detail) in enumerate(dependency_steps, start=1):
        _append_step(
            steps,
            200 + offset,
            severity,
            domain,
            title,
            detail,
            "These domains can expose private, staff, token, or cross-community state after cutover.",
            True,
            "restore_plan.human_confirmation",
        )


def _append_step(
    steps: list[RestorePlanStep],
    order: int,
    severity: str,
    domain: str,
    title: str,
    detail: str,
    risk: str,
    human_confirmation_required: bool,
    source: str,
) -> None:
    steps.append(
        RestorePlanStep(
            order=order,
            severity=severity,
            domain=domain,
            title=title,
            detail=detail,
            risk=risk,
            human_confirmation_required=human_confirmation_required,
            source=source,
        )
    )


def _restore_plan_domain_for_text(text: str) -> str:
    normalized = text.lower()
    if "communit" in normalized:
        return "community"
    if "membership" in normalized or "member" in normalized:
        return "membership"
    if "character" in normalized or "face" in normalized:
        return "character"
    if "claim" in normalized or "reserve" in normalized:
        return "claims/reserves"
    if "wanted" in normalized:
        return "wanted"
    if "notification" in normalized:
        return "notification"
    if "continuity" in normalized or "source" in normalized:
        return "continuity"
    if "export" in normalized:
        return "export"
    if "session" in normalized or "auth" in normalized or "user" in normalized:
        return "auth posture"
    if "schema" in normalized or "migration" in normalized or "table" in normalized:
        return "schema"
    if "foreign" in normalized or "integrity" in normalized:
        return "storage"
    return "operations"


def _restore_check_table_names(connection: sqlite3.Connection) -> set[str]:
    rows = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        """
    ).fetchall()
    return {str(row["name"]) for row in rows}


def _restore_check_integrity(
    connection: sqlite3.Connection,
    failures: list[str],
) -> str:
    try:
        row = connection.execute("PRAGMA integrity_check").fetchone()
    except sqlite3.Error as exc:
        failures.append(f"integrity_check unavailable: {_restore_check_error(exc)}")
        return "unavailable"
    return str(row[0] if row is not None else "unavailable")


def _restore_check_foreign_keys(
    connection: sqlite3.Connection,
    failures: list[str],
) -> int:
    try:
        return len(connection.execute("PRAGMA foreign_key_check").fetchall())
    except sqlite3.Error as exc:
        failures.append(f"foreign_key_check unavailable: {_restore_check_error(exc)}")
        return -1


def _restore_check_text_pragma(
    connection: sqlite3.Connection,
    pragma_name: str,
    failures: list[str],
) -> str:
    try:
        row = connection.execute(f"PRAGMA {pragma_name}").fetchone()
    except sqlite3.Error as exc:
        failures.append(f"{pragma_name} unavailable: {_restore_check_error(exc)}")
        return "unavailable"
    return str(row[0] if row is not None else "unavailable")


def _restore_check_int_pragma(
    connection: sqlite3.Connection,
    pragma_name: str,
    failures: list[str],
) -> int:
    try:
        row = connection.execute(f"PRAGMA {pragma_name}").fetchone()
    except sqlite3.Error as exc:
        failures.append(f"{pragma_name} unavailable: {_restore_check_error(exc)}")
        return -1
    return int(row[0] if row is not None else -1)


def _restore_check_latest_migration(
    connection: sqlite3.Connection,
    failures: list[str],
) -> int:
    try:
        row = connection.execute("SELECT MAX(version) AS version FROM schema_migrations").fetchone()
    except sqlite3.Error as exc:
        failures.append(f"migration ledger unavailable: {_restore_check_error(exc)}")
        return 0
    return int(row["version"] or 0)


def _restore_check_counts(
    connection: sqlite3.Connection,
    table_names: set[str],
    failures: list[str],
) -> list[RestoreCheckCount]:
    counts: list[RestoreCheckCount] = []
    for label, table_name in RESTORE_CHECK_CORE_TABLES:
        if table_name not in table_names:
            failures.append(f"missing table: {table_name}")
            continue
        row = connection.execute(
            f"SELECT COUNT(*) AS count FROM {table_name}"  # noqa: S608 - fixed constants.
        ).fetchone()
        counts.append(
            RestoreCheckCount(
                label=label,
                table_name=table_name,
                count=int(row["count"] if row is not None else 0),
            )
        )
    return counts


def _restore_check_readback(
    connection: sqlite3.Connection,
    table_names: set[str],
) -> list[RestoreCheckReadback]:
    if "communities" not in table_names:
        return [RestoreCheckReadback("communities", "failed", "communities table missing")]
    from elbysodic.db import ForumRepository

    repo = ForumRepository(connection)
    checks: list[RestoreCheckReadback] = []
    try:
        communities = repo.list_communities()
    except (LookupError, sqlite3.Error) as exc:
        return [RestoreCheckReadback("communities", "failed", _restore_check_error(exc))]
    if not communities:
        return [RestoreCheckReadback("communities", "failed", "no community rows")]
    community = communities[0]
    checks.append(
        RestoreCheckReadback(
            "communities",
            "ok",
            f"{len(communities)} community row(s), first id {community.id}",
        )
    )
    checks.append(_restore_check_membership_readback(repo, community.id))
    checks.append(_restore_check_world_readback(repo, community.id))
    checks.append(_restore_check_thread_readback(repo, community.id))
    workflow_tables = (
        "user_sessions",
        "command_submissions",
        "community_invitations",
        "community_access_requests",
        "plotting_rooms",
        "notifications",
    )
    workflow_total = sum(
        count.count
        for count in _restore_check_counts(connection, table_names, [])
        if count.table_name in workflow_tables
    )
    checks.append(
        RestoreCheckReadback(
            "workflow rows",
            "ok",
            f"{workflow_total} counted session/workflow row(s)",
        )
    )
    return checks


def _restore_check_membership_readback(
    repo: OperationsRepository,
    community_id: int,
) -> RestoreCheckReadback:
    try:
        memberships = repo.list_memberships(community_id)
    except (LookupError, sqlite3.Error) as exc:
        return RestoreCheckReadback("memberships", "failed", _restore_check_error(exc))
    return RestoreCheckReadback("memberships", "ok", f"{len(memberships)} membership row(s)")


def _restore_check_world_readback(
    repo: RestoreCheckRepository,
    community_id: int,
) -> RestoreCheckReadback:
    try:
        boards = repo.list_boards(community_id)
        materials = repo.list_materials(community_id, status=None)
    except (LookupError, sqlite3.Error) as exc:
        return RestoreCheckReadback("world rows", "failed", _restore_check_error(exc))
    return RestoreCheckReadback(
        "world rows",
        "ok",
        f"{len(boards)} board row(s), {len(materials)} material row(s)",
    )


def _restore_check_thread_readback(
    repo: RestoreCheckRepository,
    community_id: int,
) -> RestoreCheckReadback:
    try:
        threads = repo.list_threads(community_id)
        posts_by_thread = repo.list_posts_for_threads(
            community_id,
            [thread.id for thread in threads[:20]],
        )
    except (LookupError, sqlite3.Error) as exc:
        return RestoreCheckReadback("thread rows", "failed", _restore_check_error(exc))
    post_count = sum(len(posts) for posts in posts_by_thread.values())
    return RestoreCheckReadback(
        "thread rows",
        "ok",
        f"{len(threads)} thread row(s), {post_count} sampled post row(s)",
    )


def _restore_check_error(exc: BaseException) -> str:
    return f"{exc.__class__.__name__}: {exc}"


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
            _access_request_item_label(item.request) for item in writer_access_requests[:2]
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
        href=_writer_activation_href(writer_access_requests),
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


def _writer_activation_href(
    writer_access_requests: Sequence[AccessRequestManagementItemLike],
) -> str:
    if writer_access_requests:
        return f"/studio/access-requests/{writer_access_requests[0].request.id}"
    return "/studio/launch"


def _application_review_href(application: ApplicationCharacterView) -> str:
    return f"/applications/{application.character.slug}"


def _navigation_warning_href(warning: NavigationHealthWarning) -> str:
    if warning.href:
        return warning.href
    return "/studio/structure#navigation"


def _first_required_launch_gap_href(studio: DirectorStudio) -> str | None:
    for item in studio.launch_readiness.items:
        if item.is_required and not item.is_complete:
            return item.href
    return None


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
