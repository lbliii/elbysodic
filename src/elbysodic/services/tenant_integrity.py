"""Read-only tenant integrity audit reports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from elbysodic.db.repositories.identity import (
    MembershipRoleIntegrityIssue,
    SessionIdentityIntegrityIssue,
    TenantPairIntegrityIssue,
)
from elbysodic.services import policies
from elbysodic.services.read_models import ForumView

type TenantIntegritySeverity = Literal["critical", "high", "medium"]


@dataclass(frozen=True, slots=True)
class TenantIntegrityFinding:
    code: str
    severity: TenantIntegritySeverity
    domain: str
    table_name: str
    row_id: int
    community_id: int | None
    reason: str
    remediation_hint: str


@dataclass(frozen=True, slots=True)
class TenantIntegrityCommunitySummary:
    community_id: int | None
    critical_count: int
    high_count: int
    medium_count: int


@dataclass(frozen=True, slots=True)
class TenantIntegrityAuditReport:
    findings: tuple[TenantIntegrityFinding, ...]
    community_summaries: tuple[TenantIntegrityCommunitySummary, ...]

    @property
    def ok(self) -> bool:
        return not self.findings

    @property
    def severe_count(self) -> int:
        return sum(1 for finding in self.findings if finding.severity in {"critical", "high"})


class TenantIntegrityAuditRepository(Protocol):
    def list_membership_role_integrity_issues(self) -> list[MembershipRoleIntegrityIssue]: ...

    def list_session_identity_integrity_issues(self) -> list[SessionIdentityIntegrityIssue]: ...

    def list_tenant_pair_integrity_issues(self) -> list[TenantPairIntegrityIssue]: ...


def tenant_integrity_audit(
    repo: TenantIntegrityAuditRepository,
    *,
    community_id: int | None = None,
) -> TenantIntegrityAuditReport:
    findings = tuple(
        sorted(
            _tenant_integrity_findings(repo, community_id=community_id),
            key=lambda finding: (
                _severity_sort_key(finding.severity),
                finding.community_id or 0,
                finding.table_name,
                finding.row_id,
                finding.code,
            ),
        )
    )
    return TenantIntegrityAuditReport(
        findings=findings,
        community_summaries=_community_summaries(findings),
    )


def tenant_integrity_audit_for_viewer(
    repo: TenantIntegrityAuditRepository,
    viewer: ForumView,
) -> TenantIntegrityAuditReport:
    if not policies.can_manage_world(viewer.membership, viewer.role):
        raise PermissionError("director access is required to read tenant integrity audits")
    return tenant_integrity_audit(repo, community_id=viewer.community.id)


def format_tenant_integrity_audit_report(report: TenantIntegrityAuditReport) -> str:
    status = "ok" if report.ok else "failed"
    lines = [f"tenant-integrity-audit {status}", f"findings: {len(report.findings)}"]
    for summary in report.community_summaries:
        community_label = (
            f"community {summary.community_id}"
            if summary.community_id is not None
            else "global/session"
        )
        lines.append(
            f"{community_label}: critical={summary.critical_count} "
            f"high={summary.high_count} medium={summary.medium_count}"
        )
    for finding in report.findings:
        community_label = (
            f"community={finding.community_id}"
            if finding.community_id is not None
            else "community=global/session"
        )
        lines.append(
            f"{finding.severity} {finding.code} {community_label} "
            f"table={finding.table_name} row={finding.row_id}: {finding.reason}; "
            f"remediation={finding.remediation_hint}"
        )
    return "\n".join(lines)


def _tenant_integrity_findings(
    repo: TenantIntegrityAuditRepository,
    *,
    community_id: int | None,
) -> list[TenantIntegrityFinding]:
    findings: list[TenantIntegrityFinding] = []
    findings.extend(
        _membership_role_finding(issue)
        for issue in repo.list_membership_role_integrity_issues()
        if _matches_community(issue.community_id, community_id)
    )
    findings.extend(
        _session_identity_finding(issue)
        for issue in repo.list_session_identity_integrity_issues()
        if _matches_community(issue.selected_community_id, community_id)
    )
    findings.extend(
        _tenant_pair_finding(issue)
        for issue in repo.list_tenant_pair_integrity_issues()
        if _matches_community(issue.community_id, community_id)
    )
    return findings


def _membership_role_finding(issue: MembershipRoleIntegrityIssue) -> TenantIntegrityFinding:
    return TenantIntegrityFinding(
        code="membership_role_missing",
        severity="high",
        domain="membership_roles",
        table_name="community_memberships",
        row_id=issue.membership_id,
        community_id=issue.community_id,
        reason="membership role does not resolve inside its community",
        remediation_hint="assign a valid same-community role before allowing membership actions",
    )


def _session_identity_finding(issue: SessionIdentityIntegrityIssue) -> TenantIntegrityFinding:
    return TenantIntegrityFinding(
        code="session_identity_drift",
        severity="high",
        domain="sessions",
        table_name="user_sessions",
        row_id=issue.session_id,
        community_id=issue.selected_community_id,
        reason=issue.reason,
        remediation_hint="clear the selected membership or reselect an active same-user membership",
    )


def _tenant_pair_finding(issue: TenantPairIntegrityIssue) -> TenantIntegrityFinding:
    return TenantIntegrityFinding(
        code="tenant_pair_invalid",
        severity=_tenant_pair_severity(issue),
        domain=_tenant_pair_domain(issue.table_name),
        table_name=issue.table_name,
        row_id=issue.row_id,
        community_id=issue.community_id,
        reason=issue.reason,
        remediation_hint=_tenant_pair_remediation(issue.table_name),
    )


def _tenant_pair_severity(issue: TenantPairIntegrityIssue) -> TenantIntegritySeverity:
    if issue.table_name in {
        "threads",
        "posts",
        "post_revisions",
        "notifications",
        "plotting_rooms",
        "plotting_room_participants",
        "plotting_room_messages",
        "community_access_requests",
        "community_access_request_events",
        "character_applications",
        "character_application_events",
    }:
        return "critical"
    return "high"


def _tenant_pair_domain(table_name: str) -> str:
    if table_name in {"threads", "posts", "post_revisions", "thread_participants"}:
        return "scenes"
    if table_name.startswith("plotting_room"):
        return "plotting"
    if table_name.startswith("community_access_request") or table_name == "community_invitations":
        return "access"
    if table_name.startswith("character_application") or table_name in {
        "character_claims",
        "character_reserves",
    }:
        return "casting"
    if table_name == "notifications":
        return "notifications"
    return "tenant_pairs"


def _tenant_pair_remediation(table_name: str) -> str:
    if table_name == "notifications":
        return "drop or retarget the notification after verifying target ownership"
    if table_name in {"threads", "posts", "post_revisions", "thread_participants"}:
        return "repair scene authorship or move the row into the correct community"
    if table_name.startswith("plotting_room"):
        return "repair plotting ownership, source, target, or participant references"
    if table_name.startswith("community_access_request"):
        return "repair access-request ownership before reviewing or inviting"
    if table_name == "community_invitations":
        return "revoke and recreate the invitation in the correct community"
    return "repair or remove the cross-community reference before production use"


def _community_summaries(
    findings: tuple[TenantIntegrityFinding, ...],
) -> tuple[TenantIntegrityCommunitySummary, ...]:
    community_ids = sorted(
        {finding.community_id for finding in findings}, key=lambda value: value or 0
    )
    return tuple(
        TenantIntegrityCommunitySummary(
            community_id=community_id,
            critical_count=sum(
                1
                for finding in findings
                if finding.community_id == community_id and finding.severity == "critical"
            ),
            high_count=sum(
                1
                for finding in findings
                if finding.community_id == community_id and finding.severity == "high"
            ),
            medium_count=sum(
                1
                for finding in findings
                if finding.community_id == community_id and finding.severity == "medium"
            ),
        )
        for community_id in community_ids
    )


def _matches_community(found_community_id: int | None, requested_community_id: int | None) -> bool:
    return requested_community_id is None or found_community_id == requested_community_id


def _severity_sort_key(severity: TenantIntegritySeverity) -> int:
    match severity:
        case "critical":
            return 0
        case "high":
            return 1
        case "medium":
            return 2
